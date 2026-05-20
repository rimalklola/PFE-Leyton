import os
import sys
import uuid
import json
import subprocess
import time
import sqlite3
from concurrent.futures import ThreadPoolExecutor
from typing import Optional

# ---------------------------------------------------------------------------
# Path bootstrap
# In Docker: __file__ = /app/main.py  →  dirname twice = /  (wrong).
# SERVICES_ROOT env var is set in the Dockerfile to /app/services.
# Locally it falls back to the standard project layout.
# ---------------------------------------------------------------------------
_SERVICES_ROOT = os.environ.get(
    "SERVICES_ROOT",
    os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "services"),
)
if _SERVICES_ROOT not in sys.path:
    sys.path.insert(0, _SERVICES_ROOT)

from fastapi import FastAPI, HTTPException, Query, Request, UploadFile, File, BackgroundTasks
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from prometheus_fastapi_instrumentator import Instrumentator
from prometheus_client import Counter, Histogram, Gauge
from shared.registry import get_runs, get_last_run, DB_PATH

# ---------------------------------------------------------------------------
# Service discovery
# The platform discovers services by scanning SERVICES_ROOT for service.json
# manifests. No hardcoded list — adding a new service requires only:
#   1. Create services/<name>/service.json
#   2. Create services/<name>/main.py
#   3. Create services/<name>/Dockerfile
# ---------------------------------------------------------------------------

# Maximum allowed upload size: 20 MB
MAX_UPLOAD_BYTES = 20 * 1024 * 1024
ALLOWED_EXTENSIONS = {".xlsx", ".xls", ".pdf", ".zip"}


def _load_service_catalog(services_root: str) -> dict:
    """
    Scan services_root for service.json manifests and return a dict
    keyed by service name. Unknown or malformed manifests are skipped.
    """
    catalog = {}
    if not os.path.isdir(services_root):
        return catalog
    for entry in sorted(os.listdir(services_root)):
        manifest_path = os.path.join(services_root, entry, "service.json")
        main_path = os.path.join(services_root, entry, "main.py")
        if not os.path.isfile(manifest_path) or not os.path.isfile(main_path):
            continue
        try:
            with open(manifest_path) as f:
                manifest = json.load(f)
            if "name" not in manifest:
                continue
            catalog[manifest["name"]] = manifest
        except (json.JSONDecodeError, OSError):
            continue
    return catalog


SERVICE_CATALOG: dict = _load_service_catalog(_SERVICES_ROOT)
VALID_SERVICES: list = list(SERVICE_CATALOG.keys())

# ---------------------------------------------------------------------------
# FastAPI app
# ---------------------------------------------------------------------------
app = FastAPI(
    title="Leyton Automation Platform",
    description=(
        "Internal automation platform for LEYTON Belgium. "
        "Services are discovered automatically from their service.json manifests."
    ),
    version="2.0.0",
)

_TEMPLATES_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "templates")
templates = Jinja2Templates(directory=_TEMPLATES_DIR)

# ---------------------------------------------------------------------------
# Prometheus metrics
# ---------------------------------------------------------------------------
service_runs_total = Counter(
    "leyton_service_runs_total",
    "Total number of service executions",
    ["service", "status"],
)
service_duration_seconds = Histogram(
    "leyton_service_duration_seconds",
    "Service execution duration in seconds",
    ["service"],
    buckets=[0.5, 1.0, 2.0, 5.0, 10.0, 30.0, 60.0, 120.0, 300.0],
)
services_currently_running = Gauge(
    "leyton_services_currently_running",
    "Number of services currently executing",
)
service_error_total = Counter(
    "leyton_service_error_total",
    "Total number of failed service executions",
    ["service"],
)
Instrumentator().instrument(app).expose(app, include_in_schema=False)

# ---------------------------------------------------------------------------
# In-memory run state
# Tracks live status for active/recent runs (complements the SQLite registry).
# ---------------------------------------------------------------------------
_run_status: dict = {}
executor = ThreadPoolExecutor(max_workers=4)


# ---------------------------------------------------------------------------
# Core execution logic
# ---------------------------------------------------------------------------

def _execute_service(service_name: str, run_id: str, env_extra: dict = None):
    """
    Run a service as an isolated subprocess.
    - Uses the service manifest timeout (default 300s).
    - Emits Prometheus metrics on completion.
    - Stores structured status in _run_status for polling.
    """
    manifest = SERVICE_CATALOG.get(service_name, {})
    timeout = manifest.get("timeout", 300)
    service_dir = os.path.join(_SERVICES_ROOT, service_name)

    _run_status[run_id] = {
        "run_id":     run_id,
        "service":    service_name,
        "status":     "running",
        "started_at": time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime()),
        "error":      None,
    }

    services_currently_running.inc()
    t0 = time.time()
    final_status = "failed"

    env = os.environ.copy()
    if env_extra:
        env.update(env_extra)

    try:
        result = subprocess.run(
            [sys.executable, "main.py"],
            cwd=service_dir,
            capture_output=True,
            text=True,
            timeout=timeout,
            env=env,
        )
        if result.returncode == 0:
            final_status = "completed"
        else:
            final_status = "failed"
            _run_status[run_id]["error"] = (result.stderr or "Non-zero exit code")[:500]

    except subprocess.TimeoutExpired:
        final_status = "timeout"
        _run_status[run_id]["error"] = f"Service timed out after {timeout}s"
    except Exception as exc:
        final_status = "failed"
        _run_status[run_id]["error"] = str(exc)
    finally:
        duration = time.time() - t0
        services_currently_running.dec()
        service_runs_total.labels(service=service_name, status=final_status).inc()
        service_duration_seconds.labels(service=service_name).observe(duration)
        if final_status != "completed":
            service_error_total.labels(service=service_name).inc()

    _run_status[run_id]["status"]      = final_status
    _run_status[run_id]["duration_ms"] = int((time.time() - t0) * 1000)
    _run_status[run_id]["finished_at"] = time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime())


def _validate_upload(file: UploadFile, content: bytes):
    """Validate file size and extension before saving."""
    ext = os.path.splitext(file.filename or "")[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"File type '{ext}' not allowed. Accepted: {', '.join(ALLOWED_EXTENSIONS)}",
        )
    if len(content) > MAX_UPLOAD_BYTES:
        raise HTTPException(
            status_code=413,
            detail=f"File '{file.filename}' exceeds the 20 MB size limit.",
        )


# ===========================================================================
# WEB UI ROUTES
# ===========================================================================

@app.get("/", response_class=HTMLResponse, include_in_schema=False)
def ui_dashboard(request: Request):
    runs  = get_runs()
    total   = len(runs)
    success = sum(1 for r in runs if r.get("status") == "success")
    failed  = sum(1 for r in runs if r.get("status") == "failed")
    rate    = round(success / total * 100) if total > 0 else 0

    services = [
        {"name": name, "last_run_status": (get_last_run(name) or {}).get("status")}
        for name in VALID_SERVICES
    ]
    return templates.TemplateResponse("dashboard.html", {
        "request":        request,
        "active_page":    "dashboard",
        "total_runs":     total,
        "success_rate":   rate,
        "failed_runs":    failed,
        "services_count": len(VALID_SERVICES),
        "recent_runs":    runs[:10],
        "services":       services,
    })


@app.get("/ui/services", response_class=HTMLResponse, include_in_schema=False)
def ui_services(request: Request):
    services = []
    for name, manifest in SERVICE_CATALOG.items():
        last = get_last_run(name)
        services.append({
            "key":         name,
            "title":       manifest.get("name", name).replace("-", " ").title(),
            "description": manifest.get("description", ""),
            "icon":        manifest.get("icon", "fas fa-cog"),
            "output":      manifest.get("output", {}).get("description", ""),
            "last_status": (last or {}).get("status"),
        })

    service_meta_json = json.dumps({
        name: {
            "title":       m.get("name", name).replace("-", " ").title(),
            "description": m.get("description", ""),
            "input_type":  m.get("input_type", "form"),
            "accept":      m.get("accept", ""),
            "fields":      m.get("fields", []),
        }
        for name, m in SERVICE_CATALOG.items()
    })
    return templates.TemplateResponse("services.html", {
        "request":           request,
        "active_page":       "services",
        "services":          services,
        "service_meta_json": service_meta_json,
    })


@app.get("/ui/history", response_class=HTMLResponse, include_in_schema=False)
def ui_history(
    request: Request,
    service: Optional[str] = Query(None),
    status:  Optional[str] = Query(None),
):
    runs = get_runs(service_name=service)
    if status:
        runs = [r for r in runs if r.get("status") == status]
    return templates.TemplateResponse("history.html", {
        "request":          request,
        "active_page":      "history",
        "runs":             runs,
        "service_names":    VALID_SERVICES,
        "selected_service": service or "",
        "selected_status":  status or "",
    })


# ===========================================================================
# API ROUTES
# ===========================================================================

@app.post("/run/{service_name}", summary="Trigger a service run (no input)")
def trigger_service(service_name: str, background_tasks: BackgroundTasks):
    if service_name not in VALID_SERVICES:
        raise HTTPException(status_code=404, detail=f"Unknown service '{service_name}'.")
    run_id = str(uuid.uuid4())
    background_tasks.add_task(_execute_service, service_name, run_id)
    return {"run_id": run_id, "service": service_name, "status": "queued"}


@app.post("/run/{service_name}/upload", summary="Trigger a service with file upload(s)")
async def trigger_service_upload(
    service_name: str,
    background_tasks: BackgroundTasks,
    files: list[UploadFile] = File(...),
):
    if service_name not in VALID_SERVICES:
        raise HTTPException(status_code=404, detail=f"Unknown service '{service_name}'.")

    upload_dir = os.path.join(_SERVICES_ROOT, service_name, "uploads")
    os.makedirs(upload_dir, exist_ok=True)

    saved_paths = []
    for f in files:
        content = await f.read()
        _validate_upload(f, content)
        dest = os.path.join(upload_dir, f.filename)
        with open(dest, "wb") as out:
            out.write(content)
        saved_paths.append(dest)

    run_id    = str(uuid.uuid4())
    env_extra = {"INPUT_FILES": json.dumps(saved_paths)}
    background_tasks.add_task(_execute_service, service_name, run_id, env_extra)
    return {"run_id": run_id, "service": service_name, "status": "queued",
            "files_received": len(saved_paths)}


@app.post("/run/{service_name}/form", summary="Trigger a service with form parameters")
async def trigger_service_form(
    service_name: str,
    background_tasks: BackgroundTasks,
    request: Request,
):
    if service_name not in VALID_SERVICES:
        raise HTTPException(status_code=404, detail=f"Unknown service '{service_name}'.")

    form_data = await request.form()
    env_extra = {f"PARAM_{k.upper()}": str(v) for k, v in form_data.items()}

    run_id = str(uuid.uuid4())
    background_tasks.add_task(_execute_service, service_name, run_id, env_extra)
    return {"run_id": run_id, "service": service_name, "status": "queued"}


@app.get("/runs/{run_id}", summary="Get status of a specific run")
def get_run_status(run_id: str):
    if run_id in _run_status:
        return _run_status[run_id]
    raise HTTPException(status_code=404, detail=f"Run '{run_id}' not found.")


@app.get("/runs", summary="List run history from registry")
def list_runs(
    service: Optional[str] = Query(None),
    limit:   int           = Query(50, ge=1, le=500),
):
    runs = get_runs(service_name=service)
    return {"runs": runs[:limit], "total": len(runs)}


@app.get("/services", summary="Service catalog — all registered services")
def list_services():
    result = []
    for name, manifest in SERVICE_CATALOG.items():
        last = get_last_run(name)
        result.append({
            "name":                 name,
            "version":              manifest.get("version", "1.0.0"),
            "description":          manifest.get("description", ""),
            "tags":                 manifest.get("tags", []),
            "input_type":           manifest.get("input_type", "form"),
            "timeout":              manifest.get("timeout", 300),
            "last_run_at":          (last or {}).get("ran_at"),
            "last_run_status":      (last or {}).get("status"),
            "last_run_duration_ms": (last or {}).get("duration_ms"),
        })
    return {"services": result, "count": len(result)}


@app.get("/download/{service_name}", summary="Download latest output file")
def download_output(service_name: str):
    if service_name not in VALID_SERVICES:
        raise HTTPException(status_code=404, detail="Unknown service.")

    output_dir = os.path.join(_SERVICES_ROOT, service_name, "output")
    if not os.path.isdir(output_dir):
        raise HTTPException(status_code=404, detail="No output directory found.")

    files = [
        f for f in os.listdir(output_dir)
        if os.path.isfile(os.path.join(output_dir, f))
        and not f.startswith(".")
        and f.endswith((".xlsx", ".json", ".pdf", ".csv"))
    ]
    if not files:
        raise HTTPException(status_code=404, detail="No output file found for this service.")

    latest   = max(files, key=lambda f: os.path.getmtime(os.path.join(output_dir, f)))
    filepath = os.path.join(output_dir, latest)
    return FileResponse(path=filepath, filename=latest)


@app.get("/health", summary="Liveness check")
def health():
    conn       = sqlite3.connect(DB_PATH)
    total_runs = conn.execute("SELECT COUNT(*) FROM runs").fetchone()[0]
    conn.close()
    return {
        "status":          "ok",
        "services_count":  len(VALID_SERVICES),
        "total_runs":      total_runs,
        "platform_version": app.version,
    }


@app.get("/ready", summary="Readiness check")
def ready():
    """
    Readiness differs from liveness: it checks that the platform is
    fully operational — services directory reachable, DB writable,
    at least one service registered.
    """
    issues = []

    if not os.path.isdir(_SERVICES_ROOT):
        issues.append("Services directory not found.")

    if not VALID_SERVICES:
        issues.append("No services discovered from manifests.")

    try:
        conn = sqlite3.connect(DB_PATH)
        conn.execute("SELECT 1 FROM runs LIMIT 1")
        conn.close()
    except Exception as exc:
        issues.append(f"Database not reachable: {exc}")

    if issues:
        raise HTTPException(status_code=503, detail={"ready": False, "issues": issues})

    return {
        "ready":            True,
        "services":         VALID_SERVICES,
        "services_root":    _SERVICES_ROOT,
    }
