# Grafana Terraform Multi-Instance Management

Manage 30+ Grafana OSS instances with varying configurations using a modular approach.

## Folder Structure

```
terraform/
├── modules/                          # Reusable modules
│   └── grafana-core/                 # Core Grafana resources
│       ├── main.tf                   # Provider config
│       ├── variables.tf              # Input variables (feature flags)
│       ├── outputs.tf                # Outputs
│       ├── folders.tf                # Folder resources
│       ├── datasources.tf            # Datasource resources (conditional)
│       ├── dashboards.tf             # Dashboard resources (conditional)
│       └── alerting.tf               # Alerting resources (conditional)
│
├── instances/                        # Per-instance configurations
│   ├── _template/                    # Copy this for new instances
│   │   ├── main.tf
│   │   └── terraform.tfvars.example
│   │
│   ├── grafana-oss-local/            # Local dev - Prometheus + Loki
│   ├── grafana-oss-dev/              # Dev - Only Loki, no dashboards
│   ├── grafana-oss-staging/          # Staging - Multiple DS, 3 alerts
│   ├── grafana-oss-prod/             # Prod - Full setup with teams
│   └── ... (add more instances)
│
├── shared/                           # Shared resources across instances
│   ├── dashboards/                   # Common dashboard JSONs
│   └── alert-templates/              # Common alert rule templates
│
├── grafana-oss/                      # Step-by-step learning (original)
└── terraform-guide.md                # Documentation
```

## Instance Configurations

| Instance | Datasources | Dashboards | Alerts | Teams |
|----------|-------------|------------|--------|-------|
| grafana-oss-local | Prometheus + Loki | ✅ | ❌ | ❌ |
| grafana-oss-dev | Loki only | ❌ | ❌ | ❌ |
| grafana-oss-staging | Multiple | ✅ | 3 rules | ❌ |
| grafana-oss-prod | Multiple | ✅ | Many | ✅ |

## Quick Start

```bash
# 1. Go to instance directory
cd instances/grafana-oss-dev

# 2. Copy and configure
cp terraform.tfvars.example terraform.tfvars
# Edit terraform.tfvars with your values

# 3. Initialize and apply
terraform init
terraform apply
```

## Adding New Instance

```bash
# 1. Copy template
cp -r instances/_template instances/grafana-oss-newinstance

# 2. Configure
cd instances/grafana-oss-newinstance
cp terraform.tfvars.example terraform.tfvars
# Edit terraform.tfvars - enable only what you need

# 3. Apply
terraform init
terraform apply
```

## Feature Flags

Each instance can enable/disable features independently:

```hcl
# terraform.tfvars
enable_folders     = true   # Always true
enable_datasources = true   # Configure which datasources
enable_dashboards  = false  # Set true if you have dashboards
enable_alerting    = false  # Set true + provide webhook_url
enable_teams       = false  # Set true for access control
```

## Datasource Examples

```hcl
# Only Loki
datasources = {
  Loki = {
    type       = "loki"
    url        = "http://loki:3100"
    is_default = true
  }
}

# Multiple datasources
datasources = {
  Prometheus = {
    type       = "prometheus"
    url        = "http://prometheus:9090"
    is_default = true
  }
  Loki = {
    type = "loki"
    url  = "http://loki:3100"
  }
  CloudWatch = {
    type      = "cloudwatch"
    json_data = { defaultRegion = "us-east-1" }
  }
}
```

## Bulk Import Scripts

Shared scripts in `scripts/` work with any instance:

```bash
cd instances/grafana-oss-dev

# Import all resources (folders, datasources, dashboards)
../../scripts/bulk-import-all.sh --url http://localhost:3000 --token your-token

# Or individual imports
../../scripts/bulk-import-folders.sh --url $URL --token $TOKEN
../../scripts/bulk-import-datasources.sh --url $URL --token $TOKEN
../../scripts/bulk-import-dashboards.sh --url $URL --token $TOKEN

# Preview mode
../../scripts/bulk-import-all.sh --url $URL --token $TOKEN --dry-run

# Generate .tf files only (no import)
../../scripts/bulk-import-all.sh --url $URL --token $TOKEN --generate
```

See [scripts/README.md](scripts/README.md) for full documentation.

## Bulk Operations

Apply to all instances:

```bash
for dir in instances/grafana-oss-*/; do
  echo "Applying $dir"
  (cd "$dir" && terraform init && terraform apply -auto-approve)
done
```

## References

- [Terraform Guide](terraform-guide.md)
- [Step-by-Step Learning](grafana-oss/STEPS.md)
- [Grafana Provider Docs](https://registry.terraform.io/providers/grafana/grafana/latest/docs)
