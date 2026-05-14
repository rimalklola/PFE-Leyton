# ─────────────────────────────────────────────────────────────────────────────
# Input variables — all values come from terraform.tfvars (gitignored) or
# from environment variables prefixed with TF_VAR_ in CI/CD.
# ─────────────────────────────────────────────────────────────────────────────

variable "railway_token" {
  description = "Railway API token. Set via TF_VAR_railway_token in CI/CD secrets."
  type        = string
  sensitive   = true
}

variable "project_name" {
  description = "Name of the Railway project."
  type        = string
  default     = "leyton-automation"
}

variable "github_owner" {
  description = "GitHub username or org — used to reference the GHCR image."
  type        = string
}

variable "image_tag" {
  description = "Docker image tag to deploy. Defaults to latest; CI/CD passes the git SHA."
  type        = string
  default     = "latest"
}

variable "grafana_admin_password" {
  description = "Grafana admin password for the production deployment."
  type        = string
  sensitive   = true
  default     = "changeme"
}
