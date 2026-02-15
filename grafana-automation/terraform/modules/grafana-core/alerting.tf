# =============================================================================
# Alerting - Contact Points, Rules, Notification Policy
# =============================================================================

# Webhook Contact Point
resource "grafana_contact_point" "webhook" {
  count = var.enable_alerting && var.webhook_url != "" ? 1 : 0

  name = "${var.instance_name}-webhook"

  webhook {
    url         = var.webhook_url
    http_method = "POST"
    max_alerts  = 10
  }
}

# Alert Rules from configuration
resource "grafana_rule_group" "this" {
  for_each = var.enable_alerting && length(var.alert_rules) > 0 ? { "alerts" = true } : {}

  name             = "${var.instance_name}-alerts"
  folder_uid       = length(grafana_folder.this) > 0 ? values(grafana_folder.this)[0].uid : ""
  interval_seconds = 60

  dynamic "rule" {
    for_each = var.alert_rules
    content {
      name      = rule.value.name
      condition = "C"
      for       = rule.value.for_duration

      data {
        ref_id         = "A"
        datasource_uid = rule.value.datasource_uid
        relative_time_range {
          from = 600
          to   = 0
        }
        model = jsonencode({
          expr  = rule.value.expr
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
          expression = "$B > ${rule.value.threshold}"
          type       = "math"
          refId      = "C"
        })
      }

      labels      = { severity = rule.value.severity }
      annotations = { summary = coalesce(rule.value.summary, "${rule.value.name} triggered") }
    }
  }
}

# Notification Policy
resource "grafana_notification_policy" "this" {
  count = var.enable_alerting && var.webhook_url != "" ? 1 : 0

  group_by        = ["alertname"]
  contact_point   = grafana_contact_point.webhook[0].name
  group_wait      = "30s"
  group_interval  = "5m"
  repeat_interval = "4h"
}
