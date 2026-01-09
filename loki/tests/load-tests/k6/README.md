# Loki Load Testing with Grafana k6

Load test Grafana Loki using [Grafana k6](https://k6.io/) with the [xk6-loki extension](https://github.com/grafana/xk6-loki).

## Overview

k6 with xk6-loki extension allows you to:
- **Push logs** - Simulate write path load with configurable streams and sizes
- **Query logs** - Test read path performance with randomized LogQL queries
- **Multi-tenant testing** - Test single-tenant or multi-tenant configurations

## Prerequisites

### Install k6 with xk6-loki Extension

```bash
# Option 1: Build from source using xk6
go install go.k6.io/xk6/cmd/xk6@latest
xk6 build --with github.com/grafana/xk6-loki@latest

# Option 2: Use Docker
docker run --rm -it -v $(pwd):/scripts grafana/xk6-loki:latest run /scripts/test.js

# Option 3: Download pre-built binary (check releases)
# https://github.com/grafana/xk6-loki/releases
```

### Verify Installation

```bash
./k6 version
# Should show k6 with xk6-loki extension
```

## Quick Start

### Basic Push Test

```bash
./k6 run push-test.js
```

### Basic Query Test

```bash
./k6 run query-test.js
```

### Combined Write + Read Test

```bash
./k6 run combined-test.js
```

## Test Files

| File | Description |
|------|-------------|
| `push-test.js` | Write path load testing |
| `query-test.js` | Read path load testing |
| `combined-test.js` | Combined write + read testing |
| `multi-tenant-test.js` | Multi-tenant load testing |

## Configuration

### Environment Variables

```bash
export LOKI_URL="http://localhost:3100"
export LOKI_TENANT="fake"
export VUS=10
export DURATION="5m"

./k6 run push-test.js
```

### Command Line Options

```bash
# Override VUs and duration
./k6 run --vus 20 --duration 10m push-test.js

# Output results to JSON
./k6 run --out json=results.json push-test.js

# Output to InfluxDB for Grafana visualization
./k6 run --out influxdb=http://localhost:8086/k6 push-test.js
```

## Key Concepts

### Streams and Labels

xk6-loki generates streams with these labels:
- **Predefined**: `instance`, `os`, `format`
- **Optional**: `namespace`, `app`, `pod`, `language`, `word`

Label cardinality controls unique stream count:
```javascript
const conf = new loki.Config(BASE_URL, 10000, 1.0, {
  namespace: 5,    // 5 different namespaces
  app: 10,         // 10 different apps
  pod: 50,         // 50 different pods
});
// Max unique streams = 3 (os) × 5 (format) × 5 × 10 × 50 × VUs
```

### Log Formats

xk6-loki uses [flog](https://github.com/mingrammer/flog) to generate realistic logs:
- `apache_common` - Apache common log format
- `apache_combined` - Apache combined log format
- `apache_error` - Apache error log format
- `rfc3164` - Syslog RFC3164
- `rfc5424` - Syslog RFC5424
- `json` - JSON format

### Multi-Tenancy

```javascript
// Single tenant (all VUs use same tenant)
const conf = new loki.Config("http://user:pass@localhost:3100", ...);

// Multi-tenant (each VU gets unique tenant: xk6-tenant-$VU)
const conf = new loki.Config("http://localhost:3100", ...);
```

## Metrics

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

## Success Criteria

| Metric | Target |
|--------|--------|
| Push latency (p99) | < 500ms |
| Query latency (p99) | < 5s |
| Error rate | < 0.1% |
| Throughput | > 10K lines/sec |

## Reference

- [xk6-loki GitHub](https://github.com/grafana/xk6-loki)
- [Grafana Blog: Load Testing Loki with k6](https://grafana.com/blog/a-quick-guide-to-load-testing-grafana-loki-with-grafana-k6/)
- [k6 Documentation](https://k6.io/docs/)
