# Prometheus Metrics Reference

This document provides a reference for key Prometheus metrics used by the testing framework for monitoring, validation, and performance analysis.

## Overview

The testing framework collects and analyzes Prometheus internal metrics to:
- Validate deployment health
- Measure performance characteristics
- Identify breaking points
- Monitor resource utilization

## Prometheus Internal Metrics

### TSDB Metrics

Metrics related to the Time Series Database (TSDB).

| Metric | Type | Description |
|--------|------|-------------|
| `prometheus_tsdb_head_series` | Gauge | Current number of active series in the head block |
| `prometheus_tsdb_head_samples_appended_total` | Counter | Total samples appended to the head block |
| `prometheus_tsdb_head_chunks` | Gauge | Total number of chunks in the head block |
| `prometheus_tsdb_head_chunks_created_total` | Counter | Total chunks created in the head block |
| `prometheus_tsdb_head_chunks_removed_total` | Counter | Total chunks removed from the head block |
| `prometheus_tsdb_head_gc_duration_seconds` | Summary | Runtime of garbage collection in the head block |
| `prometheus_tsdb_head_min_time` | Gauge | Minimum timestamp in the head block |
| `prometheus_tsdb_head_max_time` | Gauge | Maximum timestamp in the head block |
| `prometheus_tsdb_blocks_loaded` | Gauge | Number of currently loaded data blocks |
| `prometheus_tsdb_compaction_duration_seconds` | Histogram | Duration of compaction runs |
| `prometheus_tsdb_compactions_total` | Counter | Total number of compactions |
| `prometheus_tsdb_compactions_failed_total` | Counter | Total number of failed compactions |
| `prometheus_tsdb_wal_fsync_duration_seconds` | Summary | Duration of WAL fsync operations |
| `prometheus_tsdb_wal_page_flushes_total` | Counter | Total number of WAL page flushes |
| `prometheus_tsdb_wal_truncate_duration_seconds` | Summary | Duration of WAL truncation |
| `prometheus_tsdb_checkpoint_creations_total` | Counter | Total number of checkpoint creations |
| `prometheus_tsdb_checkpoint_deletions_total` | Counter | Total number of checkpoint deletions |

### Query Engine Metrics

Metrics related to PromQL query execution.

| Metric | Type | Description |
|--------|------|-------------|
| `prometheus_engine_query_duration_seconds` | Summary | Query execution duration by slice |
| `prometheus_engine_queries` | Counter | Total queries executed |
| `prometheus_engine_queries_concurrent_max` | Gauge | Maximum concurrent queries |
| `prometheus_engine_query_samples_total` | Counter | Total samples loaded by queries |
| `prometheus_engine_query_log_enabled` | Gauge | Whether query logging is enabled |
| `prometheus_engine_query_log_failures_total` | Counter | Total query log failures |

### Scraping Metrics

Metrics related to target scraping.

| Metric | Type | Description |
|--------|------|-------------|
| `prometheus_target_scrapes_exceeded_sample_limit_total` | Counter | Scrapes exceeding sample limit |
| `prometheus_target_scrapes_sample_duplicate_timestamp_total` | Counter | Samples with duplicate timestamps |
| `prometheus_target_scrapes_sample_out_of_bounds_total` | Counter | Samples out of accepted time bounds |
| `prometheus_target_scrapes_sample_out_of_order_total` | Counter | Out-of-order samples |
| `prometheus_target_scrape_pool_targets` | Gauge | Current targets in scrape pool |
| `prometheus_target_scrape_pool_sync_total` | Counter | Total scrape pool syncs |
| `prometheus_target_scrape_pools_total` | Counter | Total scrape pools created |
| `prometheus_target_scrape_pools_failed_total` | Counter | Total failed scrape pool creations |
| `prometheus_sd_discovered_targets` | Gauge | Discovered targets by scrape config |
| `prometheus_sd_received_updates_total` | Counter | Service discovery updates received |
| `prometheus_sd_updates_total` | Counter | Service discovery updates processed |

### HTTP API Metrics

Metrics related to the HTTP API.

| Metric | Type | Description |
|--------|------|-------------|
| `prometheus_http_requests_total` | Counter | Total HTTP requests by handler and code |
| `prometheus_http_request_duration_seconds` | Histogram | HTTP request duration |
| `prometheus_http_response_size_bytes` | Histogram | HTTP response size |

### Remote Write/Read Metrics

Metrics for remote storage operations.

| Metric | Type | Description |
|--------|------|-------------|
| `prometheus_remote_storage_samples_total` | Counter | Total samples sent to remote storage |
| `prometheus_remote_storage_samples_pending` | Gauge | Samples pending in remote storage queue |
| `prometheus_remote_storage_samples_failed_total` | Counter | Failed remote storage samples |
| `prometheus_remote_storage_samples_retried_total` | Counter | Retried remote storage samples |
| `prometheus_remote_storage_samples_dropped_total` | Counter | Dropped remote storage samples |
| `prometheus_remote_storage_sent_batch_duration_seconds` | Histogram | Duration of remote write batches |
| `prometheus_remote_storage_queue_highest_sent_timestamp_seconds` | Gauge | Highest timestamp sent to remote storage |
| `prometheus_remote_storage_shards` | Gauge | Number of remote storage shards |
| `prometheus_remote_storage_shards_min` | Gauge | Minimum remote storage shards |
| `prometheus_remote_storage_shards_max` | Gauge | Maximum remote storage shards |
| `prometheus_remote_storage_shards_desired` | Gauge | Desired remote storage shards |

### Alerting Metrics

Metrics related to alerting.

| Metric | Type | Description |
|--------|------|-------------|
| `prometheus_rule_evaluations_total` | Counter | Total rule evaluations |
| `prometheus_rule_evaluation_failures_total` | Counter | Failed rule evaluations |
| `prometheus_rule_evaluation_duration_seconds` | Summary | Rule evaluation duration |
| `prometheus_rule_group_duration_seconds` | Summary | Rule group evaluation duration |
| `prometheus_rule_group_iterations_total` | Counter | Total rule group iterations |
| `prometheus_rule_group_iterations_missed_total` | Counter | Missed rule group iterations |
| `prometheus_rule_group_last_duration_seconds` | Gauge | Last rule group evaluation duration |
| `prometheus_rule_group_last_evaluation_timestamp_seconds` | Gauge | Last rule group evaluation timestamp |
| `prometheus_rule_group_rules` | Gauge | Number of rules in a group |
| `prometheus_notifications_total` | Counter | Total notifications sent |
| `prometheus_notifications_failed_total` | Counter | Failed notifications |
| `prometheus_notifications_queue_length` | Gauge | Notification queue length |
| `prometheus_notifications_queue_capacity` | Gauge | Notification queue capacity |
| `prometheus_notifications_dropped_total` | Counter | Dropped notifications |

### Process Metrics

Standard Go process metrics.

| Metric | Type | Description |
|--------|------|-------------|
| `process_cpu_seconds_total` | Counter | Total CPU time spent |
| `process_resident_memory_bytes` | Gauge | Resident memory size |
| `process_virtual_memory_bytes` | Gauge | Virtual memory size |
| `process_open_fds` | Gauge | Number of open file descriptors |
| `process_max_fds` | Gauge | Maximum file descriptors |
| `process_start_time_seconds` | Gauge | Process start time |

### Go Runtime Metrics

Go runtime metrics.

| Metric | Type | Description |
|--------|------|-------------|
| `go_goroutines` | Gauge | Number of goroutines |
| `go_threads` | Gauge | Number of OS threads |
| `go_gc_duration_seconds` | Summary | GC pause duration |
| `go_memstats_alloc_bytes` | Gauge | Bytes allocated and in use |
| `go_memstats_alloc_bytes_total` | Counter | Total bytes allocated |
| `go_memstats_heap_alloc_bytes` | Gauge | Heap bytes allocated |
| `go_memstats_heap_inuse_bytes` | Gauge | Heap bytes in use |
| `go_memstats_heap_objects` | Gauge | Number of heap objects |
| `go_memstats_stack_inuse_bytes` | Gauge | Stack bytes in use |

---

## Test Framework Metrics

Metrics collected by the testing framework during test execution.

### Performance Metrics

| Metric | Description | Unit |
|--------|-------------|------|
| `query_latency_p50` | 50th percentile query latency | milliseconds |
| `query_latency_p90` | 90th percentile query latency | milliseconds |
| `query_latency_p99` | 99th percentile query latency | milliseconds |
| `scrape_success_rate` | Percentage of successful scrapes | percent |
| `scrape_duration_avg` | Average scrape duration | seconds |

### Resource Metrics

| Metric | Description | Unit |
|--------|-------------|------|
| `cpu_utilization_avg` | Average CPU utilization | percent |
| `cpu_utilization_max` | Maximum CPU utilization | percent |
| `memory_utilization_avg` | Average memory utilization | percent |
| `memory_utilization_max` | Maximum memory utilization | percent |
| `disk_io_read_bytes` | Disk read bytes | bytes |
| `disk_io_write_bytes` | Disk write bytes | bytes |

### k6 Load Test Metrics

Metrics from k6 load tests.

| Metric | Description | Unit |
|--------|-------------|------|
| `http_req_duration` | HTTP request duration | milliseconds |
| `http_req_blocked` | Time blocked before request | milliseconds |
| `http_req_connecting` | Time establishing connection | milliseconds |
| `http_req_tls_handshaking` | TLS handshake time | milliseconds |
| `http_req_sending` | Time sending request | milliseconds |
| `http_req_waiting` | Time waiting for response | milliseconds |
| `http_req_receiving` | Time receiving response | milliseconds |
| `http_req_failed` | Failed request rate | percent |
| `http_reqs` | Total HTTP requests | count |
| `iterations` | Total test iterations | count |
| `vus` | Current virtual users | count |
| `vus_max` | Maximum virtual users | count |

---

## Key Metrics for Testing

### Sanity Tests

Essential metrics for basic validation:

```promql
# Check if Prometheus is up
up{job="prometheus"} == 1

# Verify self-scraping
prometheus_target_scrape_pool_targets{scrape_job="prometheus"}

# Check TSDB health
prometheus_tsdb_head_series > 0
```

### Load Tests

Metrics to monitor during load testing:

```promql
# Query performance
rate(prometheus_engine_query_duration_seconds_sum[5m]) /
rate(prometheus_engine_query_duration_seconds_count[5m])

# Scrape performance
rate(prometheus_target_scrapes_exceeded_sample_limit_total[5m])

# Memory usage
process_resident_memory_bytes / 1024 / 1024  # MB

# Active series growth
rate(prometheus_tsdb_head_series[5m])
```

### Stress Tests

Metrics for identifying breaking points:

```promql
# Sample ingestion rate
rate(prometheus_tsdb_head_samples_appended_total[1m])

# Query queue depth
prometheus_engine_queries_concurrent_max

# WAL performance
rate(prometheus_tsdb_wal_fsync_duration_seconds_sum[5m])

# Compaction health
rate(prometheus_tsdb_compactions_failed_total[5m])
```

### Reliability Tests

Metrics for recovery validation:

```promql
# WAL replay progress
prometheus_tsdb_head_min_time

# Checkpoint status
prometheus_tsdb_checkpoint_creations_total

# Target rediscovery
prometheus_sd_discovered_targets
```

---

## Thresholds

Default thresholds used by the testing framework (configurable in `thresholds.yaml`):

| Metric | Threshold | Test Type |
|--------|-----------|-----------|
| API response time | < 1000ms | Sanity |
| Query latency p99 | < 500ms | Load |
| Scrape success rate | > 99% | Load |
| CPU utilization | < 80% | Load |
| Memory utilization | < 85% | Load |
| Min series before failure | > 1M | Stress |
| Min ingestion rate | > 100K/s | Stress |
| Simple query latency | < 50ms | Performance |
| Complex query latency | < 500ms | Performance |
| Recovery time | < 60s | Reliability |

## See Also

- [Test Types](../testing/test-types.md) - Description of each test type
- [Interpreting Results](../testing/interpreting-results.md) - How to analyze test reports
- [Configuration Schema](config-schema.md) - Threshold configuration
