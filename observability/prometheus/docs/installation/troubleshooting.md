# Troubleshooting Guide

Common issues and solutions for Prometheus installation and operation.

## Quick Diagnostics

### Health Checks

```bash
# API health
curl http://localhost:9090/-/healthy

# Ready check
curl http://localhost:9090/-/ready

# Configuration status
curl http://localhost:9090/api/v1/status/config

# Runtime info
curl http://localhost:9090/api/v1/status/runtimeinfo
```

### Key Metrics to Check

```promql
# Is Prometheus scraping itself?
up{job="prometheus"}

# Active time series
prometheus_tsdb_head_series

# Scrape duration
prometheus_target_interval_length_seconds

# Memory usage
process_resident_memory_bytes

# Failed scrapes
up == 0
```

## Installation Issues

### Service Won't Start

#### Linux (systemd)

```bash
# Check status
sudo systemctl status prometheus

# View detailed logs
sudo journalctl -u prometheus -n 100 --no-pager

# Check for configuration errors
promtool check config /etc/prometheus/prometheus.yml
```

**Common causes:**
- Port 9090 already in use
- Invalid YAML configuration
- Permission issues on data directory
- Missing binary or wrong path

**Solutions:**

```bash
# Check port usage
sudo ss -tlnp | grep 9090
sudo lsof -i :9090

# Fix permissions
sudo chown -R prometheus:prometheus /var/lib/prometheus
sudo chmod 755 /var/lib/prometheus

# Validate config
promtool check config /etc/prometheus/prometheus.yml
```

#### macOS (launchd)

```bash
# Check logs
cat /usr/local/var/log/prometheus/prometheus.error.log

# Check if loaded
launchctl list | grep prometheus

# Reload service
launchctl unload ~/Library/LaunchAgents/io.prometheus.prometheus.plist
launchctl load ~/Library/LaunchAgents/io.prometheus.prometheus.plist
```

#### Windows

```powershell
# Check service status
Get-Service prometheus

# View event logs
Get-EventLog -LogName Application -Source prometheus -Newest 20

# Check port
Get-NetTCPConnection -LocalPort 9090
```

#### Docker

```bash
# Check container logs
docker logs prometheus

# Check if container is running
docker ps -a | grep prometheus

# Inspect container
docker inspect prometheus
```

#### Kubernetes

```bash
# Check pod status
kubectl get pods -n monitoring

# Describe pod for events
kubectl describe pod -n monitoring prometheus-prometheus-kube-prometheus-prometheus-0

# View logs
kubectl logs -n monitoring prometheus-prometheus-kube-prometheus-prometheus-0 -c prometheus
```

### Configuration Errors

#### Validate Configuration

```bash
# Using promtool
promtool check config /path/to/prometheus.yml

# Docker
docker run --rm -v /path/to/prometheus.yml:/etc/prometheus/prometheus.yml:ro \
  prom/prometheus promtool check config /etc/prometheus/prometheus.yml

# Kubernetes
kubectl exec -n monitoring prometheus-prometheus-kube-prometheus-prometheus-0 -c prometheus -- \
  promtool check config /etc/prometheus/config_out/prometheus.env.yaml
```

#### Common YAML Errors

**Indentation issues:**
```yaml
# Wrong
scrape_configs:
- job_name: "prometheus"
  static_configs:
  - targets: ["localhost:9090"]

# Correct
scrape_configs:
  - job_name: "prometheus"
    static_configs:
      - targets: ["localhost:9090"]
```

**Invalid duration format:**
```yaml
# Wrong
scrape_interval: 15 seconds

# Correct
scrape_interval: 15s
```

**Missing quotes:**
```yaml
# Wrong (YAML interprets as boolean)
job_name: true

# Correct
job_name: "true"
```

### Permission Denied

#### Linux

```bash
# Fix data directory
sudo chown -R prometheus:prometheus /var/lib/prometheus
sudo chmod 755 /var/lib/prometheus

# Fix config file
sudo chown prometheus:prometheus /etc/prometheus/prometheus.yml
sudo chmod 644 /etc/prometheus/prometheus.yml
```

#### Docker

```bash
# Prometheus runs as nobody (65534)
sudo chown -R 65534:65534 /path/to/data

# Or run as root (not recommended)
docker run --user root ...
```

#### Kubernetes

```yaml
# Add securityContext to pod spec
securityContext:
  runAsUser: 65534
  runAsGroup: 65534
  fsGroup: 65534
```

### Port Already in Use

```bash
# Find process using port 9090
# Linux
sudo ss -tlnp | grep 9090
sudo lsof -i :9090

# macOS
lsof -i :9090

# Windows
Get-NetTCPConnection -LocalPort 9090 | Select-Object OwningProcess
Get-Process -Id <PID>

# Kill process or change Prometheus port
# --web.listen-address=0.0.0.0:9091
```

## Scraping Issues

### Targets Not Discovered

#### Check Target Status

```bash
# Via API
curl 'http://localhost:9090/api/v1/targets' | jq '.data.activeTargets'

# Or visit http://localhost:9090/targets in browser
```

#### Static Targets

```yaml
# Verify target is reachable
curl http://target-host:port/metrics

# Check firewall rules
# Linux
sudo iptables -L -n | grep 9090

# Check DNS resolution
nslookup target-host
```

#### Kubernetes Service Discovery

```bash
# Check pod annotations
kubectl get pods -o yaml | grep -A5 "prometheus.io"

# Verify ServiceMonitor selector matches
kubectl get servicemonitor <name> -o yaml
kubectl get prometheus -o yaml | grep -A10 serviceMonitorSelector

# Check RBAC permissions
kubectl auth can-i list pods --as=system:serviceaccount:monitoring:prometheus
```

### Scrape Failures

#### Check Error Messages

```promql
# Failed scrapes
scrape_samples_scraped{job="<job_name>"} == 0

# Scrape duration
scrape_duration_seconds{job="<job_name>"}
```

#### Common Errors

**Connection refused:**
- Target not running
- Wrong port
- Firewall blocking

**Context deadline exceeded:**
- Target too slow
- Increase `scrape_timeout`

**Certificate errors:**
```yaml
# Skip TLS verification (not recommended for production)
scrape_configs:
  - job_name: "my-job"
    scheme: https
    tls_config:
      insecure_skip_verify: true
```

**Authentication required:**
```yaml
scrape_configs:
  - job_name: "my-job"
    basic_auth:
      username: user
      password: pass
    # Or use bearer token
    bearer_token_file: /path/to/token
```

## Performance Issues

### High Memory Usage

#### Diagnose

```bash
# Check active series
curl -s 'http://localhost:9090/api/v1/query?query=prometheus_tsdb_head_series' | jq '.data.result[0].value[1]'

# Check memory usage
curl -s 'http://localhost:9090/api/v1/query?query=process_resident_memory_bytes' | jq '.data.result[0].value[1]'

# Top series by cardinality
curl -s 'http://localhost:9090/api/v1/status/tsdb' | jq '.data.seriesCountByMetricName | to_entries | sort_by(-.value) | .[0:10]'
```

#### Solutions

1. **Reduce retention:**
```yaml
# prometheus.yml or command line
--storage.tsdb.retention.time=7d
```

2. **Drop high-cardinality metrics:**
```yaml
metric_relabel_configs:
  - source_labels: [__name__]
    regex: 'high_cardinality_metric.*'
    action: drop
```

3. **Increase memory limits:**
```yaml
# Kubernetes
resources:
  limits:
    memory: 8Gi
```

4. **Use remote write for long-term storage:**
```yaml
remote_write:
  - url: http://mimir:9009/api/v1/push
```

### Slow Queries

#### Diagnose

```promql
# Query duration histogram
prometheus_engine_query_duration_seconds

# Slow queries in logs
# Look for "slow query" messages
```

#### Solutions

1. **Optimize queries:**
   - Use `rate()` instead of `increase()` for counters
   - Limit time range
   - Use recording rules for complex queries

2. **Add recording rules:**
```yaml
groups:
  - name: example
    rules:
      - record: job:http_requests:rate5m
        expr: sum(rate(http_requests_total[5m])) by (job)
```

3. **Increase query timeout:**
```yaml
--query.timeout=2m
```

### Disk Space Issues

#### Check Usage

```bash
# Linux
df -h /var/lib/prometheus

# Docker
docker exec prometheus df -h /prometheus

# Kubernetes
kubectl exec -n monitoring prometheus-prometheus-kube-prometheus-prometheus-0 -c prometheus -- df -h /prometheus
```

#### Solutions

1. **Reduce retention:**
```yaml
--storage.tsdb.retention.time=7d
--storage.tsdb.retention.size=50GB
```

2. **Clean up old data:**
```bash
# Delete blocks older than retention
# Prometheus does this automatically, but you can trigger compaction
curl -X POST http://localhost:9090/api/v1/admin/tsdb/clean_tombstones
```

3. **Expand storage (Kubernetes):**
```bash
kubectl patch pvc <pvc-name> -n monitoring -p '{"spec":{"resources":{"requests":{"storage":"100Gi"}}}}'
```

## Kubernetes-Specific Issues

### Pod Stuck in Pending

```bash
kubectl describe pod -n monitoring <pod-name>

# Common causes:
# - Insufficient resources
# - PVC not bound
# - Node selector/affinity mismatch
```

### PVC Not Bound

```bash
# Check PVC status
kubectl get pvc -n monitoring
kubectl describe pvc -n monitoring <pvc-name>

# Check StorageClass
kubectl get storageclass

# Check events
kubectl get events -n monitoring --sort-by='.lastTimestamp'
```

### ServiceMonitor Not Working

```bash
# Check ServiceMonitor exists
kubectl get servicemonitors -n monitoring

# Verify labels match Prometheus selector
kubectl get prometheus -n monitoring -o yaml | grep -A10 serviceMonitorSelector

# Check target service exists and has correct labels
kubectl get svc -l <selector-labels>

# Check endpoints
kubectl get endpoints <service-name>
```

### CRDs Missing

```bash
# Check if CRDs are installed
kubectl get crd | grep monitoring.coreos.com

# Install CRDs
kubectl apply --server-side -f https://raw.githubusercontent.com/prometheus-operator/prometheus-operator/main/example/prometheus-operator-crd/monitoring.coreos.com_prometheuses.yaml
```

## Remote Write Issues

### Failed Samples

```promql
# Check failed samples
prometheus_remote_storage_samples_failed_total

# Check pending samples
prometheus_remote_storage_pending_samples

# Check retried samples
prometheus_remote_storage_retried_samples_total
```

### Common Errors

**Connection refused:**
- Remote endpoint not reachable
- Wrong URL

**401 Unauthorized:**
- Missing or invalid authentication

**429 Too Many Requests:**
- Rate limiting, reduce batch size

**5xx errors:**
- Remote endpoint issues

### Solutions

```yaml
remote_write:
  - url: http://mimir:9009/api/v1/push
    # Add authentication
    headers:
      X-Scope-OrgID: tenant1
    # Tune queue config
    queue_config:
      capacity: 10000
      max_shards: 50
      max_samples_per_send: 5000
    # Add retry config
    write_relabel_configs:
      - source_labels: [__name__]
        regex: 'unwanted_metric.*'
        action: drop
```

## Alerting Issues

### Alerts Not Firing

```bash
# Check rule evaluation
curl 'http://localhost:9090/api/v1/rules' | jq '.data.groups[].rules[] | select(.type=="alerting")'

# Check Alertmanager connection
curl 'http://localhost:9090/api/v1/alertmanagers'
```

### Alerts Not Reaching Alertmanager

```bash
# Check Alertmanager is configured
curl 'http://localhost:9090/api/v1/status/config' | jq '.data.yaml' | grep -A10 alerting

# Check Alertmanager is reachable
curl http://alertmanager:9093/-/healthy
```

## Getting Help

### Collect Diagnostic Information

```bash
# Prometheus version
prometheus --version

# Configuration (sanitized)
curl http://localhost:9090/api/v1/status/config

# Runtime info
curl http://localhost:9090/api/v1/status/runtimeinfo

# TSDB status
curl http://localhost:9090/api/v1/status/tsdb

# Targets
curl http://localhost:9090/api/v1/targets

# Recent logs
journalctl -u prometheus -n 500 --no-pager
```

### Resources

- [Prometheus Documentation](https://prometheus.io/docs/)
- [Prometheus GitHub Issues](https://github.com/prometheus/prometheus/issues)
- [Prometheus Mailing List](https://groups.google.com/g/prometheus-users)
- [Prometheus Slack](https://slack.cncf.io/) (#prometheus channel)
