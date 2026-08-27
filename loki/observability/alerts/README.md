# Loki Datasource-Managed Alerts (Ruler)

## Overview

These are **datasource-managed alert rules** — evaluated natively by Loki's ruler component, not by Grafana's alert engine. Loki evaluates LogQL expressions on a schedule and sends firing alerts directly to Alertmanager.

## Directory Structure

```
alerts/
├── README.md
└── rules/
    └── fake/                    # Tenant name (fake = default when auth_enabled: false)
        └── error-alerts.yaml   # Rule groups
```

## How It Works

```
Logs ingested → Loki ruler evaluates LogQL expressions → Fires to Alertmanager → Notifications
```

1. Loki's ruler loads YAML rule files from its configured storage path
2. Every `evaluation_interval` (30s in our config), it runs each LogQL `expr`
3. If the expression returns results above threshold and `for` duration is met, the alert fires
4. Firing alerts are POSTed to the configured `alertmanager_url`

## Adding New Rules

Create or edit YAML files under `rules/fake/`. The ruler picks up changes on `poll_interval` (30s).

Rule format:
```yaml
groups:
  - name: my_group
    interval: 30s  # optional, overrides global evaluation_interval
    rules:
      - alert: MyAlert
        expr: |
          count_over_time({job="myapp"} |= "ERROR" [5m]) > 10
        for: 2m
        labels:
          severity: warning
        annotations:
          summary: "{{ $labels.job }} has errors"
```

## Verifying Rules Are Loaded

```bash
# List all rules via API
curl http://localhost:3100/loki/api/v1/rules

# Check ruler ring status
curl http://localhost:3100/ruler/ring
```

## Differences from Grafana-Managed Alerts

| Feature | Datasource-Managed (Ruler) | Grafana-Managed |
|---------|---------------------------|-----------------|
| Evaluation engine | Loki ruler | Grafana alerting |
| Rule storage | Loki filesystem/object store | Grafana database |
| Alert routing | Direct to Alertmanager | Grafana notification policies |
| Rule format | Prometheus-style YAML | Grafana JSON model |
| UI management | API or file editing | Grafana UI |
| Multi-tenancy | Per-tenant rule dirs | Grafana RBAC |
