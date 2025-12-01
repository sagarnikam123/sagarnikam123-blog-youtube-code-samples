# Advanced Grafana Automation Guide

Advanced tools and techniques for complex Grafana automation scenarios.

## Overview

This guide covers advanced tools and patterns for sophisticated Grafana automation, including complex dashboard generation, GitOps workflows, and enterprise-grade automation patterns.

## Advanced Dashboard Generation

### [Grafanalib](https://github.com/weaveworks/grafanalib) (Weaveworks)

#### Installation
```bash
pip install grafanalib
```

#### Advanced Dashboard Generation
```python
from grafanalib.core import (
    Dashboard, Graph, Template, Templating, ROUNDING_FACTOR
)
from grafanalib.prometheus import PrometheusTarget

# Create template for instance selection
instance_template = Template(
    name="instance",
    query="label_values(up, instance)",
    dataSource="Prometheus",
    multi=True,
    includeAll=True
)

# Create templating
templating = Templating([instance_template])

# Create panels with template variables
cpu_panel = Graph(
    title="CPU Usage by Instance",
    dataSource="Prometheus",
    targets=[
        PrometheusTarget(
            expr='100 - (avg by (instance) (irate(node_cpu_seconds_total{mode="idle", instance=~"$instance"}[5m])) * 100)',
            refId="A",
            legendFormat="{{instance}}"
        )
    ],
    gridPos={"h": 8, "w": 24, "x": 0, "y": 0}
)

# Create advanced dashboard
dashboard = Dashboard(
    title="Advanced System Monitoring",
    tags=["system", "advanced", "templated"],
    templating=templating,
    panels=[cpu_panel],
    time={"from": "now-6h", "to": "now"},
    refresh="30s"
)

# Generate JSON
import json
with open('advanced-dashboard.json', 'w') as f:
    json.dump(dashboard.to_json_data(), f, indent=2)
```

#### Complex Dashboard Factory
```python
from grafanalib.core import *
from grafanalib.prometheus import PrometheusTarget
import json

class AdvancedDashboardFactory:
    def __init__(self, datasource="Prometheus"):
        self.datasource = datasource

    def create_service_dashboard(self, service_name, metrics_config):
        panels = []
        y_pos = 0

        # SLI Panels
        for sli_name, sli_config in metrics_config.get('slis', {}).items():
            panel = self._create_sli_panel(
                title=f"{service_name} {sli_name}",
                expr=sli_config['expr'],
                threshold=sli_config.get('threshold'),
                y=y_pos
            )
            panels.append(panel)
            y_pos += 8

        # Error Budget Panel
        if 'slo_target' in metrics_config:
            error_budget_panel = self._create_error_budget_panel(
                service_name, metrics_config['slo_target'], y_pos
            )
            panels.append(error_budget_panel)
            y_pos += 8

        # Dependency Panels
        for dep_name, dep_config in metrics_config.get('dependencies', {}).items():
            dep_panel = self._create_dependency_panel(
                service_name, dep_name, dep_config, y_pos
            )
            panels.append(dep_panel)
            y_pos += 8

        # Create template variables
        templates = self._create_service_templates(service_name)

        return Dashboard(
            title=f"{service_name} Service Dashboard",
            tags=["service", service_name, "sli", "slo"],
            templating=Templating(templates),
            panels=panels,
            time={"from": "now-1h", "to": "now"},
            refresh="30s"
        )

    def _create_sli_panel(self, title, expr, threshold=None, y=0):
        panel = Stat(
            title=title,
            dataSource=self.datasource,
            targets=[PrometheusTarget(expr=expr, refId="A")],
            gridPos={"h": 8, "w": 6, "x": 0, "y": y}
        )

        if threshold:
            panel.thresholds = [
                {"color": "green", "value": None},
                {"color": "red", "value": threshold}
            ]

        return panel

    def _create_error_budget_panel(self, service_name, slo_target, y):
        return Graph(
            title=f"{service_name} Error Budget",
            dataSource=self.datasource,
            targets=[
                PrometheusTarget(
                    expr=f'1 - (increase(sli_errors_total{{service="{service_name}"}}[30d]) / increase(sli_requests_total{{service="{service_name}"}}[30d]))',
                    refId="A",
                    legendFormat="Error Budget"
                )
            ],
            gridPos={"h": 8, "w": 12, "x": 0, "y": y},
            yAxes=[
                {"min": 0, "max": 1, "unit": "percentunit"}
            ]
        )

    def _create_dependency_panel(self, service_name, dep_name, dep_config, y):
        return Graph(
            title=f"{service_name} -> {dep_name} Dependency",
            dataSource=self.datasource,
            targets=[
                PrometheusTarget(
                    expr=dep_config['latency_expr'],
                    refId="A",
                    legendFormat="Latency"
                ),
                PrometheusTarget(
                    expr=dep_config['error_expr'],
                    refId="B",
                    legendFormat="Error Rate"
                )
            ],
            gridPos={"h": 8, "w": 12, "x": 12, "y": y}
        )

    def _create_service_templates(self, service_name):
        return [
            Template(
                name="instance",
                query=f'label_values(up{{service="{service_name}"}}, instance)',
                dataSource=self.datasource,
                multi=True,
                includeAll=True
            ),
            Template(
                name="version",
                query=f'label_values(up{{service="{service_name}"}}, version)',
                dataSource=self.datasource,
                multi=False,
                includeAll=True
            )
        ]

# Usage
factory = AdvancedDashboardFactory()

service_config = {
    'slis': {
        'Availability': {
            'expr': 'up{service="api"}',
            'threshold': 0.99
        },
        'Latency': {
            'expr': 'histogram_quantile(0.95, rate(http_request_duration_seconds_bucket{service="api"}[5m]))',
            'threshold': 0.5
        }
    },
    'slo_target': 0.999,
    'dependencies': {
        'database': {
            'latency_expr': 'rate(database_query_duration_seconds_sum{service="api"}[5m]) / rate(database_query_duration_seconds_count{service="api"}[5m])',
            'error_expr': 'rate(database_errors_total{service="api"}[5m])'
        }
    }
}

dashboard = factory.create_service_dashboard("api", service_config)
with open('api-service-dashboard.json', 'w') as f:
    json.dump(dashboard.to_json_data(), f, indent=2)
```

### [Grafana Dash Gen](https://github.com/uber/grafana-dash-gen) (Uber)

#### Installation
```bash
pip install grafana-dashboard-generator
```

#### Advanced Usage
```python
from grafana_dash_gen import DashboardGenerator, Panel, Target, Template

class ServiceDashboardGenerator:
    def __init__(self, service_name):
        self.service_name = service_name
        self.dash_gen = DashboardGenerator(
            title=f"{service_name} Service Dashboard",
            tags=["service", service_name]
        )

    def add_golden_signals(self):
        # Latency
        latency_panel = Panel(
            title="Request Latency",
            panel_type="graph",
            targets=[
                Target(
                    expr=f'histogram_quantile(0.95, rate(http_request_duration_seconds_bucket{{service="{self.service_name}"}}[5m]))',
                    ref_id="A",
                    legend_format="95th percentile"
                ),
                Target(
                    expr=f'histogram_quantile(0.50, rate(http_request_duration_seconds_bucket{{service="{self.service_name}"}}[5m]))',
                    ref_id="B",
                    legend_format="50th percentile"
                )
            ],
            y_axes=[{"unit": "s"}]
        )
        self.dash_gen.add_panel(latency_panel)

        # Traffic
        traffic_panel = Panel(
            title="Request Rate",
            panel_type="graph",
            targets=[
                Target(
                    expr=f'rate(http_requests_total{{service="{self.service_name}"}}[5m])',
                    ref_id="A",
                    legend_format="{{method}} {{status}}"
                )
            ],
            y_axes=[{"unit": "reqps"}]
        )
        self.dash_gen.add_panel(traffic_panel)

        # Errors
        error_panel = Panel(
            title="Error Rate",
            panel_type="singlestat",
            targets=[
                Target(
                    expr=f'rate(http_requests_total{{service="{self.service_name}", status=~"5.."}[5m]}) / rate(http_requests_total{{service="{self.service_name}"}}[5m])',
                    ref_id="A"
                )
            ],
            thresholds=[0.01, 0.05],
            colors=["green", "yellow", "red"]
        )
        self.dash_gen.add_panel(error_panel)

        # Saturation
        saturation_panel = Panel(
            title="CPU Usage",
            panel_type="graph",
            targets=[
                Target(
                    expr=f'rate(process_cpu_seconds_total{{service="{self.service_name}"}}[5m])',
                    ref_id="A",
                    legend_format="{{instance}}"
                )
            ],
            y_axes=[{"unit": "percent", "max": 1}]
        )
        self.dash_gen.add_panel(saturation_panel)

    def add_business_metrics(self, metrics_config):
        for metric_name, metric_config in metrics_config.items():
            panel = Panel(
                title=metric_config['title'],
                panel_type=metric_config.get('type', 'graph'),
                targets=[
                    Target(
                        expr=metric_config['expr'],
                        ref_id="A",
                        legend_format=metric_config.get('legend', '')
                    )
                ]
            )
            self.dash_gen.add_panel(panel)

    def generate(self):
        return self.dash_gen.generate()

# Usage
generator = ServiceDashboardGenerator("payment-service")
generator.add_golden_signals()
generator.add_business_metrics({
    'payment_volume': {
        'title': 'Payment Volume',
        'expr': 'sum(rate(payments_total[5m]))',
        'type': 'singlestat'
    },
    'payment_amount': {
        'title': 'Payment Amount',
        'expr': 'sum(rate(payment_amount_total[5m]))',
        'legend': 'Total Amount'
    }
})

dashboard_json = generator.generate()
with open('payment-service-dashboard.json', 'w') as f:
    f.write(dashboard_json)
```

## GitOps Tools

### [Grizzly](https://github.com/grafana/grizzly) - GitOps Tool

> **Note**: Grizzly is deprecated but still widely used in existing setups.

#### Installation
```bash
# Download binary
wget https://github.com/grafana/grizzly/releases/latest/download/grr-linux-amd64
chmod +x grr-linux-amd64
sudo mv grr-linux-amd64 /usr/local/bin/grr

# Or using Go
go install github.com/grafana/grizzly/cmd/grr@latest
```

#### Configuration
```bash
# Set Grafana URL and token
export GRAFANA_URL="http://localhost:3000"
export GRAFANA_TOKEN="your-api-token"

# Or use config file
grr config set grafana.url http://localhost:3000
grr config set grafana.token your-api-token
```

#### GitOps Workflow
```bash
# Pull existing resources from Grafana
grr pull

# Show differences
grr diff

# Apply changes
grr apply resources/

# Watch for changes
grr watch resources/
```

#### Advanced Grizzly Usage
```yaml
# grizzly-config.yaml
targets:
  dev:
    grafana:
      url: https://dev-grafana.company.com
      token: ${DEV_GRAFANA_TOKEN}
  prod:
    grafana:
      url: https://grafana.company.com
      token: ${PROD_GRAFANA_TOKEN}

resources:
  - dashboards/
  - datasources/
  - alerts/
```

```bash
# Deploy to specific environment
grr apply --target dev resources/
grr apply --target prod resources/

# Selective deployment
grr apply --resource-type Dashboard resources/
grr apply --resource-type DataSource resources/
```

## Advanced Grafanactl Operations

### Dashboards as Code
```bash
# Initialize dashboard project
mkdir my-dashboards && cd my-dashboards
grafanactl dashboard init

# Generate dashboard from template
grafanactl dashboard generate --template prometheus

# Validate dashboards
grafanactl dashboard validate .

# Deploy dashboards
grafanactl dashboard deploy .

# Watch for changes
grafanactl dashboard watch .
```

### Resource Exploration
```bash
# Describe resource
grafanactl describe dashboard my-dashboard-uid
grafanactl describe datasource prometheus

# Get resource in different formats
grafanactl get dashboard my-dashboard-uid -o wide
grafanactl get dashboard my-dashboard-uid -o yaml
grafanactl get dashboard my-dashboard-uid -o json

# Filter resources
grafanactl get dashboards --selector "tag=monitoring"
grafanactl get dashboards --field-selector "folder=monitoring"
```

### Bulk Operations
```bash
# Export all dashboards
grafanactl get dashboards -o yaml > all-dashboards.yaml

# Export specific folder
grafanactl get dashboards --folder monitoring -o yaml > monitoring-dashboards.yaml

# Apply multiple resources
grafanactl apply -f dashboards/
grafanactl apply -R -f .

# Delete multiple resources
grafanactl delete -f dashboards/
```

## CI/CD Integration Patterns

### GitHub Actions Advanced Workflow
```yaml
name: Advanced Grafana Deployment

on:
  push:
    branches: [main]
    paths: ['grafana/**']
  pull_request:
    paths: ['grafana/**']

env:
  GRAFANA_CONFIG_DIR: grafana

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.9'

      - name: Install dependencies
        run: |
          pip install yamllint jsonschema grafanalib
          wget https://github.com/grafana/grafanactl/releases/latest/download/grafanactl-linux-amd64
          chmod +x grafanactl-linux-amd64
          sudo mv grafanactl-linux-amd64 /usr/local/bin/grafanactl

      - name: Lint YAML files
        run: yamllint $GRAFANA_CONFIG_DIR/

      - name: Validate JSON dashboards
        run: |
          find $GRAFANA_CONFIG_DIR/ -name "*.json" -exec jq . {} \;

      - name: Validate Grafana configs
        run: grafanactl validate $GRAFANA_CONFIG_DIR/

      - name: Generate dashboards from code
        run: |
          cd $GRAFANA_CONFIG_DIR/generators
          python generate_all_dashboards.py

      - name: Upload generated dashboards
        uses: actions/upload-artifact@v3
        with:
          name: generated-dashboards
          path: $GRAFANA_CONFIG_DIR/generated/

  deploy-dev:
    needs: validate
    if: github.event_name == 'pull_request'
    runs-on: ubuntu-latest
    environment: development
    steps:
      - uses: actions/checkout@v3

      - name: Download generated dashboards
        uses: actions/download-artifact@v3
        with:
          name: generated-dashboards
          path: $GRAFANA_CONFIG_DIR/generated/

      - name: Deploy to dev
        env:
          GRAFANA_URL: ${{ secrets.DEV_GRAFANA_URL }}
          GRAFANA_TOKEN: ${{ secrets.DEV_GRAFANA_TOKEN }}
        run: |
          grafanactl apply -f $GRAFANA_CONFIG_DIR/
          grafanactl apply -f $GRAFANA_CONFIG_DIR/generated/

  deploy-prod:
    needs: validate
    if: github.ref == 'refs/heads/main'
    runs-on: ubuntu-latest
    environment: production
    steps:
      - uses: actions/checkout@v3

      - name: Download generated dashboards
        uses: actions/download-artifact@v3
        with:
          name: generated-dashboards
          path: $GRAFANA_CONFIG_DIR/generated/

      - name: Deploy to production
        env:
          GRAFANA_URL: ${{ secrets.PROD_GRAFANA_URL }}
          GRAFANA_TOKEN: ${{ secrets.PROD_GRAFANA_TOKEN }}
        run: |
          # Deploy with confirmation
          grafanactl apply -f $GRAFANA_CONFIG_DIR/ --confirm
          grafanactl apply -f $GRAFANA_CONFIG_DIR/generated/ --confirm

      - name: Verify deployment
        env:
          GRAFANA_URL: ${{ secrets.PROD_GRAFANA_URL }}
          GRAFANA_TOKEN: ${{ secrets.PROD_GRAFANA_TOKEN }}
        run: |
          python scripts/verify_deployment.py

      - name: Notify deployment
        if: always()
        run: |
          curl -X POST "${{ secrets.SLACK_WEBHOOK }}" \
            -H 'Content-type: application/json' \
            -d '{
              "text": "Grafana deployment ${{ job.status }}: ${{ github.event.head_commit.message }}"
            }'
```

### GitLab CI Advanced Pipeline
```yaml
# .gitlab-ci.yml
stages:
  - validate
  - generate
  - deploy-dev
  - deploy-staging
  - deploy-prod

variables:
  GRAFANA_CONFIG_DIR: "grafana"
  PYTHON_VERSION: "3.9"

.grafana_base: &grafana_base
  image: python:${PYTHON_VERSION}
  before_script:
    - pip install yamllint jsonschema grafanalib
    - wget https://github.com/grafana/grafanactl/releases/latest/download/grafanactl-linux-amd64
    - chmod +x grafanactl-linux-amd64
    - mv grafanactl-linux-amd64 /usr/local/bin/grafanactl

validate:
  <<: *grafana_base
  stage: validate
  script:
    - yamllint $GRAFANA_CONFIG_DIR/
    - find $GRAFANA_CONFIG_DIR/ -name "*.json" -exec jq . {} \;
    - grafanactl validate $GRAFANA_CONFIG_DIR/
  only:
    changes:
      - grafana/**/*

generate:
  <<: *grafana_base
  stage: generate
  script:
    - cd $GRAFANA_CONFIG_DIR/generators
    - python generate_all_dashboards.py
  artifacts:
    paths:
      - $GRAFANA_CONFIG_DIR/generated/
    expire_in: 1 hour
  only:
    changes:
      - grafana/**/*

deploy_dev:
  <<: *grafana_base
  stage: deploy-dev
  script:
    - grafanactl apply -f $GRAFANA_CONFIG_DIR/
    - grafanactl apply -f $GRAFANA_CONFIG_DIR/generated/
  environment:
    name: development
    url: https://dev-grafana.company.com
  variables:
    GRAFANA_URL: $DEV_GRAFANA_URL
    GRAFANA_TOKEN: $DEV_GRAFANA_TOKEN
  only:
    - develop

deploy_staging:
  <<: *grafana_base
  stage: deploy-staging
  script:
    - grafanactl apply -f $GRAFANA_CONFIG_DIR/
    - grafanactl apply -f $GRAFANA_CONFIG_DIR/generated/
  environment:
    name: staging
    url: https://staging-grafana.company.com
  variables:
    GRAFANA_URL: $STAGING_GRAFANA_URL
    GRAFANA_TOKEN: $STAGING_GRAFANA_TOKEN
  only:
    - main
  when: manual

deploy_prod:
  <<: *grafana_base
  stage: deploy-prod
  script:
    - grafanactl apply -f $GRAFANA_CONFIG_DIR/ --confirm
    - grafanactl apply -f $GRAFANA_CONFIG_DIR/generated/ --confirm
    - python scripts/verify_deployment.py
  environment:
    name: production
    url: https://grafana.company.com
  variables:
    GRAFANA_URL: $PROD_GRAFANA_URL
    GRAFANA_TOKEN: $PROD_GRAFANA_TOKEN
  only:
    - main
  when: manual
  allow_failure: false
```

## Automation Scripts

### Dashboard Provisioning Script
```bash
#!/bin/bash
# advanced-provision-grafana.sh

set -e

GRAFANA_URL="${GRAFANA_URL:-http://localhost:3000}"
GRAFANA_TOKEN="$GRAFANA_TOKEN"
CONFIG_DIR="${CONFIG_DIR:-./grafana-config}"

if [ -z "$GRAFANA_TOKEN" ]; then
    echo "Error: GRAFANA_TOKEN environment variable is required"
    exit 1
fi

echo "🚀 Starting advanced Grafana provisioning..."

# Function to create resource with retry
create_resource() {
    local resource_type=$1
    local resource_file=$2
    local max_retries=3
    local retry_count=0

    while [ $retry_count -lt $max_retries ]; do
        if curl -s -X POST "$GRAFANA_URL/api/$resource_type" \
           -H "Authorization: Bearer $GRAFANA_TOKEN" \
           -H "Content-Type: application/json" \
           -d @"$resource_file" | jq '.'; then
            echo "✅ Successfully created $resource_type from $resource_file"
            return 0
        else
            retry_count=$((retry_count + 1))
            echo "⚠️  Retry $retry_count/$max_retries for $resource_file"
            sleep 2
        fi
    done

    echo "❌ Failed to create $resource_type from $resource_file after $max_retries retries"
    return 1
}

# Create folders first
echo "📁 Creating folders..."
for folder_file in "$CONFIG_DIR"/folders/*.json; do
    if [ -f "$folder_file" ]; then
        create_resource "folders" "$folder_file"
    fi
done

# Create datasources
echo "🔌 Creating datasources..."
for datasource_file in "$CONFIG_DIR"/datasources/*.json; do
    if [ -f "$datasource_file" ]; then
        create_resource "datasources" "$datasource_file"
    fi
done

# Wait for datasources to be ready
echo "⏳ Waiting for datasources to be ready..."
sleep 5

# Create dashboards
echo "📊 Creating dashboards..."
for dashboard_file in "$CONFIG_DIR"/dashboards/*.json; do
    if [ -f "$dashboard_file" ]; then
        create_resource "dashboards/db" "$dashboard_file"
    fi
done

# Create alerts
echo "🚨 Creating alerts..."
for alert_file in "$CONFIG_DIR"/alerts/*.json; do
    if [ -f "$alert_file" ]; then
        create_resource "ruler/grafana/api/v1/rules" "$alert_file"
    fi
done

# Verify deployment
echo "🔍 Verifying deployment..."
python3 << EOF
import requests
import json

def verify_grafana_health():
    response = requests.get("$GRAFANA_URL/api/health")
    if response.status_code == 200:
        print("✅ Grafana is healthy")
        return True
    else:
        print("❌ Grafana health check failed")
        return False

def verify_datasources():
    response = requests.get(
        "$GRAFANA_URL/api/datasources",
        headers={"Authorization": "Bearer $GRAFANA_TOKEN"}
    )
    if response.status_code == 200:
        datasources = response.json()
        print(f"✅ Found {len(datasources)} datasources")
        return True
    else:
        print("❌ Failed to fetch datasources")
        return False

def verify_dashboards():
    response = requests.get(
        "$GRAFANA_URL/api/search?type=dash-db",
        headers={"Authorization": "Bearer $GRAFANA_TOKEN"}
    )
    if response.status_code == 200:
        dashboards = response.json()
        print(f"✅ Found {len(dashboards)} dashboards")
        return True
    else:
        print("❌ Failed to fetch dashboards")
        return False

if verify_grafana_health() and verify_datasources() and verify_dashboards():
    print("🎉 All verifications passed!")
else:
    print("💥 Some verifications failed!")
    exit(1)
EOF

echo "✅ Advanced Grafana provisioning completed successfully!"
```

### Configuration Drift Detection
```python
#!/usr/bin/env python3
# scripts/detect-config-drift.py

import requests
import yaml
import json
import sys
import os
from deepdiff import DeepDiff

class GrafanaDriftDetector:
    def __init__(self, grafana_url, token):
        self.grafana_url = grafana_url.rstrip('/')
        self.headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }

    def get_live_dashboard(self, uid):
        response = requests.get(
            f"{self.grafana_url}/api/dashboards/uid/{uid}",
            headers=self.headers
        )
        if response.status_code == 200:
            return response.json()["dashboard"]
        return None

    def get_live_datasource(self, name):
        response = requests.get(
            f"{self.grafana_url}/api/datasources/name/{name}",
            headers=self.headers
        )
        if response.status_code == 200:
            return response.json()
        return None

    def normalize_dashboard(self, dashboard):
        # Remove fields that change automatically
        ignore_fields = ["id", "version", "meta", "schemaVersion"]
        normalized = dashboard.copy()

        for field in ignore_fields:
            normalized.pop(field, None)

        # Normalize panel IDs (they can change)
        if "panels" in normalized:
            for i, panel in enumerate(normalized["panels"]):
                panel["id"] = i + 1

        return normalized

    def normalize_datasource(self, datasource):
        ignore_fields = ["id", "orgId", "version", "readOnly"]
        normalized = datasource.copy()

        for field in ignore_fields:
            normalized.pop(field, None)

        return normalized

    def detect_dashboard_drift(self, config_dir):
        drift_detected = False

        for root, dirs, files in os.walk(f"{config_dir}/dashboards"):
            for file in files:
                if file.endswith(('.json', '.yaml', '.yml')):
                    filepath = os.path.join(root, file)

                    # Load dashboard from file
                    with open(filepath, 'r') as f:
                        if file.endswith('.json'):
                            code_dashboard = json.load(f)
                        else:
                            data = yaml.safe_load(f)
                            code_dashboard = data.get('spec', data)

                    # Get UID from dashboard
                    uid = code_dashboard.get('uid')
                    if not uid:
                        print(f"⚠️  No UID found in {filepath}, skipping")
                        continue

                    # Get live dashboard
                    live_dashboard = self.get_live_dashboard(uid)
                    if not live_dashboard:
                        print(f"❌ Dashboard {uid} not found in Grafana")
                        drift_detected = True
                        continue

                    # Normalize and compare
                    normalized_code = self.normalize_dashboard(code_dashboard)
                    normalized_live = self.normalize_dashboard(live_dashboard)

                    diff = DeepDiff(normalized_code, normalized_live, ignore_order=True)

                    if diff:
                        print(f"⚠️  Configuration drift detected in dashboard {uid} ({filepath})")
                        print(f"   Differences: {diff}")
                        drift_detected = True
                    else:
                        print(f"✅ Dashboard {uid} matches code version")

        return drift_detected

    def detect_datasource_drift(self, config_dir):
        drift_detected = False

        for root, dirs, files in os.walk(f"{config_dir}/datasources"):
            for file in files:
                if file.endswith(('.json', '.yaml', '.yml')):
                    filepath = os.path.join(root, file)

                    # Load datasource from file
                    with open(filepath, 'r') as f:
                        if file.endswith('.json'):
                            code_datasource = json.load(f)
                        else:
                            data = yaml.safe_load(f)
                            code_datasource = data.get('spec', data)

                    # Get name from datasource
                    name = code_datasource.get('name')
                    if not name:
                        print(f"⚠️  No name found in {filepath}, skipping")
                        continue

                    # Get live datasource
                    live_datasource = self.get_live_datasource(name)
                    if not live_datasource:
                        print(f"❌ Datasource {name} not found in Grafana")
                        drift_detected = True
                        continue

                    # Normalize and compare
                    normalized_code = self.normalize_datasource(code_datasource)
                    normalized_live = self.normalize_datasource(live_datasource)

                    diff = DeepDiff(normalized_code, normalized_live, ignore_order=True)

                    if diff:
                        print(f"⚠️  Configuration drift detected in datasource {name} ({filepath})")
                        print(f"   Differences: {diff}")
                        drift_detected = True
                    else:
                        print(f"✅ Datasource {name} matches code version")

        return drift_detected

def main():
    grafana_url = os.environ.get('GRAFANA_URL', 'http://localhost:3000')
    grafana_token = os.environ.get('GRAFANA_TOKEN')
    config_dir = os.environ.get('CONFIG_DIR', './grafana-config')

    if not grafana_token:
        print("❌ GRAFANA_TOKEN environment variable is required")
        sys.exit(1)

    detector = GrafanaDriftDetector(grafana_url, grafana_token)

    print("🔍 Detecting configuration drift...")

    dashboard_drift = detector.detect_dashboard_drift(config_dir)
    datasource_drift = detector.detect_datasource_drift(config_dir)

    if dashboard_drift or datasource_drift:
        print("💥 Configuration drift detected!")
        sys.exit(1)
    else:
        print("🎉 No configuration drift detected!")
        sys.exit(0)

if __name__ == "__main__":
    main()
```

## Best Practices

### 1. Code Organization
```
advanced-grafana-automation/
├── generators/
│   ├── dashboard_factory.py
│   ├── service_dashboards.py
│   └── sli_slo_dashboards.py
├── templates/
│   ├── service-dashboard.json.j2
│   └── alert-rules.yaml.j2
├── scripts/
│   ├── deploy.sh
│   ├── validate.py
│   └── drift-detection.py
├── config/
│   ├── dev/
│   ├── staging/
│   └── prod/
└── tests/
    ├── test_generators.py
    └── test_validation.py
```

### 2. Testing Strategies
```python
# tests/test_dashboard_generation.py
import unittest
import json
from generators.dashboard_factory import AdvancedDashboardFactory

class TestDashboardGeneration(unittest.TestCase):
    def setUp(self):
        self.factory = AdvancedDashboardFactory()

    def test_service_dashboard_generation(self):
        config = {
            'slis': {
                'Availability': {
                    'expr': 'up{service="test"}',
                    'threshold': 0.99
                }
            }
        }

        dashboard = self.factory.create_service_dashboard("test", config)
        dashboard_json = dashboard.to_json_data()

        # Validate structure
        self.assertIn('title', dashboard_json)
        self.assertIn('panels', dashboard_json)
        self.assertTrue(len(dashboard_json['panels']) > 0)

        # Validate JSON serialization
        json_str = json.dumps(dashboard_json)
        self.assertIsInstance(json_str, str)

    def test_template_variables(self):
        templates = self.factory._create_service_templates("test")
        self.assertTrue(len(templates) > 0)
        self.assertEqual(templates[0].name, "instance")

if __name__ == '__main__':
    unittest.main()
```

### 3. Performance Optimization
```python
# Parallel dashboard generation
import concurrent.futures
import threading

class ParallelDashboardGenerator:
    def __init__(self, max_workers=4):
        self.max_workers = max_workers
        self.lock = threading.Lock()

    def generate_service_dashboards(self, services_config):
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = {
                executor.submit(self._generate_single_dashboard, service, config): service
                for service, config in services_config.items()
            }

            results = {}
            for future in concurrent.futures.as_completed(futures):
                service = futures[future]
                try:
                    dashboard = future.result()
                    with self.lock:
                        results[service] = dashboard
                        print(f"✅ Generated dashboard for {service}")
                except Exception as e:
                    print(f"❌ Failed to generate dashboard for {service}: {e}")

            return results

    def _generate_single_dashboard(self, service, config):
        factory = AdvancedDashboardFactory()
        return factory.create_service_dashboard(service, config)
```

## References

- [Grafanalib Documentation](https://grafanalib.readthedocs.io/)
- [Grafana Dash Gen Repository](https://github.com/uber/grafana-dash-gen)
- [Grizzly Documentation](https://grafana.github.io/grizzly/)
- [Advanced GitOps Patterns](https://www.gitops.tech/)
