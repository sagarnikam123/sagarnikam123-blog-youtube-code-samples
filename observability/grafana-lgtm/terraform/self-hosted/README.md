# Grafana LGTM — Terraform configuration management

The official `grafana/grafana` Terraform provider manages Grafana resources on any self-hosted instance: dashboards, datasources, folders, alert rules, contact points, and more.

## What Terraform manages

- Grafana datasources (Mimir, Loki, Tempo)
- Folders and dashboards
- Alert rules and notification policies
- Service accounts and API keys

Terraform does **not** provision the LGTM stack itself. Deploy Grafana, Loki, Mimir, and Tempo first using Docker Compose or Helm.

## Configure credentials

```bash
export GRAFANA_URL="http://localhost:3000"
export GRAFANA_AUTH="your-service-account-token"
```

## Apply

```bash
terraform init
terraform plan
terraform apply
```

## Notes

- Create a service account in Grafana (Administration → Service Accounts) with Editor or Admin role.
- The provider works with any Grafana instance (self-hosted, Grafana Cloud, or Kubernetes).
- Pin the provider version for reproducible deployments.

Official sources:
- [Grafana Terraform provider](https://registry.terraform.io/providers/grafana/grafana/latest)
- [Grafana IaC docs](https://grafana.com/docs/grafana/latest/as-code/infrastructure-as-code/terraform/)
