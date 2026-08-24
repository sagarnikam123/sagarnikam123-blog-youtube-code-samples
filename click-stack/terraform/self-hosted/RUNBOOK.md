# ClickStack Terraform — Self-Hosted Runbook

Step-by-step commands to manage a free/self-hosted ClickStack deployment with Terraform.

## Prerequisites

- Terraform >= 1.5
- ClickStack already running (Docker Compose or Helm)
- A personal ClickStack API access key (create in ClickStack UI → Settings → API Keys)
- A ClickStack logs source ID (from ClickStack UI → Settings → Sources)

## 1. Set credentials

```bash
export CLICKSTACK_ENDPOINT="http://localhost:8080"
export CLICKSTACK_API_KEY="your-personal-clickstack-api-key"
```

## 2. Discover available sources and connections

```bash
curl -s -H "Authorization: Bearer ${CLICKSTACK_API_KEY}" \
  "${CLICKSTACK_ENDPOINT}/api/v1/sources" | jq '.[] | {id, name, kind}'
```

```bash
curl -s -H "Authorization: Bearer ${CLICKSTACK_API_KEY}" \
  "${CLICKSTACK_ENDPOINT}/api/v1/connections" | jq '.[] | {id, name}'
```

## 3. Configure variables

```bash
cd click-stack/terraform/self-hosted

cp terraform.tfvars.example terraform.tfvars
```

Edit `terraform.tfvars`:

```hcl
logs_source_id = "paste-source-id-here"
# team_id      = "paste-team-id-here"   # only for non-default team
```

## 4. Initialize Terraform

```bash
terraform init
```

Expected output includes installing `clickhouse/clickhouse v3.25.0`.

## 5. Format and validate

```bash
terraform fmt
terraform validate
```

You will see an alpha-resource warning for `clickhouse_clickstack_dashboard`; that is expected during beta.

## 6. Plan

```bash
terraform plan
```

Review the plan output. Confirm one `clickhouse_clickstack_dashboard` resource will be created.

## 7. Apply

```bash
terraform apply
```

Type `yes` when prompted. On success, the dashboard ID is printed:

```
Apply complete! Resources: 1 added, 0 changed, 0 destroyed.

Outputs:

dashboard_id = "..."
```

Open ClickStack → Dashboards to verify the new dashboard.

## 8. Update a dashboard

Edit `main.tf` (tile name, source, filters, etc.), then:

```bash
terraform plan
terraform apply
```

## 9. Import an existing dashboard

Add a matching `clickhouse_clickstack_dashboard` resource block first, then:

```bash
terraform import clickhouse_clickstack_dashboard.logs <dashboard-id>
```

For a non-default team:

```bash
terraform import clickhouse_clickstack_dashboard.logs <team-id>/<dashboard-id>
```

## 10. Bulk-export existing ClickStack resources

From the ClickStack UI, open any resource → click the Terraform icon → copy the import block. Then:

```bash
terraform plan -generate-config-out=generated.tf
```

## 11. Destroy

```bash
terraform destroy
```

Type `yes` to confirm dashboard removal.

## Notes

- Manage each dashboard from one source of truth (Terraform or UI, not both).
- UI edits are not surfaced as drift; a subsequent `terraform apply` will overwrite them.
- The ClickStack Terraform resources are beta; pin the provider version.
- Terraform does not provision ClickStack itself. Use Docker Compose or Helm first.

## Reference

- [ClickStack Terraform provider announcement](https://clickhouse.com/blog/clickstack-terraform-provider)
- [ClickHouse/clickhouse provider](https://registry.terraform.io/providers/ClickHouse/clickhouse/latest)
- [Provider source](https://github.com/ClickHouse/terraform-provider-clickhouse)
