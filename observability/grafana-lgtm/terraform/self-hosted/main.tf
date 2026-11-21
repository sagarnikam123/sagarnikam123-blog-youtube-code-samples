resource "grafana_folder" "observability" {
  title = "Observability"
}

resource "grafana_data_source" "mimir" {
  type = "prometheus"
  name = "Mimir"
  url  = "http://mimir:9009/prometheus"

  json_data_encoded = jsonencode({
    httpMethod = "POST"
  })
}

resource "grafana_data_source" "loki" {
  type = "loki"
  name = "Loki"
  url  = "http://loki:3100"
}

resource "grafana_data_source" "tempo" {
  type = "tempo"
  name = "Tempo"
  url  = "http://tempo:3200"
}
