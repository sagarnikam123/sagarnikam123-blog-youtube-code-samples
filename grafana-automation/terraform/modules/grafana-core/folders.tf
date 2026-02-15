# =============================================================================
# Folders
# =============================================================================

resource "grafana_folder" "this" {
  for_each = local.folders

  title = each.value.title
  uid   = coalesce(each.value.uid, "${var.instance_name}-${each.key}")
}
