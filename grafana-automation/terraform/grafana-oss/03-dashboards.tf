# Step 3: Dashboards
# Command: terraform apply -target=grafana_dashboard.golden_signals
# Destroy: terraform destroy -target=grafana_dashboard.golden_signals
# Reference: https://registry.terraform.io/providers/grafana/grafana/latest/docs/resources/dashboard

# =============================================================================
# Golden Signals Dashboard (from Grafana.com)
# Source: https://grafana.com/grafana/dashboards/24372-service-health-golden-signals/
# Uses TestData datasource for demo purposes
# =============================================================================
resource "grafana_dashboard" "golden_signals" {
  config_json = file("${path.module}/dashboards/golden-signals.json")
  folder      = grafana_folder.main.uid
  overwrite   = true
}
