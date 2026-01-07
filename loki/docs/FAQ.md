# Loki FAQ

## General

### What is the difference between monolithic and distributed mode?

- **Monolithic**: All components run in a single process. Best for local development, testing, and small-scale deployments.
- **Distributed (Simple Scalable)**: Components split into read, write, and backend paths. Better for production and high-volume workloads.

### Which deployment mode should I use?

| Use Case | Recommended Mode |
|----------|------------------|
| Local development | Monolithic |
| Testing/POC | Monolithic |
| < 100GB/day ingestion | Monolithic |
| > 100GB/day ingestion | Simple Scalable |
| High availability required | Simple Scalable |

### What's the difference between inmemory and memberlist KV store?

- **inmemory**: Single-node only, no network overhead, faster startup
- **memberlist**: Multi-node clustering, gossip protocol, required for distributed deployments

Use `inmemory` for single-node/monolithic, `memberlist` for multi-node/distributed.

## Storage

### What storage backends does Loki support?

- **Filesystem**: Local disk storage (development only)
- **S3**: AWS S3 or S3-compatible (MinIO, etc.)
- **GCS**: Google Cloud Storage
- **Azure Blob**: Azure Blob Storage

### Should I use Thanos objstore client?

Thanos objstore is opt-in in Loki 3.6.x and recommended for new deployments. It provides:
- Better performance
- More consistent behavior across cloud providers
- Active development

### MinIO bucket doesn't exist error

```
NoSuchBucket: The specified bucket does not exist
```

Create the bucket before starting Loki:
```bash
mc mb myminio/loki-data
```

Or use the `start-minio.sh` script which creates required buckets automatically.

## Log Collectors

### Fluent Bit vs Promtail vs Alloy?

| Collector | Best For |
|-----------|----------|
| Fluent Bit | Lightweight, multi-format parsing, Kubernetes |
| Promtail | Simple Loki-native setup, service discovery |
| Alloy | OpenTelemetry, metrics + logs + traces |

### Fluent Bit not sending logs to Loki

1. Check if Fluent Bit is running: `ps aux | grep fluent-bit`
2. Check metrics: `curl http://127.0.0.1:2020/api/v1/metrics`
3. Verify `files_opened > 0` in metrics
4. Check Loki is accessible: `curl http://127.0.0.1:3100/ready`

### Fluent Bit ${HOME} or env variables not working

Fluent Bit's `env` section only accepts static values. You cannot nest variables like:
```yaml
# WRONG - doesn't work
env:
  LOG_DIR: ${HOME}/data/log/logger
```

Use system env variables directly in paths:
```yaml
# CORRECT
path: ${HOME}/data/log/logger/app.log
```

### Fluent Bit tail input parser option

The `parser` option in tail input accepts only ONE parser name:
```yaml
# CORRECT
- name: tail
  parser: json_parser

# WRONG - multiple parsers not supported
- name: tail
  parser: json_parser,logfmt_parser
```

For mixed log formats, use separate tail inputs per format.

## Helm Installation

### Memberlist warnings during startup

```
msg="joining memberlist cluster" err="no such host"
```

These warnings are normal during startup. They resolve once the pod is fully up and the memberlist service is available.

### MinIO endpoint configuration

For Helm deployments with bundled MinIO:
```yaml
# values-minio.yaml
loki:
  storage:
    s3:
      endpoint: http://loki-minio.loki.svc:9000
```

Note: The endpoint format is `loki-minio.<namespace>.svc`

## Querying

### Query timeout errors

Increase timeout in limits_config:
```yaml
limits_config:
  query_timeout: 5m
```

### "too many outstanding requests" error

Increase query concurrency:
```yaml
querier:
  max_concurrent: 8

frontend:
  max_outstanding_per_tenant: 2048
```

## Troubleshooting

### Loki not starting - compactor error

```
failed to init delete store: failed to get s3 object
```

Ensure:
1. Storage backend (MinIO/S3) is running
2. Bucket exists
3. Credentials are correct
4. Endpoint URL is accessible

### Check Loki health

```bash
# Ready check
curl http://127.0.0.1:3100/ready

# Metrics
curl http://127.0.0.1:3100/metrics

# Config
curl http://127.0.0.1:3100/config
```

### View Loki logs

```bash
# Binary install
# Check terminal where Loki is running

# Kubernetes
kubectl logs -n loki -l app.kubernetes.io/name=loki -f
```


## Metrics & Monitoring

### Fluent Bit Metrics

Fluent Bit exposes metrics at `http://127.0.0.1:2020/api/v1/metrics`

```bash
curl -s http://127.0.0.1:2020/api/v1/metrics | jq
```

#### Key Input Metrics (per tail input)

| Metric | Description |
|--------|-------------|
| `records` | Total records/lines read from file |
| `bytes` | Total bytes read |
| `files_opened` | Number of files currently being tailed |
| `files_closed` | Files closed (rotation, deletion) |
| `files_rotated` | File rotation events detected |

#### Key Output Metrics (per Loki output)

| Metric | Description |
|--------|-------------|
| `proc_records` | Records processed/sent to Loki |
| `proc_bytes` | Bytes sent to Loki |
| `errors` | Failed send attempts |
| `retries` | Retry attempts |
| `retries_failed` | Retries that ultimately failed |
| `dropped_records` | Records dropped (buffer full, etc.) |

#### Example: Check lines exported to Loki

```bash
# Get all output metrics
curl -s http://127.0.0.1:2020/api/v1/metrics | jq '.output'

# Response shows proc_records per Loki output:
# "loki.0": {"proc_records": 1523, "proc_bytes": 245678, "errors": 0, ...}
# "loki.1": {"proc_records": 892, "proc_bytes": 156234, "errors": 0, ...}
```

#### Prometheus Metrics

Fluent Bit also exposes Prometheus format at `http://127.0.0.1:2020/api/v1/metrics/prometheus`

```bash
curl -s http://127.0.0.1:2020/api/v1/metrics/prometheus | grep fluentbit_output
```

### Loki Metrics

Loki exposes Prometheus metrics at `http://127.0.0.1:3100/metrics`

#### Key Ingestion Metrics

| Metric | Description |
|--------|-------------|
| `loki_distributor_lines_received_total` | Total log lines received |
| `loki_distributor_bytes_received_total` | Total bytes received |
| `loki_ingester_chunks_created_total` | Chunks created |
| `loki_ingester_chunks_flushed_total` | Chunks flushed to storage |

#### Example: Check lines ingested into Loki

```bash
# Total lines received
curl -s http://127.0.0.1:3100/metrics | grep loki_distributor_lines_received_total

# Total bytes received
curl -s http://127.0.0.1:3100/metrics | grep loki_distributor_bytes_received_total

# Ingestion rate (lines/sec) - use with Prometheus or calculate delta
curl -s http://127.0.0.1:3100/metrics | grep loki_distributor_lines_received_total
```

#### Key Query Metrics

| Metric | Description |
|--------|-------------|
| `loki_request_duration_seconds` | Request latency histogram |
| `loki_query_frontend_queries_total` | Total queries processed |
| `loki_querier_tail_active` | Active tail queries |

#### Key Storage Metrics

| Metric | Description |
|--------|-------------|
| `loki_chunk_store_chunks_stored_total` | Chunks stored |
| `loki_compactor_running` | Compactor status (1=running) |
| `loki_boltdb_shipper_uploads_total` | Index uploads to object store |

#### Health & Status

| Metric | Description |
|--------|-------------|
| `loki_build_info` | Loki version info |
| `loki_ingester_memory_chunks` | In-memory chunks count |
| `loki_ingester_wal_records_logged_total` | WAL records written |

### Quick Health Check Commands

```bash
# Fluent Bit: Records read vs sent
curl -s http://127.0.0.1:2020/api/v1/metrics | jq '{
  input_records: [.input[].records] | add,
  output_records: [.output[].proc_records] | add,
  output_errors: [.output[].errors] | add
}'

# Loki: Lines ingested
curl -s http://127.0.0.1:3100/metrics 2>/dev/null | grep -E "^loki_distributor_lines_received_total"

# Loki: Ready status
curl -s http://127.0.0.1:3100/ready

# Loki: Ingester status
curl -s http://127.0.0.1:3100/ring | head -20
```

### How much data received in Loki (MB/GB)?

```bash
# Total bytes received (raw number)
curl -s http://127.0.0.1:3100/metrics | grep loki_distributor_bytes_received_total

# Convert to MB/GB
curl -s http://127.0.0.1:3100/metrics | grep "^loki_distributor_bytes_received_total" | \
  awk '{printf "%.2f MB (%.2f GB)\n", $2/1024/1024, $2/1024/1024/1024}'

# Per-tenant breakdown
curl -s http://127.0.0.1:3100/metrics | grep loki_distributor_bytes_received_total | \
  awk -F'[{"}]' '{for(i=1;i<=NF;i++) if($i ~ /tenant/) print $(i+2), $NF}' | \
  awk '{printf "%s: %.2f MB\n", $1, $2/1024/1024}'
```

### What is the last data/timestamp received in Loki?

Use LogQL to find the most recent log entry:

```bash
# Using logcli - get latest log timestamp
logcli query '{job=~".+"}' --limit=1 --since=1h

# Using curl - query API
curl -G "http://127.0.0.1:3100/loki/api/v1/query_range" \
  --data-urlencode 'query={job=~".+"}' \
  --data-urlencode 'limit=1' \
  --data-urlencode 'direction=backward' | jq '.data.result[0].values[0][0]'

# Convert nanosecond timestamp to human readable
curl -G "http://127.0.0.1:3100/loki/api/v1/query_range" \
  --data-urlencode 'query={job=~".+"}' \
  --data-urlencode 'limit=1' \
  --data-urlencode 'direction=backward' 2>/dev/null | \
  jq -r '.data.result[0].values[0][0] | tonumber / 1000000000 | strftime("%Y-%m-%d %H:%M:%S")'
```

Using Loki metrics (approximate):
```bash
# Check when last chunk was created (indicates recent ingestion)
curl -s http://127.0.0.1:3100/metrics | grep loki_ingester_chunks_created_total
```

### How many failed logs in Fluent Bit?

```bash
# Total errors across all outputs
curl -s http://127.0.0.1:2020/api/v1/metrics | jq '[.output[].errors] | add'

# Detailed error breakdown per output
curl -s http://127.0.0.1:2020/api/v1/metrics | jq '.output | to_entries[] | {name: .key, errors: .value.errors, retries: .value.retries, retries_failed: .value.retries_failed, dropped: .value.dropped_records}'

# Prometheus format - total errors
curl -s http://127.0.0.1:2020/api/v1/metrics/prometheus | grep -E "fluentbit_output_errors_total|fluentbit_output_retries"
```

Key error metrics:
| Metric | Description |
|--------|-------------|
| `errors` | Total failed send attempts |
| `retries` | Retry attempts made |
| `retries_failed` | Retries that ultimately failed |
| `dropped_records` | Records dropped (buffer overflow, etc.) |

### What errors are in Fluent Bit or Loki? (Using Metrics)

#### Fluent Bit Error Detection

```bash
# Check for any errors in outputs
curl -s http://127.0.0.1:2020/api/v1/metrics | jq '{
  total_errors: [.output[].errors] | add,
  total_retries_failed: [.output[].retries_failed] | add,
  total_dropped: [.output[].dropped_records] | add,
  outputs_with_errors: [.output | to_entries[] | select(.value.errors > 0) | .key]
}'

# Prometheus format - all error-related metrics
curl -s http://127.0.0.1:2020/api/v1/metrics/prometheus | grep -E "(error|retry|drop)"
```

#### Loki Error Detection

```bash
# Discarded/rejected samples (rate limiting, validation errors)
curl -s http://127.0.0.1:3100/metrics | grep loki_discarded_samples_total

# Request errors by route
curl -s http://127.0.0.1:3100/metrics | grep -E "loki_request_duration_seconds_count.*status_code=\"[45]"

# Ingester errors
curl -s http://127.0.0.1:3100/metrics | grep -E "loki_ingester.*(error|failed)"

# Compactor errors
curl -s http://127.0.0.1:3100/metrics | grep -E "loki_compactor.*(error|failed)"

# WAL errors
curl -s http://127.0.0.1:3100/metrics | grep -E "loki_ingester_wal.*(error|failed|corrupt)"
```

#### Key Error Metrics Summary

| Component | Metric | Description |
|-----------|--------|-------------|
| **Fluent Bit** | `errors` | Failed output attempts |
| **Fluent Bit** | `retries_failed` | Exhausted retries |
| **Fluent Bit** | `dropped_records` | Lost records |
| **Loki** | `loki_discarded_samples_total` | Rejected logs (by reason) |
| **Loki** | `loki_request_duration_seconds_count{status_code=~"4..\\|5.."}` | HTTP errors |
| **Loki** | `loki_ingester_wal_corruptions_total` | WAL corruption events |

#### Common Error Reasons in `loki_discarded_samples_total`

| Reason | Description |
|--------|-------------|
| `rate_limited` | Ingestion rate limit exceeded |
| `line_too_long` | Log line exceeds max_line_size |
| `stream_limit` | Too many streams per tenant |
| `per_stream_rate_limit` | Per-stream rate limit exceeded |
| `invalid_labels` | Malformed or invalid labels |

#### Quick Error Summary Script

```bash
#!/bin/bash
echo "=== Fluent Bit Errors ==="
curl -s http://127.0.0.1:2020/api/v1/metrics 2>/dev/null | jq '{
  errors: [.output[].errors] | add // 0,
  retries_failed: [.output[].retries_failed] | add // 0,
  dropped: [.output[].dropped_records] | add // 0
}' 2>/dev/null || echo "Fluent Bit not reachable"

echo ""
echo "=== Loki Discarded Samples ==="
curl -s http://127.0.0.1:3100/metrics 2>/dev/null | grep loki_discarded_samples_total || echo "No discarded samples"

echo ""
echo "=== Loki HTTP Errors (4xx/5xx) ==="
curl -s http://127.0.0.1:3100/metrics 2>/dev/null | grep -E 'loki_request_duration_seconds_count.*status_code="[45]' | head -5 || echo "No HTTP errors"
```

### Key Operational Metrics for Loki

These are the most important metrics to monitor for Loki's operational efficiency:

#### Ingestion Health

| Metric | Description | Alert Threshold |
|--------|-------------|-----------------|
| `loki_distributor_bytes_received_total` | Total bytes ingested | Monitor rate |
| `loki_distributor_lines_received_total` | Total log lines ingested | Monitor rate |
| `loki_distributor_ingester_clients` | Connected ingesters | Should be > 0 |
| `loki_ingester_memory_chunks` | In-memory chunks | High = memory pressure |
| `loki_ingester_memory_streams_labels_bytes` | Memory used by stream labels | Monitor growth |

```bash
# Quick ingestion health check
curl -s http://127.0.0.1:3100/metrics | grep -E "^loki_(distributor_bytes_received_total|distributor_lines_received_total|distributor_ingester_clients|ingester_memory_chunks)"
```

#### WAL (Write-Ahead Log) Health

| Metric | Description | Alert Threshold |
|--------|-------------|-----------------|
| `loki_ingester_wal_bytes_in_use` | WAL disk usage | Monitor growth |
| `loki_ingester_wal_logged_bytes_total` | Total bytes written to WAL | Monitor rate |
| `loki_ingester_wal_disk_full_failures_total` | WAL disk full errors | > 0 = critical |
| `loki_ingester_wal_replay_active` | WAL replay in progress | 1 during startup |

```bash
# WAL health check
curl -s http://127.0.0.1:3100/metrics | grep -E "^loki_ingester_wal_(bytes_in_use|logged_bytes_total|disk_full_failures_total|replay_active)"
```

#### Chunk Lifecycle

| Metric | Description | Alert Threshold |
|--------|-------------|-----------------|
| `loki_ingester_chunks_created_total` | Chunks created | Monitor rate |
| `loki_ingester_chunks_flush_failures_total` | Failed chunk flushes | > 0 = investigate |
| `loki_ingester_flush_queue_length` | Pending flush queue | High = backpressure |
| `loki_chunk_store_deduped_chunks_total` | Deduplicated chunks | Normal operation |

```bash
# Chunk health check
curl -s http://127.0.0.1:3100/metrics | grep -E "^loki_ingester_(chunks_created_total|chunks_flush_failures_total|flush_queue_length)"
```

#### Compactor Health

| Metric | Description | Alert Threshold |
|--------|-------------|-----------------|
| `loki_boltdb_shipper_compactor_running` | Compactor status | 1 = running |
| `loki_compactor_apply_retention_operation_total` | Retention runs | Monitor success |
| `loki_compactor_apply_retention_last_successful_run_timestamp_seconds` | Last successful retention | Stale = problem |

```bash
# Compactor health check
curl -s http://127.0.0.1:3100/metrics | grep -E "^loki_(boltdb_shipper_compactor_running|compactor_apply_retention)"
```

#### Cache Efficiency

| Metric | Description | Alert Threshold |
|--------|-------------|-----------------|
| `loki_cache_hits` | Cache hits by cache type | Higher = better |
| `loki_cache_fetched_keys` | Total cache lookups | Compare with hits |
| `loki_embeddedcache_memory_bytes` | Cache memory usage | Monitor limits |
| `loki_cache_corrupt_chunks_total` | Corrupted cache entries | > 0 = investigate |

```bash
# Cache efficiency (hit ratio)
curl -s http://127.0.0.1:3100/metrics | grep -E "^loki_cache_(hits|fetched_keys)" | grep -v "bucket"
```

#### Query Performance

| Metric | Description | Alert Threshold |
|--------|-------------|-----------------|
| `loki_request_duration_seconds` | Request latency | p99 > 10s = slow |
| `loki_query_frontend_connected_clients` | Connected queriers | Should be > 0 |
| `loki_querier_tail_active` | Active tail queries | Monitor for load |

```bash
# Query performance
curl -s http://127.0.0.1:3100/metrics | grep -E "^loki_(request_duration_seconds|query_frontend_connected_clients|querier_tail_active)" | grep -v "bucket"
```

#### Error Tracking

| Metric | Description | Alert Threshold |
|--------|-------------|-----------------|
| `loki_discarded_samples_total` | Rejected logs by reason | > 0 = investigate |
| `loki_internal_log_messages_total{level="error"}` | Internal errors | Monitor growth |
| `loki_ingester_autoforget_unhealthy_ingesters_total` | Ring health issues | > 0 = ring problem |

```bash
# Error summary
curl -s http://127.0.0.1:3100/metrics | grep -E "^loki_(discarded_samples_total|internal_log_messages_total|ingester_autoforget)"
```

#### Complete Health Check Script

```bash
#!/bin/bash
LOKI_URL="${1:-http://127.0.0.1:3100}"

echo "=== Loki Operational Health Check ==="
echo ""

echo "--- Ingestion ---"
curl -s "$LOKI_URL/metrics" | grep -E "^loki_distributor_(bytes_received_total|lines_received_total|ingester_clients)" 2>/dev/null || echo "No ingestion metrics"

echo ""
echo "--- Memory ---"
curl -s "$LOKI_URL/metrics" | grep -E "^loki_ingester_memory_(chunks|streams_labels_bytes)" 2>/dev/null || echo "No memory metrics"

echo ""
echo "--- WAL ---"
curl -s "$LOKI_URL/metrics" | grep -E "^loki_ingester_wal_(bytes_in_use|disk_full_failures_total)" 2>/dev/null || echo "No WAL metrics"

echo ""
echo "--- Chunks ---"
curl -s "$LOKI_URL/metrics" | grep -E "^loki_ingester_(chunks_created_total|chunks_flush_failures_total|flush_queue_length)" 2>/dev/null || echo "No chunk metrics"

echo ""
echo "--- Compactor ---"
curl -s "$LOKI_URL/metrics" | grep -E "^loki_boltdb_shipper_compactor_running" 2>/dev/null || echo "Compactor not running"

echo ""
echo "--- Errors ---"
curl -s "$LOKI_URL/metrics" | grep -E "^loki_(discarded_samples_total|internal_log_messages_total.*error)" 2>/dev/null || echo "No errors"

echo ""
echo "--- Ready Status ---"
curl -s "$LOKI_URL/ready" 2>/dev/null || echo "Loki not ready"
```

### Grafana Dashboards

For visual monitoring, import these community dashboards:

- **Fluent Bit**: Dashboard ID `7752` (Fluent Bit Monitoring)
- **Loki**: Dashboard ID `13407` (Loki & Promtail) or `14055` (Loki Operational)
