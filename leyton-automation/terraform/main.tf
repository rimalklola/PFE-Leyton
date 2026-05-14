# ─────────────────────────────────────────────────────────────────────────────
# Leyton Automation Platform — Infrastructure as Code
#
# Provider : Railway (free tier, no credit card required)
# Resources: 1 project, 2 services (api + grafana), environment variables
#
# To apply:
#   cd terraform
#   terraform init
#   terraform plan
#   terraform apply
# ─────────────────────────────────────────────────────────────────────────────

terraform {
  required_version = ">= 1.6"

  required_providers {
    railway = {
      source  = "celest-dev/railway"
      version = "~> 0.4"
    }
  }

  # Optional: store state remotely so the team shares the same state.
  # Uncomment to enable Terraform Cloud backend.
  # backend "remote" {
  #   organization = "leyton-belgium"
  #   workspaces { name = "leyton-automation" }
  # }
}

provider "railway" {
  token = var.railway_token
}

# ── Project ───────────────────────────────────────────────────────────────────
# A Railway project is a logical container for services and environments.
# All services in the same project share a private network automatically.

resource "railway_project" "leyton" {
  name        = var.project_name
  description = "Leyton Belgium R&D automation platform — managed by Terraform"
}

# ── Environments ──────────────────────────────────────────────────────────────
# Railway supports multiple environments (production, staging, PR previews).
# Each environment is an independent deployment of all services.

resource "railway_environment" "production" {
  name       = "production"
  project_id = railway_project.leyton.id
}

# ── API Service ───────────────────────────────────────────────────────────────
# Deploys the Docker image built and pushed to GHCR by the CI/CD pipeline.
# Railway automatically exposes the service on a public HTTPS URL.

resource "railway_service" "api" {
  name       = "leyton-api"
  project_id = railway_project.leyton.id

  source {
    image = "ghcr.io/${var.github_owner}/leyton-api:${var.image_tag}"
  }
}

# ── API Environment Variables ─────────────────────────────────────────────────
# These are injected into the container at runtime — no hardcoded values
# in the image. This is the 12-Factor App principle (config in environment).

resource "railway_variable_collection" "api_vars" {
  project_id     = railway_project.leyton.id
  environment_id = railway_environment.production.id
  service_id     = railway_service.api.id

  variables = {
    ENVIRONMENT   = "production"
    LOG_LEVEL     = "INFO"
    DATABASE_PATH = "/data/runs.db"
    PORT          = "8000"
  }
}

# ── Grafana Service ───────────────────────────────────────────────────────────
# Deploys the official Grafana image directly from Docker Hub.

resource "railway_service" "grafana" {
  name       = "leyton-grafana"
  project_id = railway_project.leyton.id

  source {
    image = "grafana/grafana:10.4.2"
  }
}

resource "railway_variable_collection" "grafana_vars" {
  project_id     = railway_project.leyton.id
  environment_id = railway_environment.production.id
  service_id     = railway_service.grafana.id

  variables = {
    GF_SECURITY_ADMIN_USER     = "admin"
    GF_SECURITY_ADMIN_PASSWORD = var.grafana_admin_password
    GF_USERS_ALLOW_SIGN_UP     = "false"
    GF_SERVER_ROOT_URL         = "https://leyton-grafana.up.railway.app"
  }
}
