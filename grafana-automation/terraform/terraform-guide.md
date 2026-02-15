# Terraform Grafana Provider Guide

Complete guide for managing Grafana resources using Terraform Infrastructure as Code.

Focus: Grafana OSS, Amazon Managed Grafana (AMG), and Azure Managed Grafana.

---

## Table of Contents

1. [Introduction](#1-introduction)
2. [Prerequisites](#2-prerequisites)
3. [Provider Setup](#3-provider-setup)
4. [Data Sources](#4-data-sources)
5. [Folders & Permissions](#5-folders--permissions)
6. [Dashboards](#6-dashboards)
7. [Alerting](#7-alerting)
8. [Access Control](#8-access-control)
9. [OnCall Management](#9-oncall-management)
10. [Multi-Environment Patterns](#10-multi-environment-patterns)
11. [CI/CD Integration](#11-cicd-integration)
12. [Best Practices](#12-best-practices)
13. [Troubleshooting](#13-troubleshooting)
14. [References](#14-references)

---

## 1. Introduction

### What is Grafana Terraform Provider?

The [Grafana Terraform Provider](https://registry.terraform.io/providers/grafana/grafana/latest/docs) enables Infrastructure as Code management for Grafana instances.

### Supported Platforms

| Platform | Description |
|----------|-------------|
| Grafana OSS | Self-hosted open source Grafana |
| Amazon Managed Grafana (AMG) | AWS fully managed Grafana service |
| Azure Managed Grafana | Azure fully managed Grafana service |
| Grafana Cloud | Grafana Labs hosted service (limited coverage here) |

### What Can You Manage?

#### Core Resources (OSS, AMG, Azure)

| Category | Resources | Description |
|----------|-----------|-------------|
| **Data Connectivity** | `grafana_data_source`, `grafana_data_source_permission` | Connect to Prometheus, Loki, CloudWatch, Azure Monitor, etc. |
| **Organization** | `grafana_folder`, `grafana_folder_permission` | Organize and secure dashboards |
| **Visualization** | `grafana_dashboard`, `grafana_library_panel`, `grafana_dashboard_permission`, `grafana_dashboard_public` | Create and manage visualizations |
| **Alerting** | `grafana_rule_group`, `grafana_contact_point`, `grafana_notification_policy`, `grafana_mute_timing`, `grafana_message_template` | Complete alerting stack |
| **Access Control** | `grafana_organization`, `grafana_team`, `grafana_user`, `grafana_service_account`, `grafana_service_account_token` | User and permission management |
| **Other** | `grafana_annotation`, `grafana_playlist`, `grafana_sso_settings` | Annotations, playlists, SSO |

#### Grafana Cloud Specific Resources

| Category | Resources | Description |
|----------|-----------|-------------|
| **Stack Management** | `grafana_cloud_stack`, `grafana_cloud_stack_service_account` | Manage cloud stacks |
| **Access** | `grafana_cloud_access_policy`, `grafana_cloud_access_policy_token` | Cloud access policies |
| **Plugins** | `grafana_cloud_plugin_installation` | Install plugins |
| **Synthetic Monitoring** | `grafana_synthetic_monitoring_check`, `grafana_synthetic_monitoring_probe` | Uptime monitoring |
| **OnCall** | `grafana_oncall_integration`, `grafana_oncall_schedule`, `grafana_oncall_escalation_chain` | Incident management |
| **Machine Learning** | `grafana_machine_learning_job`, `grafana_machine_learning_outlier_detector` | ML features |
| **SLO** | `grafana_slo` | Service Level Objectives |
| **Reporting** | `grafana_report` | Scheduled PDF reports (Enterprise) |

> **Reference**: [Full Provider Documentation](https://registry.terraform.io/providers/grafana/grafana/latest/docs)

### Benefits of Terraform for Grafana

- **Version Control**: Track all configuration changes in Git
- **Consistency**: Same configuration across dev/staging/prod
- **Automation**: Integrate with CI/CD pipelines
- **Rollback**: Easy reversion using Terraform state
- **Audit Trail**: Complete history of who changed what
- **Reduced Errors**: Eliminate manual configuration mistakes

---

## 2. Prerequisites

### Software Requirements

| Tool | Minimum Version | Purpose |
|------|-----------------|---------|
| Terraform | >= 1.0 | Infrastructure as Code tool |
| Grafana | >= 9.1 | For alerting features |
| Grafana Terraform Provider | >= 2.0 | Grafana resource management |

### Authentication Requirements

| Platform | Authentication Method |
|----------|----------------------|
| Grafana OSS | API Key or Basic Auth (username:password) |
| Amazon Managed Grafana | Workspace API Key (short-lived) |
| Azure Managed Grafana | Service Account Token via Azure CLI |

### Required Permissions

For full Terraform management, you need Admin-level access:
- Create/modify/delete dashboards, folders, data sources
- Manage alerting resources
- Create service accounts and API keys

---

## 3. Provider Setup

### 3.1 Grafana OSS (Self-Hosted)

```hcl
# versions.tf
terraform {
  required_version = ">= 1.0"
  required_providers {
    grafana = {
      source  = "grafana/grafana"
      version = ">= 2.0"
    }
  }
}

# provider.tf
provider "grafana" {
  url  = var.grafana_url    # e.g., "http://localhost:3000"
  auth = var.grafana_auth   # API key or "admin:admin"
}

# variables.tf
variable "grafana_url" {
  description = "Grafana server URL"
  type        = string
}

variable "grafana_auth" {
  description = "Grafana API key or username:password"
  type        = string
  sensitive   = true
}
```

### 3.2 Amazon Managed Grafana (AMG)

AMG uses a **two-plane architecture**:
- **Control Plane** (AWS Provider): Workspace, IAM roles, SSO
- **Data Plane** (Grafana Provider): Dashboards, data sources, alerts

```hcl
# versions.tf
terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = ">= 4.0"
    }
    grafana = {
      source  = "grafana/grafana"
      version = ">= 2.0"
    }
  }
}

# Control Plane: Create AMG Workspace
resource "aws_grafana_workspace" "main" {
  name                     = "my-grafana-workspace"
  account_access_type      = "CURRENT_ACCOUNT"
  authentication_providers = ["AWS_SSO"]
  permission_type          = "SERVICE_MANAGED"
  role_arn                 = aws_iam_role.grafana.arn
  data_sources             = ["CLOUDWATCH", "PROMETHEUS", "XRAY"]
}

# IAM Role for AMG
resource "aws_iam_role" "grafana" {
  name = "grafana-workspace-role"
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action    = "sts:AssumeRole"
      Effect    = "Allow"
      Principal = { Service = "grafana.amazonaws.com" }
    }]
  })
}

# API Key for Terraform (short-lived)
resource "aws_grafana_workspace_api_key" "terraform" {
  key_name        = "terraform-key"
  key_role        = "ADMIN"
  seconds_to_live = 3600
  workspace_id    = aws_grafana_workspace.main.id
}

# Data Plane: Grafana Provider
provider "grafana" {
  url  = aws_grafana_workspace.main.endpoint
  auth = aws_grafana_workspace_api_key.terraform.key
}
```

#### AMG API Key Best Practice

> **Important**: API keys expire. For production, manage keys outside Terraform.

```bash
# Create key before Terraform run
API_KEY=$(aws grafana create-workspace-api-key \
  --workspace-id $WORKSPACE_ID \
  --key-name "terraform-$(date +%s)" \
  --key-role ADMIN \
  --seconds-to-live 300 \
  --query 'key' --output text)

# Run Terraform
terraform apply -var="grafana_api_key=$API_KEY"

# Delete key after completion
aws grafana delete-workspace-api-key \
  --workspace-id $WORKSPACE_ID \
  --key-name "terraform-$(date +%s)"
```

### 3.3 Azure Managed Grafana

```hcl
# versions.tf
terraform {
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = ">= 3.0"
    }
    grafana = {
      source  = "grafana/grafana"
      version = ">= 2.0"
    }
  }
}

provider "azurerm" {
  features {}
}

# Create Azure Managed Grafana Instance
resource "azurerm_dashboard_grafana" "main" {
  name                              = "amg-${var.app_name}-${var.environment}"
  resource_group_name               = azurerm_resource_group.main.name
  location                          = azurerm_resource_group.main.location
  api_key_enabled                   = true
  deterministic_outbound_ip_enabled = true
  public_network_access_enabled     = true

  identity {
    type = "SystemAssigned"
  }
}

# Grant Monitoring Reader to Grafana
resource "azurerm_role_assignment" "grafana_monitoring" {
  scope                = data.azurerm_subscription.current.id
  role_definition_name = "Monitoring Reader"
  principal_id         = azurerm_dashboard_grafana.main.identity[0].principal_id
}

# Grant Grafana Admin to administrators
resource "azurerm_role_assignment" "grafana_admin" {
  scope                = azurerm_dashboard_grafana.main.id
  role_definition_name = "Grafana Admin"
  principal_id         = var.admin_group_id
}
```

#### Azure Service Account Setup

Use Azure CLI to create service account for Terraform:

```bash
# Install AMG extension
az extension add --name amg

# Create service account
az grafana service-account create \
  --name $GRAFANA_NAME \
  --service-account terraform \
  --role Admin

# Create token
GRAFANA_TOKEN=$(az grafana service-account token create \
  --name $GRAFANA_NAME \
  --service-account terraform \
  --token terraform-token \
  --time-to-live 1d \
  --query key -o tsv)

# Use in Terraform
export TF_VAR_grafana_auth=$GRAFANA_TOKEN
```

```hcl
# Grafana Provider for Azure
provider "grafana" {
  url  = azurerm_dashboard_grafana.main.endpoint
  auth = var.grafana_auth
}
```

---

## 4. Data Sources

Data sources connect Grafana to your metrics, logs, and traces backends.

### 4.1 Common Data Sources

```hcl
# Prometheus
resource "grafana_data_source" "prometheus" {
  type       = "prometheus"
  name       = "Prometheus"
  url        = "http://prometheus:9090"
  is_default = true

  json_data_encoded = jsonencode({
    httpMethod     = "POST"
    manageAlerts   = true
    prometheusType = "Prometheus"
  })
}

# Loki (Logs)
resource "grafana_data_source" "loki" {
  type = "loki"
  name = "Loki"
  url  = "http://loki:3100"

  json_data_encoded = jsonencode({
    maxLines = 1000
  })
}

# Elasticsearch
resource "grafana_data_source" "elasticsearch" {
  type     = "elasticsearch"
  name     = "Elasticsearch"
  url      = "http://elasticsearch:9200"
  database = "[logs-]YYYY.MM.DD"

  json_data_encoded = jsonencode({
    esVersion       = "8.0.0"
    timeField       = "@timestamp"
    logMessageField = "message"
  })
}
```

### 4.2 Cloud Provider Data Sources

```hcl
# AWS CloudWatch (for AMG)
resource "grafana_data_source" "cloudwatch" {
  type = "cloudwatch"
  name = "CloudWatch"

  json_data_encoded = jsonencode({
    defaultRegion = "us-east-1"
    authType      = "default"  # Uses workspace IAM role
  })
}

# Azure Monitor
resource "grafana_data_source" "azure_monitor" {
  type = "grafana-azure-monitor-datasource"
  name = "Azure Monitor"

  json_data_encoded = jsonencode({
    cloudName      = "azuremonitor"
    subscriptionId = var.azure_subscription_id
    tenantId       = var.azure_tenant_id
    clientId       = var.azure_client_id
  })

  secure_json_data_encoded = jsonencode({
    clientSecret = var.azure_client_secret
  })
}
```

### 4.3 Data Source with Authentication

```hcl
# Prometheus with Bearer Token
resource "grafana_data_source" "prometheus_secure" {
  type = "prometheus"
  name = "Prometheus-Secure"
  url  = "https://prometheus.example.com"

  json_data_encoded = jsonencode({
    httpMethod      = "POST"
    httpHeaderName1 = "Authorization"
  })

  secure_json_data_encoded = jsonencode({
    httpHeaderValue1 = "Bearer ${var.prometheus_token}"
  })
}
```

---

## 5. Folders & Permissions

Folders organize dashboards and provide permission boundaries.

### 5.1 Creating Folders

```hcl
resource "grafana_folder" "monitoring" {
  title = "System Monitoring"
  uid   = "system-monitoring"
}

resource "grafana_folder" "applications" {
  title = "Application Dashboards"
  uid   = "app-dashboards"
}

resource "grafana_folder" "alerts" {
  title = "Alert Rules"
  uid   = "alert-rules"
}
```

### 5.2 Folder Permissions

```hcl
resource "grafana_folder_permission" "monitoring_perms" {
  folder_uid = grafana_folder.monitoring.uid

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
```

---

## 6. Dashboards

### 6.1 Dashboard from JSON File

```hcl
resource "grafana_dashboard" "system_metrics" {
  config_json = file("${path.module}/dashboards/system-metrics.json")
  folder      = grafana_folder.monitoring.uid
  overwrite   = true
}
```

### 6.2 Multiple Dashboards from Directory

```hcl
resource "grafana_dashboard" "app_dashboards" {
  for_each    = fileset("${path.module}/dashboards/apps", "*.json")
  config_json = file("${path.module}/dashboards/apps/${each.value}")
  folder      = grafana_folder.applications.uid
}
```

### 6.3 Inline Dashboard Definition

```hcl
resource "grafana_dashboard" "cpu_overview" {
  config_json = jsonencode({
    title   = "CPU Overview"
    tags    = ["system", "cpu"]
    refresh = "30s"
    time    = { from = "now-1h", to = "now" }

    panels = [
      {
        id    = 1
        title = "CPU Usage"
        type  = "stat"
        gridPos = { h = 8, w = 12, x = 0, y = 0 }
        targets = [{
          expr  = "100 - (avg(irate(node_cpu_seconds_total{mode=\"idle\"}[5m])) * 100)"
          refId = "A"
        }]
        fieldConfig = {
          defaults = { unit = "percent", min = 0, max = 100 }
        }
      }
    ]
  })
  folder = grafana_folder.monitoring.uid
}
```

### 6.4 Dashboard with Template Variables

```hcl
resource "grafana_dashboard" "advanced" {
  config_json = jsonencode({
    title = "Advanced System Dashboard"
    tags  = ["system", "advanced"]

    templating = {
      list = [
        {
          name       = "instance"
          type       = "query"
          query      = "label_values(up, instance)"
          datasource = { type = "prometheus", uid = grafana_data_source.prometheus.uid }
          multi      = true
          includeAll = true
          refresh    = 1
        }
      ]
    }

    panels = [
      {
        id    = 1
        title = "CPU by Instance"
        type  = "timeseries"
        gridPos = { h = 8, w = 24, x = 0, y = 0 }
        targets = [{
          expr         = "100 - (avg by (instance) (irate(node_cpu_seconds_total{mode=\"idle\", instance=~\"$instance\"}[5m])) * 100)"
          legendFormat = "{{instance}}"
          refId        = "A"
        }]
      }
    ]
  })
  folder = grafana_folder.monitoring.uid
}
```

---

## 7. Alerting

Grafana Alerting (v9+) provides a complete alerting stack manageable via Terraform.

### Alerting Architecture

```
Alert Rules → Notification Policies → Contact Points → External Systems
                    ↓
              Mute Timings (optional)
```

### 7.1 Alert Rules

```hcl
resource "grafana_rule_group" "system_alerts" {
  name             = "system-alerts"
  folder_uid       = grafana_folder.alerts.uid
  interval_seconds = 60
  org_id           = 1

  rule {
    name      = "High CPU Usage"
    condition = "C"
    for       = "5m"

    # Query the datasource
    data {
      ref_id         = "A"
      datasource_uid = grafana_data_source.prometheus.uid
      relative_time_range { from = 600, to = 0 }
      model = jsonencode({
        expr  = "100 - (avg(irate(node_cpu_seconds_total{mode=\"idle\"}[5m])) * 100)"
        refId = "A"
      })
    }

    # Reduce to single value
    data {
      ref_id         = "B"
      datasource_uid = "__expr__"
      relative_time_range { from = 0, to = 0 }
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
      relative_time_range { from = 0, to = 0 }
      model = jsonencode({
        expression = "$B > 80"
        type       = "math"
        refId      = "C"
      })
    }

    no_data_state  = "NoData"
    exec_err_state = "Alerting"

    annotations = {
      summary     = "High CPU usage detected"
      description = "CPU usage is above 80% for more than 5 minutes"
    }

    labels = {
      severity = "warning"
      team     = "infrastructure"
    }
  }
}
```

### 7.2 Contact Points

```hcl
# Slack
resource "grafana_contact_point" "slack" {
  name = "Slack Alerts"

  slack {
    url = var.slack_webhook_url
    text = <<EOT
{{ len .Alerts.Firing }} alerts firing!
{{ range .Alerts.Firing }}
{{ template "Alert Instance Template" . }}
{{ end }}
EOT
  }
}

# Email
resource "grafana_contact_point" "email" {
  name = "Email Alerts"

  email {
    addresses = ["alerts@company.com"]
    subject   = "[{{ .Status | toUpper }}] {{ .GroupLabels.alertname }}"
  }
}

# PagerDuty
resource "grafana_contact_point" "pagerduty" {
  name = "PagerDuty Critical"

  pagerduty {
    integration_key = var.pagerduty_key
    severity        = "critical"
  }
}

# Reusable Message Template
resource "grafana_message_template" "alert_template" {
  name = "Alert Instance Template"

  template = <<EOT
{{ define "Alert Instance Template" }}
Firing: {{ .Labels.alertname }}
Silence: {{ .SilenceURL }}
{{ end }}
EOT
}
```

### 7.3 Notification Policies

```hcl
resource "grafana_notification_policy" "main" {
  group_by        = ["alertname"]
  contact_point   = grafana_contact_point.slack.name
  group_wait      = "45s"
  group_interval  = "6m"
  repeat_interval = "3h"

  # Route critical alerts to PagerDuty
  policy {
    matcher {
      label = "severity"
      match = "="
      value = "critical"
    }
    contact_point   = grafana_contact_point.pagerduty.name
    group_wait      = "10s"
    repeat_interval = "1h"
    mute_timings    = [grafana_mute_timing.weekends.name]
  }

  # Route database alerts to email
  policy {
    matcher {
      label = "team"
      match = "="
      value = "database"
    }
    contact_point = grafana_contact_point.email.name
  }
}
```

### 7.4 Mute Timings

```hcl
resource "grafana_mute_timing" "weekends" {
  name = "Weekend Mute"

  intervals {
    weekdays = ["saturday", "sunday"]
  }
}

resource "grafana_mute_timing" "maintenance" {
  name = "Maintenance Window"

  intervals {
    times {
      start = "02:00"
      end   = "04:00"
    }
    weekdays = ["sunday"]
  }
}
```

---

## 8. Access Control

### 8.1 Organizations

```hcl
resource "grafana_organization" "team_alpha" {
  name         = "Team Alpha"
  admin_user   = "admin"
  create_users = false
  admins       = ["admin@company.com"]
  editors      = ["editor@company.com"]
  viewers      = ["viewer@company.com"]
}
```

### 8.2 Teams

```hcl
resource "grafana_team" "devops" {
  name  = "DevOps Team"
  email = "devops@company.com"
}

resource "grafana_team" "platform" {
  name  = "Platform Team"
  email = "platform@company.com"
}
```

### 8.3 Service Accounts

```hcl
resource "grafana_service_account" "ci_cd" {
  name        = "ci-cd-automation"
  role        = "Editor"
  is_disabled = false
}

resource "grafana_service_account_token" "ci_cd" {
  name               = "ci-cd-token"
  service_account_id = grafana_service_account.ci_cd.id
  seconds_to_live    = 86400  # 24 hours
}

output "ci_cd_token" {
  value     = grafana_service_account_token.ci_cd.key
  sensitive = true
}
```

---

## 9. OnCall Management

Grafana OnCall manages incident response, on-call schedules, and escalations.

### 9.1 Provider Setup

```hcl
provider "grafana" {
  alias               = "oncall"
  oncall_access_token = var.oncall_token
  oncall_url          = "http://oncall:8080"  # Only for OSS, omit for Cloud
}
```

### 9.2 Integration

```hcl
resource "grafana_oncall_integration" "alertmanager" {
  provider = grafana.oncall
  name     = "Production Alertmanager"
  type     = "alertmanager"

  default_route {}
}
```

### 9.3 Escalation Chain

```hcl
resource "grafana_oncall_escalation_chain" "default" {
  provider = grafana.oncall
  name     = "Default Escalation"
}

resource "grafana_oncall_escalation" "notify_schedule" {
  provider                     = grafana.oncall
  escalation_chain_id          = grafana_oncall_escalation_chain.default.id
  type                         = "notify_on_call_from_schedule"
  notify_on_call_from_schedule = grafana_oncall_schedule.primary.id
  position                     = 0
}
```

### 9.4 On-Call Schedule

```hcl
resource "grafana_oncall_schedule" "primary" {
  provider  = grafana.oncall
  name      = "Primary On-Call"
  type      = "calendar"
  time_zone = "UTC"
  shifts    = [grafana_oncall_on_call_shift.weekly.id]
}

resource "grafana_oncall_on_call_shift" "weekly" {
  provider   = grafana.oncall
  name       = "Weekly Rotation"
  type       = "rolling_users"
  start      = "2024-01-01T00:00:00"
  duration   = 60 * 60 * 24  # 24 hours
  frequency  = "weekly"
  by_day     = ["MO", "TU", "WE", "TH", "FR", "SA", "SU"]
  week_start = "MO"
  time_zone  = "UTC"

  rolling_users = [
    [data.grafana_oncall_user.user1.id],
    [data.grafana_oncall_user.user2.id]
  ]
}
```

### 9.5 Alert Routing

```hcl
resource "grafana_oncall_route" "critical" {
  provider            = grafana.oncall
  integration_id      = grafana_oncall_integration.alertmanager.id
  escalation_chain_id = grafana_oncall_escalation_chain.critical.id
  routing_regex       = "\"severity\": \"critical\""
  position            = 0
}
```

---

## 10. Multi-Environment Patterns

### 10.1 Module Structure

```
terraform/
├── modules/
│   └── grafana/
│       ├── main.tf
│       ├── variables.tf
│       ├── outputs.tf
│       └── dashboards/
│           └── *.json
├── environments/
│   ├── dev/
│   │   ├── main.tf
│   │   └── terraform.tfvars
│   ├── staging/
│   └── prod/
```

### 10.2 Reusable Module

```hcl
# modules/grafana/variables.tf
variable "environment" { type = string }
variable "grafana_url" { type = string }
variable "grafana_auth" { type = string; sensitive = true }
variable "prometheus_url" { type = string }
variable "alerting_enabled" { type = bool; default = true }

# modules/grafana/main.tf
terraform {
  required_providers {
    grafana = { source = "grafana/grafana", version = ">= 2.0" }
  }
}

provider "grafana" {
  url  = var.grafana_url
  auth = var.grafana_auth
}

resource "grafana_folder" "main" {
  title = "${title(var.environment)} Monitoring"
  uid   = "${var.environment}-monitoring"
}

resource "grafana_data_source" "prometheus" {
  type       = "prometheus"
  name       = "Prometheus-${var.environment}"
  url        = var.prometheus_url
  is_default = true
}

resource "grafana_dashboard" "system" {
  count       = var.alerting_enabled ? 1 : 0
  config_json = file("${path.module}/dashboards/system.json")
  folder      = grafana_folder.main.uid
}
```

### 10.3 Environment Configuration

```hcl
# environments/prod/main.tf
module "grafana" {
  source = "../../modules/grafana"

  environment      = "prod"
  grafana_url      = "https://grafana.company.com"
  grafana_auth     = var.grafana_token
  prometheus_url   = "http://prometheus-prod:9090"
  alerting_enabled = true
}

# environments/dev/main.tf
module "grafana" {
  source = "../../modules/grafana"

  environment      = "dev"
  grafana_url      = "http://grafana-dev:3000"
  grafana_auth     = var.grafana_token
  prometheus_url   = "http://prometheus-dev:9090"
  alerting_enabled = false
}
```

---

## 11. CI/CD Integration

### 11.1 GitHub Actions

```yaml
name: Deploy Grafana Configuration

on:
  push:
    branches: [main]
    paths: ['terraform/grafana/**']
  pull_request:
    branches: [main]
    paths: ['terraform/grafana/**']

jobs:
  terraform:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Setup Terraform
        uses: hashicorp/setup-terraform@v3
        with:
          terraform_version: 1.6.0

      - name: Terraform Init
        run: terraform init
        working-directory: terraform/grafana

      - name: Terraform Format Check
        run: terraform fmt -check
        working-directory: terraform/grafana

      - name: Terraform Plan
        run: terraform plan -out=tfplan
        working-directory: terraform/grafana
        env:
          TF_VAR_grafana_auth: ${{ secrets.GRAFANA_TOKEN }}
          TF_VAR_grafana_url: ${{ secrets.GRAFANA_URL }}

      - name: Terraform Apply
        if: github.ref == 'refs/heads/main' && github.event_name == 'push'
        run: terraform apply -auto-approve tfplan
        working-directory: terraform/grafana
        env:
          TF_VAR_grafana_auth: ${{ secrets.GRAFANA_TOKEN }}
          TF_VAR_grafana_url: ${{ secrets.GRAFANA_URL }}
```

### 11.2 GitLab CI

```yaml
stages:
  - validate
  - plan
  - apply

variables:
  TF_ROOT: terraform/grafana

.terraform:
  image: hashicorp/terraform:1.6
  before_script:
    - cd $TF_ROOT
    - terraform init

validate:
  extends: .terraform
  stage: validate
  script:
    - terraform validate
    - terraform fmt -check

plan:
  extends: .terraform
  stage: plan
  script:
    - terraform plan -out=tfplan
  artifacts:
    paths: [$TF_ROOT/tfplan]
    expire_in: 1 week

apply:
  extends: .terraform
  stage: apply
  script:
    - terraform apply -auto-approve tfplan
  dependencies: [plan]
  only: [main]
  when: manual
```

---

## 12. Best Practices

### 12.1 State Management

```hcl
terraform {
  backend "s3" {
    bucket         = "company-terraform-state"
    key            = "grafana/terraform.tfstate"
    region         = "us-east-1"
    encrypt        = true
    dynamodb_table = "terraform-locks"
  }
}
```

### 12.2 Sensitive Data

```hcl
# Never hardcode secrets
variable "grafana_auth" {
  type      = string
  sensitive = true
}

# Use external secret management
data "aws_secretsmanager_secret_version" "grafana" {
  secret_id = "grafana/api-token"
}

locals {
  grafana_auth = jsondecode(data.aws_secretsmanager_secret_version.grafana.secret_string)["token"]
}
```

### 12.3 Resource Naming Convention

```hcl
locals {
  name_prefix = "${var.project}-${var.environment}"
}

resource "grafana_folder" "main" {
  title = "${local.name_prefix}-monitoring"
  uid   = "${local.name_prefix}-monitoring"
}
```

### 12.4 Dashboard Version Control

- Store dashboard JSON files in Git
- Use `file()` function to load dashboards
- Set `overwrite = true` to handle updates

### 12.5 Import Existing Resources

```bash
# Import existing dashboard
terraform import grafana_dashboard.existing <dashboard-uid>

# Import existing datasource
terraform import grafana_data_source.existing <datasource-id>

# Import existing folder
terraform import grafana_folder.existing <folder-uid>
```

---

## 13. Troubleshooting

### Common Issues

| Issue | Cause | Solution |
|-------|-------|----------|
| Authentication failed | Invalid/expired API key | Regenerate API key, check permissions |
| Resource not found | Wrong UID or ID | Use `terraform import` to sync state |
| AMG API key expired | TTL exceeded | Create new key before Terraform run |
| Azure access denied | Missing role assignment | Add Grafana Admin role to identity |
| State drift | Manual UI changes | Run `terraform refresh` then `plan` |

### Debugging Commands

```bash
# Test API connectivity
curl -H "Authorization: Bearer $GRAFANA_TOKEN" "$GRAFANA_URL/api/user"

# Refresh state
terraform refresh

# Show current state
terraform state list
terraform state show grafana_dashboard.main

# Remove problematic resource from state
terraform state rm grafana_dashboard.problematic

# Enable debug logging
export TF_LOG=DEBUG
terraform plan
```

---

## 14. References

### Official Documentation

- [Grafana Terraform Provider](https://registry.terraform.io/providers/grafana/grafana/latest/docs)
- [GitHub: terraform-provider-grafana](https://github.com/grafana/terraform-provider-grafana)
- [Provider Examples](https://github.com/grafana/terraform-provider-grafana/tree/main/examples)

### Platform-Specific Guides

- [AWS: AMG Terraform Alerting](https://docs.aws.amazon.com/grafana/latest/userguide/v10-alerting-setup-provision-terraform.html)
- [Azure: Managed Grafana with Terraform](https://learn.microsoft.com/en-us/azure/managed-grafana/)

### Blog Posts & Tutorials

- [Grafana Alerts as Code](https://grafana.com/blog/grafana-alerts-as-code-get-started-with-terraform-and-grafana-alerting/)
- [OnCall and Terraform](https://grafana.com/blog/2022/08/29/get-started-with-grafana-oncall-and-terraform/)

---

*Content was rephrased for compliance with licensing restrictions.*
