# Observability as Code Guide

Complete guide to implementing Observability as Code (OaC) practices for managing monitoring infrastructure programmatically.

## Overview

Observability as Code (OaC) is the practice of managing observability resources (dashboards, alerts, datasources) using code and version control. This approach provides:

- **Version Control:** Track changes to dashboards and alerts
- **Reproducibility:** Deploy consistent configurations across environments
- **Collaboration:** Team-based development with code reviews
- **Automation:** CI/CD integration for automated deployments
- **Rollback:** Easy reversion to previous configurations

## Key Components

### 1. Infrastructure as Code (IaC)
- **Terraform** - Declarative infrastructure management
- **Pulumi** - Modern IaC with familiar programming languages
- **CloudFormation** - AWS-native infrastructure management

### 2. Configuration Management
- **Ansible** - Agentless automation platform
- **Chef** - Configuration management and automation
- **Puppet** - Infrastructure automation and configuration

### 3. GitOps
- **Git-based workflows** for deployments
- **Pull request reviews** for changes
- **Automated deployments** from Git repositories
- **Rollback capabilities** through Git history

### 4. SDK/Libraries
- **Grafana Foundation SDK** - Type-safe dashboard generation
- **grafanalib** - Python library for dashboard creation
- **Custom libraries** - Organization-specific tooling

### 5. CLI Tools
- **grafanactl** - Official Grafana CLI
- **grizzly** - GitOps tool for Grafana (deprecated)
- **Custom scripts** - Organization-specific automation

## Workflow Patterns

### 1. Define Resources as Code

#### Dashboard as Code Example
```yaml
# dashboard.yaml
apiVersion: grizzly.grafana.com/v1alpha1
kind: Dashboard
metadata:
  name: system-overview
spec:
  title: "System Overview"
  tags: ["system", "monitoring"]
  panels:
    - title: "CPU Usage"
      type: "stat"
      targets:
        - expr: "100 - (avg(irate(node_cpu_seconds_total{mode='idle'}[5m])) * 100)"
```

#### Terraform Example
```hcl
resource "grafana_dashboard" "system_metrics" {
  config_json = jsonencode({
    title = "System Metrics"
    tags  = ["system", "monitoring"]
    panels = [
      {
        title = "CPU Usage"
        type  = "stat"
        targets = [{
          expr = "100 - (avg(irate(node_cpu_seconds_total{mode=\"idle\"}[5m])) * 100)"
        }]
      }
    ]
  })
}
```

### 2. Version Control

#### Repository Structure
```
observability-config/
├── dashboards/
│   ├── system/
│   │   ├── cpu-metrics.yaml
│   │   └── memory-metrics.yaml
│   └── application/
│       └── api-metrics.yaml
├── datasources/
│   ├── prometheus.yaml
│   └── loki.yaml
├── alerts/
│   ├── system-alerts.yaml
│   └── app-alerts.yaml
├── folders/
│   └── monitoring-folders.yaml
└── .github/
    └── workflows/
        └── deploy.yml
```

#### Git Workflow
```bash
# Initialize Git repository
git init observability-config
cd observability-config

# Add dashboard configurations
mkdir dashboards datasources alerts
echo "dashboard.yaml" > dashboards/
git add .
git commit -m "Initial observability configuration"

# Create feature branch
git checkout -b feature/new-dashboard
# Make changes
git add .
git commit -m "Add new application dashboard"
git push origin feature/new-dashboard
# Create pull request for review
```

### 3. Automated Deployment

#### GitHub Actions Example
```yaml
# .github/workflows/deploy.yml
name: Deploy Observability Config
on:
  push:
    branches: [main]
    paths: ['dashboards/**', 'alerts/**']

jobs:
  deploy:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        environment: [dev, staging, prod]
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Deploy to ${{ matrix.environment }}
        env:
          GRAFANA_URL: ${{ secrets[format('GRAFANA_URL_{0}', matrix.environment)] }}
          GRAFANA_TOKEN: ${{ secrets[format('GRAFANA_TOKEN_{0}', matrix.environment)] }}
        run: |
          grafanactl apply -f dashboards/
          grafanactl apply -f datasources/
          grafanactl apply -f alerts/
```

#### GitLab CI Example
```yaml
# .gitlab-ci.yml
stages:
  - validate
  - deploy

variables:
  GRAFANA_CONFIG_DIR: "grafana-config"

validate:
  stage: validate
  script:
    - yamllint $GRAFANA_CONFIG_DIR/
    - grafanactl validate $GRAFANA_CONFIG_DIR/
  only:
    - merge_requests

deploy_dev:
  stage: deploy
  script:
    - grafanactl apply --target dev $GRAFANA_CONFIG_DIR/
  environment:
    name: development
  only:
    - develop

deploy_prod:
  stage: deploy
  script:
    - grafanactl apply --target prod $GRAFANA_CONFIG_DIR/
  environment:
    name: production
  only:
    - main
  when: manual
```

## Environment Management

### 1. Environment-Specific Configuration

#### Development Environment
```yaml
# environments/dev/config.yaml
grafana:
  url: "https://dev-grafana.company.com"
  folder: "dev-monitoring"
datasources:
  prometheus:
    url: "http://prometheus-dev:9090"
    editable: true
alerts:
  enabled: false
```

#### Production Environment
```yaml
# environments/prod/config.yaml
grafana:
  url: "https://grafana.company.com"
  folder: "production-monitoring"
datasources:
  prometheus:
    url: "http://prometheus-prod:9090"
    editable: false
alerts:
  enabled: true
  critical_only: true
```

### 2. Configuration Templates

#### Templated Dashboard
```yaml
# templates/service-dashboard.yaml.j2
apiVersion: v1
kind: Dashboard
metadata:
  name: "{{ service_name }}-dashboard"
spec:
  title: "{{ service_name | title }} Service Dashboard"
  tags: ["service", "{{ service_name }}"]
  panels:
    - title: "{{ service_name | title }} Response Time"
      type: "timeseries"
      targets:
        - expr: "histogram_quantile(0.95, rate(http_request_duration_seconds_bucket{service=\"{{ service_name }}\"}[5m]))"
    - title: "{{ service_name | title }} Error Rate"
      type: "stat"
      targets:
        - expr: "rate(http_requests_total{service=\"{{ service_name }}\", status=~\"5..\"}[5m])"
```

#### Template Generation Script
```python
#!/usr/bin/env python3
import yaml
from jinja2 import Template

services = ["api", "database", "cache", "queue"]

with open("templates/service-dashboard.yaml.j2", "r") as f:
    template = Template(f.read())

for service in services:
    dashboard = template.render(service_name=service)
    with open(f"dashboards/{service}-dashboard.yaml", "w") as f:
        f.write(dashboard)
    print(f"Generated dashboard for {service}")
```

## Validation Pipelines

### 1. Pre-commit Validation
```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/adrienverge/yamllint
    rev: v1.28.0
    hooks:
      - id: yamllint
        args: [-c=.yamllint.yaml]
  
  - repo: local
    hooks:
      - id: grafana-validate
        name: Validate Grafana configs
        entry: grafanactl validate
        language: system
        files: \.(yaml|yml)$
        pass_filenames: false
```

### 2. CI Validation Pipeline
```yaml
# .github/workflows/validate.yml
name: Validate Observability Config

on:
  pull_request:
    paths: ['dashboards/**', 'alerts/**', 'datasources/**']

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
          pip install yamllint jsonschema
          wget https://github.com/grafana/grafanactl/releases/latest/download/grafanactl-linux-amd64
          chmod +x grafanactl-linux-amd64
          sudo mv grafanactl-linux-amd64 /usr/local/bin/grafanactl

      - name: Validate YAML syntax
        run: yamllint .

      - name: Validate JSON syntax
        run: |
          find dashboards/ -name "*.json" -exec jq . {} \;

      - name: Validate Grafana configs
        run: grafanactl validate .

      - name: Check for required fields
        run: |
          python scripts/validate-required-fields.py
```

### 3. Custom Validation Script
```python
#!/usr/bin/env python3
# scripts/validate-required-fields.py

import os
import yaml
import json
import sys

def validate_dashboard(dashboard_data):
    required_fields = ['title', 'panels']
    errors = []
    
    for field in required_fields:
        if field not in dashboard_data:
            errors.append(f"Missing required field: {field}")
    
    if 'panels' in dashboard_data:
        for i, panel in enumerate(dashboard_data['panels']):
            if 'title' not in panel:
                errors.append(f"Panel {i} missing title")
            if 'targets' not in panel:
                errors.append(f"Panel {i} missing targets")
    
    return errors

def main():
    errors = []
    
    # Validate YAML dashboards
    for root, dirs, files in os.walk('dashboards'):
        for file in files:
            if file.endswith('.yaml') or file.endswith('.yml'):
                filepath = os.path.join(root, file)
                with open(filepath, 'r') as f:
                    try:
                        data = yaml.safe_load(f)
                        if 'spec' in data:  # Kubernetes-style resource
                            dashboard_errors = validate_dashboard(data['spec'])
                        else:
                            dashboard_errors = validate_dashboard(data)
                        
                        if dashboard_errors:
                            errors.extend([f"{filepath}: {error}" for error in dashboard_errors])
                    except yaml.YAMLError as e:
                        errors.append(f"{filepath}: YAML parsing error - {e}")
    
    # Validate JSON dashboards
    for root, dirs, files in os.walk('dashboards'):
        for file in files:
            if file.endswith('.json'):
                filepath = os.path.join(root, file)
                with open(filepath, 'r') as f:
                    try:
                        data = json.load(f)
                        dashboard_errors = validate_dashboard(data)
                        if dashboard_errors:
                            errors.extend([f"{filepath}: {error}" for error in dashboard_errors])
                    except json.JSONDecodeError as e:
                        errors.append(f"{filepath}: JSON parsing error - {e}")
    
    if errors:
        print("Validation errors found:")
        for error in errors:
            print(f"  - {error}")
        sys.exit(1)
    else:
        print("All validations passed!")

if __name__ == "__main__":
    main()
```

## Best Practices

### 1. Repository Organization
```
observability-as-code/
├── README.md
├── .gitignore
├── .pre-commit-config.yaml
├── environments/
│   ├── dev/
│   ├── staging/
│   └── prod/
├── dashboards/
│   ├── infrastructure/
│   ├── applications/
│   └── business/
├── datasources/
├── alerts/
│   ├── infrastructure/
│   └── applications/
├── templates/
├── scripts/
│   ├── validate.py
│   ├── generate.py
│   └── deploy.sh
└── docs/
    ├── getting-started.md
    └── contributing.md
```

### 2. Naming Conventions
```yaml
# Use consistent naming patterns
dashboards:
  - infrastructure-cpu-usage
  - infrastructure-memory-usage
  - application-api-performance
  - business-user-metrics

alerts:
  - infra-high-cpu-usage
  - infra-disk-space-low
  - app-api-error-rate-high
  - app-database-connection-failed

folders:
  - infrastructure-monitoring
  - application-monitoring
  - business-metrics
```

### 3. Documentation Standards
```markdown
# Dashboard: API Performance

## Purpose
Monitor API performance metrics including response times, error rates, and throughput.

## Metrics
- Response time (95th percentile)
- Error rate (5xx responses)
- Request throughput (requests/second)
- Database query time

## Alerts
- High error rate (>5% for 5 minutes)
- Slow response time (>2s for 10 minutes)

## Runbooks
- [High Error Rate Runbook](runbooks/api-high-error-rate.md)
- [Slow Response Time Runbook](runbooks/api-slow-response.md)
```

### 4. Change Management
```yaml
# .github/PULL_REQUEST_TEMPLATE.md
## Changes
- [ ] New dashboard
- [ ] Modified dashboard
- [ ] New alert
- [ ] Modified alert
- [ ] New datasource

## Testing
- [ ] Validated locally
- [ ] Tested in dev environment
- [ ] Reviewed by team

## Impact
- [ ] No breaking changes
- [ ] Backward compatible
- [ ] Requires coordination

## Checklist
- [ ] Documentation updated
- [ ] Tests added/updated
- [ ] Follows naming conventions
```

## Migration Strategies

### 1. Gradual Migration
```bash
#!/bin/bash
# migrate-to-code.sh

# Phase 1: Export existing dashboards
echo "Phase 1: Exporting existing dashboards..."
grafanactl get dashboards -o yaml > existing-dashboards.yaml

# Phase 2: Convert to code format
echo "Phase 2: Converting to code format..."
python scripts/convert-to-code.py existing-dashboards.yaml

# Phase 3: Validate converted dashboards
echo "Phase 3: Validating converted dashboards..."
grafanactl validate dashboards/

# Phase 4: Deploy to dev environment
echo "Phase 4: Testing in dev environment..."
grafanactl apply --target dev dashboards/

echo "Migration phase completed successfully!"
```

### 2. Parallel Deployment
```yaml
# Deploy both old and new dashboards in parallel
- name: Deploy legacy dashboards
  run: |
    # Keep existing dashboards running
    echo "Legacy dashboards still active"

- name: Deploy new code-based dashboards
  run: |
    # Deploy new dashboards with different names
    grafanactl apply -f dashboards/ --suffix "-v2"

- name: Validate new dashboards
  run: |
    # Test new dashboards
    python scripts/validate-dashboards.py --suffix "-v2"

- name: Switch traffic
  run: |
    # Update folder references to new dashboards
    python scripts/switch-to-new-dashboards.py
```

## Monitoring and Observability

### 1. Pipeline Monitoring
```yaml
# Monitor deployment pipeline health
- name: Report deployment status
  if: always()
  run: |
    curl -X POST "$SLACK_WEBHOOK" \
      -H 'Content-type: application/json' \
      -d '{
        "text": "Grafana deployment ${{ job.status }}: ${{ github.event.head_commit.message }}"
      }'
```

### 2. Configuration Drift Detection
```python
#!/usr/bin/env python3
# scripts/detect-drift.py

import requests
import yaml
import json

def get_live_dashboard(grafana_url, token, uid):
    response = requests.get(
        f"{grafana_url}/api/dashboards/uid/{uid}",
        headers={"Authorization": f"Bearer {token}"}
    )
    return response.json()["dashboard"]

def compare_dashboards(code_dashboard, live_dashboard):
    # Remove fields that change automatically
    ignore_fields = ["id", "version", "meta"]
    
    for field in ignore_fields:
        live_dashboard.pop(field, None)
    
    return code_dashboard == live_dashboard

def main():
    # Load dashboards from code
    with open("dashboards/api-dashboard.yaml", "r") as f:
        code_dashboard = yaml.safe_load(f)
    
    # Get live dashboard
    live_dashboard = get_live_dashboard(
        "https://grafana.company.com",
        "your-token",
        "api-dashboard-uid"
    )
    
    if not compare_dashboards(code_dashboard, live_dashboard):
        print("⚠️  Configuration drift detected!")
        print("Live dashboard differs from code version")
        return 1
    else:
        print("✅ No configuration drift detected")
        return 0

if __name__ == "__main__":
    exit(main())
```

## References

- [GitOps Principles](https://www.gitops.tech/)
- [Infrastructure as Code Best Practices](https://www.terraform.io/docs/cloud/guides/recommended-practices/)
- [Grafana Provisioning Documentation](https://grafana.com/docs/grafana/latest/administration/provisioning/)
- [Kubernetes Configuration Management](https://kubernetes.io/docs/concepts/configuration/)