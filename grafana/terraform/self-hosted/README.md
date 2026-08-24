# Grafana — Terraform configuration management

The official `grafana/grafana` Terraform provider manages Grafana resources on any self-hosted instance: folders, datasources, dashboards, alert rules, contact points, notification policies, service accounts, and more.

## What Terraform manages

- Folders and dashboards (JSON model)
- Datasources (Prometheus, Loki, Tempo, etc.)
- Alerting (rules, contact points, notification policies, mute timings)
- Service accounts and API keys
- Library panels and playlists
- Annotations and SLOs

Terraform does **not** install Grafana. Deploy first using Docker, Helm, binary, or operator.

## Prerequisites

- Grafana running and accessible
- A service account token (Administration → Service Accounts → Add service account → Create token)
- Terraform 1.5+

## Configure credentials

```bash
export GRAFANA_URL="http://localhost:3000"
export GRAFANA_AUTH="your-service-account-token"
```

Or set them in `terraform.tfvars`:

```hcl
grafana_url  = "http://localhost:3000"
grafana_auth = "glsa_xxxxxxxxxxxx"
```

## Apply

```bash
terraform init
terraform fmt
terraform validate
terraform plan
terraform apply
```

## Import existing resources

```bash
# Import a dashboard by UID
terraform import grafana_dashboard.example <dashboard-uid>

# Import a folder by UID
terraform import grafana_folder.observability <folder-uid>

# Import a datasource by ID
terraform import grafana_data_source.prometheus <datasource-id>
```

## Notes

- The provider works with self-hosted Grafana OSS, Grafana Enterprise, and Grafana Cloud.
- Pin the provider version for reproducible deployments.
- Use service account tokens (not legacy API keys) for authentication.
- Dashboards are managed as JSON — use `config_json` with `jsonencode()`.

Official sources:
- [Grafana Terraform provider](https://registry.terraform.io/providers/grafana/grafana/latest)
- [Deploy dashboards with Terraform](https://grafana.com/docs/learning-paths/deploy-dashboard-terraform/configure-provider/)
- [Provider documentation](https://grafana.com/docs/grafana/latest/as-code/infrastructure-as-code/terraform/)
