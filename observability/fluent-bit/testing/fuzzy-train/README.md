# fuzzy-train — Log Generator for Fluent Bit Testing

fuzzy-train generates realistic fake logs in multiple formats to test Fluent Bit's
collection, parsing, filtering, and forwarding to Loki.

- **Docker Hub**: https://hub.docker.com/r/sagarnikam123/fuzzy-train
- **GitHub**: https://github.com/sagarnikam123/fuzzy-train
- **Latest image**: `sagarnikam123/fuzzy-train:2.2.0`

## What it tests

| Scenario | Manifest |
|----------|----------|
| Single pod writing to stdout | `deployment-stdout.yaml` |
| Multiple pods (one per node) writing to stdout | `daemonset-stdout.yaml` |
| Multiple formats simultaneously | `deployment-multi-format.yaml` |

## Log Formats Available

| Format | `--log-format` value | Use case |
|--------|----------------------|----------|
| JSON | `JSON` | Default, structured logs |
| Logfmt | `logfmt` | Go-style logs |
| Apache Common | `apache common` | Web server logs |
| Apache Combined | `apache combined` | Web server logs with referrer |
| Apache Error | `apache error` | Web server error logs |
| BSD Syslog | `bsd syslog` | RFC3164 syslog |
| Syslog | `syslog` | RFC5424 syslog |

## Quick Deploy

```bash
# Create namespace
kubectl create namespace fuzzy-train

# Deploy stdout (fluent-bit picks up via tail input)
kubectl apply -f deployment-stdout.yaml

# Deploy daemonset (one pod per node, higher volume)
kubectl apply -f daemonset-stdout.yaml

# Deploy multiple formats at once
kubectl apply -f deployment-multi-format.yaml
```

## Verify logs in Loki (Grafana Explore)

```logql
# All fuzzy-train logs
{namespace="fuzzy-train"}

# By format
{namespace="fuzzy-train", container="fuzzy-train-json"}
{namespace="fuzzy-train", container="fuzzy-train-logfmt"}
{namespace="fuzzy-train", container="fuzzy-train-apache"}

# Filter by log level
{namespace="fuzzy-train"} |= "ERROR"
{namespace="fuzzy-train"} |= "WARN"

# Parse JSON log line and filter by level field
{namespace="fuzzy-train"} | json | level="ERROR"

# Rate of logs per second
rate({namespace="fuzzy-train"}[1m])
```

## Cleanup

```bash
kubectl delete namespace fuzzy-train
```
