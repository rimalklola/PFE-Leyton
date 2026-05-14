# Phase 1 — CI/CD Pipeline Hardening

## Philosophy

Continuous Integration and Continuous Delivery (CI/CD) is the backbone of the DevOps
philosophy. The core principle is simple: **every code change is automatically verified
before it can reach production**. No human needs to remember to run tests, check for
security issues, or build a Docker image — the pipeline does it every time, without fail.

This phase transforms the project from a collection of scripts that work on one developer's
machine into a system with automated quality gates. It answers a key question in DevOps:

> *"How do you ship code fast without breaking things?"*

The answer is: you automate every check that would otherwise be manual.

---

## Pipeline Architecture

The pipeline has 5 sequential stages. Each stage must pass before the next one starts.
A failure at any stage blocks the deployment.

```
┌──────────┐    ┌──────────┐    ┌──────────────────┐    ┌────────────────┐    ┌─────────┐
│  LINT    │───▶│ SECURITY │───▶│  TEST + COVERAGE  │───▶│  BUILD + PUSH  │───▶│ SUMMARY │
│ (flake8) │    │  (bandit │    │ (pytest + cov 80%)│    │ (Docker + GHCR)│    │  gate   │
│          │    │ pip-audit)│    │                  │    │                │    │         │
└──────────┘    └──────────┘    └──────────────────┘    └────────────────┘    └─────────┘
   parallel         parallel          parallel               parallel
   per service      per service       per service            per service
```

All 8 services run through every stage **in parallel** — a matrix strategy. Total pipeline
runtime is determined by the slowest service, not the sum of all services.

---

## Stage 1 — Lint

**Tool:** `flake8`
**Config:** `--max-line-length=120 --extend-ignore=E402`

### What it does
Flake8 is a static analysis tool that reads Python source code without executing it and
checks for:
- **Syntax errors** — code that would crash immediately on import
- **Style violations** — inconsistent indentation, unused imports, undefined names
- **PEP 8 compliance** — Python's official style guide

### Why it matters (DevOps perspective)
Style inconsistency is a silent productivity killer in team environments. When every
developer formats code differently, code reviews become noisy and merge conflicts become
frequent. A linter enforced in CI means the pipeline — not a human reviewer — catches
style issues. Developers get feedback in seconds instead of waiting for a review.

### Configuration decisions
| Flag | Reason |
|------|--------|
| `--max-line-length=120` | Default 79 chars is too restrictive for modern screens and structured log calls |
| `--extend-ignore=E402` | Services use `sys.path` manipulation before imports, which is intentional |

---

## Stage 2 — Security Scanning

### Tool 1: Bandit
**Purpose:** Static analysis for Python-specific security vulnerabilities.

Bandit reads the Abstract Syntax Tree (AST) of each Python file and flags patterns known
to introduce security vulnerabilities:

| Bandit check | What it catches |
|---|---|
| B102 | `exec()` — arbitrary code execution |
| B301/B302 | `pickle` deserialization — remote code execution risk |
| B324 | Use of weak hash functions (MD5, SHA1) |
| B501–B509 | SSL/TLS misconfigurations |
| B602/B603 | Shell injection via `subprocess` with `shell=True` |
| B105/B106 | Hardcoded passwords in source code |

**Severity flag `-ll`:** Only medium and high severity issues are reported. Low-severity
findings (like use of `assert` in tests) would generate noise without adding value.

### Tool 2: pip-audit
**Purpose:** Checks every declared dependency against the OSV vulnerability database
(Google's Open Source Vulnerabilities) and the PyPI Advisory Database.

**Why this matters:** A service can have perfectly written code but use a dependency with
a known CVE. In 2021, the Log4Shell vulnerability (CVE-2021-44228) affected thousands of
systems that had no direct code issues — the vulnerability was in a dependency. pip-audit
catches this class of risk automatically on every push.

### DevOps principle illustrated
Security is not a phase at the end of development — it is a gate at the beginning of
every deployment. This is the **Shift Left** principle: move security checks earlier in
the development lifecycle where fixes are cheaper and faster.

---

## Stage 3 — Tests with Coverage Gate

**Tools:** `pytest` + `pytest-cov`
**Threshold:** 80% — the pipeline fails if any service drops below this.

### Coverage explained
Code coverage measures what percentage of the source code is actually executed during
the test suite. An 80% threshold means that at least 8 out of every 10 lines must be
covered by at least one test.

```
services/folder-creator/main.py
  Lines:    45
  Covered:  38
  Coverage: 84.4%  ✓ passes gate

services/pdf-timesheet-extractor/main.py
  Lines:    120
  Covered:  88
  Coverage: 73.3%  ✗ fails gate — pipeline blocked
```

### Coverage report artifacts
After every run, the pipeline uploads a `coverage.xml` file per service as a GitHub
Actions artifact. These XML reports follow the standard Cobertura format and can be
imported into SonarQube, Codecov, or any CI dashboard tool.

### Why 80% and not 100%?
100% coverage is achievable but often counterproductive — it encourages writing tests
that hit lines without testing behaviour (e.g., testing `__init__` with no assertions).
80% is an industry-standard threshold that ensures the critical paths are tested while
leaving room for pragmatic decisions about what genuinely needs testing.

### DevOps principle illustrated
The pipeline **enforces** the threshold — it does not just report it. This is the
difference between a metric and a gate. A metric you can ignore. A gate stops the
deployment.

---

## Stage 4 — Build and Push to Registry

**Tools:** Docker Buildx, `docker/build-push-action`, GitHub Container Registry (GHCR)

### What happens
1. Docker Buildx builds the image using the service's `Dockerfile`
2. The image is tagged with two identifiers:
   - `:latest` — always points to the most recent successful build on `main`
   - `:<git-sha>` — immutable tag pointing to the exact commit (e.g., `:a3f9d12e`)
3. On push to `main`, the image is pushed to `ghcr.io`
4. On pull requests, the image is built but **not** pushed (validation only)

### Image tags explained

```
ghcr.io/leyton/leyton-folder-creator:latest        ← always the newest
ghcr.io/leyton/leyton-folder-creator:a3f9d12e      ← pinned to commit
```

The SHA tag is critical for traceability. If a bug is introduced, you can deploy the
previous SHA tag to roll back instantly — without rebuilding anything.

### Layer caching
```yaml
cache-from: type=gha,scope=${{ matrix.service }}
cache-to:   type=gha,scope=${{ matrix.service }},mode=max
```

Docker images are built in layers. If the `requirements.txt` hasn't changed, Docker
reuses the cached dependency layer and only rebuilds the application layer. The `gha`
cache type stores these layers in GitHub Actions' cache, persisting them across runs.

**Impact:** First build of a service: ~90 seconds. Subsequent builds with no dependency
changes: ~15 seconds.

### GHCR vs Docker Hub
| | GitHub Container Registry | Docker Hub |
|---|---|---|
| Cost | Free for public repos | Free tier limited to 1 private repo |
| Auth | `GITHUB_TOKEN` (automatic) | Requires separate credentials |
| Integration | Native GitHub Actions support | Requires secret management |
| Access control | Inherits repo permissions | Separate user management |

---

## Stage 5 — Pipeline Summary Gate

A single job (`pipeline-passed`) that depends on all 4 previous stages. It succeeds only
if every stage passed. This job is what you configure as the **required status check** in
GitHub branch protection rules.

**Why:** Without this, you could set individual jobs as required, but matrix jobs create
one status check per service (8 lint + 8 test + 8 build = 24 checks to configure). The
summary gate is a single check that represents the entire pipeline.

---

## Trigger Strategy

| Event | Lint | Security | Test | Build | Push to GHCR |
|---|---|---|---|---|---|
| Push to `main` | ✓ | ✓ | ✓ | ✓ | ✓ |
| Pull Request to `main` | ✓ | ✓ | ✓ | ✓ (build only) | ✗ |

Pull requests validate code quality without publishing images. Only verified, merged code
reaches the registry.

---

## How to Read Pipeline Results

Navigate to the repository on GitHub → **Actions** tab → select the latest workflow run.

```
CI/CD Pipeline
├── Lint [folder-creator]           ✓ 12s
├── Lint [timesheet-prefill]        ✓ 11s
├── ...
├── Security [folder-creator]       ✓ 18s
├── ...
├── Test [folder-creator]           ✓ 24s   coverage: 84%
├── Test [pdf-timesheet-extractor]  ✗ 19s   coverage: 73% — BELOW THRESHOLD
├── ...
└── Pipeline passed                 ✗  blocked by test failure
```

A red `✗` on `pipeline-passed` means the branch cannot be merged. The developer must
fix the failing service and push again.

---

## Running the Same Checks Locally

Before pushing, run the same checks locally to catch issues early:

```bash
# Lint
python -m flake8 services/folder-creator/main.py --max-line-length=120 --extend-ignore=E402

# Security
pip install bandit pip-audit
bandit services/folder-creator/main.py -ll
pip-audit -r services/folder-creator/requirements.txt

# Tests with coverage
cd services/folder-creator
python -m pytest test_folder_creator.py -v --cov=. --cov-report=term-missing --cov-fail-under=80
```

---

## Files Modified in This Phase

| File | Change |
|------|--------|
| `.github/workflows/ci-cd.yml` | Full pipeline rewrite — 5 stages, security scan, coverage gate, GHCR push |
| `services/folder-creator/requirements.txt` | Fixed encoding issue in comment |
