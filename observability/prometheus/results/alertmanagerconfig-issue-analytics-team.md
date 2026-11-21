# AlertmanagerConfig Configuration Issue

**Date:** 2026-01-16
**Cluster:** scnx-global-dev-aps1-eks
**Severity:** Warning
**Affected Team:** Analytics

---

## Summary

The `AlertmanagerConfig` resource in the `analytics` namespace has a configuration error that is causing `PrometheusOperatorSyncFailed` alerts cluster-wide.

---

## Problem

The Prometheus Operator is failing to sync Alertmanager configuration due to a missing required field.

**Error Message:**
```
AlertmanagerConfig analytics/analytics-policy-management-service-config:
EmailConfig[0]: SMTP smarthost is a mandatory field, it is neither specified
at global config nor at receiver level
```

---

## Affected Resource

```yaml
apiVersion: monitoring.coreos.com/v1alpha1
kind: AlertmanagerConfig
metadata:
  name: analytics-policy-management-service-config
  namespace: analytics
  labels:
    app.kubernetes.io/instance: analytics-policy-management-service
    app.kubernetes.io/managed-by: Helm
    release: prometheus
```

---

## Current Configuration (Problematic)

```yaml
spec:
  receivers:
  - name: slack-email
    emailConfigs:
    - requireTLS: true
      sendResolved: true
      to: apms-alerts-aaaapsmhauuvot3vxdnsqaslyi@securonix.org.slack.com
      # ❌ MISSING: smarthost (SMTP server address)
      # ❌ MISSING: from (sender email address)
```

---

## Required Fix

Add the missing `smarthost` and `from` fields to the emailConfigs:

```yaml
spec:
  receivers:
  - name: slack-email
    emailConfigs:
    - to: "apms-alerts-aaaapsmhauuvot3vxdnsqaslyi@securonix.org.slack.com"
      smarthost: "smtp.your-mail-server.com:587"  # ✅ Required
      from: "alertmanager@securonix.com"          # ✅ Required
      requireTLS: true
      sendResolved: true
```

**OR** if email alerts are not needed, remove the `emailConfigs` section entirely:

```yaml
spec:
  receivers:
  - name: slack-email
    # Remove emailConfigs if not using email notifications
  route:
    receiver: slack-email
    # ... rest of route config
```

---

## How to Fix

### Option 1: Update Helm Chart Values

If using Helm, update your values file for `analytics-policy-management-service`:

```yaml
alertmanagerConfig:
  receivers:
  - name: slack-email
    emailConfigs:
    - to: "apms-alerts-...@securonix.org.slack.com"
      smarthost: "smtp.your-server.com:587"
      from: "alertmanager@securonix.com"
      requireTLS: true
      sendResolved: true
```

Then upgrade:
```bash
helm upgrade analytics-policy-management-service <chart> -n analytics -f values.yaml
```

### Option 2: Patch Directly (Temporary)

```bash
kubectl patch alertmanagerconfig analytics-policy-management-service-config \
  -n analytics --type=merge -p '{
  "spec": {
    "receivers": [{
      "name": "slack-email",
      "emailConfigs": [{
        "to": "apms-alerts-aaaapsmhauuvot3vxdnsqaslyi@securonix.org.slack.com",
        "smarthost": "smtp.your-server.com:587",
        "from": "alertmanager@securonix.com",
        "requireTLS": true,
        "sendResolved": true
      }]
    }]
  }
}'
```

### Option 3: Delete if Not Needed

```bash
kubectl delete alertmanagerconfig analytics-policy-management-service-config -n analytics
```

---

## Impact

| Component | Impact |
|-----------|--------|
| Prometheus scraping | ✅ Not affected |
| Metrics collection | ✅ Not affected |
| Remote write to Mimir | ✅ Not affected |
| Alert rule evaluation | ✅ Not affected |
| Email notifications for APMS alerts | ❌ Not working |
| PrometheusOperatorSyncFailed alert | ⚠️ Firing continuously |

---

## Verification

After fixing, verify the sync is successful:

```bash
# Check operator logs
kubectl logs -n prometheus -l app.kubernetes.io/name=prometheus-operator --tail=20 | grep -i "analytics"

# Verify no sync errors
kubectl logs -n prometheus -l app.kubernetes.io/name=prometheus-operator --tail=50 | grep -i "error"

# Check alert is resolved
kubectl get prometheusrules -A | grep -i sync
```

---

## Contact

For questions about this issue, contact the Platform/SRE team.
