# Fluent Bit Metrics Analysis & Dashboard Guide

## Available Metrics from http://127.0.0.1:2020/api/v2/metrics/prometheus

### 📊 **System & Runtime Metrics**

#### **1. Uptime & Build Info**
```prometheus
fluentbit_uptime{hostname="spiralDuct"} 1189
fluentbit_build_info{hostname="spiralDuct",version="4.1.1",os="macos"} 1761553217
fluentbit_process_start_time_seconds{hostname="spiralDuct"} 1761553217
fluentbit_hot_reloaded_times{hostname="spiralDuct"} 0
```

**📈 Suggested Graphs:**
- **Uptime Graph**: `fluentbit_uptime` - **Time Series** (Line chart) showing service uptime
- **Version Info**: `fluentbit_build_info` - **Stat Panel** showing version & OS
- **Hot Reloads**: `fluentbit_hot_reloaded_times` - **Stat Panel** (Counter) of configuration reloads

---

### 📥 **Input Metrics (Log Collection)**

#### **2. Input Volume & Performance**
```prometheus
fluentbit_input_bytes_total{name="tail.0"} 2562345
fluentbit_input_records_total{name="tail.0"} 12426
fluentbit_input_files_opened_total{name="tail.0"} 4
```

**📈 Suggested Graphs:**
- **Input Rate**: `rate(fluentbit_input_records_total[5m])` - **Time Series** (Records per second)
- **Input Throughput**: `rate(fluentbit_input_bytes_total[5m])` - **Time Series** (Bytes per second)  
- **Files Monitored**: `fluentbit_input_files_opened_total` - **Stat Panel** (Number of log files)
- **Average Record Size**: `fluentbit_input_bytes_total / fluentbit_input_records_total` - **Gauge** (Bytes per record)

#### **3. Input Buffer & Ring Buffer**
```prometheus
fluentbit_input_ring_buffer_writes_total{name="tail.0"} 0
fluentbit_input_ring_buffer_retries_total{name="tail.0"} 0
fluentbit_input_ring_buffer_retry_failures_total{name="tail.0"} 0
```

**📈 Suggested Graphs:**
- **Buffer Health**: `fluentbit_input_ring_buffer_retry_failures_total` - **Stat Panel** (Alert on failures)
- **Buffer Pressure**: `rate(fluentbit_input_ring_buffer_retries_total[5m])` - **Time Series** (Retry rate)

---

### 📤 **Output Metrics (Log Forwarding)**

#### **4. Output Performance & Reliability**
```prometheus
fluentbit_output_proc_records_total{name="loki.0"} 12416
fluentbit_output_proc_bytes_total{name="loki.0"} 2560202
fluentbit_output_errors_total{name="loki.0"} 0
fluentbit_output_retries_total{name="loki.0"} 0
fluentbit_output_dropped_records_total{name="loki.0"} 0
```

**📈 Suggested Graphs:**
- **Output Rate**: `rate(fluentbit_output_proc_records_total[5m])` - **Time Series** (Records/sec to Loki)
- **Output Throughput**: `rate(fluentbit_output_proc_bytes_total[5m])` - **Time Series** (Bytes/sec to Loki)
- **Error Rate**: `rate(fluentbit_output_errors_total[5m])` - **Time Series** (Errors per second)
- **Success Rate**: `(rate(fluentbit_output_proc_records_total[5m]) / (rate(fluentbit_output_proc_records_total[5m]) + rate(fluentbit_output_errors_total[5m]))) * 100` - **Gauge** (Percentage)
- **Dropped Records**: `rate(fluentbit_output_dropped_records_total[5m])` - **Time Series** (Data loss indicator)

#### **5. Output Latency (Performance)**
```prometheus
fluentbit_output_latency_seconds_bucket{le="1.0",input="tail.0",output="loki.0"} 871
fluentbit_output_latency_seconds_sum{input="tail.0",output="loki.0"} 1186.33
fluentbit_output_latency_seconds_count{input="tail.0",output="loki.0"} 1188
```

**📈 Suggested Graphs:**
- **Average Latency**: `fluentbit_output_latency_seconds_sum / fluentbit_output_latency_seconds_count` - **Gauge** (Seconds)
- **P95 Latency**: `histogram_quantile(0.95, rate(fluentbit_output_latency_seconds_bucket[5m]))` - **Time Series** (95th percentile)
- **P99 Latency**: `histogram_quantile(0.99, rate(fluentbit_output_latency_seconds_bucket[5m]))` - **Time Series** (99th percentile)
- **Latency Heatmap**: `fluentbit_output_latency_seconds_bucket` - **Heatmap** (Latency distribution)

---

### 💾 **Storage & Memory Metrics**

#### **6. Storage Layer Health**
```prometheus
fluentbit_storage_chunks 1
fluentbit_storage_mem_chunks 1
fluentbit_storage_fs_chunks 0
fluentbit_input_storage_memory_bytes{name="tail.0"} 2056
```

**📈 Suggested Graphs:**
- **Memory Usage**: `fluentbit_input_storage_memory_bytes` - **Time Series** (Memory consumption)
- **Chunk Distribution**: `fluentbit_storage_mem_chunks` vs `fluentbit_storage_fs_chunks` - **Pie Chart** (Memory vs Filesystem)
- **Storage Pressure**: `fluentbit_input_storage_overlimit` - **Stat Panel** (Memory limit alerts)

#### **7. Input Status & Health**
```prometheus
fluentbit_input_ingestion_paused{name="tail.0"} 0
fluentbit_input_storage_overlimit{name="tail.0"} 0
```

**📈 Suggested Graphs:**
- **Input Status**: `fluentbit_input_ingestion_paused` - **Stat Panel** (0=Running, 1=Paused)
- **Memory Overlimit**: `fluentbit_input_storage_overlimit` - **Stat Panel** (Alert indicator)

---

### 🌐 **Network & Connection Metrics**

#### **8. Upstream Connections**
```prometheus
fluentbit_output_upstream_total_connections{name="loki.0"} 1
fluentbit_output_upstream_busy_connections{name="loki.0"} 0
fluentbit_output_chunk_available_capacity_percent{name="loki.0"} 100
```

**📈 Suggested Graphs:**
- **Connection Pool**: `fluentbit_output_upstream_total_connections` - **Stat Panel** (Total connections)
- **Active Connections**: `fluentbit_output_upstream_busy_connections` - **Time Series** (Busy connections)
- **Capacity**: `fluentbit_output_chunk_available_capacity_percent` - **Gauge** (Available capacity %)

---

### 📋 **Log Level Metrics**

#### **9. Internal Logging**
```prometheus
fluentbit_logger_logs_total{message_type="error"} 0
fluentbit_logger_logs_total{message_type="warn"} 0
fluentbit_logger_logs_total{message_type="info"} 11
```

**📈 Suggested Graphs:**
- **Log Levels**: `fluentbit_logger_logs_total` by `message_type` - **Bar Chart** (Stacked)
- **Error Rate**: `rate(fluentbit_logger_logs_total{message_type="error"}[5m])` - **Time Series** (Errors per second)

---

## 🎯 **Recommended Dashboard Layout**

### **Row 1: Overview**
- Uptime | Version Info | Status (Running/Paused)

### **Row 2: Throughput**
- Input Rate (records/sec) | Output Rate (records/sec) | Throughput (bytes/sec)

### **Row 3: Performance**
- Average Latency | P95 Latency | Success Rate %

### **Row 4: Health & Errors**
- Error Rate | Dropped Records | Retry Rate | Memory Usage

### **Row 5: Storage & Connections**
- Memory Chunks | FS Chunks | Connection Pool | Available Capacity

## 🚨 **Key Alerts to Set**

1. **High Error Rate**: `rate(fluentbit_output_errors_total[5m]) > 0.1`
2. **Dropped Records**: `rate(fluentbit_output_dropped_records_total[5m]) > 0`
3. **High Latency**: `histogram_quantile(0.95, rate(fluentbit_output_latency_seconds_bucket[5m])) > 2`
4. **Memory Overlimit**: `fluentbit_input_storage_overlimit == 1`
5. **Service Down**: `up{job="fluent-bit-v2"} == 0`

## 📊 **Sample PromQL Queries**

```prometheus
# Data processing efficiency
(fluentbit_output_proc_records_total / fluentbit_input_records_total) * 100

# Average record processing time
fluentbit_output_latency_seconds_sum / fluentbit_output_latency_seconds_count

# Input vs Output rate comparison
rate(fluentbit_input_records_total[5m]) - rate(fluentbit_output_proc_records_total[5m])

# Memory efficiency (bytes per record)
fluentbit_input_storage_memory_bytes / fluentbit_input_storage_chunks
```