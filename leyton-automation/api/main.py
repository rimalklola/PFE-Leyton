import os
import sys
import uuid
import subprocess
import time
from concurrent.futures import ThreadPoolExecutor
from typing import Optional

_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_SERVICES_ROOT = os.path.join(_PROJECT_ROOT, "services")

if _SERVICES_ROOT not in sys.path:
    sys.path.insert(0, _SERVICES_ROOT)

from fastapi import FastAPI, HTTPException, Query, Request, UploadFile, File, Form
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from prometheus_fastapi_instrumentator import Instrumentator
from prometheus_client import Counter, Histogram, Gauge
from shared.registry import get_runs, get_last_run, DB_PATH
import sqlite3

app = FastAPI(
    title="Leyton Automation API",
    description="Orchestration layer for all Leyton Belgium automation services",
    version="1.0.0",
)

# ── Templates ─────────────────────────────────────────────────────────────────
_TEMPLATES_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "templates")
templates = Jinja2Templates(directory=_TEMPLATES_DIR)

# ── Prometheus custom metrics ──────────────────────────────────────────────────
service_runs_total = Counter(
    "leyton_service_runs_total",
    "Total number of service executions",
    ["service", "status"],
)
service_duration_seconds = Histogram(
    "leyton_service_duration_seconds",
    "Service execution duration in seconds",
    ["service"],
    buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0, 60.0, 120.0, 300.0],
)
services_currently_running = Gauge(
    "leyton_services_currently_running",
    "Number of services currently executing",
)
Instrumentator().instrument(app).expose(app, include_in_schema=False)
# ──────────────────────────────────────────────────────────────────────────────

executor = ThreadPoolExecutor(max_workers=4)

VALID_SERVICES = [
    "folder-creator",
    "timesheet-consolidator",
    "handover-generator",
    "web-scraper",
]

SERVICE_META = {
    "folder-creator": {
        "title": "Folder Creator",
        "description": "Upload a ZIP of client documents and get back a fully organised mission folder hierarchy.",
        "icon": "fas fa-folder-open",
        "output": "Folder structure + metadata.json",
        "input_type": "file",
        "accept": ".zip",
    },
    "timesheet-consolidator": {
        "title": "Timesheet Consolidator",
        "description": "Upload one or more PDF or Excel timesheets. Get back a single consolidated pivot table of R&D hours per employee per month.",
        "icon": "fas fa-table",
        "output": "Consolidated Excel (.xlsx)",
        "input_type": "files",
        "accept": ".xlsx,.xls,.pdf",
    },
    "handover-generator": {
        "title": "Handover Generator",
        "description": "Fill in the mission details and get a structured handover document ready to pass to the incoming consultant.",
        "icon": "fas fa-handshake",
        "output": "Handover document (.xlsx)",
        "input_type": "form",
        "fields": [
            {"name": "client_name",          "label": "Client Name",           "type": "text",     "required": True},
            {"name": "outgoing_consultant",  "label": "Outgoing Consultant",   "type": "text",     "required": True},
            {"name": "incoming_consultant",  "label": "Incoming Consultant",   "type": "text",     "required": True},
            {"name": "mission_type",         "label": "Mission Type",          "type": "select",   "required": True,
             "options": ["CIR", "BELSPO", "CII", "JEI", "Other"]},
            {"name": "mission_start",        "label": "Mission Start Date",    "type": "date",     "required": False},
            {"name": "active_projects",      "label": "Active Projects",       "type": "textarea", "required": False,
             "placeholder": "Project 1 — status\nProject 2 — status"},
            {"name": "key_contacts",         "label": "Key Client Contacts",   "type": "textarea", "required": False,
             "placeholder": "Name, role, email"},
            {"name": "pending_tasks",        "label": "Pending Tasks",         "type": "textarea", "required": False,
             "placeholder": "Task 1\nTask 2"},
            {"name": "notes",                "label": "Important Notes",       "type": "textarea", "required": False,
             "placeholder": "Anything the incoming consultant must know"},
        ],
    },
    "web-scraper": {
        "title": "Web Scraper",
        "description": "Paste a list of URLs (one per line) and get back a compiled Excel file with the content of all those pages.",
        "icon": "fas fa-globe",
        "output": "Scraped data (.xlsx)",
        "input_type": "urls",
    },
}

_run_status: dict = {}


def _execute_service(service_name: str, run_id: str, env_extra: dict = None):
    service_dir = os.path.join(_SERVICES_ROOT, service_name)
    started_at = time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime())
    _run_status[run_id] = {
        "run_id": run_id,
        "service": service_name,
        "status": "running",
        "started_at": started_at,
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
            timeout=300,
            env=env,
        )
        final_status = "completed" if result.returncode == 0 else "failed"
        if result.returncode != 0:
            _run_status[run_id]["error"] = (result.stderr or "Non-zero exit code")[:500]
    except subprocess.TimeoutExpired:
        final_status = "timeout"
        _run_status[run_id]["error"] = "Service timed out after 300s"
    except Exception as exc:
        final_status = "failed"
        _run_status[run_id]["error"] = str(exc)
    finally:
        duration = time.time() - t0
        services_currently_running.dec()
        service_runs_total.labels(service=service_name, status=final_status).inc()
        service_duration_seconds.labels(service=service_name).observe(duration)

    _run_status[run_id]["status"] = final_status
    _run_status[run_id]["finished_at"] = time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime())


# ══════════════════════════════════════════════════════════════════════════════
# WEB UI ROUTES
# ══════════════════════════════════════════════════════════════════════════════

@app.get("/", response_class=HTMLResponse, include_in_schema=False)
def ui_dashboard(request: Request):
    runs = get_runs()
    total = len(runs)
    success = sum(1 for r in runs if r.get("status") == "success")
    failed = sum(1 for r in runs if r.get("status") == "failed")
    rate = round((success / total * 100)) if total > 0 else 0

    services = []
    for svc in VALID_SERVICES:
        last = get_last_run(svc)
        services.append({
            "name": svc,
            "last_run_status": last["status"] if last else None,
        })

    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "active_page": "dashboard",
        "total_runs": total,
        "success_rate": rate,
        "failed_runs": failed,
        "services_count": len(VALID_SERVICES),
        "recent_runs": runs[:10],
        "services": services,
    })


@app.get("/ui/services", response_class=HTMLResponse, include_in_schema=False)
def ui_services(request: Request):
    import json
    services = []
    for key in VALID_SERVICES:
        meta = SERVICE_META[key]
        last = get_last_run(key)
        services.append({
            "key": key,
            "title": meta["title"],
            "description": meta["description"],
            "icon": meta["icon"],
            "output": meta["output"],
            "last_status": last["status"] if last else None,
        })
    service_meta_json = json.dumps({
        k: {
            "title":       v["title"],
            "description": v["description"],
            "input_type":  v["input_type"],
            "accept":      v.get("accept", ""),
            "fields":      v.get("fields", []),
        }
        for k, v in SERVICE_META.items()
    })
    return templates.TemplateResponse("services.html", {
        "request": request,
        "active_page": "services",
        "services": services,
        "service_meta_json": service_meta_json,
    })


@app.get("/ui/history", response_class=HTMLResponse, include_in_schema=False)
def ui_history(
    request: Request,
    service: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
):
    runs = get_runs(service_name=service)
    if status:
        runs = [r for r in runs if r.get("status") == status]
    return templates.TemplateResponse("history.html", {
        "request": request,
        "active_page": "history",
        "runs": runs,
        "service_names": VALID_SERVICES,
        "selected_service": service or "",
        "selected_status": status or "",
    })


# ══════════════════════════════════════════════════════════════════════════════
# API ROUTES
# ══════════════════════════════════════════════════════════════════════════════

@app.post("/run/{service_name}", summary="Trigger a service run (no input)")
def trigger_service(service_name: str):
    if service_name not in VALID_SERVICES:
        raise HTTPException(status_code=404, detail=f"Unknown service '{service_name}'.")
    run_id = str(uuid.uuid4())
    executor.submit(_execute_service, service_name, run_id)
    return {"run_id": run_id, "service": service_name, "status": "started"}


@app.post("/run/{service_name}/upload", summary="Trigger a service with file upload(s)")
async def trigger_service_upload(service_name: str, files: list[UploadFile] = File(...)):
    if service_name not in VALID_SERVICES:
        raise HTTPException(status_code=404, detail=f"Unknown service '{service_name}'.")

    upload_dir = os.path.join(_SERVICES_ROOT, service_name, "uploads")
    os.makedirs(upload_dir, exist_ok=True)

    saved_paths = []
    for f in files:
        dest = os.path.join(upload_dir, f.filename)
        with open(dest, "wb") as out:
            out.write(await f.read())
        saved_paths.append(dest)

    import json
    run_id = str(uuid.uuid4())
    env_extra = {"INPUT_FILES": json.dumps(saved_paths)}
    executor.submit(_execute_service, service_name, run_id, env_extra)
    return {"run_id": run_id, "service": service_name, "status": "started",
            "files_received": len(saved_paths)}


@app.post("/run/{service_name}/form", summary="Trigger a service with form parameters")
async def trigger_service_form(service_name: str, request: Request):
    if service_name not in VALID_SERVICES:
        raise HTTPException(status_code=404, detail=f"Unknown service '{service_name}'.")

    form_data = await request.form()
    env_extra = {f"PARAM_{k.upper()}": str(v) for k, v in form_data.items()}

    run_id = str(uuid.uuid4())
    executor.submit(_execute_service, service_name, run_id, env_extra)
    return {"run_id": run_id, "service": service_name, "status": "started"}


@app.get("/runs/{run_id}", summary="Get status of a specific run")
def get_run(run_id: str):
    if run_id in _run_status:
        return _run_status[run_id]
    raise HTTPException(status_code=404, detail=f"Run '{run_id}' not found")


@app.get("/runs", summary="List run history from registry")
def list_runs(
    service: Optional[str] = Query(None),
    client_id: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=500),
):
    runs = get_runs(service_name=service, client_id=client_id)
    return {"runs": runs[:limit], "total": len(runs)}


@app.get("/services", summary="List all services with last run info")
def list_services():
    result = []
    for svc in VALID_SERVICES:
        last = get_last_run(svc)
        result.append({
            "name": svc,
            "last_run_at": last["ran_at"] if last else None,
            "last_run_status": last["status"] if last else None,
            "last_run_duration_ms": last["duration_ms"] if last else None,
        })
    return {"services": result, "count": len(result)}


@app.get("/download/{service_name}", summary="Download latest output file")
def download_output(service_name: str):
    if service_name not in VALID_SERVICES:
        raise HTTPException(status_code=404, detail="Unknown service")

    output_dir = os.path.join(_SERVICES_ROOT, service_name, "output")
    if not os.path.exists(output_dir):
        raise HTTPException(status_code=404, detail="No output directory found")

    files = [
        f for f in os.listdir(output_dir)
        if os.path.isfile(os.path.join(output_dir, f))
        and not f.startswith(".")
        and f.endswith((".xlsx", ".json", ".pdf", ".csv"))
    ]
    if not files:
        raise HTTPException(status_code=404, detail="No output file found for this service")

    latest = max(files, key=lambda f: os.path.getmtime(os.path.join(output_dir, f)))
    filepath = os.path.join(output_dir, latest)
    return FileResponse(path=filepath, filename=latest)


@app.get("/health", summary="Health check")
def health():
    conn = sqlite3.connect(DB_PATH)
    total_runs = conn.execute("SELECT COUNT(*) FROM runs").fetchone()[0]
    conn.close()
    return {
        "status": "ok",
        "services_count": len(VALID_SERVICES),
        "total_runs": total_runs,
    }
