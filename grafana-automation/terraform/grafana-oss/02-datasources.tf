# Step 2: Data Sources
# Command: terraform apply -target=grafana_data_source.prometheus
# Command: terraform apply -target=grafana_data_source.testdata
# Command: terraform apply -target=grafana_data_source.loki (optional)
# Destroy: terraform destroy -target=grafana_data_source.prometheus
# Destroy: terraform destroy -target=grafana_data_source.testdata
# Destroy: terraform destroy -target=grafana_data_source.loki
# Reference: https://registry.terraform.io/providers/grafana/grafana/latest/docs/resources/data_source

resource "grafana_data_source" "prometheus" {
  type       = "prometheus"
  name       = "Prometheus"
  url        = var.prometheus_url
  is_default = true

  json_data_encoded = jsonencode({
    httpMethod   = "POST"
    manageAlerts = true
  })
}

# TestData datasource - built-in Grafana datasource for testing/demo
# Used by Golden Signals dashboard
resource "grafana_data_source" "testdata" {
  type = "grafana-testdata-datasource"
  name = "grafana-testdata-datasource"
  uid  = "testdata"
}

# Optional: Loki datasource
resource "grafana_data_source" "loki" {
  count = var.loki_url != "" ? 1 : 0

  type = "loki"
  name = "Loki"
  url  = var.loki_url

  json_data_encoded = jsonencode({
    maxLines = 1000
  })
}
