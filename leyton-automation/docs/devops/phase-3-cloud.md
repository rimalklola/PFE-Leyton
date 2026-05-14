# Phase 3 — Cloud Deployment + Infrastructure as Code

## Philosophy

> *"If your infrastructure cannot be recreated from a text file in 10 minutes,
>  it is not infrastructure — it is archaeology."*

Infrastructure as Code (IaC) is the practice of defining servers, networks, databases,
and deployment targets in version-controlled configuration files rather than through
manual web console clicks.

Without IaC, every environment is slightly different from every other environment.
The staging server has a package that production doesn't. A developer's local config
has a flag that nobody remembers enabling. When something breaks, it is impossible to
know if it broke because of a code change or a configuration drift.

With IaC, the desired state of the infrastructure is a file in the repository. Any
environment can be torn down and rebuilt identically with a single command. This is
called **reproducibility** — a core DevOps principle.

---

## What was built

```
Before                          After
──────────────────────────────────────────────────────────────────
Push to main → Docker image     Push to main → Docker image
                                           → Railway deploy (auto)
                                           → live URL updated

Environments: local only        Environments: local + production
                                             separated by .env files

Infrastructure: defined in      Infrastructure: defined in
heads of team members           terraform/ — version controlled
```

---

## Component 1 — Environment Separation

### The problem
Without environment separation, code running locally and code running in production
are configured identically. This leads to:
- Connecting to production databases from a developer's laptop
- Debug logging in production (exposing internal state)
- Hard-coded paths that only exist on one machine

### The solution: `.env` files

```
.env.example      ← committed to git (template, no real values)
.env              ← gitignored (real values, never committed)
```

The `.env.example` file documents every configuration variable the platform needs.
A new developer copies it to `.env`, fills in their values, and the platform works.
Production values are set as environment variables in the deployment platform
(Railway), never stored in files.

### Key variables

| Variable | Development | Production |
|----------|------------|------------|
| `ENVIRONMENT` | `development` | `production` |
| `LOG_LEVEL` | `DEBUG` | `INFO` |
| `DATABASE_PATH` | `./runs.db` | `/data/runs.db` |
| `GRAFANA_ADMIN_PASSWORD` | `leyton2026` | set via Railway secret |

### The 12-Factor App principle
This follows Factor III of the 12-Factor App methodology: *"Store config in the
environment."* Configuration that varies between deployments (dev, staging, prod)
must never be hardcoded in the application. It must come from environment variables.

---

## Component 2 — Infrastructure as Code with Terraform

### What Terraform is
Terraform is the industry-standard IaC tool. It reads `.tf` files that describe
the desired state of infrastructure, compares it to the current state, and applies
only the necessary changes.

```
terraform plan    ← shows what WILL change (safe, read-only)
terraform apply   ← actually makes the changes
terraform destroy ← tears down everything (recoverable from .tf files)
```

### The state file
Terraform tracks what it has deployed in `terraform.tfstate`. This file contains
sensitive information (resource IDs, outputs) and must be:
- **gitignored** (never committed — it is in `.gitignore`)
- **stored remotely** in production (Terraform Cloud, S3 + DynamoDB locking)

### Resources defined

```hcl
railway_project.leyton          ← the Railway project container
railway_environment.production  ← the production environment
railway_service.api             ← the API container (image from GHCR)
railway_service.grafana         ← Grafana (official Docker Hub image)
railway_variable_collection.*   ← environment variables per service
```

### Why Railway
Railway was chosen for this project because:
- **Free tier** — no credit card required, sufficient for a demo
- **Docker-native** — deploys directly from a Docker image (which CI/CD already builds)
- **Auto HTTPS** — every service gets a `*.up.railway.app` URL with TLS automatically
- **Zero infrastructure management** — no VMs, no networking to configure
- **Terraform provider** — `celest-dev/railway` enables full IaC management

### Applying the infrastructure

```bash
cd terraform

# 1. Copy the example vars file and fill in your values
cp terraform.tfvars.example terraform.tfvars
# Edit terraform.tfvars: add your railway_token and github_owner

# 2. Initialise (downloads the Railway provider)
terraform init

# 3. Preview what will be created
terraform plan

# 4. Apply (creates the Railway project, services, env vars)
terraform apply

# 5. See the output URLs
terraform output
```

**Getting a Railway token:**
1. Go to railway.app → login with GitHub
2. Account Settings → Tokens → New Token
3. Copy the token into `terraform.tfvars` (never commit this file)

---

## Component 3 — Deploy Stage in CI/CD

The deploy job is Stage 5 of the pipeline and closes the GitOps loop:

```
Developer pushes to main
         ↓
Stage 1: Lint ──────────────── catches style issues
Stage 2: Security ───────────── catches vulnerabilities
Stage 3: Test + Coverage ────── ensures correctness
Stage 4: Build + GHCR push ──── produces the deployable artifact
Stage 5: Deploy to Railway ───── makes it live        ← NEW
```

### The deploy job

```yaml
deploy:
  needs: [build]
  if: github.event_name == 'push' && github.ref == 'refs/heads/main'
  environment:
    name: production
    url: https://leyton-api.up.railway.app
  steps:
    - run: railway up --service leyton-api --detach
      env:
        RAILWAY_TOKEN: ${{ secrets.RAILWAY_TOKEN }}
    - run: curl /health to verify
```

### The `environment:` block
The `environment: production` declaration in GitHub Actions does two things:
1. Shows a live deployment link in the GitHub UI (Actions → Deployments tab)
2. Enables **deployment protection rules** — you can require a manual approval
   before production deploys, adding a human gate on top of the automated ones

### Setting up the RAILWAY_TOKEN secret
1. GitHub repository → Settings → Secrets and variables → Actions
2. New repository secret → Name: `RAILWAY_TOKEN`
3. Value: your Railway API token (same one as in terraform.tfvars)

### Deployment verification
After deploying, the pipeline calls `GET /health` to confirm the service is
responding. This is a smoke test — it does not replace the full test suite but
it catches cases where the container crashes on startup.

---

## How it all fits together

```
                   ┌─────────────────────────────────────┐
                   │           DEVELOPER                  │
                   │  git push origin main                │
                   └───────────────┬─────────────────────┘
                                   │
                   ┌───────────────▼─────────────────────┐
                   │        GITHUB ACTIONS                │
                   │  lint → security → test → build      │
                   │              ↓                       │
                   │         [build passes]               │
                   │              ↓                       │
                   │   docker push ghcr.io/leyton/api     │
                   │              ↓                       │
                   │   railway up --service leyton-api    │
                   └───────────────┬─────────────────────┘
                                   │
                   ┌───────────────▼─────────────────────┐
                   │           RAILWAY                    │
                   │  pulls new image from GHCR           │
                   │  replaces running container          │
                   │  https://leyton-api.up.railway.app   │
                   └─────────────────────────────────────┘
```

Zero manual steps. Zero SSH. Zero clicking. This is GitOps.

---

## Files Created in This Phase

| File | Purpose |
|------|---------|
| `.gitignore` | Prevents secrets, state files, and outputs from being committed |
| `.env.example` | Documents all configuration variables — safe to commit |
| `terraform/main.tf` | IaC: Railway project, services, environment variables |
| `terraform/variables.tf` | Input variable declarations |
| `terraform/outputs.tf` | Output: API URL, Grafana URL, service IDs |
| `terraform/terraform.tfvars.example` | Variable values template — gitignored when filled |
| `.github/workflows/ci-cd.yml` | Added Stage 5 (deploy) and Stage 6 (summary) |
