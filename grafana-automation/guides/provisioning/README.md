# Grafana Provisioning Guide

Complete guide for using Grafana's built-in provisioning system to automatically configure resources using YAML files.

## Overview

Grafana Provisioning is the built-in method to automatically configure Grafana resources (datasources, dashboards, alerts) using YAML files. When Grafana starts, it reads these configuration files and creates/updates resources accordingly.

### Ideal For:
- **Container deployments** (Docker, Kubernetes)
- **Immutable infrastructure** patterns
- **Automated setup** without manual UI configuration
- **Version-controlled** configuration management

## Configuration Structure

```
grafana/
├── provisioning/
│   ├── datasources/
│   │   └── datasources.yaml
│   ├── dashboards/
│   │   ├── dashboards.yaml
│   │   └── json/
│   │       └── system-dashboard.json
│   ├── alerting/
│   │   ├── rules.yaml
│   │   └── policies.yaml
│   └── plugins/
│       └── plugins.yaml
└── grafana.ini
```

## Datasource Provisioning

### Basic Datasources
```yaml
# provisioning/datasources/datasources.yaml
apiVersion: 1

datasources:
  - name: Prometheus
    type: prometheus
    access: proxy
    url: http://prometheus:9090
    isDefault: true
    editable: false

  - name: Loki
    type: loki
    access: proxy
    url: http://loki:3100
    editable: false

  - name: InfluxDB
    type: influxdb
    access: proxy
    url: http://influxdb:8086
    database: telegraf
    user: admin
    secureJsonData:
      password: admin
    editable: false
```

### Advanced Datasource Configuration
```yaml
# provisioning/datasources/advanced.yaml
apiVersion: 1

datasources:
  - name: Prometheus-Advanced
    type: prometheus
    access: proxy
    url: http://prometheus:9090
    isDefault: true
    jsonData:
      httpMethod: POST
      manageAlerts: true
      prometheusType: Prometheus
      cacheLevel: High
      timeInterval: 15s
      queryTimeout: 60s
      exemplarTraceIdDestinations:
        - name: trace_id
          datasourceUid: jaeger-uid
    secureJsonData:
      httpHeaderValue1: 'Bearer your-token-here'
    editable: false

  - name: Loki-Advanced
    type: loki
    access: proxy
    url: http://loki:3100
    jsonData:
      maxLines: 1000
      derivedFields:
        - matcherRegex: "trace_id=(\\w+)"
          name: TraceID
          url: "http://jaeger:16686/trace/$${__value.raw}"
          datasourceUid: jaeger-uid
    editable: false

  - name: Jaeger
    type: jaeger
    access: proxy
    url: http://jaeger:14268
    uid: jaeger-uid
    editable: false
```

### Multiple Environment Datasources
```yaml
# provisioning/datasources/multi-env.yaml
apiVersion: 1

datasources:
  - name: Prometheus-Dev
    type: prometheus
    access: proxy
    url: http://prometheus-dev:9090
    isDefault: false
    editable: false

  - name: Prometheus-Staging
    type: prometheus
    access: proxy
    url: http://prometheus-staging:9090
    isDefault: false
    editable: false

  - name: Prometheus-Prod
    type: prometheus
    access: proxy
    url: http://prometheus-prod:9090
    isDefault: true
    editable: false
```

## Dashboard Provisioning

### Basic Dashboard Provider
```yaml
# provisioning/dashboards/dashboards.yaml
apiVersion: 1

providers:
  - name: 'System Dashboards'
    orgId: 1
    folder: 'System Monitoring'
    type: file
    disableDeletion: false
    updateIntervalSeconds: 10
    allowUiUpdates: true
    options:
      path: /etc/grafana/provisioning/dashboards/json

  - name: 'Application Dashboards'
    orgId: 1
    folder: 'Applications'
    type: file
    disableDeletion: true
    options:
      path: /var/lib/grafana/dashboards/apps
```

### Advanced Dashboard Provider
```yaml
# provisioning/dashboards/advanced.yaml
apiVersion: 1

providers:
  - name: 'Infrastructure'
    orgId: 1
    folder: 'Infrastructure'
    type: file
    disableDeletion: false
    updateIntervalSeconds: 30
    allowUiUpdates: true
    options:
      path: /etc/grafana/provisioning/dashboards/infrastructure
      foldersFromFilesStructure: true

  - name: 'Team Dashboards'
    orgId: 1
    folder: ''  # Use folder structure from files
    type: file
    disableDeletion: true
    updateIntervalSeconds: 60
    allowUiUpdates: false
    options:
      path: /etc/grafana/provisioning/dashboards/teams
      foldersFromFilesStructure: true
```

## Alert Rule Provisioning

### Basic Alert Rules
```yaml
# provisioning/alerting/rules.yaml
groups:
  - name: system-alerts
    orgId: 1
    folder: System Alerts
    interval: 1m
    rules:
      - uid: high-cpu-usage
        title: High CPU Usage
        condition: A
        data:
          - refId: A
            queryType: ''
            relativeTimeRange:
              from: 300
              to: 0
            model:
              expr: 100 - (avg(irate(node_cpu_seconds_total{mode="idle"}[5m])) * 100)
              refId: A
        noDataState: NoData
        execErrState: Alerting
        for: 5m
        annotations:
          description: 'CPU usage is above 80%'
          summary: 'High CPU usage detected'
        labels:
          severity: warning

      - uid: high-memory-usage
        title: High Memory Usage
        condition: B
        data:
          - refId: B
            queryType: ''
            relativeTimeRange:
              from: 300
              to: 0
            model:
              expr: (1 - (node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes)) * 100
              refId: B
        noDataState: NoData
        execErrState: Alerting
        for: 5m
        annotations:
          description: 'Memory usage is above 85%'
          summary: 'High memory usage detected'
        labels:
          severity: critical
```

### Application Alert Rules
```yaml
# provisioning/alerting/app-rules.yaml
groups:
  - name: application-alerts
    orgId: 1
    folder: Application Alerts
    interval: 30s
    rules:
      - uid: api-high-error-rate
        title: API High Error Rate
        condition: A
        data:
          - refId: A
            queryType: ''
            relativeTimeRange:
              from: 300
              to: 0
            model:
              expr: rate(http_requests_total{status=~"5.."}[5m]) / rate(http_requests_total[5m]) * 100
              refId: A
        noDataState: NoData
        execErrState: Alerting
        for: 2m
        annotations:
          description: 'API error rate is above 5%'
          summary: 'High API error rate detected'
        labels:
          severity: warning
          service: api

      - uid: database-connection-failure
        title: Database Connection Failure
        condition: B
        data:
          - refId: B
            queryType: ''
            relativeTimeRange:
              from: 60
              to: 0
            model:
              expr: up{job="database"} == 0
              refId: B
        noDataState: Alerting
        execErrState: Alerting
        for: 1m
        annotations:
          description: 'Database connection is down'
          summary: 'Database connection failure'
        labels:
          severity: critical
          service: database
```

## Notification Policy Provisioning

### Basic Notification Policies
```yaml
# provisioning/alerting/policies.yaml
policies:
  - orgId: 1
    receiver: grafana-default-email
    group_by: ['grafana_folder', 'alertname']
    routes:
      - receiver: slack-alerts
        object_matchers:
          - ['severity', '=', 'critical']
        group_wait: 10s
        group_interval: 5m
        repeat_interval: 12h
      - receiver: email-alerts
        object_matchers:
          - ['severity', '=', 'warning']
        group_wait: 30s
        group_interval: 10m
        repeat_interval: 24h

contactPoints:
  - orgId: 1
    name: slack-alerts
    receivers:
      - uid: slack-webhook
        type: slack
        settings:
          url: https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK
          channel: '#alerts'
          username: Grafana
          title: '🚨 Grafana Alert'
          text: |
            {{ range .Alerts }}
            **{{ .Annotations.summary }}**
            {{ .Annotations.description }}
            Labels: {{ range .Labels.SortedPairs }}{{ .Name }}={{ .Value }} {{ end }}
            {{ end }}

  - orgId: 1
    name: email-alerts
    receivers:
      - uid: email-notification
        type: email
        settings:
          addresses:
            - alerts@company.com
            - oncall@company.com
          subject: '[{{ .Status | toUpper }}] {{ .GroupLabels.alertname }}'
          message: |
            {{ range .Alerts }}
            Alert: {{ .Annotations.summary }}
            Description: {{ .Annotations.description }}
            Labels: {{ range .Labels.SortedPairs }}{{ .Name }}={{ .Value }} {{ end }}
            {{ end }}
```

### Advanced Notification Policies
```yaml
# provisioning/alerting/advanced-policies.yaml
policies:
  - orgId: 1
    receiver: default-receiver
    group_by: ['grafana_folder', 'alertname']
    group_wait: 10s
    group_interval: 5m
    repeat_interval: 12h
    routes:
      # Critical alerts to PagerDuty
      - receiver: pagerduty-critical
        object_matchers:
          - ['severity', '=', 'critical']
        group_wait: 5s
        group_interval: 2m
        repeat_interval: 1h
        
      # Service-specific routing
      - receiver: database-team
        object_matchers:
          - ['service', '=', 'database']
        group_wait: 15s
        group_interval: 5m
        repeat_interval: 6h
        
      # Time-based routing (business hours)
      - receiver: slack-business-hours
        object_matchers:
          - ['severity', '=', 'warning']
        active_time_intervals:
          - business-hours
        group_wait: 30s
        group_interval: 10m
        repeat_interval: 24h

contactPoints:
  - orgId: 1
    name: pagerduty-critical
    receivers:
      - uid: pagerduty-integration
        type: pagerduty
        settings:
          integrationKey: your-pagerduty-integration-key
          severity: critical
          component: Grafana
          group: Infrastructure

  - orgId: 1
    name: database-team
    receivers:
      - uid: database-slack
        type: slack
        settings:
          url: https://hooks.slack.com/services/DATABASE/TEAM/WEBHOOK
          channel: '#database-alerts'
          username: Grafana-DB

timeIntervals:
  - name: business-hours
    time_intervals:
      - times:
          - start_time: '09:00'
            end_time: '17:00'
        weekdays: ['monday:friday']
```

## Plugin Provisioning

```yaml
# provisioning/plugins/plugins.yaml
apiVersion: 1

apps:
  - type: grafana-clock-panel
    disabled: false
  - type: grafana-piechart-panel
    disabled: false
  - type: grafana-worldmap-panel
    disabled: false
```

## Docker Integration

### Docker Compose with Provisioning
```yaml
# docker-compose.yml
version: '3.8'
services:
  grafana:
    image: grafana/grafana:latest
    ports:
      - "3000:3000"
    volumes:
      - ./provisioning:/etc/grafana/provisioning
      - ./dashboards:/var/lib/grafana/dashboards
      - grafana-storage:/var/lib/grafana
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
      - GF_PATHS_PROVISIONING=/etc/grafana/provisioning
      - GF_INSTALL_PLUGINS=grafana-clock-panel,grafana-piechart-panel
    networks:
      - monitoring

  prometheus:
    image: prom/prometheus:latest
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
    networks:
      - monitoring

volumes:
  grafana-storage:

networks:
  monitoring:
```

### Kubernetes Deployment
```yaml
# k8s-grafana-provisioning.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: grafana-datasources
data:
  datasources.yaml: |
    apiVersion: 1
    datasources:
      - name: Prometheus
        type: prometheus
        access: proxy
        url: http://prometheus-service:9090
        isDefault: true
        editable: false
---
apiVersion: v1
kind: ConfigMap
metadata:
  name: grafana-dashboards-config
data:
  dashboards.yaml: |
    apiVersion: 1
    providers:
      - name: 'default'
        orgId: 1
        folder: ''
        type: file
        disableDeletion: false
        options:
          path: /var/lib/grafana/dashboards
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: grafana
spec:
  replicas: 1
  selector:
    matchLabels:
      app: grafana
  template:
    metadata:
      labels:
        app: grafana
    spec:
      containers:
      - name: grafana
        image: grafana/grafana:latest
        ports:
        - containerPort: 3000
        env:
        - name: GF_SECURITY_ADMIN_PASSWORD
          value: "admin"
        volumeMounts:
        - name: grafana-datasources
          mountPath: /etc/grafana/provisioning/datasources
        - name: grafana-dashboards-config
          mountPath: /etc/grafana/provisioning/dashboards
        - name: grafana-dashboards
          mountPath: /var/lib/grafana/dashboards
      volumes:
      - name: grafana-datasources
        configMap:
          name: grafana-datasources
      - name: grafana-dashboards-config
        configMap:
          name: grafana-dashboards-config
      - name: grafana-dashboards
        configMap:
          name: grafana-dashboards-json
```

## Environment-Specific Configuration

### Development Environment
```yaml
# provisioning/datasources/dev.yaml
apiVersion: 1

datasources:
  - name: Prometheus-Dev
    type: prometheus
    access: proxy
    url: http://localhost:9090
    isDefault: true
    editable: true  # Allow editing in dev
    jsonData:
      httpMethod: GET
      manageAlerts: false
```

### Production Environment
```yaml
# provisioning/datasources/prod.yaml
apiVersion: 1

datasources:
  - name: Prometheus-Prod
    type: prometheus
    access: proxy
    url: http://prometheus.monitoring.svc.cluster.local:9090
    isDefault: true
    editable: false  # Prevent editing in prod
    jsonData:
      httpMethod: POST
      manageAlerts: true
      timeInterval: 15s
      queryTimeout: 60s
    secureJsonData:
      httpHeaderValue1: 'Bearer ${PROMETHEUS_TOKEN}'
```

## Best Practices

### 1. File Organization
```
provisioning/
├── datasources/
│   ├── 01-prometheus.yaml
│   ├── 02-loki.yaml
│   └── 03-influxdb.yaml
├── dashboards/
│   ├── dashboards.yaml
│   └── json/
│       ├── system/
│       ├── application/
│       └── business/
└── alerting/
    ├── rules/
    │   ├── system-rules.yaml
    │   └── app-rules.yaml
    └── policies/
        └── notification-policies.yaml
```

### 2. Environment Variables
```yaml
# Use environment variables for sensitive data
datasources:
  - name: Prometheus
    type: prometheus
    url: ${PROMETHEUS_URL}
    secureJsonData:
      httpHeaderValue1: 'Bearer ${PROMETHEUS_TOKEN}'
```

### 3. Version Control
- Store all provisioning files in Git
- Use separate branches for different environments
- Review changes through pull requests
- Tag releases for rollback capability

### 4. Validation
```bash
# Validate YAML syntax
yamllint provisioning/

# Check Grafana configuration
docker run --rm -v $(pwd)/provisioning:/etc/grafana/provisioning \
  grafana/grafana:latest grafana-cli admin reset-admin-password --homepath /usr/share/grafana admin
```

## Troubleshooting

### Common Issues

1. **Provisioning Not Working**
   - Check file permissions
   - Verify YAML syntax
   - Check Grafana logs: `docker logs grafana`

2. **Datasource Connection Failed**
   - Verify URL accessibility from Grafana container
   - Check network connectivity
   - Validate credentials

3. **Dashboard Not Loading**
   - Ensure JSON files are valid
   - Check dashboard provider configuration
   - Verify folder permissions

### Debug Commands
```bash
# Check Grafana logs
docker logs grafana

# Validate provisioning files
docker exec grafana grafana-cli admin reset-admin-password admin

# Test datasource connectivity
curl -X GET "http://localhost:3000/api/datasources" \
  -H "Authorization: Bearer your-token"
```

## References

- [Grafana Provisioning Documentation](https://grafana.com/docs/grafana/latest/administration/provisioning/)
- [Datasource Provisioning](https://grafana.com/docs/grafana/latest/administration/provisioning/#datasources)
- [Dashboard Provisioning](https://grafana.com/docs/grafana/latest/administration/provisioning/#dashboards)
- [Alert Provisioning](https://grafana.com/docs/grafana/latest/administration/provisioning/#alerting)