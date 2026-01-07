# Loki Stress Tests

Find Loki's **breaking point** and failure modes.

## Goal
Discover system limits, degradation patterns, and recovery behavior.

## Test Scenarios

### 1. High Cardinality
- Push logs with extreme label combinations
- Test: High unique label values (e.g., user_id, request_id)
- Goal: Find stream limits per tenant

### 2. Burst Traffic
- Sudden traffic spikes (10x-100x normal)
- Test: Ingester buffer overflow
- Goal: Validate rate limiting and backpressure

### 3. Component Failure
- Kill pods during load
- Test: Ingester/Distributor failures
- Goal: Verify HA and recovery

### 4. Resource Exhaustion
- Push until OOM/CPU throttling
- Test: Memory/CPU limits
- Goal: Find resource bottlenecks

### 5. Large Logs
- Push logs near max_line_size (256KB default)
- Test: Large log line handling
- Goal: Validate truncation behavior

## Tools

| Tool | Purpose | Use Case |
|------|---------|----------|
| **flog** | Log generation | High-volume synthetic logs |
| **curl** | Direct push | Controlled stress testing |
| **logcli** | Query stress | Read path testing |
| **bash scripts** | Automation | Cardinality/burst tests |

## Failure Indicators

- ❌ Pod OOMKilled
- ❌ Rate limit errors (429)
- ❌ Query timeouts
- ❌ Ring instability
- ❌ WAL corruption
- ❌ Chunk flush failures

## Key Limits to Test

| Limit | Default | Config |
|-------|---------|--------|
| Max streams per user | 5000 | `max_global_streams_per_user` |
| Max line size | 256KB | `max_line_size` |
| Ingestion rate | 4MB/s | `ingestion_rate_mb` |
| Ingestion burst | 6MB | `ingestion_burst_size_mb` |
| Max entries per query | 5000 | `max_entries_limit_per_query` |
| Query timeout | 1m | `query_timeout` |

## Quick Start

```bash
# Run cardinality stress test
cd high-cardinality
./cardinality-bomb.sh

# Run burst traffic test
cd burst-traffic
./burst-test.sh

# Run large log test
cd large-logs
./large-line-test.sh

# Monitor for failures
watch -n1 'curl -s http://localhost:3100/metrics | grep -E "(error|dropped|rejected)"'
```

## Monitoring During Stress

```bash
# Watch for rate limiting
curl -s http://localhost:3100/metrics | grep loki_discarded_samples_total

# Watch memory usage
curl -s http://localhost:3100/metrics | grep loki_ingester_memory

# Watch WAL status
curl -s http://localhost:3100/metrics | grep loki_ingester_wal

# Check ring health
curl http://localhost:3100/ring
```
