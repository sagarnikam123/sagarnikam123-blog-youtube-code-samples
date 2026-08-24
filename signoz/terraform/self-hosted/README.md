# SigNoz — Terraform configuration management

The `SigNoz/signoz` Terraform provider manages SigNoz resources on any self-hosted instance: alert rules and dashboards.

## What Terraform manages

- Alert rules (v2 API, `signoz_rule` resource)
- Dashboards (`signoz_dashboard` resource)

Terraform does **not** provision the SigNoz platform itself. Deploy first using Docker Compose, Helm, or Foundry.

## Configure credentials

```bash
export SIGNOZ_ENDPOINT="http://localhost:8080"
export SIGNOZ_API_TOKEN="your-api-token"
```

Create an API token in SigNoz: Settings → API Tokens.

## Apply

```bash
terraform init
terraform plan
terraform apply
```

## Notes

- Provider v0.1.0+ uses the v2 rules API (`signoz_rule` resource, not the old `signoz_alert`).
- The provider is community-tier on the Terraform Registry.
- Pin the provider version for reproducibility.

Official sources:
- [SigNoz Terraform provider](https://registry.terraform.io/providers/SigNoz/signoz/latest)
- [SigNoz Terraform alerts docs](https://signoz.io/docs/alerts-management/terraform-provider-signoz/)
- [SigNoz Terraform dashboards docs](https://signoz.io/docs/dashboards/terraform-provider-signoz/)
