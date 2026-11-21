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

---

## Running Loki

### Running Loki as a Systemd Service (Recommended for Production)

Create the service file `/etc/systemd/system/loki.service`:

```ini
[Unit]
Description=Loki Service
After=network.target

[Service]
LimitNPROC=1024000
LimitNOFILE=1024000
Type=simple
ExecStart=/opt/loki/loki-linux-arm64 -config.file=/opt/loki/config/loki-config.yml -config.expand-env=true
WorkingDirectory=/opt/loki
ExecStartPre=/bin/mkdir -p /var/log/loki
StandardOutput=file:/var/log/loki/loki.log
StandardError=file:/var/log/loki/error.log
Restart=on-failure
RestartSec=5s

[Install]
WantedBy=multi-user.target
```

**Note:** Use `file:` instead of `append:` for older systemd versions. `append:` preserves logs across restarts but requires systemd 240+.

#### Systemd Commands

```bash
# Reload systemd after creating/editing service file
sudo systemctl daemon-reload

# Enable service to start on boot
sudo systemctl enable loki

# Start the service
sudo systemctl start loki

# Check service status
sudo systemctl status loki

# View logs
tail -f /var/log/loki/loki.log
tail -f /var/log/loki/error.log

# Or use journalctl
sudo journalctl -u loki -f

# Stop the service
sudo systemctl stop loki

# Restart the service
sudo systemctl restart loki
```

#### Log Rotation for Systemd Logs

Create `/etc/logrotate.d/loki`:

```
/var/log/loki/*.log {
    daily
    rotate 7
    compress
    delaycompress
    missingok
    notifempty
    copytruncate
}
```

### Running Loki in Background (Using nohup)

For quick testing or when systemd is not available:

```bash
# Start Loki in background with logs to file
nohup ./loki-linux-arm64 -config.file=config/loki-config.yml -config.expand-env=true > loki.log 2>&1 &

# Save PID for later management
echo $! > loki.pid

# View logs
tail -f loki.log

# Stop Loki using saved PID
kill $(cat loki.pid)

# Or find and kill by process name
pkill -f loki-linux-arm64

# Force kill if needed
pkill -9 -f loki-linux-arm64
```

#### One-liner with PID file

```bash
nohup ./loki-linux-arm64 -config.file=config/loki-config.yml -config.expand-env=true > loki.log 2>&1 & echo $! > loki.pid
```

#### Check if Loki is Running

```bash
# Using PID file
ps -p $(cat loki.pid)

# Using process name
ps aux | grep loki-linux-arm64

# Using pgrep
pgrep -f loki-linux-arm64
```

### Running Loki with Screen/Tmux

For interactive sessions where you want to attach/detach:

```bash
# Using screen
screen -dmS loki ./loki-linux-arm64 -config.file=config/loki-config.yml -config.expand-env=true

# Attach to session
screen -r loki

# Detach: Ctrl+A, then D

# Using tmux
tmux new-session -d -s loki './loki-linux-arm64 -config.file=config/loki-config.yml -config.expand-env=true'

# Attach to session
tmux attach -t loki

# Detach: Ctrl+B, then D
```

### Environment Variables in Config

The `-config.expand-env=true` flag enables environment variable expansion in the config file:

```yaml
# In config file
storage_config:
  object_store:
    s3:
      access_key_id: ${AWS_ACCESS_KEY_ID}
      secret_access_key: ${AWS_SECRET_ACCESS_KEY}
```

Set environment variables before starting:

```bash
export AWS_ACCESS_KEY_ID="your-access-key"
export AWS_SECRET_ACCESS_KEY="your-secret-key"
./loki-linux-arm64 -config.file=config/loki-config.yml -config.expand-env=true
```

For systemd, add to service file:

```ini
[Service]
Environment="AWS_ACCESS_KEY_ID=your-access-key"
Environment="AWS_SECRET_ACCESS_KEY=your-secret-key"
# Or use EnvironmentFile
EnvironmentFile=/opt/loki/config/loki.env
```

---

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

---

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

---

## Configuration

### Out-of-Order Writes & Timestamp Configuration

#### "entry too far behind" error

```
entry with timestamp 2026-01-07 19:43:30 ignored, reason: 'entry too far behind,
entry timestamp is: 2026-01-07T19:43:30Z, oldest acceptable timestamp is: 2026-01-07T19:43:51Z'
```

This error occurs when Loki receives log entries with timestamps that are older than what it expects for a given stream.

#### How Out-of-Order Ingestion Works

Loki's rule for out-of-order log ingestion:

> **Any logs received within `max_chunk_age/2` (default: 1 hour) of the most recent log received *for a stream* will be accepted. Any log older than this window will be rejected.**

Two critical concepts:
1. **Most recent log** - The log with the most recent timestamp received by Loki
2. **For a stream** - Loki determines the most recent log on a **stream-by-stream basis**, so different streams can have different acceptance windows

**Example:**
- Stream A's latest log: 10:00 → accepts logs from 09:00 onwards
- Stream B's latest log: 09:30 → accepts logs from 08:30 onwards
- Same log at 08:45 would be accepted by Stream B but rejected by Stream A

#### Key Configuration Settings

| Setting | Location | Default | Description |
|---------|----------|---------|-------------|
| `reject_old_samples` | `limits_config` | `true` | Whether to reject samples older than `reject_old_samples_max_age` |
| `reject_old_samples_max_age` | `limits_config` | `1w` | Maximum age of samples to accept (e.g., `168h`, `1w`) |
| `max_chunk_age` | `ingester` | `2h` | Maximum chunk duration; **out-of-order window = max_chunk_age/2** |
| `query_ingesters_within` | `querier` | `3h` | Time window to query ingesters (affects old data queryability) |

#### Out-of-Order Window Calculation

```
out_of_order_window = max_chunk_age / 2
```

With default `max_chunk_age: 2h`:
- Out-of-order window = 1 hour
- Logs up to 1 hour behind the stream's latest timestamp are accepted

**⚠️ Warning:** Grafana Labs strongly discourages increasing `max_chunk_age` to create a larger out-of-order window. Instead, use labels to separate streams so they can be ingested independently.

#### Querying Caveats for Older Data

**Important:** If you ingest data older than 2 hours from current time, it will NOT be immediately queryable!

This is because of `query_ingesters_within` (default: 3h). Loki only queries ingesters for data within this window from current time. Data outside this window is only queried from storage.

**The problem:** If you send logs from yesterday, they sit in the ingester until flushed (up to 2 hours). During this time, queries won't find them because:
- Queries for yesterday don't ask ingesters (outside `query_ingesters_within`)
- Data hasn't been flushed to storage yet

**Solutions:**
1. **Wait for flush** - For backfill operations, wait ~2 hours for data to flush to storage
2. **Increase `query_ingesters_within`** - Set to 48h to query ingesters for older data (NOT recommended - increases ingester load and cost)

#### Configuration Examples

**Allow all old samples (development/testing)**
```yaml
limits_config:
  reject_old_samples: false  # accept all samples regardless of age
```

**Production settings (recommended by Grafana Labs)**
```yaml
limits_config:
  reject_old_samples: true
  reject_old_samples_max_age: 1w  # reject samples older than 1 week

ingester:
  max_chunk_age: 2h  # out-of-order window of 1 hour (max_chunk_age/2)

querier:
  query_ingesters_within: 3h  # default, don't increase unless necessary
```

**Backfill old data (e.g., importing historical logs)**
```yaml
limits_config:
  reject_old_samples: false  # or set reject_old_samples_max_age to cover your data range

# After backfill completes, wait 2 hours for flush, then data is queryable
```

#### Common Causes of "entry too far behind"

1. **Clock skew** - Log source and Loki have different system times
2. **Delayed log shipping** - Fluent Bit/Promtail buffering or network delays
3. **Batch processing** - Processing old log files with historical timestamps
4. **Incorrect timestamp parsing** - Parser extracting wrong timestamp from logs
5. **Stream-specific timing** - Different streams have different "most recent" timestamps

#### Related Settings

| Setting | Location | Default | Description |
|---------|----------|---------|-------------|
| `increment_duplicate_timestamp` | `limits_config` | `false` | Add 1ns to duplicate timestamps to preserve order |
| `max_line_size` | `limits_config` | `256KB` | Maximum log line size before rejection/truncation |
| `max_line_size_truncate` | `limits_config` | `false` | Truncate instead of reject oversized lines |

#### Reference

Content adapted from [The concise guide to Loki: How to work with out-of-order and older logs](https://grafana.com/blog/the-concise-guide-to-loki-how-to-work-with-out-of-order-and-older-logs/) by Grafana Labs.

---

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

---

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

# Prometheus format
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

### Quick Health Check Commands

```bash
# Fluent Bit: Records read vs sent
curl -s http://127.0.0.1:2020/api/v1/metrics | jq '{
  input_records: [.input[].records] | add,
  output_records: [.output[].proc_records] | add,
  output_errors: [.output[].errors] | add
}'

# Loki: Lines ingested
curl -s http://127.0.0.1:3100/metrics | grep -E "^loki_distributor_lines_received_total"

# Loki: Ready status
curl -s http://127.0.0.1:3100/ready
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

### How many failed logs in Fluent Bit?

```bash
# Total errors across all outputs
curl -s http://127.0.0.1:2020/api/v1/metrics | jq '[.output[].errors] | add'

# Detailed error breakdown per output
curl -s http://127.0.0.1:2020/api/v1/metrics | jq '.output | to_entries[] | {name: .key, errors: .value.errors, retries: .value.retries, retries_failed: .value.retries_failed, dropped: .value.dropped_records}'
```

### What errors are in Fluent Bit or Loki?

#### Fluent Bit Error Detection

```bash
curl -s http://127.0.0.1:2020/api/v1/metrics | jq '{
  total_errors: [.output[].errors] | add,
  total_retries_failed: [.output[].retries_failed] | add,
  total_dropped: [.output[].dropped_records] | add,
  outputs_with_errors: [.output | to_entries[] | select(.value.errors > 0) | .key]
}'
```

#### Loki Error Detection

```bash
# Discarded/rejected samples
curl -s http://127.0.0.1:3100/metrics | grep loki_discarded_samples_total

# Request errors by route
curl -s http://127.0.0.1:3100/metrics | grep -E "loki_request_duration_seconds_count.*status_code=\"[45]"

# Ingester errors
curl -s http://127.0.0.1:3100/metrics | grep -E "loki_ingester.*(error|failed)"

# WAL errors
curl -s http://127.0.0.1:3100/metrics | grep -E "loki_ingester_wal.*(error|failed|corrupt)"
```

#### Common Error Reasons in `loki_discarded_samples_total`

| Reason | Description |
|--------|-------------|
| `rate_limited` | Ingestion rate limit exceeded |
| `line_too_long` | Log line exceeds max_line_size |
| `stream_limit` | Too many streams per tenant |
| `per_stream_rate_limit` | Per-stream rate limit exceeded |
| `invalid_labels` | Malformed or invalid labels |

### Quick Operational Status Commands

#### All-in-One Health Check Script

```bash
#!/bin/bash
LOKI_URL="${1:-http://127.0.0.1:3100}"

echo "=== Loki Health Check ==="

echo "--- Ready Status ---"
curl -s "$LOKI_URL/ready"
echo ""

echo "--- Ingestion ---"
curl -s "$LOKI_URL/metrics" | grep -E "^loki_distributor_(lines_received_total|bytes_received_total|ingester_clients)"

echo "--- Memory & Chunks ---"
curl -s "$LOKI_URL/metrics" | grep -E "^loki_ingester_(memory_chunks|chunks_created_total|chunks_flushed_total|flush_queue_length)"

echo "--- WAL ---"
curl -s "$LOKI_URL/metrics" | grep -E "^loki_ingester_wal_(bytes_in_use|disk_full_failures_total)"

echo "--- Compactor ---"
curl -s "$LOKI_URL/metrics" | grep -E "^loki_boltdb_shipper_compactor_running"

echo "--- Errors ---"
curl -s "$LOKI_URL/metrics" | grep -E "^loki_discarded_samples_total"
```

#### Individual Status Commands

```bash
# Distributor - log ingestion
curl -s http://127.0.0.1:3100/metrics | grep loki_distributor_lines_received_total
curl -s http://127.0.0.1:3100/metrics | grep loki_distributor_ingester_clients

# Ingester ring (HTML page)
curl -s http://127.0.0.1:3100/ring

# Chunks in memory
curl -s http://127.0.0.1:3100/metrics | grep loki_ingester_memory_chunks

# WAL status
curl -s http://127.0.0.1:3100/metrics | grep loki_ingester_wal_bytes_in_use

# Chunks flushed to storage
curl -s http://127.0.0.1:3100/metrics | grep loki_ingester_chunks_flushed_total

# Compactor ring (HTML page)
curl -s http://127.0.0.1:3100/compactor/ring

# Scheduler ring (if use_scheduler_ring: true)
curl -s http://127.0.0.1:3100/scheduler/ring

# Index gateway ring (if mode: ring)
curl -s http://127.0.0.1:3100/indexgateway/ring
```

#### Key Metrics Reference

| Category | Metric | Description | Alert If |
|----------|--------|-------------|----------|
| **Ingestion** | `loki_distributor_lines_received_total` | Log lines received | Rate drops |
| **Ingestion** | `loki_distributor_ingester_clients` | Connected ingesters | = 0 |
| **Memory** | `loki_ingester_memory_chunks` | In-memory chunks | Too high |
| **WAL** | `loki_ingester_wal_bytes_in_use` | WAL disk usage | Growing fast |
| **WAL** | `loki_ingester_wal_disk_full_failures_total` | Disk full errors | > 0 |
| **Chunks** | `loki_ingester_chunks_flushed_total` | Chunks to storage | Not increasing |
| **Chunks** | `loki_ingester_chunks_flush_failures_total` | Flush failures | > 0 |
| **Compactor** | `loki_boltdb_shipper_compactor_running` | Compactor status | = 0 |
| **Errors** | `loki_discarded_samples_total` | Rejected logs | > 0 |
| **Cache** | `loki_cache_hits` / `loki_cache_fetched_keys` | Hit ratio | Low ratio |

#### Understanding Chunk Flush Timing

Chunks are flushed to storage when:

| Condition | Config Setting | Default |
|-----------|----------------|---------|
| Stream idle | `chunk_idle_period` | 30m |
| Chunk age reached | `max_chunk_age` | 2h |
| Chunk size reached | `chunk_target_size` | 1.5MB |
| Graceful shutdown | N/A | Always |

If `loki_ingester_chunks_flushed_total` is 0:
- Streams are still active (receiving logs within idle period)
- Chunks haven't reached target size
- max_chunk_age hasn't been reached yet

To force flush for testing:
```bash
# Option 1: Stop log source and wait for chunk_idle_period
# Option 2: Graceful shutdown (flushes WAL)
kill -SIGTERM <loki_pid>
```

### Grafana Dashboards

For visual monitoring, import these community dashboards:

- **Fluent Bit**: Dashboard ID `7752` (Fluent Bit Monitoring)
- **Loki**: Dashboard ID `13407` (Loki & Promtail) or `14055` (Loki Operational)

---

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
curl http://127.0.0.1:3100/ready   # Ready check
curl http://127.0.0.1:3100/config  # View config
```

See "Quick Operational Status Commands" section for detailed health checks.

### View Loki logs

```bash
# Binary install with systemd
tail -f /var/log/loki/loki.log
sudo journalctl -u loki -f

# Binary install with nohup
tail -f loki.log

# Kubernetes
kubectl logs -n loki -l app.kubernetes.io/name=loki -f
```

### Troubleshooting Out-of-Order Writes

```bash
# 1. Check system time on log source vs Loki
date

# 2. Verify timestamp in log file matches expected format
tail -1 /path/to/logfile.log

# 3. Check Loki's current config
curl -s http://127.0.0.1:3100/config | grep -A5 "limits_config"

# 4. Check discarded samples metric
curl -s http://127.0.0.1:3100/metrics | grep loki_discarded_samples_total
```

### Quick Error Summary Script

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

---

## Installation Notes

### Helm Installation

#### Memberlist warnings during startup

```
msg="joining memberlist cluster" err="no such host"
```

These warnings are normal during startup. They resolve once the pod is fully up and the memberlist service is available.

#### MinIO endpoint configuration

For Helm deployments with bundled MinIO:
```yaml
# values-minio.yaml
loki:
  storage:
    s3:
      endpoint: http://loki-minio.loki.svc:9000
```

Note: The endpoint format is `loki-minio.<namespace>.svc`

### Binary Installation

See "Running Loki" section for systemd service setup and nohup commands.

Download binaries from: https://github.com/grafana/loki/releases
