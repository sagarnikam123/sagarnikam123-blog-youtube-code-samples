# Grafana OSS - Step-by-Step Provisioning
#
# Configuration:
#   Copy terraform.tfvars.example to terraform.tfvars and update values.
#   See terraform.tfvars.example for Grafana OSS, AMG, and Azure Managed Grafana examples.
#
# Steps:
# 1. terraform init                    - Initialize provider
# 2. terraform apply -target=...       - Apply one resource at a time
#
# Order of provisioning:
# Step 1: grafana_folder.main          (01-folders.tf)
# Step 2: grafana_data_source.*        (02-datasources.tf)
# Step 3: grafana_dashboard.*          (03-dashboards.tf)
# Step 4: grafana_contact_point.*      (04-alerting.tf)
# Step 5: grafana_rule_group.*         (04-alerting.tf)
# Step 6: grafana_notification_policy  (04-alerting.tf)
# Step 7: grafana_team.*               (05-access.tf)
#
# References:
# - Grafana Terraform Provider: https://registry.terraform.io/providers/grafana/grafana/latest/docs
# - GitHub: https://github.com/grafana/terraform-provider-grafana

terraform {
  required_version = ">= 1.0"

  required_providers {
    grafana = {
      source  = "grafana/grafana"
      version = ">= 2.0"
    }
  }
}

provider "grafana" {
  url  = var.grafana_url
  auth = var.grafana_auth
}
