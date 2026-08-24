resource "grafana_folder" "observability" {
  title = "Observability"
}

resource "grafana_data_source" "prometheus" {
  type = "prometheus"
  name = "Prometheus"
  url  = "http://prometheus:9090"

  json_data_encoded = jsonencode({
    httpMethod = "POST"
  })
}

resource "grafana_dashboard" "example" {
  folder = grafana_folder.observability.id

  config_json = jsonencode({
    title = "Terraform-managed Dashboard"
    panels = [
      {
        id         = 1
        type       = "timeseries"
        title      = "CPU Usage"
        gridPos    = { h = 8, w = 12, x = 0, y = 0 }
        datasource = { type = "prometheus", uid = grafana_data_source.prometheus.uid }
        targets = [
          { expr = "rate(process_cpu_seconds_total[5m])", refId = "A" }
        ]
      }
    ]
    schemaVersion = 39
  })
}
