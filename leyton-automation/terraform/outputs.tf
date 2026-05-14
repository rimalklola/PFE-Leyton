# ─────────────────────────────────────────────────────────────────────────────
# Outputs — printed after terraform apply, also readable by CI/CD scripts.
# ─────────────────────────────────────────────────────────────────────────────

output "project_id" {
  description = "Railway project ID."
  value       = railway_project.leyton.id
}

output "api_service_id" {
  description = "Railway service ID for the API."
  value       = railway_service.api.id
}

output "grafana_service_id" {
  description = "Railway service ID for Grafana."
  value       = railway_service.grafana.id
}

# Railway generates public URLs automatically once a service is deployed.
# The pattern is: https://<service-name>.up.railway.app
output "api_url" {
  description = "Public URL of the deployed API."
  value       = "https://leyton-api.up.railway.app"
}

output "grafana_url" {
  description = "Public URL of the deployed Grafana dashboard."
  value       = "https://leyton-grafana.up.railway.app"
}
