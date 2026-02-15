# Step 4-6: Alerting (Contact Points, Rules, Notification Policy)
# Enable by setting in terraform.tfvars:
#   alerting_enabled = true
#   webhook_url      = "https://webhook.site/your-unique-id"
#
# Commands:
# terraform plan -target=grafana_contact_point.webhook[0]
# terraform apply -target=grafana_contact_point.webhook[0]
# terraform plan -target=grafana_rule_group.system_alerts[0]
# terraform apply -target=grafana_rule_group.system_alerts[0]
# terraform plan -target=grafana_notification_policy.main[0]
# terraform apply -target=grafana_notification_policy.main[0]
#
# Destroy:
# terraform destroy -target=grafana_notification_policy.main[0]
# terraform destroy -target=grafana_rule_group.system_alerts[0]
# terraform destroy -target=grafana_contact_point.webhook[0]
#
# References:
# - https://registry.terraform.io/providers/grafana/grafana/latest/docs/resources/contact_point
# - https://registry.terraform.io/providers/grafana/grafana/latest/docs/resources/rule_group
# - https://registry.terraform.io/providers/grafana/grafana/latest/docs/resources/notification_policy

# =============================================================================
# Contact Points
# =============================================================================

# Webhook Contact Point (for testing use webhook.site)
resource "grafana_contact_point" "webhook" {
  count = var.alerting_enabled && var.webhook_url != "" ? 1 : 0

  name = "Webhook"

  webhook {
    url         = var.webhook_url
    http_method = "POST"
    max_alerts  = 10
  }
}

# =============================================================================
# Alert Rules
# =============================================================================

resource "grafana_rule_group" "system_alerts" {
  count = var.alerting_enabled ? 1 : 0

  name             = "system-alerts"
  folder_uid       = grafana_folder.main.uid
  interval_seconds = 60

  rule {
    name      = "High CPU Usage"
    condition = "C"
    for       = "5m"

    # Query the datasource
    data {
      ref_id         = "A"
      datasource_uid = grafana_data_source.prometheus.uid
      relative_time_range {
        from = 600
        to   = 0
      }
      model = jsonencode({
        expr  = "100 - (avg(irate(node_cpu_seconds_total{mode=\"idle\"}[5m])) * 100)"
        refId = "A"
      })
    }

    # Reduce to single value
    data {
      ref_id         = "B"
      datasource_uid = "__expr__"
      relative_time_range {
        from = 0
        to   = 0
      }
      model = jsonencode({
        expression = "A"
        type       = "reduce"
        reducer    = "last"
        refId      = "B"
      })
    }

    # Threshold condition
    data {
      ref_id         = "C"
      datasource_uid = "__expr__"
      relative_time_range {
        from = 0
        to   = 0
      }
      model = jsonencode({
        expression = "$B > 80"
        type       = "math"
        refId      = "C"
      })
    }

    labels      = { severity = "warning" }
    annotations = { summary = "CPU usage above 80%" }
  }

  rule {
    name      = "High Memory Usage"
    condition = "C"
    for       = "5m"

    data {
      ref_id         = "A"
      datasource_uid = grafana_data_source.prometheus.uid
      relative_time_range {
        from = 600
        to   = 0
      }
      model = jsonencode({
        expr  = "(1 - (node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes)) * 100"
        refId = "A"
      })
    }

    data {
      ref_id         = "B"
      datasource_uid = "__expr__"
      relative_time_range {
        from = 0
        to   = 0
      }
      model = jsonencode({
        expression = "A"
        type       = "reduce"
        reducer    = "last"
        refId      = "B"
      })
    }

    data {
      ref_id         = "C"
      datasource_uid = "__expr__"
      relative_time_range {
        from = 0
        to   = 0
      }
      model = jsonencode({
        expression = "$B > 85"
        type       = "math"
        refId      = "C"
      })
    }

    labels      = { severity = "critical" }
    annotations = { summary = "Memory usage above 85%" }
  }
}

# =============================================================================
# Notification Policy
# =============================================================================

resource "grafana_notification_policy" "main" {
  count = var.alerting_enabled && var.webhook_url != "" ? 1 : 0

  group_by        = ["alertname"]
  contact_point   = grafana_contact_point.webhook[0].name
  group_wait      = "30s"
  group_interval  = "5m"
  repeat_interval = "4h"
}
