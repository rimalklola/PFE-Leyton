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

from fastapi import FastAPI, HTTPException, Query
from prometheus_fastapi_instrumentator import Instrumentator
from prometheus_client import Counter, Histogram, Gauge
from shared.registry import get_runs, get_last_run, DB_PATH
import sqlite3

app = FastAPI(
    title="Leyton Automation API",
    description="Orchestration layer for all Leyton Belgium automation services",
    version="1.0.0",
)

# ── Prometheus custom metrics ──────────────────────────────────────────────────
# Counts every service execution, labelled by service name and outcome.
service_runs_total = Counter(
    "leyton_service_runs_total",
    "Total number of service executions",
    ["service", "status"],
)

# Records how long each service takes (seconds). Used for P50/P95/P99 charts.
service_duration_seconds = Histogram(
    "leyton_service_duration_seconds",
    "Service execution duration in seconds",
    ["service"],
    buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0, 60.0, 120.0, 300.0],
)

# Live count of services currently executing (gauge goes up on start, down on finish).
services_currently_running = Gauge(
    "leyton_services_currently_running",
    "Number of services currently executing",
)

# Auto-instruments all HTTP endpoints: request count, duration, status codes.
Instrumentator().instrument(app).expose(app, include_in_schema=False)
# ──────────────────────────────────────────────────────────────────────────────

executor = ThreadPoolExecutor(max_workers=4)

VALID_SERVICES = [
    "folder-creator",
    "timesheet-prefill",
    "belspo-extractor",
    "handover-generator",
    "galileo-reporter",
    "web-scraper",
    "pdf-timesheet-extractor",
    "client-onboarding-generator",
]

_run_status: dict = {}


def _execute_service(service_name: str, run_id: str):
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

    try:
        result = subprocess.run(
            [sys.executable, "main.py"],
            cwd=service_dir,
            capture_output=True,
            text=True,
            timeout=300,
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


@app.post("/run/{service_name}", summary="Trigger a service run")
def trigger_service(service_name: str):
    if service_name not in VALID_SERVICES:
        raise HTTPException(
            status_code=404,
            detail=f"Unknown service '{service_name}'. Valid: {VALID_SERVICES}",
        )
    run_id = str(uuid.uuid4())
    executor.submit(_execute_service, service_name, run_id)
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
