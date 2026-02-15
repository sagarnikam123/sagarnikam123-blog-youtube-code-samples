# Step 7: Access Control (Teams, Folder Permissions)
# Command: terraform apply -target=grafana_team.devops
# Command: terraform apply -target=grafana_folder_permission.main
# Destroy: terraform destroy -target=grafana_folder_permission.main
# Destroy: terraform destroy -target=grafana_team.devops
#
# References:
# - https://registry.terraform.io/providers/grafana/grafana/latest/docs/resources/team
# - https://registry.terraform.io/providers/grafana/grafana/latest/docs/resources/folder_permission

resource "grafana_team" "devops" {
  name  = "DevOps"
  email = "devops@example.com"
}

resource "grafana_folder_permission" "main" {
  folder_uid = grafana_folder.main.uid

  permissions {
    role       = "Viewer"
    permission = "View"
  }

  permissions {
    role       = "Editor"
    permission = "Edit"
  }

  permissions {
    team_id    = grafana_team.devops.id
    permission = "Admin"
  }
}
