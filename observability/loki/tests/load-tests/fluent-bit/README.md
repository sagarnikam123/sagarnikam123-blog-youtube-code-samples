# Fluent Bit - Log Forwarding to Loki

Uses [Fluent Bit](https://fluentbit.io/) for high-performance log forwarding to Loki.

## What is Fluent Bit?

Fluent Bit is a lightweight, high-performance log processor and forwarder:
- **Performance**: Low memory footprint (~450KB)
- **Plugins**: Native Loki output plugin
- **Parsers**: JSON, logfmt, regex, Apache, nginx
- **Features**: Buffering, retry, multiline

## Quick Start

### 1. Binary Installation

```bash
# macOS
brew install fluent-bit

# Run with config
fluent-bit -c fluent-bit-loki.yaml
```

### 2. Docker

```bash
docker run -d --name fluent-bit \
  -v $(pwd)/fluent-bit-loki.yaml:/fluent-bit/etc/fluent-bit.yaml \
  -v /var/log:/var/log:ro \
  fluent/fluent-bit:latest \
  -c /fluent-bit/etc/fluent-bit.yaml
```

### 3. Kubernetes

```bash
kubectl apply -f kubernetes/fluent-bit-daemonset.yaml -n loki-test
```

## Configuration Examples

### Basic File Tail to Loki

```yaml
service:
  flush: 1
  log_level: info

pipeline:
  inputs:
    - name: tail
      path: /var/log/app/*.log
      tag: app.logs
      read_from_head: false
      db: /tmp/fluent-bit-app.db

  outputs:
    - name: loki
      match: "*"
      host: localhost
      port: 3100
      labels: job=fluent-bit, env=test
      auto_kubernetes_labels: off
```

### JSON Logs with Parsing

```yaml
service:
  flush: 1
  log_level: info
  parsers_file: parsers.conf

pipeline:
  inputs:
    - name: tail
      path: /var/log/app/*.json
      tag: app.json
      parser: json
      db: /tmp/fluent-bit-json.db

  outputs:
    - name: loki
      match: "*"
      host: localhost
      port: 3100
      labels: job=app, format=json
      label_keys: $level,$service
```

### Multi-Tenant Configuration

```yaml
pipeline:
  inputs:
    - name: tail
      path: /var/log/tenant-a/*.log
      tag: tenant-a
      db: /tmp/fb-tenant-a.db

    - name: tail
      path: /var/log/tenant-b/*.log
      tag: tenant-b
      db: /tmp/fb-tenant-b.db

  outputs:
    - name: loki
      match: tenant-a
      host: localhost
      port: 3100
      tenant_id: tenant-a
      labels: job=app

    - name: loki
      match: tenant-b
      host: localhost
      port: 3100
      tenant_id: tenant-b
      labels: job=app
```

### Load Testing Configuration

```yaml
service:
  flush: 1
  log_level: warn
  http_server: on
  http_listen: 0.0.0.0
  http_port: 2020

pipeline:
  inputs:
    - name: tail
      path: ${HOME}/data/log/logger/*.log
      tag: load-test
      read_from_head: false
      refresh_interval: 5
      db: /tmp/fluent-bit-load.db
      mem_buf_limit: 50MB

  outputs:
    - name: loki
      match: "*"
      host: 127.0.0.1
      port: 3100
      labels: job=load-test
      batch_wait: 1
      batch_size: 1048576
      line_format: json
      http_user: ""
      http_passwd: ""
      tenant_id: ""
```

## Key Parameters

| Parameter | Description | Default |
|-----------|-------------|---------|
| `host` | Loki hostname | localhost |
| `port` | Loki port | 3100 |
| `labels` | Static labels | - |
| `label_keys` | Dynamic labels from log | - |
| `tenant_id` | X-Scope-OrgID header | - |
| `batch_wait` | Max wait before flush (sec) | 1 |
| `batch_size` | Max batch size (bytes) | 1MB |
| `line_format` | json or key_value | json |

## Monitoring Fluent Bit

```bash
# Enable HTTP server in config
# http_server: on
# http_port: 2020

# Check metrics
curl http://localhost:2020/api/v1/metrics

# Check health
curl http://localhost:2020/api/v1/health

# Key metrics
curl -s http://localhost:2020/api/v1/metrics/prometheus | grep -E "fluentbit_(input|output)"
```

## Troubleshooting

```bash
# Enable debug logging
# log_level: debug

# Check tail position DB
ls -la /tmp/fluent-bit-*.db

# Reset position (re-read from head)
rm /tmp/fluent-bit-*.db

# Test config syntax
fluent-bit -c fluent-bit-loki.yaml --dry-run
```

## Parsers

Create `parsers.conf`:

```ini
[PARSER]
    Name        json
    Format      json
    Time_Key    time
    Time_Format %Y-%m-%dT%H:%M:%S.%L

[PARSER]
    Name        logfmt
    Format      logfmt

[PARSER]
    Name        apache
    Format      regex
    Regex       ^(?<host>[^ ]*) [^ ]* (?<user>[^ ]*) \[(?<time>[^\]]*)\] "(?<method>\S+)(?: +(?<path>[^\"]*?)(?: +\S*)?)?" (?<code>[^ ]*) (?<size>[^ ]*)(?: "(?<referer>[^\"]*)" "(?<agent>[^\"]*)")?$
    Time_Key    time
    Time_Format %d/%b/%Y:%H:%M:%S %z
```

## Resources

- [Fluent Bit Documentation](https://docs.fluentbit.io/)
- [Loki Output Plugin](https://docs.fluentbit.io/manual/pipeline/outputs/loki)
- [YAML Configuration](https://docs.fluentbit.io/manual/administration/configuring-fluent-bit/yaml)
