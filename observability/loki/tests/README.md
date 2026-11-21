# Loki Performance Testing

Comprehensive testing suite for Loki - both **load testing** (expected capacity) and **stress testing** (breaking points).

## Structure

```
tests/
├── load-tests/          # Normal capacity validation
│   ├── fluent-bit/
│   ├── promtail/
│   ├── grafana-alloy/
│   ├── flog/
│   ├── logcli/
│   └── curl/
│
└── stress-tests/        # Breaking point discovery
    ├── high-cardinality/
    ├── burst-traffic/
    ├── component-failure/
    ├── resource-exhaustion/
    └── large-logs/
```

## Testing Types

### Load Tests (Expected Capacity)
**Goal**: Verify system handles normal and peak log ingestion with acceptable performance.

**Scenarios**:
- Steady-state ingestion (1K-10K lines/sec)
- Multi-tenant workloads
- Query performance validation
- Mixed read/write operations

**Success Criteria**:
- ✅ Push latency < 500ms (p99)
- ✅ Query latency < 5s (p99)
- ✅ Error rate < 0.1%
- ✅ No pod restarts
- ✅ No log drops

### Stress Tests (Breaking Points)
**Goal**: Find system limits, degradation patterns, and recovery behavior.

**Scenarios**:
- Label cardinality explosion (high unique label values)
- Traffic bursts (10x-100x normal)
- Component failures (pod kills)
- Resource exhaustion (OOM, CPU)
- Large log lines (near max_line_size)

**Failure Indicators**:
- ❌ Pod OOMKilled
- ❌ Logs dropped (rate limited)
- ❌ Query timeouts
- ❌ Ring instability
- ❌ WAL corruption

## Testing Tools

| Tool | Load Testing | Stress Testing | Purpose |
|------|--------------|----------------|---------|
| **Fluent Bit** | ✅ | ✅ | Log collection & forwarding |
| **Promtail** | ✅ | ✅ | Native Loki log shipper |
| **Grafana Alloy** | ✅ | ✅ | Multi-tenant log ingestion |
| **flog** | ✅ | ✅ | Fake log generator |
| **logcli** | ✅ | ✅ | Query testing & validation |
| **curl** | ✅ | ✅ | Direct push API testing |

## Quick Start

### Load Testing

```bash
# Fluent Bit log forwarding
cd load-tests/fluent-bit
fluent-bit -c fluent-bit-loki.yaml

# Promtail log collection
cd load-tests/promtail
promtail -config.file=promtail-config.yaml

# flog log generator
cd load-tests/flog
docker run -d --name flog mingrammer/flog -f json -l -d 100ms

# Query testing with logcli
cd load-tests/logcli
./test-queries.sh

# Direct push with curl
cd load-tests/curl
./push-logs.sh
```

### Stress Testing

```bash
# High cardinality test
cd stress-tests/high-cardinality
./cardinality-bomb.sh

# Burst traffic test
cd stress-tests/burst-traffic
./burst-test.sh

# Large log lines
cd stress-tests/large-logs
./large-line-test.sh
```

## Monitoring During Tests

```bash
# Watch Loki metrics
curl http://localhost:3100/metrics | grep -E "loki_(ingester|distributor|querier)"

# Check ring status
curl http://localhost:3100/ring

# Check ready status
curl http://localhost:3100/ready

# Query logs
logcli query '{job="test"}' --limit=10

# Check ingestion rate
curl -s http://localhost:3100/metrics | grep loki_distributor_lines_received_total
```

## Test Workflow

1. **Baseline**: Run load tests to establish normal performance
2. **Stress**: Gradually increase load to find breaking points
3. **Failure**: Test component failures and recovery
4. **Analysis**: Review metrics, logs, and resource usage
5. **Optimize**: Adjust configuration based on findings

## Tool Selection Guide

### For Write Path Testing
- **Fluent Bit** - High-performance log forwarding
- **Promtail** - Native Loki integration
- **Grafana Alloy** - Multi-tenant scenarios
- **flog** - Fake log generation

### For Read Path Testing
- **logcli** - Query validation and performance
- **curl** - Direct API testing

### For Resilience Testing
- **Component Failure** - Manual failure injection
- **Resource Exhaustion** - OOM, CPU stress

## Key Metrics to Monitor

### Ingestion
- `loki_distributor_lines_received_total` - Lines received
- `loki_distributor_bytes_received_total` - Bytes received
- `loki_ingester_chunks_created_total` - Chunks created
- `loki_ingester_wal_records_logged_total` - WAL writes

### Query
- `loki_request_duration_seconds` - Request latency
- `loki_querier_tail_active` - Active tail connections

### Health
- `loki_ingester_memory_chunks` - In-memory chunks
- `loki_compactor_running` - Compactor status
