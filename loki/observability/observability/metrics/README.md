# Metrics Collection Directory

This directory contains collected metrics from the Loki monolithic stack for analysis and dashboard creation.

## Files Structure

```
metrics/
├── README.md                           # This file
├── loki-3.5.x-monolithic-metrics      # Loki metrics snapshot
├── fluent-bit-v2-metrics              # Fluent Bit v2 API metrics
├── fluent-bit-v1-metrics              # Fluent Bit v1 API metrics (if different)
└── prometheus-self-metrics             # Prometheus own metrics
```

## Collection Commands

### Loki Metrics
```bash
curl -s http://localhost:3100/metrics > loki-3.5.x-monolithic-metrics
```

### Fluent Bit Metrics
```bash
# v2 API (recommended)
curl -s http://localhost:2020/api/v2/metrics/prometheus > fluent-bit-v2-metrics

# v1 API (for comparison)
curl -s http://localhost:2020/api/v1/metrics/prometheus > fluent-bit-v1-metrics
```

### Prometheus Self-Metrics
```bash
curl -s http://localhost:9090/metrics > prometheus-self-metrics
```

## Usage

These metrics files are used for:

1. **Dashboard Development**: Analyze available metrics before creating Grafana dashboards
2. **Alert Rule Creation**: Identify key metrics for alerting thresholds
3. **Performance Analysis**: Understand metric patterns and relationships
4. **Documentation**: Reference for PromQL query development

## Analysis Guides

- **Loki Metrics**: See `../dashboards/loki-metrics-guide.md`
- **Fluent Bit Metrics**: See `../dashboards/fluent-bit-metrics-guide.md`

## Automation

To collect all metrics automatically:

```bash
#!/bin/bash
# collect-all-metrics.sh

METRICS_DIR="/Users/snikam/Documents/git/sagarnikam123-blog-youtube-code-samples/loki/monolithic/observability/prometheus/metrics"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# Collect Loki metrics
curl -s http://localhost:3100/metrics > "$METRICS_DIR/loki-metrics-$TIMESTAMP"

# Collect Fluent Bit metrics
curl -s http://localhost:2020/api/v2/metrics/prometheus > "$METRICS_DIR/fluent-bit-v2-metrics-$TIMESTAMP"

# Collect Prometheus metrics
curl -s http://localhost:9090/metrics > "$METRICS_DIR/prometheus-metrics-$TIMESTAMP"

echo "Metrics collected with timestamp: $TIMESTAMP"
```

## Key Metrics Summary

### From Loki (`loki-3.5.x-monolithic-metrics`):
- **Build Info**: `loki_build_info` - Version and build details
- **Ingestion**: `loki_bytes_per_line_*` - Log processing metrics
- **Storage**: `loki_chunk_store_*` - Chunk and index performance
- **Cache**: `loki_cache_*` - Cache hit rates and efficiency
- **Compactor**: `loki_boltdb_shipper_*` - Maintenance operations
- **Rings**: `ring_member_*` - Ring membership and health

### From Fluent Bit (`fluent-bit-v2-metrics`):
- **System**: `fluentbit_uptime`, `fluentbit_build_info`
- **Input**: `fluentbit_input_*` - Log collection metrics
- **Output**: `fluentbit_output_*` - Log forwarding metrics
- **Storage**: `fluentbit_storage_*` - Buffer and memory usage
- **Latency**: `fluentbit_output_latency_seconds_*` - Performance metrics

## Refresh Schedule

Metrics should be refreshed:
- **During development**: After each configuration change
- **For monitoring**: Daily or weekly snapshots
- **For troubleshooting**: Real-time collection during issues

## Notes

- Metrics reflect the state at collection time
- Some metrics are cumulative counters, others are instantaneous gauges
- Use `rate()` function in PromQL for counter metrics
- Histogram metrics provide percentile calculations
