# =============================================================================
# Datasources - Conditional creation based on configuration
# =============================================================================

resource "grafana_data_source" "this" {
  for_each = var.enable_datasources ? var.datasources : {}

  type       = each.value.type
  name       = each.key
  url        = each.value.url
  is_default = each.value.is_default

  json_data_encoded = length(each.value.json_data) > 0 ? jsonencode(each.value.json_data) : null

  secure_json_data_encoded = length(each.value.secure_json_data) > 0 ? jsonencode(each.value.secure_json_data) : null
}
