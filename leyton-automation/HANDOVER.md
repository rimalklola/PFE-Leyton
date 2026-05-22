# Project Handover — Leyton Automation Platform

## Context

PFE (final year project) at INPT, internship at LEYTON Morocco.
Thesis theme: DevOps. Soutenance in approximately 2-3 weeks.
Student: Rim Lakhiri (rlakhiri@leyton.com)
GitHub: https://github.com/rimalklola/PFE-Leyton

---

## What the project is

An internal automation platform for LEYTON Belgium consultants.
Four services that automate repetitive document tasks, wrapped in a
full DevOps infrastructure (CI/CD, observability, IaC, containerization).

The thesis contribution is NOT the individual services — they are the use case.
The contribution is the platform engineering infrastructure that makes
any automation operationally scalable and production-ready.

One-sentence pitch for the jury:
"I designed an internal automation platform where each service is a
self-describing, independently deployable unit — with a defined contract,
health status, and operational metrics — that any consultant can trigger
through a self-service web interface, with full execution traceability."

---

## Repository structure

```
leyton-automation/
├── api/
│   ├── main.py                  # FastAPI orchestration layer (v2.0.0)
│   ├── requirements.txt         # API + all service deps (openpyxl, pdfplumber, etc.)
│   ├── Dockerfile               # Build context: project root (.)
│   └── templates/               # Jinja2 Bootstrap 5 web UI
│       ├── base.html
│       ├── dashboard.html
│       ├── services.html
│       └── history.html
├── services/
│   ├── shared/
│   │   ├── registry.py          # SQLite run registry (log_run, get_runs, get_last_run)
│   │   └── logger.py            # Structured JSON logger (ServiceLogger)
│   ├── folder-creator/
│   │   ├── service.json         # Service manifest (name, version, fields, timeout, etc.)
│   │   ├── main.py
│   │   ├── mock_data.py
│   │   ├── test_folder_creator.py
│   │   ├── requirements.txt
│   │   └── Dockerfile
│   ├── timesheet-consolidator/
│   │   ├── service.json
│   │   ├── main.py              # Handles Excel + PDF, alias-based column detection
│   │   ├── test_timesheet_consolidator.py  # 22 tests, 95% coverage
│   │   ├── requirements.txt
│   │   └── Dockerfile
│   ├── handover-generator/
│   │   ├── service.json
│   │   ├── main.py
│   │   ├── mock_data.py
│   │   ├── test_handover_generator.py
│   │   ├── requirements.txt
│   │   └── Dockerfile
│   └── web-scraper/
│       ├── service.json
│       ├── main.py
│       ├── mock_data.py
│       ├── test_web_scraper.py
│       ├── requirements.txt
│       └── Dockerfile
├── monitoring/
│   ├── prometheus/prometheus.yml
│   ├── grafana/
│   │   ├── provisioning/datasources/   # Prometheus + Loki auto-configured
│   │   ├── provisioning/dashboards/
│   │   └── dashboards/leyton-platform.json
│   ├── loki/loki-config.yml
│   └── promtail/promtail.yml
├── .github/workflows/ci-cd.yml  # 6-stage pipeline
├── docker-compose.yml
├── Makefile
└── runs.db                      # SQLite registry (gitignored in production)
```

---

## The 4 services

### folder-creator
- Input: form (client_name, consultant, mission_type, year, contact)
- Output: folder hierarchy at services/folder-creator/output/clients/<name>/
- Reads: PARAM_CLIENT_NAME, PARAM_CONSULTANT, PARAM_MISSION_TYPE, PARAM_YEAR
- Demo mode: uses MOCK_CONTRACTS[:1] if no PARAM_CLIENT_NAME set
- Coverage: 86%

### timesheet-consolidator
- Input: one or more PDF or Excel files (uploaded via multipart)
- Output: Consolidated_Timesheets_YYYYMMDD_HHMMSS.xlsx
- Key feature: alias-based column detection (FR + EN column names),
  wide-format detection (one column per month), multi-sheet scanning,
  header row search up to row 10
- Reads: INPUT_FILES env var (JSON list of file paths set by API)
- Demo mode: generates sample_timesheet.xlsx fixture if no files provided
- Coverage: 95%

### handover-generator
- Input: form (client_name, outgoing/incoming consultant, mission_type, etc.)
- Output: Handover_<ClientName>_YYYYMMDD.xlsx
- Reads: PARAM_CLIENT_NAME, PARAM_OUTGOING_CONSULTANT, PARAM_INCOMING_CONSULTANT,
         PARAM_MISSION_TYPE, PARAM_MISSION_START, PARAM_KEY_CONTACTS,
         PARAM_PENDING_TASKS, PARAM_NOTES
- Demo mode: uses MOCK_HANDOVER_DATA if no PARAM_CLIENT_NAME set
- Coverage: 94%

### web-scraper
- Input: newline-separated URLs (textarea form)
- Output: Belspo_Technical_Profile_YYYYMMDD.xlsx (2 sheets: profiles + draft text)
- Reads: PARAM_URLS env var
- Demo mode: uses MOCK_CLIENTS if PARAM_URLS not set
- Coverage: 83%

---

## API architecture (api/main.py)

### Service discovery
Services are discovered at startup by scanning SERVICES_ROOT for service.json
manifests. No hardcoded list. Adding a new service = create folder with
service.json + main.py + Dockerfile, zero API changes needed.

```python
SERVICE_CATALOG = _load_service_catalog(_SERVICES_ROOT)
VALID_SERVICES  = list(SERVICE_CATALOG.keys())
```

### Key env vars (set in Dockerfile)
- SERVICES_ROOT=/app/services   — overrides path calculation in Docker
- PYTHONPATH=/app/services       — makes shared/ importable

### Execution model
Services run as isolated subprocesses via FastAPI BackgroundTasks.
Timeout comes from the service's manifest (default 300s).
Status tracked in _run_status dict (in-memory, keyed by run_id UUID).

### Endpoints
| Method | Path | Description |
|--------|------|-------------|
| GET | / | Dashboard UI |
| GET | /ui/services | Services UI with forms |
| GET | /ui/history | Run history UI |
| GET | /health | Liveness check |
| GET | /ready | Readiness check (services dir + DB + catalog) |
| GET | /services | Service catalog (manifest metadata) |
| GET | /runs | Run history from SQLite |
| GET | /runs/{run_id} | Live run status (polling) |
| POST | /run/{name} | Trigger with no input |
| POST | /run/{name}/upload | Trigger with file upload(s) |
| POST | /run/{name}/form | Trigger with form params |
| GET | /download/{name} | Download latest output file |
| GET | /metrics | Prometheus metrics |
| GET | /docs | Swagger UI |

### Upload security
- Extension allowlist: .xlsx, .xls, .pdf, .zip
- Max file size: 20 MB
- Validated in _validate_upload() before saving to disk

### Prometheus metrics
- leyton_service_runs_total{service, status}        — Counter
- leyton_service_duration_seconds{service}           — Histogram
- leyton_services_currently_running                  — Gauge
- leyton_service_error_total{service}                — Counter (new)
- Standard FastAPI/HTTP metrics via prometheus_fastapi_instrumentator

---

## CI/CD pipeline (.github/workflows/ci-cd.yml)

6 stages, matrix across 4 services:

1. **lint** — flake8, max-line-length=120, E402 ignored
2. **security** — Bandit (static analysis) + pip-audit (dependency CVEs)
3. **test** — pytest with --cov-fail-under=80 (coverage gate)
4. **build** — Docker build + push to GHCR (ghcr.io/rimalklola/leyton-*)
5. **deploy** — Railway CLI deploy (push to main only)
6. **pipeline-passed** — single required status check for branch protection

Coverage results:
- folder-creator: 86%
- timesheet-consolidator: 95%
- handover-generator: 94%
- web-scraper: 83%

---

## Local URLs (docker compose up --build -d)

| Service | URL | Credentials |
|---------|-----|-------------|
| Web UI | http://localhost:8000 | — |
| API Docs | http://localhost:8000/docs | — |
| Prometheus | http://localhost:9090 | — |
| Grafana | http://localhost:3001 | admin / leyton2026 |
| Loki | http://localhost:3100 | — |

---

## Common commands

```bash
make dev          # Start API locally with hot-reload
make up           # Start full Docker stack
make down         # Stop Docker stack
make test         # Run all tests with coverage
make lint         # Lint all services
make catalog      # Show discovered services (calls /services)
make health       # Check /health endpoint
make history      # Last 20 runs from SQLite
```

---

## Shared layer (services/shared/)

### registry.py
- DB_PATH: leyton-automation/runs.db (SQLite)
- log_run(service, status, output_file, duration_ms, error_message, client_id)
- get_runs(service_name=None, client_id=None) → list of dicts
- get_last_run(service_name) → dict or None

### logger.py
- ServiceLogger(service_name) — structured JSON to stdout
- Methods: log.info(), log.warning(), log.error()
- Each log line includes: timestamp, service, level, message, correlation_id, **kwargs

---

## What was intentionally NOT built

- Redis / Celery — ThreadPoolExecutor + BackgroundTasks is adequate at this scale
- PostgreSQL — SQLite is sufficient, migration risk not worth it for PFE
- JWT authentication — internal tool, single office
- Kubernetes — Railway + docker-compose is the deployment story
- AI/LLM features — out of scope, kept deliberately
- Circuit breakers — overkill for 4 services

---

## What still needs to be done

1. **Non-root Docker user** — add USER nobody to each Dockerfile (security hardening)
2. **SLO metrics** — error rate and p95 latency Prometheus recording rules
3. **Grafana dashboard** — configure leyton-platform.json with actual panels
4. **Chapter 5 of the report** — implementation chapter with screenshots
5. **General conclusion** — perspectives section referencing the spec improvements
6. **docker-compose.yml version line removed** — already done locally, push pending

---

## Report status (LaTeX on Overleaf)

- Chapter 1 (Introduction): done
- Chapter 2 (State of the art): done
- Chapter 3 (Operational Diagnostic): done — 6 consultant interviews, FR/NFR tables
- Chapter 4 (Architecture and Design): done — TikZ diagrams, tech stack tables
- Chapter 5 (Implementation): NOT DONE — needs screenshots of live platform
- General Conclusion: NOT DONE
- Abstract: done in FR/EN/AR

---

## Key framing for the soutenance

The project is NOT about complex automation logic.
The project IS about industrializing internal operational automations
through DevOps and platform engineering practices.

Jury question: "Why not just use n8n or Power Automate?"
Answer: "Those tools don't support custom Python logic against heterogeneous
client documents, cannot be version-controlled with a coverage gate,
and have no structured metrics emission. The platform is extensible by design —
adding a new service requires zero changes to the orchestration layer."

Jury question: "Why only 4 services?"
Answer: "The services are a proof of concept. The platform is the contribution.
A 5th service can be added in an afternoon: service.json + main.py + Dockerfile,
and the pipeline handles everything else automatically."
