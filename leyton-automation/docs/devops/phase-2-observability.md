# Phase 2 — Observability Stack

## Philosophy

Running software is not the same as understanding it. A service can be deployed, passing
all tests, and still be silently failing for 80% of users. Without observability, the
only way to find out is when a user complains.

Observability is the practice of instrumenting a system so that its internal state can
be inferred from its external outputs. It rests on **three pillars**:

| Pillar | Question it answers | Tool used |
|--------|--------------------|-----------| 
| **Metrics** | *How is the system performing?* | Prometheus |
| **Logs** | *What happened and when?* | Loki + Promtail |
| **Dashboards** | *Is anything wrong right now?* | Grafana |

Without metrics you are blind. Without logs you cannot diagnose. Without dashboards
you cannot act fast enough. All three are required.

---

## Architecture

```
  ┌─────────────────────────────────────────────────────────────┐
  │                        GRAFANA :3000                        │
  │          (dashboards, visualisation, alerting UI)           │
  └──────────────────────┬──────────────────┬───────────────────┘
                         │                  │
              reads metrics            reads logs
                         │                  │
             ┌───────────▼──┐    ┌──────────▼──────────┐
             │  PROMETHEUS   │    │        LOKI          │
             │  :9090        │    │        :3100         │
             │  (time-series │    │  (log aggregation)   │
             │   metrics DB) │    │                      │
             └───────────────┘    └─────────┬────────────┘
                     ▲                      ▲
               scrapes /metrics         pushed by
               every 15s                    │
                     │             ┌────────┴────────┐
             ┌───────┴─────┐       │    PROMTAIL      │
             │  FASTAPI     │       │  (log shipper)  │
             │  API :8000   │       │  reads Docker   │
             │  /metrics    │       │  container logs │
             └─────────────┘       └─────────────────┘
```

---

## Component 1 — Prometheus

### What it is
Prometheus is a time-series database designed for metrics. It works on a **pull model**:
every 15 seconds it sends an HTTP GET to the `/metrics` endpoint of each configured
target and stores the response.

### Metrics exposed by the Leyton API

**Auto-instrumented (from `prometheus-fastapi-instrumentator`):**

| Metric | Type | Description |
|--------|------|-------------|
| `http_requests_total` | Counter | Total HTTP requests, labelled by method, path, status code |
| `http_request_duration_seconds` | Histogram | Request duration distribution |
| `http_request_size_bytes` | Summary | Incoming request size |
| `http_response_size_bytes` | Summary | Outgoing response size |

**Custom metrics (Leyton-specific):**

| Metric | Type | Labels | Description |
|--------|------|--------|-------------|
| `leyton_service_runs_total` | Counter | `service`, `status` | Every service execution, by outcome |
| `leyton_service_duration_seconds` | Histogram | `service` | Execution time distribution per service |
| `leyton_services_currently_running` | Gauge | — | Live count of executing services |

### Counter vs Histogram vs Gauge

- **Counter:** a number that only goes up (runs, errors, requests). Use `rate()` or
  `increase()` in PromQL to get the per-second or per-window rate.
- **Histogram:** records observations in configurable buckets (e.g., how many runs took
  < 1s, < 5s, < 30s). Enables P50/P95/P99 quantile calculations.
- **Gauge:** a number that goes up and down (running services, memory usage, queue depth).

### PromQL examples

```promql
# Service run rate per minute (last 5 min window)
rate(leyton_service_runs_total[5m]) * 60

# Overall success rate
sum(leyton_service_runs_total{status="completed"})
  / sum(leyton_service_runs_total) * 100

# P95 execution duration per service
histogram_quantile(0.95,
  sum by (le, service) (
    rate(leyton_service_duration_seconds_bucket[5m])
  )
)

# Services with success rate below 80%
sum by (service) (leyton_service_runs_total{status="completed"})
  / sum by (service) (leyton_service_runs_total) < 0.80
```

### Retention
Prometheus is configured with `--storage.tsdb.retention.time=30d`. Metrics older than
30 days are automatically deleted. For longer retention, a remote storage backend
(Thanos, Cortex, Mimir) would be added — a natural Phase 3 extension.

---

## Component 2 — Loki + Promtail

### What it is
Loki is a log aggregation system built by Grafana Labs. Unlike Elasticsearch (which
indexes every field of every log line), Loki only indexes **labels** (service name,
log level, container name). The full log content is stored compressed but not indexed.

This makes Loki 10× cheaper to run than Elasticsearch for the same log volume, at
the cost of slower full-text search. For a platform where logs are structured JSON
(which they are — we built `ServiceLogger` to emit JSON), querying by label is usually
sufficient.

### How logs flow

```
service container stdout
        ↓
Docker runtime (writes to /var/lib/docker/containers/<id>/<id>-json.log)
        ↓
Promtail (reads Docker log files via docker_sd_configs)
        ↓  relabelling: adds {service="folder-creator", level="INFO"}
        ↓  pipeline: parses JSON body, extracts correlation_id
Loki (stores log lines, indexed by labels)
        ↓
Grafana logs panel (query: {service="folder-creator"} | json)
```

### Promtail pipeline stages
The `promtail.yml` config includes a pipeline that parses the JSON body of each log
line emitted by `ServiceLogger`:

```
{"timestamp":"2026-05-11T14:32:00","service":"folder-creator",
 "level":"INFO","message":"Folder created","correlation_id":"a3f9..."}
```

After parsing:
- Label `service=folder-creator` is added (for filtering in Grafana)
- Label `level=INFO` is added (for colour-coding in Grafana)
- The `message` field becomes the displayed log line

### LogQL examples

```logql
# All logs from folder-creator
{service="folder-creator"}

# Only errors across all services
{service=~".+"} | json | level="ERROR"

# Logs containing a specific correlation ID
{service=~".+"} | json | correlation_id="a3f9d12e-..."

# Error rate over time (metric from logs)
sum(rate({service=~".+"} | json | level="ERROR" [5m])) by (service)
```

---

## Component 3 — Grafana

### What it is
Grafana is a dashboard and visualisation platform. It connects to multiple datasources
(Prometheus for metrics, Loki for logs) and renders panels into dashboards.

### Pre-provisioned dashboard
The dashboard at `monitoring/grafana/dashboards/leyton-platform.json` is automatically
loaded when Grafana starts — no manual import needed. It contains 10 panels:

| Panel | Type | Datasource | What it shows |
|-------|------|-----------|---------------|
| Total Service Runs | Stat | Prometheus | All-time execution count |
| Success Rate | Stat | Prometheus | % completed vs total, colour-coded |
| Currently Running | Stat | Prometheus | Live gauge, turns red if > 4 |
| Avg Duration (P50) | Stat | Prometheus | Median execution time |
| Service Runs Over Time | Time series | Prometheus | Run activity per service, last 24h |
| Run Outcomes | Donut chart | Prometheus | completed / failed / timeout split |
| Total Runs by Service | Bar gauge | Prometheus | Horizontal bar, sorted descending |
| Success Rate by Service | Bar gauge | Prometheus | Per-service %, red/orange/green |
| Duration Percentiles | Time series | Prometheus | P50/P95/P99 per service |
| Live Service Logs | Logs panel | Loki | Real-time structured logs |

### Access
- URL: `http://localhost:3000`
- Username: `admin`
- Password: `leyton2026`

### Why P95/P99 matter
The average hides the worst-case experience. If the average duration of `web-scraper`
is 2 seconds but the P99 is 45 seconds, 1% of runs are taking 22× longer than average.
That 1% represents a real failure mode. Percentiles expose it; averages do not.

---

## How to Start the Stack

```bash
# Start everything (services + API + monitoring)
docker-compose up -d

# Start only the monitoring stack (if services are running separately)
docker-compose up -d prometheus grafana loki promtail

# View Prometheus targets (are they being scraped?)
open http://localhost:9090/targets

# View Grafana dashboard
open http://localhost:3000
# Login: admin / leyton2026
# Navigate: Dashboards → Leyton Automation Platform
```

### Verify metrics are flowing
```bash
# Check the API /metrics endpoint directly
curl http://localhost:8000/metrics | grep leyton_

# Expected output:
# leyton_service_runs_total{service="folder-creator",status="completed"} 3.0
# leyton_service_duration_seconds_bucket{service="folder-creator",le="1.0"} 3.0
# leyton_services_currently_running 0.0
```

### Verify logs are flowing
In Grafana, open the Explore tab, select Loki datasource, and run:
```logql
{service=~".+"} | json
```
You should see log lines from all services that have run.

---

## Files Created in This Phase

```
monitoring/
├── prometheus/
│   └── prometheus.yml              ← scrape config (15s interval, leyton-api target)
├── grafana/
│   ├── provisioning/
│   │   ├── datasources/
│   │   │   ├── prometheus.yml      ← auto-registers Prometheus datasource
│   │   │   └── loki.yml            ← auto-registers Loki datasource
│   │   └── dashboards/
│   │       └── dashboards.yml      ← tells Grafana where to load dashboards from
│   └── dashboards/
│       └── leyton-platform.json    ← the full pre-built dashboard (10 panels)
├── loki/
│   └── loki-config.yml             ← TSDB schema, local filesystem storage
└── promtail/
    └── promtail.yml                ← Docker SD, JSON pipeline, ships to Loki

api/
├── main.py                         ← added 3 custom metrics + Instrumentator
└── requirements.txt                ← added prometheus-fastapi-instrumentator

docker-compose.yml                  ← added prometheus, grafana, loki, promtail
                                       added networks (app-net, monitoring)
                                       added named volumes
                                       added healthcheck on api service
```

---

## DevOps Principles Illustrated

**The shift from black-box to white-box monitoring.**
Before this phase, the only way to know a service was failing was to check the output
file manually. After this phase, a dashboard shows it within 15 seconds of the failure.

**Metrics as a first-class concern.**
Metrics are not added after the fact — they are part of the application code. The three
custom counters in `api/main.py` were written alongside the business logic that produces
them. This is the observability-first mindset.

**Structured logs as a foundation for log analytics.**
The `ServiceLogger` class built in Phase 0 emits JSON. JSON logs were the right choice
not just for readability, but because they are directly queryable in Loki with `| json`
without any custom parsing configuration.
