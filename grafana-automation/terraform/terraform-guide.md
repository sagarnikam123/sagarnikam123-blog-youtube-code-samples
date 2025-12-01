# Terraform Grafana Provider Guide

Complete guide for managing Grafana resources using Terraform Infrastructure as Code.

## Overview

The Terraform Grafana Provider allows you to manage Grafana resources (dashboards, datasources, folders, alerts) using Infrastructure as Code principles with Terraform.

### Key Benefits:
- **Infrastructure as Code**: Version-controlled Grafana configuration
- **State Management**: Track resource changes and dependencies
- **Multi-Environment**: Consistent deployments across environments
- **Automation**: Integrate with CI/CD pipelines
- **Rollback**: Easy reversion using Terraform state

## Installation and Setup

### Provider Configuration
```hcl
# versions.tf
terraform {
  required_version = ">= 1.0"
  required_providers {
    grafana = {
      source  = "grafana/grafana"
      version = "~> 2.0"
    }
  }
}

# Configure the Grafana Provider
provider "grafana" {
  url  = var.grafana_url
  auth = var.grafana_token
  # org_id = 1  # Optional: specify organization ID
}
```

### Variables
```hcl
# variables.tf
variable "grafana_url" {
  description = "Grafana server URL"
  type        = string
  default     = "http://localhost:3000"
}

variable "grafana_token" {
  description = "Grafana API token"
  type        = string
  sensitive   = true
}

variable "environment" {
  description = "Environment name"
  type        = string
  default     = "dev"
}
```

### Terraform Configuration
```hcl
# terraform.tfvars
grafana_url   = "http://localhost:3000"
grafana_token = "your-api-token-here"
environment   = "production"
```

## Datasource Management

### Basic Datasources
```hcl
# datasources.tf

# Prometheus datasource
resource "grafana_data_source" "prometheus" {
  type       = "prometheus"
  name       = "Prometheus"
  url        = "http://prometheus:9090"
  is_default = true

  json_data_encoded = jsonencode({
    httpMethod     = "POST"
    manageAlerts   = true
    prometheusType = "Prometheus"
    cacheLevel     = "High"
  })
}

# Loki datasource
resource "grafana_data_source" "loki" {
  type = "loki"
  name = "Loki"
  url  = "http://loki:3100"

  json_data_encoded = jsonencode({
    maxLines = 1000
  })
}

# InfluxDB datasource
resource "grafana_data_source" "influxdb" {
  type     = "influxdb"
  name     = "InfluxDB"
  url      = "http://influxdb:8086"
  database = "telegraf"
  username = "admin"
  password = "admin"

  json_data_encoded = jsonencode({
    httpMode = "GET"
  })
}
```

### Advanced Datasource Configuration
```hcl
# advanced-datasources.tf

# Prometheus with authentication
resource "grafana_data_source" "prometheus_secure" {
  type       = "prometheus"
  name       = "Prometheus-Secure"
  url        = "https://prometheus.example.com"
  is_default = false

  json_data_encoded = jsonencode({
    httpMethod   = "POST"
    manageAlerts = true
    timeInterval = "15s"
    queryTimeout = "60s"
    httpHeaderName1 = "Authorization"
  })

  secure_json_data_encoded = jsonencode({
    httpHeaderValue1 = "Bearer ${var.prometheus_token}"
  })
}

# Jaeger datasource
resource "grafana_data_source" "jaeger" {
  type = "jaeger"
  name = "Jaeger"
  url  = "http://jaeger:14268"
  uid  = "jaeger-uid"

  json_data_encoded = jsonencode({
    tracesToLogs = {
      datasourceUid = grafana_data_source.loki.uid
      tags          = ["trace_id"]
    }
  })
}

# CloudWatch datasource
resource "grafana_data_source" "cloudwatch" {
  type = "cloudwatch"
  name = "CloudWatch"

  json_data_encoded = jsonencode({
    defaultRegion = "us-east-1"
    authType      = "keys"
  })

  secure_json_data_encoded = jsonencode({
    accessKey = var.aws_access_key
    secretKey = var.aws_secret_key
  })
}
```

### Environment-Specific Datasources
```hcl
# environment-datasources.tf

locals {
  datasource_configs = {
    dev = {
      prometheus_url = "http://prometheus-dev:9090"
      loki_url      = "http://loki-dev:3100"
    }
    staging = {
      prometheus_url = "http://prometheus-staging:9090"
      loki_url      = "http://loki-staging:3100"
    }
    prod = {
      prometheus_url = "http://prometheus-prod:9090"
      loki_url      = "http://loki-prod:3100"
    }
  }
}

resource "grafana_data_source" "prometheus_env" {
  type       = "prometheus"
  name       = "Prometheus-${var.environment}"
  url        = local.datasource_configs[var.environment].prometheus_url
  is_default = true

  json_data_encoded = jsonencode({
    httpMethod     = "POST"
    manageAlerts   = var.environment == "prod" ? true : false
    prometheusType = "Prometheus"
  })
}

resource "grafana_data_source" "loki_env" {
  type = "loki"
  name = "Loki-${var.environment}"
  url  = local.datasource_configs[var.environment].loki_url

  json_data_encoded = jsonencode({
    maxLines = var.environment == "prod" ? 5000 : 1000
  })
}
```

## Folder Management

### Basic Folders
```hcl
# folders.tf

resource "grafana_folder" "monitoring" {
  title = "System Monitoring"
  uid   = "system-monitoring"
}

resource "grafana_folder" "applications" {
  title = "Application Dashboards"
  uid   = "app-dashboards"
}

resource "grafana_folder" "business" {
  title = "Business Metrics"
  uid   = "business-metrics"
}
```

### Folder Permissions
```hcl
# folder-permissions.tf

resource "grafana_folder_permission" "monitoring_permissions" {
  folder_uid = grafana_folder.monitoring.uid

  permissions {
    role       = "Editor"
    permission = "Edit"
  }

  permissions {
    role       = "Viewer"
    permission = "View"
  }

  permissions {
    team_id    = grafana_team.devops.id
    permission = "Admin"
  }
}

resource "grafana_team" "devops" {
  name  = "DevOps Team"
  email = "devops@company.com"
}
```

## Dashboard Management

### Simple Dashboard
```hcl
# dashboards.tf

resource "grafana_dashboard" "system_metrics" {
  config_json = jsonencode({
    title = "System Metrics"
    tags  = ["system", "monitoring"]

    panels = [
      {
        id    = 1
        title = "CPU Usage"
        type  = "stat"
        targets = [
          {
            expr  = "100 - (avg(irate(node_cpu_seconds_total{mode=\"idle\"}[5m])) * 100)"
            refId = "A"
          }
        ]
        gridPos = {
          h = 8
          w = 12
          x = 0
          y = 0
        }
        fieldConfig = {
          defaults = {
            unit = "percent"
            min  = 0
            max  = 100
          }
        }
      }
    ]

    time = {
      from = "now-1h"
      to   = "now"
    }

    refresh = "30s"
  })

  folder = grafana_folder.monitoring.id
}
```

### Complex Dashboard with Template Variables
```hcl
# complex-dashboard.tf

locals {
  dashboard_config = {
    title = "Advanced System Dashboard"
    tags  = ["system", "monitoring", "advanced"]

    templating = {
      list = [
        {
          name  = "instance"
          type  = "query"
          query = "label_values(up, instance)"
          datasource = {
            type = "prometheus"
            uid  = grafana_data_source.prometheus.uid
          }
          multi       = true
          includeAll  = true
          allValue    = ".*"
          refresh     = 1
        },
        {
          name  = "job"
          type  = "query"
          query = "label_values(up, job)"
          datasource = {
            type = "prometheus"
            uid  = grafana_data_source.prometheus.uid
          }
          multi      = false
          includeAll = false
          refresh    = 1
        }
      ]
    }

    panels = [
      {
        id    = 1
        title = "CPU Usage by Instance"
        type  = "timeseries"
        targets = [
          {
            expr  = "100 - (avg by (instance) (irate(node_cpu_seconds_total{mode=\"idle\", instance=~\"$instance\", job=\"$job\"}[5m])) * 100)"
            refId = "A"
            legendFormat = "{{instance}}"
          }
        ]
        gridPos = {
          h = 8
          w = 24
          x = 0
          y = 0
        }
        fieldConfig = {
          defaults = {
            unit = "percent"
            min  = 0
            max  = 100
          }
        }
      },
      {
        id    = 2
        title = "Memory Usage by Instance"
        type  = "timeseries"
        targets = [
          {
            expr  = "(1 - (node_memory_MemAvailable_bytes{instance=~\"$instance\", job=\"$job\"} / node_memory_MemTotal_bytes{instance=~\"$instance\", job=\"$job\"})) * 100"
            refId = "B"
            legendFormat = "{{instance}}"
          }
        ]
        gridPos = {
          h = 8
          w = 24
          x = 0
          y = 8
        }
        fieldConfig = {
          defaults = {
            unit = "percent"
            min  = 0
            max  = 100
          }
        }
      }
    ]

    time = {
      from = "now-6h"
      to   = "now"
    }

    refresh = "30s"
  }
}

resource "grafana_dashboard" "advanced_system" {
  config_json = jsonencode(local.dashboard_config)
  folder      = grafana_folder.monitoring.id
}
```

### Dashboard from File
```hcl
# dashboard-from-file.tf

resource "grafana_dashboard" "imported_dashboard" {
  config_json = file("${path.module}/dashboards/system-overview.json")
  folder      = grafana_folder.monitoring.id
}

# Multiple dashboards from directory
resource "grafana_dashboard" "app_dashboards" {
  for_each = fileset("${path.module}/dashboards/apps", "*.json")

  config_json = file("${path.module}/dashboards/apps/${each.value}")
  folder      = grafana_folder.applications.id
}
```

## Alert Management

### Alert Rules
```hcl
# alerts.tf

resource "grafana_rule_group" "system_alerts" {
  name             = "system-alerts"
  folder_uid       = grafana_folder.monitoring.uid
  interval_seconds = 60

  rule {
    name      = "HighCPUUsage"
    condition = "A"

    data {
      ref_id = "A"

      relative_time_range {
        from = 300
        to   = 0
      }

      datasource_uid = grafana_data_source.prometheus.uid
      model = jsonencode({
        expr  = "100 - (avg(irate(node_cpu_seconds_total{mode=\"idle\"}[5m])) * 100)"
        refId = "A"
      })
    }

    no_data_state  = "NoData"
    exec_err_state = "Alerting"
    for            = "5m"

    annotations = {
      description = "CPU usage is above 80%"
      summary     = "High CPU usage detected"
    }

    labels = {
      severity = "warning"
      team     = "infrastructure"
    }
  }

  rule {
    name      = "HighMemoryUsage"
    condition = "B"

    data {
      ref_id = "B"

      relative_time_range {
        from = 300
        to   = 0
      }

      datasource_uid = grafana_data_source.prometheus.uid
      model = jsonencode({
        expr  = "(1 - (node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes)) * 100"
        refId = "B"
      })
    }

    no_data_state  = "NoData"
    exec_err_state = "Alerting"
    for            = "5m"

    annotations = {
      description = "Memory usage is above 85%"
      summary     = "High memory usage detected"
    }

    labels = {
      severity = "critical"
      team     = "infrastructure"
    }
  }
}
```

### Contact Points
```hcl
# contact-points.tf

resource "grafana_contact_point" "slack_alerts" {
  name = "slack-alerts"

  slack {
    url      = var.slack_webhook_url
    channel  = "#alerts"
    username = "Grafana"
    title    = "🚨 Grafana Alert"
    text     = <<-EOT
      {{ range .Alerts }}
      **{{ .Annotations.summary }}**
      {{ .Annotations.description }}
      Labels: {{ range .Labels.SortedPairs }}{{ .Name }}={{ .Value }} {{ end }}
      {{ end }}
    EOT
  }
}

resource "grafana_contact_point" "email_alerts" {
  name = "email-alerts"

  email {
    addresses = ["alerts@company.com", "oncall@company.com"]
    subject   = "[{{ .Status | toUpper }}] {{ .GroupLabels.alertname }}"
    message   = <<-EOT
      {{ range .Alerts }}
      Alert: {{ .Annotations.summary }}
      Description: {{ .Annotations.description }}
      Labels: {{ range .Labels.SortedPairs }}{{ .Name }}={{ .Value }} {{ end }}
      {{ end }}
    EOT
  }
}

resource "grafana_contact_point" "pagerduty_critical" {
  name = "pagerduty-critical"

  pagerduty {
    integration_key = var.pagerduty_integration_key
    severity        = "critical"
    component       = "Grafana"
    group           = "Infrastructure"
  }
}
```

### Notification Policies
```hcl
# notification-policies.tf

resource "grafana_notification_policy" "default_policy" {
  group_by      = ["grafana_folder", "alertname"]
  contact_point = grafana_contact_point.slack_alerts.name

  group_wait      = "10s"
  group_interval  = "5m"
  repeat_interval = "12h"

  policy {
    matcher {
      label = "severity"
      match = "="
      value = "critical"
    }
    contact_point   = grafana_contact_point.pagerduty_critical.name
    group_wait      = "5s"
    group_interval  = "2m"
    repeat_interval = "1h"
  }

  policy {
    matcher {
      label = "team"
      match = "="
      value = "database"
    }
    contact_point   = grafana_contact_point.email_alerts.name
    group_wait      = "15s"
    group_interval  = "5m"
    repeat_interval = "6h"
  }
}
```

## User and Team Management

### Teams
```hcl
# teams.tf

resource "grafana_team" "devops" {
  name  = "DevOps Team"
  email = "devops@company.com"
}

resource "grafana_team" "platform" {
  name  = "Platform Team"
  email = "platform@company.com"
}

resource "grafana_team" "security" {
  name  = "Security Team"
  email = "security@company.com"
}
```

### Users
```hcl
# users.tf

resource "grafana_user" "john_doe" {
  email    = "john.doe@company.com"
  name     = "John Doe"
  login    = "john.doe"
  password = "temporary-password"
  is_admin = false
}

resource "grafana_team_preferences" "devops_preferences" {
  team_id           = grafana_team.devops.id
  theme             = "dark"
  home_dashboard_id = grafana_dashboard.system_metrics.dashboard_id
  timezone          = "UTC"
}
```

## Multi-Environment Setup

### Environment-Specific Configuration
```hcl
# environments/dev/main.tf
module "grafana_dev" {
  source = "../../modules/grafana"

  environment    = "dev"
  grafana_url    = "http://grafana-dev.company.com"
  grafana_token  = var.dev_grafana_token

  prometheus_url = "http://prometheus-dev:9090"
  loki_url      = "http://loki-dev:3100"

  alert_enabled = false
}

# environments/prod/main.tf
module "grafana_prod" {
  source = "../../modules/grafana"

  environment    = "prod"
  grafana_url    = "https://grafana.company.com"
  grafana_token  = var.prod_grafana_token

  prometheus_url = "http://prometheus-prod:9090"
  loki_url      = "http://loki-prod:3100"

  alert_enabled = true
}
```

### Grafana Module
```hcl
# modules/grafana/main.tf

variable "environment" {
  description = "Environment name"
  type        = string
}

variable "grafana_url" {
  description = "Grafana URL"
  type        = string
}

variable "grafana_token" {
  description = "Grafana API token"
  type        = string
  sensitive   = true
}

variable "prometheus_url" {
  description = "Prometheus URL"
  type        = string
}

variable "loki_url" {
  description = "Loki URL"
  type        = string
}

variable "alert_enabled" {
  description = "Enable alerting"
  type        = bool
  default     = true
}

# Provider configuration
terraform {
  required_providers {
    grafana = {
      source  = "grafana/grafana"
      version = "~> 2.0"
    }
  }
}

provider "grafana" {
  url  = var.grafana_url
  auth = var.grafana_token
}

# Resources
resource "grafana_folder" "monitoring" {
  title = "${title(var.environment)} Monitoring"
  uid   = "${var.environment}-monitoring"
}

resource "grafana_data_source" "prometheus" {
  type       = "prometheus"
  name       = "Prometheus-${var.environment}"
  url        = var.prometheus_url
  is_default = true
}

resource "grafana_data_source" "loki" {
  type = "loki"
  name = "Loki-${var.environment}"
  url  = var.loki_url
}

resource "grafana_dashboard" "system_overview" {
  count = var.alert_enabled ? 1 : 0

  config_json = templatefile("${path.module}/templates/system-dashboard.json.tpl", {
    environment    = var.environment
    prometheus_uid = grafana_data_source.prometheus.uid
  })

  folder = grafana_folder.monitoring.id
}
```

## Advanced Patterns

### Dynamic Dashboard Generation
```hcl
# dynamic-dashboards.tf

locals {
  services = ["api", "database", "cache", "queue"]

  service_dashboards = {
    for service in local.services : service => {
      title = "${title(service)} Service Dashboard"
      panels = [
        {
          title = "${title(service)} Response Time"
          expr  = "histogram_quantile(0.95, rate(http_request_duration_seconds_bucket{service=\"${service}\"}[5m]))"
        },
        {
          title = "${title(service)} Error Rate"
          expr  = "rate(http_requests_total{service=\"${service}\", status=~\"5..\"}[5m])"
        }
      ]
    }
  }
}

resource "grafana_dashboard" "service_dashboards" {
  for_each = local.service_dashboards

  config_json = jsonencode({
    title = each.value.title
    tags  = ["service", each.key]

    panels = [
      for i, panel in each.value.panels : {
        id    = i + 1
        title = panel.title
        type  = "timeseries"
        targets = [
          {
            expr  = panel.expr
            refId = "A"
          }
        ]
        gridPos = {
          h = 8
          w = 12
          x = (i % 2) * 12
          y = floor(i / 2) * 8
        }
      }
    ]
  })

  folder = grafana_folder.applications.id
}
```

### Conditional Resources
```hcl
# conditional-resources.tf

resource "grafana_rule_group" "production_alerts" {
  count = var.environment == "prod" ? 1 : 0

  name             = "production-critical-alerts"
  folder_uid       = grafana_folder.monitoring.uid
  interval_seconds = 30

  rule {
    name      = "ServiceDown"
    condition = "A"

    data {
      ref_id = "A"

      relative_time_range {
        from = 60
        to   = 0
      }

      datasource_uid = grafana_data_source.prometheus.uid
      model = jsonencode({
        expr  = "up{job=\"api\"} == 0"
        refId = "A"
      })
    }

    no_data_state  = "Alerting"
    exec_err_state = "Alerting"
    for            = "1m"

    annotations = {
      description = "Service is down"
      summary     = "Critical service failure"
    }

    labels = {
      severity = "critical"
    }
  }
}
```

## CI/CD Integration

### GitHub Actions
```yaml
# .github/workflows/terraform-grafana.yml
name: Deploy Grafana Configuration

on:
  push:
    branches: [main]
    paths: ['terraform/grafana/**']

jobs:
  terraform:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v3

      - name: Setup Terraform
        uses: hashicorp/setup-terraform@v2
        with:
          terraform_version: 1.5.0

      - name: Terraform Init
        run: terraform init
        working-directory: terraform/grafana

      - name: Terraform Plan
        run: terraform plan
        working-directory: terraform/grafana
        env:
          TF_VAR_grafana_token: ${{ secrets.GRAFANA_TOKEN }}
          TF_VAR_grafana_url: ${{ secrets.GRAFANA_URL }}

      - name: Terraform Apply
        if: github.ref == 'refs/heads/main'
        run: terraform apply -auto-approve
        working-directory: terraform/grafana
        env:
          TF_VAR_grafana_token: ${{ secrets.GRAFANA_TOKEN }}
          TF_VAR_grafana_url: ${{ secrets.GRAFANA_URL }}
```

### GitLab CI
```yaml
# .gitlab-ci.yml
stages:
  - validate
  - plan
  - apply

variables:
  TF_ROOT: terraform/grafana

before_script:
  - cd $TF_ROOT
  - terraform init

validate:
  stage: validate
  script:
    - terraform validate
    - terraform fmt -check

plan:
  stage: plan
  script:
    - terraform plan -out=tfplan
  artifacts:
    paths:
      - $TF_ROOT/tfplan
    expire_in: 1 week

apply:
  stage: apply
  script:
    - terraform apply -auto-approve tfplan
  dependencies:
    - plan
  only:
    - main
```

## Best Practices

### 1. State Management
```hcl
# backend.tf
terraform {
  backend "s3" {
    bucket = "company-terraform-state"
    key    = "grafana/terraform.tfstate"
    region = "us-east-1"
  }
}
```

### 2. Resource Naming
```hcl
locals {
  name_prefix = "${var.environment}-${var.project}"

  common_tags = {
    Environment = var.environment
    Project     = var.project
    ManagedBy   = "terraform"
  }
}

resource "grafana_folder" "monitoring" {
  title = "${local.name_prefix}-monitoring"
  uid   = "${local.name_prefix}-monitoring"
}
```

### 3. Sensitive Data
```hcl
# Use Terraform variables for sensitive data
variable "grafana_token" {
  description = "Grafana API token"
  type        = string
  sensitive   = true
}

# Use external data sources for secrets
data "aws_secretsmanager_secret_version" "grafana_token" {
  secret_id = "grafana/api-token"
}

locals {
  grafana_token = jsondecode(data.aws_secretsmanager_secret_version.grafana_token.secret_string)["token"]
}
```

### 4. Validation
```hcl
variable "environment" {
  description = "Environment name"
  type        = string

  validation {
    condition     = contains(["dev", "staging", "prod"], var.environment)
    error_message = "Environment must be dev, staging, or prod."
  }
}
```

## Troubleshooting

### Common Issues

1. **Provider Authentication**
   ```bash
   # Test API connectivity
   curl -H "Authorization: Bearer $GRAFANA_TOKEN" \
        "$GRAFANA_URL/api/user"
   ```

2. **Resource Import**
   ```bash
   # Import existing dashboard
   terraform import grafana_dashboard.existing <dashboard-uid>

   # Import existing datasource
   terraform import grafana_data_source.existing <datasource-id>
   ```

3. **State Issues**
   ```bash
   # Refresh state
   terraform refresh

   # Remove resource from state
   terraform state rm grafana_dashboard.problematic
   ```

## References

- [Terraform Grafana Provider Documentation](https://registry.terraform.io/providers/grafana/grafana/latest/docs)
- [Grafana API Documentation](https://grafana.com/docs/grafana/latest/developers/http_api/)
- [Terraform Best Practices](https://www.terraform.io/docs/cloud/guides/recommended-practices/index.html)
