# Loki Load Tests

Validate Loki performance under **expected** traffic conditions.

## Goal
Verify system handles normal and peak log ingestion with acceptable performance.

## Test Scenarios

### 1. k6 with xk6-loki (Recommended)
- Professional load testing tool from Grafana Labs
- Push and query path testing
- Multi-tenant support
- Detailed metrics and thresholds

### 2. Fluent Bit
- High-performance log forwarding to Loki
- Target: 1K-10K lines/sec
- Multiple parsers (JSON, logfmt, Apache)

### 3. Promtail
- Native Loki log shipper
- File tailing with position tracking
- Label extraction and relabeling

### 4. Grafana Alloy
- Multi-tenant log ingestion
- OpenTelemetry support
- Service discovery

### 5. flog
- Fake log generator
- Configurable formats (JSON, Apache, Common)
- Rate-controlled output

### 6. logcli
- Query performance testing
- LogQL validation
- Tail functionality

## Tools

| Tool | Purpose | Use Case |
|------|---------|----------|
| **k6 + xk6-loki** | Load testing | Professional write/read path testing |
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

### k6 Load Testing (Recommended)

```bash
# Build k6 with xk6-loki extension
xk6 build --with github.com/grafana/xk6-loki@latest

# Run push test
./k6 run k6/push-test.js

# Run query test
./k6 run k6/query-test.js

# Run combined write + read test
./k6 run k6/combined-test.js

# Run with custom VUs and duration
./k6 run --vus 20 --duration 10m k6/push-test.js
```

### Other Tools

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

## k6 Metrics (xk6-loki)

### Push Metrics
| Metric | Description |
|--------|-------------|
| `loki_client_lines` | Total lines pushed |
| `loki_client_uncompressed_bytes` | Total uncompressed bytes pushed |

### Query Metrics
| Metric | Description |
|--------|-------------|
| `loki_bytes_processed_total` | Total bytes processed by queries |
| `loki_lines_processed_total` | Total lines processed by queries |
| `loki_bytes_processed_per_second` | Query throughput (bytes/sec) |
| `loki_lines_processed_per_second` | Query throughput (lines/sec) |

## Reference

- [Grafana Blog: Load Testing Loki with k6](https://grafana.com/blog/a-quick-guide-to-load-testing-grafana-loki-with-grafana-k6/)
- [xk6-loki GitHub](https://github.com/grafana/xk6-loki)
- [k6 Documentation](https://k6.io/docs/)
