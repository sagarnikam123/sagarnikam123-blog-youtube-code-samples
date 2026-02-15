# Step-by-Step Provisioning Guide

## Resource Files

| File | Resources | Description |
|------|-----------|-------------|
| `01-folders.tf` | `grafana_folder` | Organize dashboards |
| `02-datasources.tf` | `grafana_data_source` | Prometheus, TestData, Loki connections |
| `03-dashboards.tf` | `grafana_dashboard` | Golden Signals dashboard |
| `04-alerting.tf` | `grafana_contact_point`, `grafana_rule_group`, `grafana_notification_policy` | Alerting stack |
| `05-access.tf` | `grafana_team`, `grafana_folder_permission` | Access control |
| `06-service-accounts.tf` | `grafana_service_account`, `grafana_service_account_token` | API access for CI/CD |
| `07-extras.tf` | `grafana_mute_timing`, `grafana_annotation`, `grafana_playlist`, `grafana_library_panel`, `grafana_organization` | Additional resources (commented examples) |
| `dashboards/` | JSON files | Dashboard JSON files (Golden Signals) |

## Prerequisites

1. Running Grafana instance
2. Terraform installed
3. Copy `terraform.tfvars.example` to `terraform.tfvars` and update values

## Initialize

```bash
terraform init
```

## Step 1: Create Folder

```bash
terraform apply -target=grafana_folder.main
```

**Destroy**:
```bash
# terraform destroy -target=grafana_folder.main
```

Verify: Check Grafana UI → Dashboards → Folders

## Step 2: Create Data Sources

```bash
# Prometheus (required)
terraform plan -target=grafana_data_source.prometheus
terraform apply -target=grafana_data_source.prometheus

# TestData (for Golden Signals dashboard)
terraform plan -target=grafana_data_source.testdata
terraform apply -target=grafana_data_source.testdata

# Loki (optional - set loki_url in tfvars first)
terraform plan -target=grafana_data_source.loki
terraform apply -target=grafana_data_source.loki
```

**Destroy**:
```bash
# terraform destroy -target=grafana_data_source.prometheus
# terraform destroy -target=grafana_data_source.testdata
# terraform destroy -target=grafana_data_source.loki
```

Verify: Grafana UI → Connections → Data sources → Click datasource → Test

## Step 3: Create Dashboards

```bash
# Golden Signals (uses TestData - from https://grafana.com/grafana/dashboards/24372)
terraform plan -target=grafana_dashboard.golden_signals
terraform apply -target=grafana_dashboard.golden_signals
```

**Destroy**:
```bash
# terraform destroy -target=grafana_dashboard.golden_signals
```

Verify: Grafana UI → Dashboards → Dev Monitoring folder

## Step 4: Enable Alerting (Optional)

Update `terraform.tfvars`:
```hcl
alerting_enabled = true
# Note: Get your unique webhook URL from https://webhook.site/ (different for each person)
webhook_url      = "https://webhook.site/40265b47-d1ce-4b3d-8817-003d995b7a5d"
```

```bash
# Contact point
terraform apply -target=grafana_contact_point.webhook

# Alert rules
terraform apply -target=grafana_rule_group.system_alerts

# Notification policy
terraform apply -target=grafana_notification_policy.main
```

Verify: Grafana UI → Alerting → Alert rules

**Tip**: Use [webhook.site](https://webhook.site) for testing - it provides a free endpoint to inspect incoming requests.

## Step 5: Create Team & Permissions (Optional)

```bash
terraform apply -target=grafana_team.devops
terraform apply -target=grafana_folder_permission.main
```

**Destroy**:
```bash
# terraform destroy -target=grafana_folder_permission.main
# terraform destroy -target=grafana_team.devops
```

Verify: Grafana UI → Administration → Teams

## Step 6: Create Service Account (Optional)

Service accounts are used for API access in CI/CD pipelines.

```bash
terraform apply -target=grafana_service_account.terraform
terraform apply -target=grafana_service_account_token.terraform
```

**Destroy**:
```bash
# terraform destroy -target=grafana_service_account_token.terraform
# terraform destroy -target=grafana_service_account.terraform
```

Get the token:
```bash
terraform output -raw service_account_token
```

Verify: Grafana UI → Administration → Service accounts

## Step 7: Mute Timings (Optional)

Silence alerts during maintenance windows or weekends.

```bash
terraform apply -target=grafana_mute_timing.weekends
terraform apply -target=grafana_mute_timing.maintenance
```

**Destroy**:
```bash
# terraform destroy -target=grafana_mute_timing.weekends
# terraform destroy -target=grafana_mute_timing.maintenance
```

Verify: Grafana UI → Alerting → Notification policies → Mute timings

## Apply All Remaining

After verifying each step, apply everything:

```bash
terraform apply
```

## Bulk Import Existing Resources

If you have existing Grafana resources created via UI that you want to manage with Terraform, use the shared bulk import scripts from `../scripts/`:

### Import Folders

```bash
# Preview what will be imported
GRAFANA_TOKEN=your-token ../scripts/bulk-import-folders.sh --url http://localhost:3000 --dry-run

# Generate .tf file only (no import)
GRAFANA_TOKEN=your-token ../scripts/bulk-import-folders.sh --url http://localhost:3000 --generate

# Generate and import
GRAFANA_TOKEN=your-token ../scripts/bulk-import-folders.sh --url http://localhost:3000
```

### Import Data Sources

```bash
# Preview
GRAFANA_TOKEN=your-token ../scripts/bulk-import-datasources.sh --url http://localhost:3000 --dry-run

# Generate and import
GRAFANA_TOKEN=your-token ../scripts/bulk-import-datasources.sh --url http://localhost:3000
```

### Import Dashboards

```bash
# Preview
GRAFANA_TOKEN=your-token ../scripts/bulk-import-dashboards.sh --url http://localhost:3000 --dry-run

# Generate and import (also downloads dashboard JSON files)
GRAFANA_TOKEN=your-token ../scripts/bulk-import-dashboards.sh --url http://localhost:3000
```

### Import Contact Points

```bash
# Preview
GRAFANA_TOKEN=your-token ../scripts/bulk-import-contact-points.sh --url http://localhost:3000 --dry-run

# Generate and import
GRAFANA_TOKEN=your-token ../scripts/bulk-import-contact-points.sh --url http://localhost:3000
```

### Import Alert Rules

```bash
# Preview
GRAFANA_TOKEN=your-token ../scripts/bulk-import-alert-rules.sh --url http://localhost:3000 --dry-run

# Generate and import
GRAFANA_TOKEN=your-token ../scripts/bulk-import-alert-rules.sh --url http://localhost:3000
```

**Generated Files**:
- `folders_imported.tf` - Terraform resource definitions for folders
- `datasources_imported.tf` - Terraform resource definitions for datasources
- `dashboards_imported.tf` - Terraform resource definitions for dashboards
- `dashboards_imported/` - Directory containing dashboard JSON files
- `contact_points_imported.tf` - Terraform resource definitions for contact points
- `alert_rules_imported.tf` - Terraform resource definitions for alert rule groups

**After Import**:
```bash
terraform plan
# Should show "No changes" if definitions match existing resources
# Adjust generated .tf files if needed until plan shows no changes
```

## Destroy

To remove all resources:

```bash
terraform destroy
```
