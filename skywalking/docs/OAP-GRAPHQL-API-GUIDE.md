# SkyWalking OAP Server GraphQL API Guide

This guide covers querying data from SkyWalking OAP (Observability Analysis Platform) Server via its GraphQL API.

> **Official Documentation**:
> - [Query Protocol](https://skywalking.apache.org/docs/main/next/en/api/query-protocol/)
> - [GraphQL Schema Repository](https://github.com/apache/skywalking-query-protocol)

## Overview

SkyWalking exposes a GraphQL endpoint at `http://<oap-server>:12800/graphql` for querying:
- Services, Instances, Endpoints metadata
- Traces and Spans
- Metrics (via MQE - Metrics Query Expression)
- Logs
- Topology maps
- Profiling data
- Alarms and Events

**Related Docs**:
- [Backend Setup](https://skywalking.apache.org/docs/main/next/en/setup/backend/backend-setup/)
- [Backend Expose Settings](https://skywalking.apache.org/docs/main/next/en/setup/backend/backend-expose/)

---

## Connection Setup

### Internal (Kubernetes)
```
http://skywalking-oap.skywalking:12800/graphql
```

### External (via Ingress)
```
https://<your-domain>/graphql
```

### Port-Forward for Local Testing
```bash
kubectl port-forward -n skywalking svc/skywalking-oap 12800:12800
# Then use: http://localhost:12800/graphql
```

---

## Duration Parameter

Most queries require a `Duration` parameter for time range:

```graphql
input Duration {
  start: String!   # Format depends on step
  end: String!
  step: Step!      # MONTH, DAY, HOUR, MINUTE, SECOND
}
```

**Time Formats by Step**:
| Step | Format | Example |
|------|--------|---------|
| SECOND | yyyy-MM-dd HHmmss | 2026-02-25 143000 |
| MINUTE | yyyy-MM-dd HHmm | 2026-02-25 1430 |
| HOUR | yyyy-MM-dd HH | 2026-02-25 14 |
| DAY | yyyy-MM-dd | 2026-02-25 |
| MONTH | yyyy-MM | 2026-02 |

---

## 1. Metadata Queries

> **Docs**: [Query Protocol - Metadata](https://skywalking.apache.org/docs/main/next/en/api/query-protocol/#metadata)

### List All Layers
```bash
curl -X POST http://localhost:12800/graphql \
  -H "Content-Type: application/json" \
  -d '{"query": "{ listLayers }"}'
```

### List Services by Layer
```bash
curl -X POST http://localhost:12800/graphql \
  -H "Content-Type: application/json" \
  -d '{"query": "{ listServices(layer: \"GENERAL\") { id name } }"}'
```

### Get Service by ID
```bash
curl -X POST http://localhost:12800/graphql \
  -H "Content-Type: application/json" \
  -d '{"query": "{ getService(serviceId: \"<SERVICE_ID>\") { id name layers } }"}'
```

### Find Service by Name
```bash
curl -X POST http://localhost:12800/graphql \
  -H "Content-Type: application/json" \
  -d '{"query": "{ findService(serviceName: \"task-manager\") { id name } }"}'
```

### List Service Instances
```bash
curl -X POST http://localhost:12800/graphql \
  -H "Content-Type: application/json" \
  -d '{
    "query": "query($duration: Duration!, $serviceId: ID!) { listInstances(duration: $duration, serviceId: $serviceId) { id name language instanceUUID } }",
    "variables": {
      "duration": {"start": "2026-02-25 00", "end": "2026-02-25 23", "step": "HOUR"},
      "serviceId": "<SERVICE_ID>"
    }
  }'
```

### Find Endpoints
```bash
curl -X POST http://localhost:12800/graphql \
  -H "Content-Type: application/json" \
  -d '{
    "query": "{ findEndpoint(keyword: \"api\", serviceId: \"<SERVICE_ID>\", limit: 10) { id name } }"
  }'
```

---

## 2. Metrics Queries (MQE)

> **Docs**:
> - [Metrics Query Expression (MQE) Syntax](https://skywalking.apache.org/docs/main/next/en/api/metrics-query-expression/)
> - [Query Protocol - Metrics V3](https://skywalking.apache.org/docs/main/next/en/api/query-protocol/#v3-apis)
> - [OAL Scripts (Metric Definitions)](https://skywalking.apache.org/docs/main/next/en/guides/backend-oal-scripts/)

SkyWalking uses Metrics Query Expression (MQE) for flexible metric queries.

### List Available Metrics
```bash
curl -X POST http://localhost:12800/graphql \
  -H "Content-Type: application/json" \
  -d '{"query": "{ listMetrics(regex: \"service_.*\") { name type catalog } }"}'
```

### Get Metric Type
```bash
curl -X POST http://localhost:12800/graphql \
  -H "Content-Type: application/json" \
  -d '{"query": "{ typeOfMetrics(name: \"service_cpm\") }"}'
```

### Execute MQE Expression - Service CPM
```bash
curl -X POST http://localhost:12800/graphql \
  -H "Content-Type: application/json" \
  -d '{
    "query": "query($expression: String!, $entity: Entity!, $duration: Duration!) { execExpression(expression: $expression, entity: $entity, duration: $duration) { type error results { metric { labels { key value } } values { id value } } } }",
    "variables": {
      "expression": "service_cpm",
      "entity": {"serviceName": "task-manager", "normal": true},
      "duration": {"start": "2026-02-25 00", "end": "2026-02-25 23", "step": "HOUR"}
    }
  }'
```

### Service Response Time
```bash
curl -X POST http://localhost:12800/graphql \
  -H "Content-Type: application/json" \
  -d '{
    "query": "query($expression: String!, $entity: Entity!, $duration: Duration!) { execExpression(expression: $expression, entity: $entity, duration: $duration) { type results { values { id value } } } }",
    "variables": {
      "expression": "service_resp_time",
      "entity": {"serviceName": "task-manager", "normal": true},
      "duration": {"start": "2026-02-25 1400", "end": "2026-02-25 1500", "step": "MINUTE"}
    }
  }'
```

### Service Percentiles (P50, P75, P90, P95, P99)
```bash
curl -X POST http://localhost:12800/graphql \
  -H "Content-Type: application/json" \
  -d '{
    "query": "query($expression: String!, $entity: Entity!, $duration: Duration!) { execExpression(expression: $expression, entity: $entity, duration: $duration) { type results { metric { labels { key value } } values { id value } } } }",
    "variables": {
      "expression": "service_percentile{p='"'"'50,75,90,95,99'"'"'}",
      "entity": {"serviceName": "task-manager", "normal": true},
      "duration": {"start": "2026-02-25 00", "end": "2026-02-25 23", "step": "HOUR"}
    }
  }'
```

### Service SLA (Success Rate)
```bash
# SLA as percentage (divide by 100 for actual %)
curl -X POST http://localhost:12800/graphql \
  -H "Content-Type: application/json" \
  -d '{
    "query": "query($expression: String!, $entity: Entity!, $duration: Duration!) { execExpression(expression: $expression, entity: $entity, duration: $duration) { type results { values { id value } } } }",
    "variables": {
      "expression": "service_sla/100",
      "entity": {"serviceName": "task-manager", "normal": true},
      "duration": {"start": "2026-02-25 00", "end": "2026-02-25 23", "step": "HOUR"}
    }
  }'
```

### Aggregation Functions
```bash
# Average CPM over time range
"expression": "avg(service_cpm)"

# Maximum response time
"expression": "max(service_resp_time)"

# Sum of calls
"expression": "sum(service_cpm)"
```

---

## 3. Trace Queries

> **Docs**:
> - [Query Protocol - Trace](https://skywalking.apache.org/docs/main/next/en/api/query-protocol/#trace)
> - [Trace Data Protocol](https://skywalking.apache.org/docs/main/next/en/api/trace-data-protocol-v3/)
> - [Trace Sampling](https://skywalking.apache.org/docs/main/next/en/setup/backend/trace-sampling/)

### Search Traces
```bash
curl -X POST http://localhost:12800/graphql \
  -H "Content-Type: application/json" \
  -d '{
    "query": "query($condition: TraceQueryCondition) { queryBasicTraces(condition: $condition) { traces { segmentId traceIds endpointNames duration start isError } total } }",
    "variables": {
      "condition": {
        "serviceId": "<SERVICE_ID>",
        "queryDuration": {"start": "2026-02-25 1400", "end": "2026-02-25 1500", "step": "MINUTE"},
        "queryOrder": "BY_DURATION",
        "paging": {"pageNum": 1, "pageSize": 20}
      }
    }
  }'
```

### Get Trace by ID
```bash
curl -X POST http://localhost:12800/graphql \
  -H "Content-Type: application/json" \
  -d '{
    "query": "query($traceId: ID!) { queryTrace(traceId: $traceId) { spans { traceId segmentId spanId parentSpanId serviceCode startTime endTime endpointName type peer component isError tags { key value } logs { time data { key value } } } } }",
    "variables": {
      "traceId": "<TRACE_ID>"
    }
  }'
```

### Query Trace Tags (Autocomplete)
```bash
# Get available tag keys
curl -X POST http://localhost:12800/graphql \
  -H "Content-Type: application/json" \
  -d '{
    "query": "query($duration: Duration!) { queryTraceTagAutocompleteKeys(duration: $duration) }",
    "variables": {
      "duration": {"start": "2026-02-25 00", "end": "2026-02-25 23", "step": "HOUR"}
    }
  }'

# Get values for a tag key
curl -X POST http://localhost:12800/graphql \
  -H "Content-Type: application/json" \
  -d '{
    "query": "query($tagKey: String!, $duration: Duration!) { queryTraceTagAutocompleteValues(tagKey: $tagKey, duration: $duration) }",
    "variables": {
      "tagKey": "http.method",
      "duration": {"start": "2026-02-25 00", "end": "2026-02-25 23", "step": "HOUR"}
    }
  }'
```

---

## 4. Topology Queries

> **Docs**: [Query Protocol - Topology](https://skywalking.apache.org/docs/main/next/en/api/query-protocol/#topology)

### Global Topology
```bash
curl -X POST http://localhost:12800/graphql \
  -H "Content-Type: application/json" \
  -d '{
    "query": "query($duration: Duration!) { getGlobalTopology(duration: $duration) { nodes { id name type isReal } calls { id source target detectPoints } } }",
    "variables": {
      "duration": {"start": "2026-02-25 00", "end": "2026-02-25 23", "step": "HOUR"}
    }
  }'
```

### Service Topology
```bash
curl -X POST http://localhost:12800/graphql \
  -H "Content-Type: application/json" \
  -d '{
    "query": "query($serviceId: ID!, $duration: Duration!) { getServiceTopology(serviceId: $serviceId, duration: $duration) { nodes { id name type } calls { id source target } } }",
    "variables": {
      "serviceId": "<SERVICE_ID>",
      "duration": {"start": "2026-02-25 00", "end": "2026-02-25 23", "step": "HOUR"}
    }
  }'
```

### Endpoint Dependencies
```bash
curl -X POST http://localhost:12800/graphql \
  -H "Content-Type: application/json" \
  -d '{
    "query": "query($endpointId: ID!, $duration: Duration!) { getEndpointDependencies(endpointId: $endpointId, duration: $duration) { nodes { id name serviceId serviceName type } calls { id source target } } }",
    "variables": {
      "endpointId": "<ENDPOINT_ID>",
      "duration": {"start": "2026-02-25 00", "end": "2026-02-25 23", "step": "HOUR"}
    }
  }'
```

---

## 5. Log Queries

> **Docs**:
> - [Query Protocol - Logs](https://skywalking.apache.org/docs/main/next/en/api/query-protocol/#logs)
> - [Log Data Protocol](https://skywalking.apache.org/docs/main/next/en/api/log-data-protocol/)
> - [Log Analyzer](https://skywalking.apache.org/docs/main/next/en/setup/backend/log-analyzer/)
> - [Native Log Agent](https://skywalking.apache.org/docs/main/next/en/setup/backend/log-agent-native/)

### Query Logs
```bash
curl -X POST http://localhost:12800/graphql \
  -H "Content-Type: application/json" \
  -d '{
    "query": "query($condition: LogQueryCondition) { queryLogs(condition: $condition) { logs { serviceName serviceInstanceName endpointName traceId timestamp contentType content tags { key value } } total } }",
    "variables": {
      "condition": {
        "serviceId": "<SERVICE_ID>",
        "queryDuration": {"start": "2026-02-25 1400", "end": "2026-02-25 1500", "step": "MINUTE"},
        "paging": {"pageNum": 1, "pageSize": 20}
      }
    }
  }'
```

### Check Keyword Search Support
```bash
curl -X POST http://localhost:12800/graphql \
  -H "Content-Type: application/json" \
  -d '{"query": "{ supportQueryLogsByKeywords }"}'
```

---

## 6. Profiling Queries

> **Docs**:
> - [Query Protocol - Profiling](https://skywalking.apache.org/docs/main/next/en/api/query-protocol/#profiling)
> - [Profiling Protocol](https://skywalking.apache.org/docs/main/next/en/api/profiling-protocol/)
> - [Trace Profiling Setup](https://skywalking.apache.org/docs/main/next/en/setup/backend/backend-trace-profiling/)
> - [eBPF Profiling](https://skywalking.apache.org/docs/main/next/en/setup/backend/backend-ebpf-profiling/)
> - [Continuous Profiling](https://skywalking.apache.org/docs/main/next/en/setup/backend/backend-continuous-profiling/)

### Create Profile Task (Tracing Profiling)
```bash
curl -X POST http://localhost:12800/graphql \
  -H "Content-Type: application/json" \
  -d '{
    "query": "mutation createProfileTask($creationRequest: ProfileTaskCreationRequest!) { createProfileTask(creationRequest: $creationRequest) { id errorReason } }",
    "variables": {
      "creationRequest": {
        "serviceId": "<SERVICE_ID>",
        "endpointName": "GET:/api/tasks",
        "startTime": -1,
        "duration": 5,
        "minDurationThreshold": 0,
        "dumpPeriod": 10,
        "maxSamplingCount": 5
      }
    }
  }'
```

**Parameters**:
- `serviceId`: Target service ID (base64 encoded)
- `endpointName`: Endpoint to profile
- `startTime`: -1 for immediate start, or Unix timestamp
- `duration`: Task duration in minutes
- `minDurationThreshold`: Min trace duration (ms) to profile
- `dumpPeriod`: Stack dump interval (ms)
- `maxSamplingCount`: Max samples per trace

### List Profile Tasks
```bash
curl -X POST http://localhost:12800/graphql \
  -H "Content-Type: application/json" \
  -d '{
    "query": "query($serviceId: ID) { getProfileTaskList(serviceId: $serviceId) { id serviceId endpointName startTime duration minDurationThreshold dumpPeriod maxSamplingCount } }",
    "variables": {
      "serviceId": "<SERVICE_ID>"
    }
  }'
```

### Get Profile Task Logs
```bash
curl -X POST http://localhost:12800/graphql \
  -H "Content-Type: application/json" \
  -d '{
    "query": "query($taskID: String) { getProfileTaskLogs(taskID: $taskID) { id instanceId instanceName operationType operationTime } }",
    "variables": {
      "taskID": "<TASK_ID>"
    }
  }'
```

### Get Profiled Segments
```bash
curl -X POST http://localhost:12800/graphql \
  -H "Content-Type: application/json" \
  -d '{
    "query": "query($taskID: ID!) { getProfileTaskSegments(taskID: $taskID) { traceId instanceId endpointNames duration start isError } }",
    "variables": {
      "taskID": "<TASK_ID>"
    }
  }'
```

---

## 7. Alarm Queries

> **Docs**:
> - [Query Protocol - Alarm](https://skywalking.apache.org/docs/main/next/en/api/query-protocol/#alarm)
> - [Alarm Configuration](https://skywalking.apache.org/docs/main/next/en/setup/backend/backend-alarm/)

### Get Alarms
```bash
curl -X POST http://localhost:12800/graphql \
  -H "Content-Type: application/json" \
  -d '{
    "query": "query($duration: Duration!, $paging: Pagination!) { getAlarm(duration: $duration, paging: $paging) { msgs { id message startTime scope scopeId tags { key value } } total } }",
    "variables": {
      "duration": {"start": "2026-02-25 00", "end": "2026-02-25 23", "step": "HOUR"},
      "paging": {"pageNum": 1, "pageSize": 20}
    }
  }'
```

### Get Alarm Trend
```bash
curl -X POST http://localhost:12800/graphql \
  -H "Content-Type: application/json" \
  -d '{
    "query": "query($duration: Duration!) { getAlarmTrend(duration: $duration) { numOfAlarm } }",
    "variables": {
      "duration": {"start": "2026-02-25 00", "end": "2026-02-25 23", "step": "HOUR"}
    }
  }'
```

---

## 8. Event Queries

> **Docs**:
> - [Query Protocol - Event](https://skywalking.apache.org/docs/main/next/en/api/query-protocol/#event)
> - [Event Concepts](https://skywalking.apache.org/docs/main/next/en/concepts-and-designs/event/)
> - [Event API](https://skywalking.apache.org/docs/main/next/en/api/event/)

### Query Events
```bash
curl -X POST http://localhost:12800/graphql \
  -H "Content-Type: application/json" \
  -d '{
    "query": "query($condition: EventQueryCondition) { queryEvents(condition: $condition) { events { uuid source { service serviceInstance endpoint } name type message parameters { key value } startTime endTime } total } }",
    "variables": {
      "condition": {
        "time": {"start": "2026-02-25 00", "end": "2026-02-25 23", "step": "HOUR"},
        "paging": {"pageNum": 1, "pageSize": 20}
      }
    }
  }'
```

---

## 9. Service Hierarchy

> **Docs**:
> - [Query Protocol - Hierarchy](https://skywalking.apache.org/docs/main/next/en/api/query-protocol/#hierarchy)
> - [Service Hierarchy Concepts](https://skywalking.apache.org/docs/main/next/en/concepts-and-designs/service-hierarchy/)
> - [Hierarchy Configuration](https://skywalking.apache.org/docs/main/next/en/concepts-and-designs/service-hierarchy-configuration/)

### Get Service Hierarchy
```bash
curl -X POST http://localhost:12800/graphql \
  -H "Content-Type: application/json" \
  -d '{
    "query": "query($serviceId: ID!, $layer: String!) { getServiceHierarchy(serviceId: $serviceId, layer: $layer) { relations { upperService { id name layer } lowerService { id name layer } } } }",
    "variables": {
      "serviceId": "<SERVICE_ID>",
      "layer": "GENERAL"
    }
  }'
```

### List Layer Levels
```bash
curl -X POST http://localhost:12800/graphql \
  -H "Content-Type: application/json" \
  -d '{"query": "{ listLayerLevels { layer level } }"}'
```

---

## 10. System Status Queries

> **Docs**:
> - [Status APIs](https://skywalking.apache.org/docs/main/next/en/status/status_apis/)
> - [Query TTL Setup](https://skywalking.apache.org/docs/main/next/en/status/query_ttl_setup/)
> - [Health Check](https://skywalking.apache.org/docs/main/next/en/api/health-check/)
> - [Config Dump (Debugging)](https://skywalking.apache.org/docs/main/next/en/debugging/config_dump/)

### Get Time Info
```bash
curl -X POST http://localhost:12800/graphql \
  -H "Content-Type: application/json" \
  -d '{"query": "{ getTimeInfo { timezone currentTimestamp } }"}'
```

### Get Records TTL
```bash
curl -X POST http://localhost:12800/graphql \
  -H "Content-Type: application/json" \
  -d '{"query": "{ getRecordsTTL { superDataset general } }"}'
```

### Get Metrics TTL
```bash
curl -X POST http://localhost:12800/graphql \
  -H "Content-Type: application/json" \
  -d '{"query": "{ getMetricsTTL { minute hour day } }"}'
```

---

## MQE Expression Reference

> **Full MQE Documentation**: [Metrics Query Expression Syntax](https://skywalking.apache.org/docs/main/next/en/api/metrics-query-expression/)

### Common Metrics

> **Metric Definitions**: [OAL Scripts](https://skywalking.apache.org/docs/main/next/en/guides/backend-oal-scripts/)

| Metric | Description |
|--------|-------------|
| `service_cpm` | Calls per minute |
| `service_resp_time` | Average response time (ms) |
| `service_sla` | Success rate (10000 = 100%) |
| `service_percentile` | Response time percentiles |
| `service_apdex` | Apdex score |
| `service_instance_cpm` | Instance CPM |
| `service_instance_resp_time` | Instance response time |
| `endpoint_cpm` | Endpoint CPM |
| `endpoint_resp_time` | Endpoint response time |
| `endpoint_sla` | Endpoint success rate |

### MQE Operations

| Operation | Example | Description |
|-----------|---------|-------------|
| Binary | `service_cpm + 100` | Arithmetic operations |
| Compare | `service_resp_time > 1000` | Returns 1 (true) or 0 (false) |
| Aggregation | `avg(service_cpm)` | avg, sum, max, min, count, latest |
| Math | `round(service_cpm/60, 2)` | abs, ceil, floor, round |
| TopN | `top_n(service_cpm, 10, des)` | Top N services/instances |
| Relabel | `relabel(service_percentile{p='50'}, p='50', percentile='P50')` | Rename labels |
| Trend | `increase(service_cpm, 5)` | increase, rate over time |

---

## 11. BanyanDB Specific Queries

> **Docs**:
> - [BanyanDB Overview](https://skywalking.apache.org/docs/skywalking-banyandb/next/readme/)
> - [BanyanDB Data Model](https://skywalking.apache.org/docs/skywalking-banyandb/next/concept/data-model/)
> - [BanyanDB Query (bydbctl)](https://skywalking.apache.org/docs/skywalking-banyandb/next/interacting/bydbctl/query/measure/)
> - [BanyanDB TTL](https://skywalking.apache.org/docs/main/next/en/banyandb/ttl/)
> - [BanyanDB Troubleshooting](https://skywalking.apache.org/docs/skywalking-banyandb/next/operation/troubleshooting/no-data/)

When using BanyanDB as storage, the `Duration` input supports an additional `coldStage` parameter:

```graphql
input Duration {
  start: String!
  end: String!
  step: Step!
  coldStage: Boolean  # Query from cold storage stage (BanyanDB only)
}
```

---

## Grafana Integration

> **Docs**:
> - [Grafana Plugin](https://grafana.com/grafana/plugins/apache-skywalking-datasource/)
> - [UI Grafana Setup](https://skywalking.apache.org/docs/main/next/en/setup/backend/ui-grafana/)

Use the [Apache SkyWalking Data Source](https://grafana.com/grafana/plugins/apache-skywalking-datasource/) plugin.

**Data Source URL**: `http://skywalking-oap.skywalking:12800/graphql`

The plugin provides:
- Service/Instance/Endpoint selectors
- MQE expression support
- Topology visualization
- Trace exploration

---

## PromQL Service (Prometheus-Compatible API)

> **Docs**: [PromQL Service](https://skywalking.apache.org/docs/main/next/en/api/promql-service/)

SkyWalking exposes a Prometheus-compatible query API, allowing Grafana (with native Prometheus data source) to query SkyWalking metrics using PromQL syntax.

### Configuration (values.yaml)

Enable PromQL in OAP server:

```yaml
oap:
  ports:
    promql: 9090  # Expose PromQL port on service
  env:
    SW_PROMQL: "default"
    SW_PROMQL_REST_HOST: "0.0.0.0"
    SW_PROMQL_REST_PORT: "9090"
    SW_PROMQL_REST_CONTEXT_PATH: "/"
```

### Grafana Data Source Setup

| Setting | Value |
|---------|-------|
| Type | Prometheus |
| URL | `http://skywalking-oap.skywalking:9090` |

### Supported PromQL Features

| Feature | Support |
|---------|---------|
| Instant Vector Selectors | ✅ (label matching: `=` only, no regex) |
| Range Vector Selectors | ✅ |
| Arithmetic Operators | ✅ (`+`, `-`, `*`, `/`, `%`) |
| Comparison Operators | ✅ (`==`, `!=`, `>`, `<`, `>=`, `<=`) |
| Aggregation | ✅ (`sum`, `min`, `max`, `avg`) |
| Vector Matching | ❌ |

### PromQL Query Examples

```promql
# Service CPM
service_cpm{service='task-manager', layer='GENERAL'}

# Service response time over 5 minutes
service_resp_time{service='task-manager', layer='GENERAL'}[5m]

# Service percentiles (P50, P75, P90, P95, P99)
service_percentile{service='task-manager', layer='GENERAL', p='50,75,90,95,99'}

# Arithmetic operations
service_cpm{service='task-manager', layer='GENERAL'} / 100

# Aggregation
sum by (service) (service_cpm{layer='GENERAL'})

# Top N instances by CPM
service_instance_cpm{parent_service='task-manager', layer='GENERAL', top_n='10', order='DES'}
```

### Metadata Queries

```promql
# List services
service_traffic{layer='GENERAL'}

# List instances
instance_traffic{layer='GENERAL', service='task-manager'}

# List endpoints
endpoint_traffic{layer='GENERAL', service='task-manager'}
```

### HTTP API Endpoints

| Endpoint | Description |
|----------|-------------|
| `GET /api/v1/query` | Instant query |
| `GET /api/v1/query_range` | Range query |
| `GET /api/v1/series` | Find series by label matchers |
| `GET /api/v1/labels` | Get label names |
| `GET /api/v1/label/<name>/values` | Get label values |
| `GET /api/v1/metadata` | Get metric metadata |

### Grafana Dashboard Variables

Configure dashboard variables for dynamic service/instance selection:

```yaml
# Service variable (Query type: Label values)
Label: service
Metric: service_traffic{layer='GENERAL'}

# Instance variable
Label: service_instance
Metric: instance_traffic{layer='GENERAL', service='$service'}

# Endpoint variable
Label: endpoint
Metric: endpoint_traffic{layer='GENERAL', service='$service'}
```

---

## LogQL Service (Loki-Compatible API)

> **Docs**: [LogQL Service](https://skywalking.apache.org/docs/main/next/en/api/logql-service/)

SkyWalking exposes a Loki-compatible query API, allowing Grafana (with native Loki data source) to query SkyWalking logs using LogQL syntax.

### Configuration (values.yaml)

Enable LogQL in OAP server:

```yaml
oap:
  ports:
    logql: 3100  # Expose LogQL port on service
  env:
    SW_LOGQL: "default"
    SW_LOGQL_REST_HOST: "0.0.0.0"
    SW_LOGQL_REST_PORT: "3100"
    SW_LOGQL_REST_CONTEXT_PATH: "/"
```

### Grafana Data Source Setup

| Setting | Value |
|---------|-------|
| Type | Loki |
| URL | `http://skywalking-oap.skywalking:3100` |

### Supported LogQL Features

| Feature | Support |
|---------|---------|
| Stream Selector | ✅ (`=` only, no regex in stream selector) |
| Line Filter (`\|=`, `!=`) | ✅ |
| Regex Line Filter (`\|~`, `!~`) | ✅ |
| Label Filter | ❌ |
| Parser | ❌ |
| Line/Label Format | ❌ |
| Metric Queries | ❌ (use LAL instead) |

### LogQL Query Examples

```logql
# Query logs by service and instance
{service="task-manager", service_instance="instance-1"}

# Query logs with trace ID
{service="task-manager", trace_id="abc123"}

# Filter logs containing keyword
{service="task-manager"} |= "ERROR"

# Filter logs NOT containing keyword
{service="task-manager"} != "DEBUG"

# Regex filter
{service="task-manager"} |~ "Exception.*timeout"

# Combined filters
{service="task-manager"} |= "ERROR" != "HealthCheck"
```

### HTTP API Endpoints

| Endpoint | Description |
|----------|-------------|
| `GET /loki/api/v1/labels` | List log tag names |
| `GET /loki/api/v1/label/<name>/values` | List log tag values |
| `GET /loki/api/v1/query_range` | Query logs with LogQL |

### Grafana Explore

In Grafana Explore with Loki data source:
1. Select the SkyWalking Loki data source
2. Use LogQL syntax: `{service="task-manager"} |= "error"`
3. Set time range and run query

---

## Complete Grafana Data Sources Summary

| Data Source | Type | URL | Use Case |
|-------------|------|-----|----------|
| SkyWalking GraphQL | SkyWalking Plugin | `http://skywalking-oap.skywalking:12800/graphql` | Full SkyWalking features (topology, traces, MQE) |
| SkyWalking PromQL | Prometheus | `http://skywalking-oap.skywalking:9090` | Metrics dashboards with PromQL |
| SkyWalking LogQL | Loki | `http://skywalking-oap.skywalking:3100` | Log exploration with LogQL |

### Verify Ports After Helm Upgrade

```bash
kubectl get svc skywalking-oap -n skywalking -o jsonpath='{.spec.ports[*].name}'
# Expected: grpc rest zipkinquery promql logql
```

---

## CLI Tool

For command-line access, use the SkyWalking CLI:

> **Docs**: [SkyWalking CLI](https://github.com/apache/skywalking-cli)

```bash
# Install
go install github.com/apache/skywalking-cli/cmd/swctl@latest

# Example: List services
swctl --base-url=http://localhost:12800/graphql service list
```

---

## References

| Topic | Documentation Link |
|-------|-------------------|
| Query Protocol | https://skywalking.apache.org/docs/main/next/en/api/query-protocol/ |
| MQE Syntax | https://skywalking.apache.org/docs/main/next/en/api/metrics-query-expression/ |
| Profiling Protocol | https://skywalking.apache.org/docs/main/next/en/api/profiling-protocol/ |
| Trace Data Protocol | https://skywalking.apache.org/docs/main/next/en/api/trace-data-protocol-v3/ |
| Log Data Protocol | https://skywalking.apache.org/docs/main/next/en/api/log-data-protocol/ |
| Event API | https://skywalking.apache.org/docs/main/next/en/api/event/ |
| Meter API | https://skywalking.apache.org/docs/main/next/en/api/meter/ |
| JVM Protocol | https://skywalking.apache.org/docs/main/next/en/api/jvm-protocol/ |
| Browser Protocol | https://skywalking.apache.org/docs/main/next/en/api/browser-protocol/ |
| Instance Properties | https://skywalking.apache.org/docs/main/next/en/api/instance-properties/ |
| PromQL Service | https://skywalking.apache.org/docs/main/next/en/api/promql-service/ |
| LogQL Service | https://skywalking.apache.org/docs/main/next/en/api/logql-service/ |
| GraphQL Schema Repo | https://github.com/apache/skywalking-query-protocol |
| SkyWalking CLI | https://github.com/apache/skywalking-cli |
| Grafana Plugin | https://grafana.com/grafana/plugins/apache-skywalking-datasource/ |
| Deprecated APIs | https://skywalking.apache.org/docs/main/next/en/api/query-protocol-deprecated/ |
