# Loki Metrics Analysis & Dashboard Guide

## Available Metrics from http://localhost:3100/metrics

### 📊 **System & Build Information**

#### **1. Build & Version Info**
```prometheus
loki_build_info{branch="release-3.5.x",goarch="amd64",goos="darwin",goversion="go1.24.1",revision="5aa8bd27",tags="netgo",version="3.5.5"} 1
```

**📈 Suggested Graphs:**
- **Version Info**: `loki_build_info` - **Stat Panel** showing version, branch, OS
- **Build Details**: `loki_build_info` - **Table** showing all build labels

---

### 📥 **Log Ingestion Metrics**

#### **2. Log Volume & Processing**
```prometheus
loki_bytes_per_line_bucket{le="512"} 25248
loki_bytes_per_line_sum 4.826913e+06
loki_bytes_per_line_count 25248
```

**📈 Suggested Graphs:**
- **Average Log Line Size**: `loki_bytes_per_line_sum / loki_bytes_per_line_count` - **Gauge** (Bytes per log line)
- **Log Line Size Distribution**: `rate(loki_bytes_per_line_bucket[5m])` - **Heatmap** (Histogram of line sizes)
- **Total Log Volume**: `rate(loki_bytes_per_line_sum[5m])` - **Time Series** (Bytes ingested per second)
- **Log Line Rate**: `rate(loki_bytes_per_line_count[5m])` - **Time Series** (Lines ingested per second)

#### **3. Distributor Metrics** (Log Entry Point)
```prometheus
# Note: These metrics appear when logs are actively being ingested
loki_distributor_ingester_append_failures_total
loki_distributor_ingester_appends_total
loki_distributor_bytes_received_total
loki_distributor_lines_received_total
```

**📈 Suggested Graphs:**
- **Ingestion Rate**: `rate(loki_distributor_lines_received_total[5m])` - **Time Series** (Lines/sec received)
- **Ingestion Throughput**: `rate(loki_distributor_bytes_received_total[5m])` - **Time Series** (Bytes/sec received)
- **Append Success Rate**: `rate(loki_distributor_ingester_appends_total[5m]) / (rate(loki_distributor_ingester_appends_total[5m]) + rate(loki_distributor_ingester_append_failures_total[5m])) * 100` - **Gauge** (Percentage)
- **Failure Rate**: `rate(loki_distributor_ingester_append_failures_total[5m])` - **Time Series** (Failed appends/sec)

---

### 💾 **Storage & Chunk Metrics**

#### **4. Chunk Store Performance**
```prometheus
loki_chunk_store_chunks_per_query_bucket{le="10"} 0
loki_chunk_store_chunks_per_query_sum 0
loki_chunk_store_chunks_per_query_count 0
loki_chunk_store_deduped_chunks_total 0
loki_chunk_store_deduped_bytes_total 0
```

**📈 Suggested Graphs:**
- **Chunks per Query**: `loki_chunk_store_chunks_per_query_sum / loki_chunk_store_chunks_per_query_count` - **Gauge** (Average chunks accessed per query)
- **Query Efficiency**: `histogram_quantile(0.95, rate(loki_chunk_store_chunks_per_query_bucket[5m]))` - **Time Series** (P95 chunks per query)
- **Deduplication Rate**: `rate(loki_chunk_store_deduped_chunks_total[5m])` - **Time Series** (Deduplicated chunks/sec)
- **Storage Efficiency**: `rate(loki_chunk_store_deduped_bytes_total[5m])` - **Time Series** (Bytes saved by deduplication)

#### **5. Index Performance**
```prometheus
loki_chunk_store_index_entries_per_chunk_bucket{le="1"} 0
loki_chunk_store_index_lookups_per_query_bucket{le="1"} 0
loki_chunk_store_series_post_intersection_per_query_bucket{le="10"} 0
loki_chunk_store_series_pre_intersection_per_query_bucket{le="10"} 0
```

**📈 Suggested Graphs:**
- **Index Efficiency**: `loki_chunk_store_index_entries_per_chunk_sum / loki_chunk_store_index_entries_per_chunk_count` - **Gauge** (Index entries per chunk)
- **Index Lookups**: `loki_chunk_store_index_lookups_per_query_sum / loki_chunk_store_index_lookups_per_query_count` - **Gauge** (Lookups per query)
- **Series Filtering**: `loki_chunk_store_series_post_intersection_per_query_sum / loki_chunk_store_series_pre_intersection_per_query_sum * 100` - **Gauge** (Series filter efficiency %)

---

### 🗄️ **Cache Performance**

#### **6. Cache Metrics (Multiple Cache Types)**
```prometheus
loki_cache_fetched_keys{name="chunksembedded-cache"} 0
loki_cache_hits{name="chunksembedded-cache"} 0
loki_cache_hits{name="frontend.index-stats-results-cache.embedded-cache"} 0
loki_cache_hits{name="frontend.label-results-cache.embedded-cache"} 0
loki_cache_hits{name="frontend.series-results-cache.embedded-cache"} 0
loki_cache_hits{name="frontend.volume-results-cache.embedded-cache"} 0
```

**📈 Suggested Graphs:**
- **Cache Hit Rate**: `rate(loki_cache_hits[5m]) / rate(loki_cache_fetched_keys[5m]) * 100` - **Time Series** (Hit rate % by cache type)
- **Cache Requests**: `rate(loki_cache_fetched_keys[5m])` - **Time Series** (Cache requests/sec by type)
- **Cache Efficiency**: `rate(loki_cache_hits[5m]) / rate(loki_cache_fetched_keys[5m]) * 100` by cache name - **Bar Chart** (Stacked, hit rates for all cache types)
- **Cache Value Sizes**: `histogram_quantile(0.95, rate(loki_cache_value_size_bytes_bucket[5m]))` - **Time Series** (P95 cache value size)

---

### 🔧 **Compactor & Maintenance**

#### **7. BoltDB Shipper & Compactor**
```prometheus
loki_boltdb_shipper_compact_tables_operation_duration_seconds 0.00010804
loki_boltdb_shipper_compact_tables_operation_last_successful_run_timestamp_seconds 1.7615541478485482e+09
loki_boltdb_shipper_compact_tables_operation_total{status="success"} 9
loki_boltdb_shipper_compactor_running 1
```

**📈 Suggested Graphs:**
- **Compactor Status**: `loki_boltdb_shipper_compactor_running` - **Stat Panel** (1=Running, 0=Stopped)
- **Compaction Duration**: `loki_boltdb_shipper_compact_tables_operation_duration_seconds` - **Time Series** (Time per compaction)
- **Compaction Success Rate**: `rate(loki_boltdb_shipper_compact_tables_operation_total{status="success"}[5m])` - **Time Series** (Successful compactions/sec)
- **Last Successful Run**: `time() - loki_boltdb_shipper_compact_tables_operation_last_successful_run_timestamp_seconds` - **Stat Panel** (Time since last success)

---

### 🔍 **Query Performance**

#### **8. Query Metrics** (Active during queries)
```prometheus
# These metrics appear during query execution:
loki_query_frontend_queries_total
loki_query_frontend_query_range_duration_seconds
loki_querier_query_duration_seconds
loki_logql_querystats_duplicates_total
loki_logql_querystats_ingester_sent_lines_total
```

**📈 Suggested Graphs:**
- **Query Rate**: `rate(loki_query_frontend_queries_total[5m])` - **Time Series** (Queries/sec)
- **Query Duration P95**: `histogram_quantile(0.95, rate(loki_query_frontend_query_range_duration_seconds_bucket[5m]))` - **Time Series** (Query latency)
- **Query Duration P99**: `histogram_quantile(0.99, rate(loki_query_frontend_query_range_duration_seconds_bucket[5m]))` - **Time Series** (Tail latency)
- **Query Latency Heatmap**: `loki_query_frontend_query_range_duration_seconds_bucket` - **Heatmap** (Query duration distribution)
- **Lines Processed**: `rate(loki_logql_querystats_ingester_sent_lines_total[5m])` - **Time Series** (Lines processed/sec in queries)

---

### 🌐 **Network & Egress**

#### **9. Cloud Storage Egress**
```prometheus
loki_azure_blob_egress_bytes_total 0
# Similar metrics for other cloud providers when configured
```

**📈 Suggested Graphs:**
- **Cloud Egress**: `rate(loki_azure_blob_egress_bytes_total[5m])` - **Time Series** (Bytes/sec from cloud storage)
- **Storage Costs**: `increase(loki_azure_blob_egress_bytes_total[24h])` - **Stat Panel** (Daily egress for cost monitoring)

---

## 🎯 **Recommended Dashboard Layout**

### **Row 1: Overview & Status**
- Build Info | Compactor Status | Cache Hit Rates Overview

### **Row 2: Ingestion Performance**
- Log Line Rate | Ingestion Throughput | Average Line Size | Append Success Rate

### **Row 3: Query Performance**
- Query Rate | P95 Query Duration | P99 Query Duration | Lines Processed/sec

### **Row 4: Storage Efficiency**
- Chunks per Query | Index Lookups per Query | Deduplication Rate | Series Filter Efficiency

### **Row 5: Cache Performance**
- Cache Hit Rates (by type) | Cache Requests/sec | Cache Value Sizes

### **Row 6: Maintenance & Health**
- Compaction Duration | Last Successful Compaction | Storage Egress

---

## 🚨 **Key Alerts to Set**

### **Critical Alerts:**
1. **Loki Down**: `up{job="loki"} == 0`
2. **High Ingestion Failures**: `rate(loki_distributor_ingester_append_failures_total[5m]) > 0.1`
3. **Compactor Not Running**: `loki_boltdb_shipper_compactor_running == 0`
4. **Old Compaction**: `time() - loki_boltdb_shipper_compact_tables_operation_last_successful_run_timestamp_seconds > 3600`

### **Warning Alerts:**
1. **High Query Latency**: `histogram_quantile(0.95, rate(loki_query_frontend_query_range_duration_seconds_bucket[5m])) > 10`
2. **Low Cache Hit Rate**: `rate(loki_cache_hits[5m]) / rate(loki_cache_fetched_keys[5m]) < 0.8`
3. **High Chunks per Query**: `loki_chunk_store_chunks_per_query_sum / loki_chunk_store_chunks_per_query_count > 1000`

---

## 📊 **Advanced PromQL Queries**

### **Performance Analysis:**
```prometheus
# Ingestion efficiency (lines per second)
rate(loki_bytes_per_line_count[5m])

# Average log line size trend
rate(loki_bytes_per_line_sum[5m]) / rate(loki_bytes_per_line_count[5m])

# Query performance vs ingestion load
rate(loki_query_frontend_queries_total[5m]) / rate(loki_distributor_lines_received_total[5m])

# Cache efficiency across all caches
sum(rate(loki_cache_hits[5m])) / sum(rate(loki_cache_fetched_keys[5m])) * 100

# Storage efficiency (deduplication rate)
rate(loki_chunk_store_deduped_bytes_total[5m]) / rate(loki_distributor_bytes_received_total[5m]) * 100
```

### **Capacity Planning:**
```prometheus
# Ingestion growth rate (week over week)
increase(loki_bytes_per_line_sum[7d])

# Query load growth
increase(loki_query_frontend_queries_total[7d])

# Storage growth rate
increase(loki_chunk_store_chunks_per_query_sum[7d])
```

---

## 💡 **Dashboard Tips**

### **Color Coding:**
- **Green**: Success rates, cache hits, healthy status
- **Yellow**: Warning thresholds, moderate latency
- **Red**: Failures, high latency, critical alerts

### **Time Ranges:**
- **Real-time panels**: Last 5-15 minutes
- **Trend analysis**: Last 24 hours to 7 days
- **Capacity planning**: Last 30 days

### **Thresholds:**
- **Query latency**: Good <1s, Warning 1-5s, Critical >5s
- **Cache hit rate**: Good >90%, Warning 80-90%, Critical <80%
- **Ingestion success**: Good >99.9%, Warning 99-99.9%, Critical <99%

This comprehensive guide provides 30+ visualization suggestions with production-ready PromQL queries for monitoring Loki performance! 🚀