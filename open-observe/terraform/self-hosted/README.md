# OpenObserve — Terraform configuration management

The official `openobserve/openobserve` Terraform provider manages OpenObserve resources on any self-hosted instance: streams, dashboards, users, and organizations.

## What Terraform manages

- Streams (with retention, full-text search keys, index fields)
- Dashboards
- Users and organizations
- Alert rules

Terraform does **not** provision the OpenObserve platform itself. Deploy first using Docker, Helm, or binary.

## Configure credentials

```bash
export OPENOBSERVE_URL="http://localhost:5080"
export OPENOBSERVE_USERNAME="root@example.com"
export OPENOBSERVE_PASSWORD="Complexpass#123"
```

## Apply

```bash
terraform init
terraform plan
terraform apply
```

Official sources:
- [OpenObserve Terraform provider](https://registry.terraform.io/providers/openobserve/openobserve/latest)
- [OpenObserve Terraform docs](https://openobserve.ai/docs/enterprise-setup/terraform/)
