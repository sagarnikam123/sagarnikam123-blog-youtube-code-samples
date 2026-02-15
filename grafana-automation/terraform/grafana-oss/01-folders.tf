# Step 1: Folders
# Command: terraform apply -target=grafana_folder.main
# Destroy: terraform destroy -target=grafana_folder.main
# Reference: https://registry.terraform.io/providers/grafana/grafana/latest/docs/resources/folder

resource "grafana_folder" "main" {
  title = "${title(var.environment)} Monitoring"
  uid   = "${var.environment}-monitoring"
}

# Optional: Additional folders
# resource "grafana_folder" "alerts" {
#   title = "${title(var.environment)} Alerts"
#   uid   = "${var.environment}-alerts"
# }

# =============================================================================
# IMPORT EXISTING FOLDERS
# =============================================================================
# To import a folder created manually in Grafana UI into Terraform state:
#
# 1. Get folder UID from Grafana:
#    - UI: Dashboards → click folder → URL shows /dashboards/f/<folder-uid>/
#    - API: curl -H "Authorization: Bearer $TOKEN" http://localhost:3000/api/folders
#
# 2. Add resource definition below (uncomment and update):
#    resource "grafana_folder" "existing" {
#      title = "Your Folder Name"
#      uid   = "your-folder-uid"
#    }
#
# 3. Run import command:
#    terraform import grafana_folder.existing <folder-uid>
#
# 4. Verify with:
#    terraform plan
#    # Should show "No changes" if definition matches existing folder
#
# Example:
# resource "grafana_folder" "imported" {
#   title = "Production Dashboards"
#   uid   = "prod-dashboards"
# }
# Command: terraform import grafana_folder.imported prod-dashboards
