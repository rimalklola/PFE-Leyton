# DevOps Strategy — Leyton Automation Platform

## Overview

This document describes the DevOps strategy applied to the Leyton Automation Platform.
The strategy follows a phased maturity model: each phase adds a layer of engineering
discipline, moving the project from a collection of local scripts to a production-grade,
observable, and automatically deployed platform.

---

## The DevOps Maturity Model

```
                                                              ← you are building toward here
  Level 5 ──── GitOps ─────────────────────────────────────── push to main = auto-deploy
  Level 4 ──── Cloud + IaC ────────────────────────────────── reproducible infrastructure
  Level 3 ──── Observability ──────────────────────────────── metrics, logs, alerts
  Level 2 ──── CI/CD Hardening ──────────────── ✓ Phase 1    coverage, security, registry
  Level 1 ──── Version Control + Basic CI ────── ✓ baseline  lint, test, docker build
  Level 0 ──── Manual scripts ──────────────────── starting point
```

Each level is a prerequisite for the next. You cannot reliably do GitOps without
observability. You cannot trust observability without a solid test suite. The levels
are not arbitrary — they reflect the order in which engineering teams solve real problems.

---

## Phases

| Phase | Topic | Status | Documentation |
|-------|-------|--------|---------------|
| 1 | CI/CD Hardening | ✅ Complete | [phase-1-cicd.md](phase-1-cicd.md) |
| 2 | Observability (Prometheus + Grafana + Loki) | ✅ Complete | [phase-2-observability.md](phase-2-observability.md) |
| 3 | Cloud Deployment + Infrastructure as Code | ✅ Complete | [phase-3-cloud.md](phase-3-cloud.md) |
| 4 | GitOps (push-to-deploy) | 🔜 Planned | phase-4-gitops.md |

---

## Phase 1 — CI/CD Hardening

**What was there before:** A basic GitHub Actions workflow with lint, test, and docker
build — one job per stage, no security checks, no coverage enforcement, no image registry.

**What was added:**

```
Before                          After
──────────────────────────────────────────────────────
lint → test → build             lint
                                security (Bandit + pip-audit)   ← NEW
                                test + coverage gate (≥80%)     ← HARDENED
                                build + GHCR push               ← HARDENED
                                pipeline-passed summary gate    ← NEW
```

**Key decisions:**
- **Coverage gate at 80%:** enforced, not just reported — a metric you can ignore is not a gate
- **Bandit `-ll`:** medium/high severity only — low severity would generate noise
- **SHA-tagged images:** every image is traceable to a specific commit for rollback
- **GHA layer cache:** 60–80% faster builds by reusing unchanged Docker layers
- **`pipeline-passed` summary job:** single required status check for branch protection

→ Full details: [phase-1-cicd.md](phase-1-cicd.md)

---

## Phase 2 — Observability (upcoming)

**Problem this solves:** The pipeline guarantees code quality before deployment. But once
the code is running, how do you know it is healthy? How do you know a service started
failing 3 hours ago?

**The three pillars of observability:**

| Pillar | Tool | What it answers |
|--------|------|----------------|
| **Logs** | JSON structured logs (already built) + Loki | What happened and when? |
| **Metrics** | Prometheus + FastAPI `/metrics` endpoint | How is the system performing? |
| **Dashboards** | Grafana | Is anything wrong right now? |

**Planned additions:**
- Prometheus scraping the FastAPI `/metrics` endpoint
- Grafana dashboard: runs/min, error rate, service duration, success rate per service
- Loki log aggregation: all service JSON logs queryable in Grafana
- Alerting rule: notify when error rate > 10% over 5 minutes

→ Documentation: phase-2-observability.md (in progress)

---

## Phase 3 — Cloud + IaC (upcoming)

**Problem this solves:** The platform runs locally. It cannot be used by consultants
unless they run it on their own machine. A real deployment needs a stable URL.

**Infrastructure as Code principle:** Infrastructure (servers, networking, databases)
should be defined in version-controlled files, not configured manually through a web
console. This makes environments reproducible, auditable, and destroyable/recreatable
at will.

**Planned stack:**
- **Terraform:** defines the cloud resources (container service, networking, storage)
- **Railway / Azure Container Apps:** hosts the running containers
- **Environment separation:** `dev` (local docker-compose) / `prod` (cloud)

→ Documentation: phase-3-cloud.md (in progress)

---

## Phase 4 — GitOps (upcoming)

**Problem this solves:** Even with CI/CD, deploying to production still requires a
manual trigger. GitOps eliminates that last manual step.

**GitOps principle:** The Git repository is the single source of truth for both the
application code AND the desired deployment state. A push to `main` that passes the
pipeline automatically updates production.

```
Developer pushes code
        ↓
Pipeline runs (lint → security → test → build)
        ↓
Image pushed to GHCR with SHA tag
        ↓
Deploy job updates the cloud service to the new image
        ↓
Production is updated — no human action required
```

→ Documentation: phase-4-gitops.md (in progress)

---

## Repository Structure

```
leyton-automation/
├── .github/
│   └── workflows/
│       └── ci-cd.yml          ← the pipeline definition
├── services/
│   ├── shared/                ← shared registry + logger
│   └── {service}/
│       ├── main.py
│       ├── mock_data.py
│       ├── requirements.txt
│       ├── Dockerfile
│       └── test_{service}.py
├── api/                       ← FastAPI orchestration layer
├── docs/
│   └── devops/                ← this folder
├── docker-compose.yml         ← local multi-service stack
├── Makefile                   ← developer shortcuts
└── runs.db                    ← SQLite run registry
```

---

## Guiding Principles

1. **Automate everything that can be automated.** If a check can be run by a machine,
   it should never be a manual step.

2. **Fail fast.** Catch problems as early as possible. A linting error found in 10
   seconds costs nothing. A security vulnerability found in production costs everything.

3. **Make the implicit explicit.** Coverage thresholds, security policies, and deployment
   targets should be in files in the repository — not in someone's head or a wiki page.

4. **Reproducibility.** Any developer should be able to check out the repository and
   get a running environment with a single command. Infrastructure as Code and Docker
   make this possible.

5. **Traceability.** Every deployed artifact should be traceable to a specific commit,
   a specific test run, and a specific build. SHA-tagged Docker images achieve this.
