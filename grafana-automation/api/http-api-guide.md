# Grafana HTTP API Guide

Complete guide for managing Grafana resources using the HTTP API with cURL and other HTTP clients.

## Authentication Setup

### API Token (Recommended)

1. **Create API Token:**
   - Go to Configuration → API Keys
   - Click "New API Key"
   - Set role (Viewer/Editor/Admin)
   - Copy the generated token

2. **Environment Setup:**
```bash
export GRAFANA_URL="http://localhost:3000"
export GRAFANA_TOKEN="your-api-token-here"
```

### Basic Authentication
```bash
export GRAFANA_USER="admin"
export GRAFANA_PASS="admin"
```

## Basic Operations with cURL

### Health Check
```bash
curl -X GET "$GRAFANA_URL/api/health" \
  -H "Authorization: Bearer $GRAFANA_TOKEN"
```

### List Dashboards
```bash
curl -X GET "$GRAFANA_URL/api/search?type=dash-db" \
  -H "Authorization: Bearer $GRAFANA_TOKEN"
```

### Get Dashboard by UID
```bash
curl -X GET "$GRAFANA_URL/api/dashboards/uid/{dashboard-uid}" \
  -H "Authorization: Bearer $GRAFANA_TOKEN"
```

### List Datasources
```bash
curl -X GET "$GRAFANA_URL/api/datasources" \
  -H "Authorization: Bearer $GRAFANA_TOKEN"
```

### List Folders
```bash
curl -X GET "$GRAFANA_URL/api/folders" \
  -H "Authorization: Bearer $GRAFANA_TOKEN"
```

## API Key Management

### Create API Key
```bash
curl -X POST "$GRAFANA_URL/api/auth/keys" \
  -H "Authorization: Bearer $GRAFANA_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "automation-key",
    "role": "Editor",
    "secondsToLive": 86400
  }'
```

### List API Keys
```bash
curl -X GET "$GRAFANA_URL/api/auth/keys" \
  -H "Authorization: Bearer $GRAFANA_TOKEN"
```

### Delete API Key
```bash
curl -X DELETE "$GRAFANA_URL/api/auth/keys/{id}" \
  -H "Authorization: Bearer $GRAFANA_TOKEN"
```

## Folder Management

### Create Folder
```bash
curl -X POST "$GRAFANA_URL/api/folders" \
  -H "Authorization: Bearer $GRAFANA_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "uid": "monitoring",
    "title": "Monitoring Dashboards"
  }'
```

### Update Folder
```bash
curl -X PUT "$GRAFANA_URL/api/folders/monitoring" \
  -H "Authorization: Bearer $GRAFANA_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Updated Monitoring Dashboards",
    "version": 1
  }'
```

### Delete Folder
```bash
curl -X DELETE "$GRAFANA_URL/api/folders/monitoring" \
  -H "Authorization: Bearer $GRAFANA_TOKEN"
```

### Get Folder Permissions
```bash
curl -X GET "$GRAFANA_URL/api/folders/monitoring/permissions" \
  -H "Authorization: Bearer $GRAFANA_TOKEN"
```

## Datasource Management

### Create Prometheus Datasource
```bash
curl -X POST "$GRAFANA_URL/api/datasources" \
  -H "Authorization: Bearer $GRAFANA_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Prometheus",
    "type": "prometheus",
    "url": "http://localhost:9090",
    "access": "proxy",
    "isDefault": true,
    "jsonData": {
      "httpMethod": "POST",
      "manageAlerts": true,
      "prometheusType": "Prometheus",
      "cacheLevel": "High"
    }
  }'
```

### Create Loki Datasource
```bash
curl -X POST "$GRAFANA_URL/api/datasources" \
  -H "Authorization: Bearer $GRAFANA_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Loki",
    "type": "loki",
    "url": "http://localhost:3100",
    "access": "proxy",
    "jsonData": {
      "maxLines": 1000
    }
  }'
```

### Create InfluxDB Datasource
```bash
curl -X POST "$GRAFANA_URL/api/datasources" \
  -H "Authorization: Bearer $GRAFANA_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "InfluxDB",
    "type": "influxdb",
    "url": "http://localhost:8086",
    "access": "proxy",
    "database": "telegraf",
    "user": "admin",
    "password": "admin",
    "jsonData": {
      "httpMode": "GET"
    }
  }'
```

### Update Datasource
```bash
curl -X PUT "$GRAFANA_URL/api/datasources/{id}" \
  -H "Authorization: Bearer $GRAFANA_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "id": 1,
    "name": "Prometheus-Updated",
    "type": "prometheus",
    "url": "http://prometheus:9090",
    "access": "proxy",
    "isDefault": true
  }'
```

### Test Datasource
```bash
curl -X POST "$GRAFANA_URL/api/datasources/{id}/health" \
  -H "Authorization: Bearer $GRAFANA_TOKEN"
```

### Delete Datasource
```bash
curl -X DELETE "$GRAFANA_URL/api/datasources/{id}" \
  -H "Authorization: Bearer $GRAFANA_TOKEN"
```

## Dashboard Management

### Create Dashboard
```bash
curl -X POST "$GRAFANA_URL/api/dashboards/db" \
  -H "Authorization: Bearer $GRAFANA_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "dashboard": {
      "id": null,
      "title": "System Metrics",
      "tags": ["system", "monitoring"],
      "timezone": "browser",
      "panels": [
        {
          "id": 1,
          "title": "CPU Usage",
          "type": "stat",
          "targets": [
            {
              "expr": "100 - (avg(irate(node_cpu_seconds_total{mode=\"idle\"}[5m])) * 100)",
              "refId": "A"
            }
          ],
          "gridPos": {"h": 8, "w": 12, "x": 0, "y": 0}
        }
      ],
      "time": {"from": "now-1h", "to": "now"},
      "refresh": "5s"
    },
    "folderUid": "monitoring",
    "overwrite": false
  }'
```

### Export Dashboard
```bash
curl -X GET "$GRAFANA_URL/api/dashboards/uid/{dashboard-uid}" \
  -H "Authorization: Bearer $GRAFANA_TOKEN" | \
  jq '.dashboard' > dashboard-backup.json
```

### Import Dashboard
```bash
curl -X POST "$GRAFANA_URL/api/dashboards/db" \
  -H "Authorization: Bearer $GRAFANA_TOKEN" \
  -H "Content-Type: application/json" \
  -d @dashboard-backup.json
```

### Update Dashboard
```bash
curl -X POST "$GRAFANA_URL/api/dashboards/db" \
  -H "Authorization: Bearer $GRAFANA_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "dashboard": {
      "uid": "existing-dashboard-uid",
      "title": "Updated Dashboard Title",
      "version": 2
    },
    "overwrite": true
  }'
```

### Delete Dashboard
```bash
curl -X DELETE "$GRAFANA_URL/api/dashboards/uid/{dashboard-uid}" \
  -H "Authorization: Bearer $GRAFANA_TOKEN"
```

### Search Dashboards
```bash
# Search by title
curl -X GET "$GRAFANA_URL/api/search?query=system" \
  -H "Authorization: Bearer $GRAFANA_TOKEN"

# Search by tag
curl -X GET "$GRAFANA_URL/api/search?tag=monitoring" \
  -H "Authorization: Bearer $GRAFANA_TOKEN"

# Search in folder
curl -X GET "$GRAFANA_URL/api/search?folderIds=1" \
  -H "Authorization: Bearer $GRAFANA_TOKEN"
```

## Alert Management

### Create Alert Rule
```bash
curl -X POST "$GRAFANA_URL/api/ruler/grafana/api/v1/rules/monitoring" \
  -H "Authorization: Bearer $GRAFANA_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "interval": "1m",
    "rules": [
      {
        "uid": "high-cpu-alert",
        "title": "High CPU Usage",
        "condition": "A",
        "data": [
          {
            "refId": "A",
            "queryType": "",
            "relativeTimeRange": {
              "from": 300,
              "to": 0
            },
            "model": {
              "expr": "100 - (avg(irate(node_cpu_seconds_total{mode=\"idle\"}[5m])) * 100)",
              "refId": "A"
            }
          }
        ],
        "noDataState": "NoData",
        "execErrState": "Alerting",
        "for": "5m",
        "annotations": {
          "description": "CPU usage is above 80%",
          "summary": "High CPU usage detected"
        },
        "labels": {
          "severity": "warning"
        }
      }
    ]
  }'
```

### List Alert Rules
```bash
curl -X GET "$GRAFANA_URL/api/ruler/grafana/api/v1/rules" \
  -H "Authorization: Bearer $GRAFANA_TOKEN"
```

### Create Contact Point
```bash
curl -X POST "$GRAFANA_URL/api/alertmanager/grafana/config/api/v1/receivers" \
  -H "Authorization: Bearer $GRAFANA_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "slack-alerts",
    "slack_configs": [
      {
        "api_url": "https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK",
        "channel": "#alerts",
        "username": "Grafana",
        "title": "🚨 Grafana Alert",
        "text": "{{ range .Alerts }}{{ .Annotations.summary }}{{ end }}"
      }
    ]
  }'
```

### Create Notification Channel (Legacy)
```bash
curl -X POST "$GRAFANA_URL/api/alert-notifications" \
  -H "Authorization: Bearer $GRAFANA_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "slack-alerts",
    "type": "slack",
    "settings": {
      "url": "https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK",
      "channel": "#alerts",
      "username": "Grafana"
    }
  }'
```

## User and Organization Management

### List Users
```bash
curl -X GET "$GRAFANA_URL/api/users" \
  -H "Authorization: Bearer $GRAFANA_TOKEN"
```

### Create User
```bash
curl -X POST "$GRAFANA_URL/api/admin/users" \
  -H "Authorization: Bearer $GRAFANA_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "John Doe",
    "email": "john@example.com",
    "login": "john",
    "password": "password123"
  }'
```

### Get Current User
```bash
curl -X GET "$GRAFANA_URL/api/user" \
  -H "Authorization: Bearer $GRAFANA_TOKEN"
```

### List Organizations
```bash
curl -X GET "$GRAFANA_URL/api/orgs" \
  -H "Authorization: Bearer $GRAFANA_TOKEN"
```

## Plugin Management

### List Installed Plugins
```bash
curl -X GET "$GRAFANA_URL/api/plugins" \
  -H "Authorization: Bearer $GRAFANA_TOKEN"
```

### Install Plugin
```bash
curl -X POST "$GRAFANA_URL/api/plugins/{plugin-id}/install" \
  -H "Authorization: Bearer $GRAFANA_TOKEN"
```

### Uninstall Plugin
```bash
curl -X DELETE "$GRAFANA_URL/api/plugins/{plugin-id}" \
  -H "Authorization: Bearer $GRAFANA_TOKEN"
```

## Advanced Operations

### Bulk Dashboard Export
```bash
#!/bin/bash
# Export all dashboards

DASHBOARDS=$(curl -s -X GET "$GRAFANA_URL/api/search?type=dash-db" \
  -H "Authorization: Bearer $GRAFANA_TOKEN" | jq -r '.[].uid')

mkdir -p dashboard-backups

for uid in $DASHBOARDS; do
  echo "Exporting dashboard: $uid"
  curl -s -X GET "$GRAFANA_URL/api/dashboards/uid/$uid" \
    -H "Authorization: Bearer $GRAFANA_TOKEN" | \
    jq '.dashboard' > "dashboard-backups/$uid.json"
done
```

### Bulk Dashboard Import
```bash
#!/bin/bash
# Import all dashboards from directory

for file in dashboard-backups/*.json; do
  echo "Importing dashboard: $file"
  curl -X POST "$GRAFANA_URL/api/dashboards/db" \
    -H "Authorization: Bearer $GRAFANA_TOKEN" \
    -H "Content-Type: application/json" \
    -d @"$file"
done
```

### Dashboard Provisioning Script
```bash
#!/bin/bash
# Complete Grafana setup script

set -e

echo "🚀 Starting Grafana provisioning..."

# Create monitoring folder
echo "📁 Creating monitoring folder..."
curl -s -X POST "$GRAFANA_URL/api/folders" \
  -H "Authorization: Bearer $GRAFANA_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "uid": "monitoring",
    "title": "Monitoring Dashboards"
  }' | jq '.'

# Create Prometheus datasource
echo "🔌 Creating Prometheus datasource..."
curl -s -X POST "$GRAFANA_URL/api/datasources" \
  -H "Authorization: Bearer $GRAFANA_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Prometheus",
    "type": "prometheus",
    "url": "http://prometheus:9090",
    "access": "proxy",
    "isDefault": true
  }' | jq '.'

# Import dashboards from directory
echo "📊 Importing dashboards..."
for dashboard_file in dashboards/*.json; do
    if [ -f "$dashboard_file" ]; then
        echo "Importing $(basename "$dashboard_file")..."
        curl -s -X POST "$GRAFANA_URL/api/dashboards/db" \
          -H "Authorization: Bearer $GRAFANA_TOKEN" \
          -H "Content-Type: application/json" \
          -d @"$dashboard_file" | jq '.'
    fi
done

echo "✅ Grafana provisioning completed!"
```

## Python Integration

### Basic API Client
```python
import requests
import json
from typing import Dict, List, Optional

class GrafanaAPI:
    def __init__(self, url: str, token: str):
        self.url = url.rstrip('/')
        self.headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }

    def create_datasource(self, config: Dict) -> Dict:
        response = requests.post(
            f'{self.url}/api/datasources',
            headers=self.headers,
            json=config
        )
        response.raise_for_status()
        return response.json()

    def create_dashboard(self, dashboard: Dict, folder_uid: str = None) -> Dict:
        payload = {
            'dashboard': dashboard,
            'overwrite': False
        }
        if folder_uid:
            payload['folderUid'] = folder_uid

        response = requests.post(
            f'{self.url}/api/dashboards/db',
            headers=self.headers,
            json=payload
        )
        response.raise_for_status()
        return response.json()

    def search_dashboards(self, query: str = '') -> List[Dict]:
        response = requests.get(
            f'{self.url}/api/search',
            headers=self.headers,
            params={'query': query, 'type': 'dash-db'}
        )
        response.raise_for_status()
        return response.json()

    def get_dashboard(self, uid: str) -> Dict:
        response = requests.get(
            f'{self.url}/api/dashboards/uid/{uid}',
            headers=self.headers
        )
        response.raise_for_status()
        return response.json()

# Usage Example
grafana = GrafanaAPI('http://localhost:3000', 'your-token')
result = grafana.create_datasource({
    'name': 'Prometheus',
    'type': 'prometheus',
    'url': 'http://localhost:9090',
    'access': 'proxy',
    'isDefault': True
})
print(f"Datasource created: {result}")
```

### Bulk Operations
```python
import os
import glob

def backup_all_dashboards(grafana_api: GrafanaAPI, backup_dir: str):
    os.makedirs(backup_dir, exist_ok=True)
    dashboards = grafana_api.search_dashboards()

    for dashboard in dashboards:
        uid = dashboard['uid']
        title = dashboard['title']
        full_dashboard = grafana_api.get_dashboard(uid)

        filename = f"{backup_dir}/{uid}-{title.replace(' ', '-')}.json"
        with open(filename, 'w') as f:
            json.dump(full_dashboard['dashboard'], f, indent=2)
        print(f"Backed up: {title}")

def restore_dashboards(grafana_api: GrafanaAPI, backup_dir: str):
    json_files = glob.glob(f"{backup_dir}/*.json")

    for file_path in json_files:
        with open(file_path, 'r') as f:
            dashboard = json.load(f)

        dashboard['id'] = None
        dashboard.pop('version', None)

        result = grafana_api.create_dashboard(dashboard)
        print(f"Restored: {dashboard['title']}")
```

## Error Handling and Best Practices

### Error Handling
```python
def safe_api_call(func, *args, **kwargs):
    try:
        response = func(*args, **kwargs)
        if response.status_code >= 400:
            print(f"API Error: {response.status_code} - {response.text}")
            return None
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")
        return None
```

### Rate Limiting
```python
import time
from functools import wraps

def rate_limit(calls_per_second=10):
    def decorator(func):
        last_called = [0.0]

        @wraps(func)
        def wrapper(*args, **kwargs):
            elapsed = time.time() - last_called[0]
            left_to_wait = 1.0 / calls_per_second - elapsed
            if left_to_wait > 0:
                time.sleep(left_to_wait)
            ret = func(*args, **kwargs)
            last_called[0] = time.time()
            return ret
        return wrapper
    return decorator
```

## Troubleshooting

### Common Issues

1. **Authentication Failed**
   ```bash
   # Check token validity
   curl -X GET "$GRAFANA_URL/api/user" \
     -H "Authorization: Bearer $GRAFANA_TOKEN"
   ```

2. **Permission Denied**
   - Verify API key has sufficient permissions
   - Check organization membership

3. **Dashboard Import Fails**
   - Remove `id` and `version` fields
   - Check datasource references
   - Validate JSON structure

### Debug Mode
```bash
# Enable verbose curl output
curl -v -X GET "$GRAFANA_URL/api/health"

# Save response for debugging
curl -X GET "$GRAFANA_URL/api/dashboards/uid/dashboard-uid" \
  -H "Authorization: Bearer $GRAFANA_TOKEN" \
  -o debug-response.json

# Pretty print JSON response
curl -X GET "$GRAFANA_URL/api/datasources" \
  -H "Authorization: Bearer $GRAFANA_TOKEN" | jq '.'
```

### Response Codes
- `200` - Success
- `400` - Bad Request (invalid JSON, missing fields)
- `401` - Unauthorized (invalid token)
- `403` - Forbidden (insufficient permissions)
- `404` - Not Found (resource doesn't exist)
- `409` - Conflict (resource already exists)
- `500` - Internal Server Error

## Security Best Practices

1. **Use API tokens** instead of basic auth
2. **Set appropriate token expiration**
3. **Use least privilege principle** for API keys
4. **Store tokens securely** in environment variables
5. **Rotate tokens regularly**
6. **Use HTTPS** in production
7. **Validate input data** before sending requests

## References

- [Grafana HTTP API Documentation](https://grafana.com/docs/grafana/latest/developers/http_api/)
- [Dashboard API](https://grafana.com/docs/grafana/latest/developers/http_api/dashboard/)
- [Datasource API](https://grafana.com/docs/grafana/latest/developers/http_api/data_source/)
- [Alerting API](https://grafana.com/docs/grafana/latest/developers/http_api/alerting/)
- [User API](https://grafana.com/docs/grafana/latest/developers/http_api/user/)