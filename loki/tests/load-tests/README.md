# Loki Load Tests

Validate Loki performance under **expected** traffic conditions.

## Goal
Verify system handles normal and peak log ingestion with acceptable performance.

## Test Scenarios

### 1. Fluent Bit
- High-performance log forwarding to Loki
- Target: 1K-10K lines/sec
- Multiple parsers (JSON, logfmt, Apache)

### 2. Promtail
- Native Loki log shipper
- File tailing with position tracking
- Label extraction and relabeling

### 3. Grafana Alloy
- Multi-tenant log ingestion
- OpenTelemetry support
- Service discovery

### 4. flog
- Fake log generator
- Configurable formats (JSON, Apache, Common)
- Rate-controlled output

### 5. logcli
- Query performance testing
- LogQL validation
- Tail functionality

## Tools

| Tool | Purpose | Use Case |
|------|---------|----------|
| **Fluent Bit** | Log forwarding | High-throughput ingestion |
| **Promtail** | Log collection | Native Loki integration |
| **Grafana Alloy** | Multi-tenant | Production-like scenarios |
| **flog** | Log generation | Synthetic load |
| **logcli** | Query testing | Read path validation |
| **curl** | API testing | Direct push testing |

## Success Criteria

- ✅ Push latency < 500ms (p99)
- ✅ Query latency < 5s (p99)
- ✅ Error rate < 0.1%
- ✅ No pod restarts
- ✅ No log drops
- ✅ Resource usage within limits

## Quick Start

```bash
# Generate fake logs with flog
cd flog
docker run -d --name flog mingrammer/flog -f json -l -d 100ms

# Forward logs with Fluent Bit
cd fluent-bit
fluent-bit -c fluent-bit-loki.yaml

# Collect logs with Promtail
cd promtail
promtail -config.file=promtail-config.yaml

# Test queries with logcli
cd logcli
./test-queries.sh

# Monitor ingestion
curl -s http://localhost:3100/metrics | grep loki_distributor_lines_received_total
```

## Key Metrics

```bash
# Lines received per second
rate(loki_distributor_lines_received_total[1m])

# Bytes received per second
rate(loki_distributor_bytes_received_total[1m])

# Push request latency
histogram_quantile(0.99, rate(loki_request_duration_seconds_bucket{route="loki_api_v1_push"}[5m]))

# Query latency
histogram_quantile(0.99, rate(loki_request_duration_seconds_bucket{route=~"loki_api_v1_query.*"}[5m]))
```
