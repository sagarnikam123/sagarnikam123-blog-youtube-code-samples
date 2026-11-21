# ClickStack Terraform — self-hosted/free edition

The official `ClickHouse/clickhouse` Terraform provider can manage ClickStack configuration for both self-hosted ClickStack and ClickHouse Cloud. This example manages a dashboard in a free, self-hosted ClickStack deployment.

## What Terraform manages

- ClickStack dashboards through `clickhouse_clickstack_dashboard`
- Dashboard JSON, tiles, filters, and source references
- Optional non-default team scoping

The provider does **not** provision ClickStack, ClickHouse, MongoDB, or the OTel Collector. Start ClickStack first with the repository's Docker Compose or Helm installation, then use this directory to manage configuration.

## Prerequisites

- Terraform 1.5 or later
- ClickStack already running
- A personal ClickStack API access key
- A ClickStack logs source ID

The ClickStack Terraform resources are beta in provider `3.25.0`; review provider release notes before upgrading.

## Configure self-hosted credentials

Keep the API key out of Terraform files and state inputs:

```bash
export CLICKSTACK_ENDPOINT="http://localhost:8080"
export CLICKSTACK_API_KEY="replace-with-personal-clickstack-api-key"
```

For a non-default team, set `team_id` in `terraform.tfvars`.

## Apply

```bash
cp terraform.tfvars.example terraform.tfvars
# Edit terraform.tfvars and set logs_source_id.
terraform init
terraform fmt
terraform validate
terraform plan
terraform apply
```

To import an existing dashboard, declare a matching resource and run:

```bash
terraform import clickhouse_clickstack_dashboard.logs <dashboard-id>
```

For a non-default self-hosted team, use `<team-id>/<dashboard-id>` as the import ID.

## Important behavior

Manage a dashboard from one source of truth. UI edits are not represented as full drift; a later Terraform update can overwrite the dashboard definition.

Official announcement: [ClickStack Terraform provider](https://clickhouse.com/blog/clickstack-terraform-provider).
