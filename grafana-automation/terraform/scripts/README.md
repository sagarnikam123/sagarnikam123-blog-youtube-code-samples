# Shared Bulk Import Scripts

These scripts work with **any Grafana instance** (OSS, AMG, Azure) by passing URL and token as arguments.

## Quick Start

```bash
# From any instance directory
cd instances/grafana-oss-dev

# Import all resources
../../scripts/bulk-import-all.sh --url http://localhost:3000 --token your-api-key

# Or use environment variables
export GRAFANA_URL=http://localhost:3000
export GRAFANA_TOKEN=your-api-key
../../scripts/bulk-import-all.sh
```

## Individual Scripts

### Import Folders
```bash
../../scripts/bulk-import-folders.sh --url $URL --token $TOKEN
../../scripts/bulk-import-folders.sh --url $URL --token $TOKEN --dry-run
../../scripts/bulk-import-folders.sh --url $URL --token $TOKEN --generate
```

### Import Datasources
```bash
../../scripts/bulk-import-datasources.sh --url $URL --token $TOKEN
```

### Import Dashboards
```bash
../../scripts/bulk-import-dashboards.sh --url $URL --token $TOKEN
```

### Import Contact Points
```bash
../../scripts/bulk-import-contact-points.sh --url $URL --token $TOKEN
```

### Import Alert Rules
```bash
../../scripts/bulk-import-alert-rules.sh --url $URL --token $TOKEN
```

### Import Everything
```bash
../../scripts/bulk-import-all.sh --url $URL --token $TOKEN
```

## Options

| Option | Description |
|--------|-------------|
| `--url URL` | Grafana URL (or set `GRAFANA_URL`) |
| `--token TOKEN` | API token (or set `GRAFANA_TOKEN`) |
| `--instance NAME` | Instance name for resource naming |
| `--prefix PREFIX` | Resource name prefix (default: `imported`) |
| `--output FILE` | Output .tf filename |
| `--dry-run` | Preview only, don't import |
| `--generate` | Generate .tf files only |
| `--help` | Show help |

## Examples

### Import from local Grafana OSS
```bash
cd instances/grafana-oss-local
../../scripts/bulk-import-all.sh \
  --url http://localhost:3000 \
  --token glsa_xxxx \
  --instance grafana-oss-local
```

### Import from Amazon Managed Grafana
```bash
cd instances/grafana-amg-prod

# First create API key
./scripts/create-api-key.sh g-xxxxxxxxxx

# Then import
../../scripts/bulk-import-all.sh \
  --url https://g-xxx.grafana-workspace.us-east-1.amazonaws.com \
  --token $API_KEY \
  --instance grafana-amg-prod
```

### Import from Azure Managed Grafana
```bash
cd instances/grafana-azure-prod

# First create service account token
./scripts/create-service-account.sh my-grafana my-resource-group

# Then import
../../scripts/bulk-import-all.sh \
  --url https://my-grafana-xxx.grafana.azure.com \
  --token $TOKEN \
  --instance grafana-azure-prod
```

### Dry run (preview only)
```bash
../../scripts/bulk-import-all.sh --url $URL --token $TOKEN --dry-run
```

### Generate .tf files without importing
```bash
../../scripts/bulk-import-all.sh --url $URL --token $TOKEN --generate
```

## Generated Files

After running import scripts:

```
instances/grafana-oss-dev/
├── main.tf
├── terraform.tfvars
├── folders_imported.tf           # Generated
├── datasources_imported.tf       # Generated
├── dashboards_imported.tf        # Generated
├── contact_points_imported.tf    # Generated
├── alert_rules_imported.tf       # Generated
└── dashboards_imported/          # Generated (JSON files)
    ├── abc123.json
    └── xyz789.json
```

## Workflow

1. **Preview**: Run with `--dry-run` to see what will be imported
2. **Generate**: Run with `--generate` to create .tf files
3. **Review**: Check generated .tf files
4. **Import**: Run without flags to import into state
5. **Verify**: Run `terraform plan` - should show "No changes"
6. **Adjust**: If plan shows changes, update .tf files to match
