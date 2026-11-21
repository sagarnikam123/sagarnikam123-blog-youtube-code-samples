# BanyanDB Query & Access Guide

This guide covers querying and accessing data directly from BanyanDB, SkyWalking's native observability database.

> **Official Documentation**:
> - [BanyanDB Overview](https://skywalking.apache.org/docs/skywalking-banyandb/next/readme/)
> - [Data Model](https://skywalking.apache.org/docs/skywalking-banyandb/next/concept/data-model/)
> - [Client Proto Definitions](https://github.com/apache/skywalking-banyandb-client-proto)

---

## Overview

BanyanDB provides multiple ways to query data:
- **bydbctl** - Command-line tool (recommended for debugging/exploration)
- **Web UI** - Browser-based interface at port 17913
- **HTTP API** - RESTful endpoints
- **gRPC API** - For programmatic access

**Default Ports**:
| Port | Protocol | Purpose |
|------|----------|---------|
| 17912 | gRPC | Client data operations |
| 17913 | HTTP | REST API & Web UI |

---

## Connection Setup

> **Docs**: [bydbctl](https://skywalking.apache.org/docs/skywalking-banyandb/next/interacting/bydbctl/bydbctl/)

### Install bydbctl
```bash
# Download from releases
# https://skywalking.apache.org/downloads/

# Or build from source
git clone https://github.com/apache/skywalking-banyandb.git
cd skywalking-banyandb
make build
```

### Configure Connection
```bash
# Config file created at ~/.bydbctl.yaml after first command
cat ~/.bydbctl.yaml
# addr: http://127.0.0.1:17913
# group: ""
```

### Port-Forward (Kubernetes)
```bash
kubectl port-forward -n skywalking svc/skywalking-banyandb 17913:17913
# Then use: http://localhost:17913
```

### TLS Connection
```bash
bydbctl --tls=true --cert <cert_file> <command>
# Or skip verification
bydbctl --tls=true --insecure=true <command>
```

---

## Data Model

> **Docs**: [Data Model](https://skywalking.apache.org/docs/skywalking-banyandb/next/concept/data-model/)

BanyanDB has three main data types:

| Type | Purpose | Example |
|------|---------|---------|
| **Measure** | Time-series metrics | `service_cpm_minute`, `endpoint_resp_time` |
| **Stream** | High-throughput events | Traces (`segment`), Logs |
| **Property** | Schema-less documents | Service metadata, configurations |

### Hierarchy
```
Group (e.g., measure-minute, stream-segment)
  └── Measure/Stream/Property
        └── Data Points/Elements
```

---

## 1. Schema Discovery

> **Docs**:
> - [Group Schema](https://skywalking.apache.org/docs/skywalking-banyandb/next/interacting/bydbctl/schema/group/)
> - [Measure Schema](https://skywalking.apache.org/docs/skywalking-banyandb/next/interacting/bydbctl/schema/measure/)
> - [Stream Schema](https://skywalking.apache.org/docs/skywalking-banyandb/next/interacting/bydbctl/schema/stream/)

### List All Groups
```bash
bydbctl group list
```

### Get Group Details
```bash
bydbctl group get -g measure-minute
```

### List Measures in a Group
```bash
bydbctl measure list -g measure-minute
```

### Get Measure Schema
```bash
bydbctl measure get -g measure-minute -n service_cpm_minute
```

Example output:
```yaml
measure:
  entity:
    tagNames:
    - entity_id
  fields:
  - name: value
    fieldType: FIELD_TYPE_INT
  - name: total
    fieldType: FIELD_TYPE_INT
  interval: 1m
  metadata:
    group: measure-minute
    name: service_cpm_minute
  tagFamilies:
  - name: storage-only
    tags:
    - name: entity_id
      type: TAG_TYPE_STRING
```

### List Streams
```bash
bydbctl stream list -g stream-segment
```

### Get Stream Schema
```bash
bydbctl stream get -g stream-segment -n segment
```

---

## 2. Query Measures (Metrics)

> **Docs**: [Query Measures](https://skywalking.apache.org/docs/skywalking-banyandb/next/interacting/bydbctl/query/measure/)

### Time Range Options

| Flag | Format | Example |
|------|--------|---------|
| Absolute | ISO 8601 | `2026-02-25T14:00:00Z` |
| Relative | Duration | `-30m`, `-1h`, `-1d` |

Default: Last 30 minutes if not specified.

### Basic Query - Last 30 Minutes
```bash
bydbctl measure query --start -30m -f - <<EOF
name: "service_cpm_minute"
groups: ["measure-minute"]
tagProjection:
  tagFamilies:
    - name: "storage-only"
      tags: ["entity_id"]
fieldProjection:
  names: ["total", "value"]
EOF
```

### Query with Absolute Time Range
```bash
bydbctl measure query -f - <<EOF
name: "service_cpm_minute"
groups: ["measure-minute"]
tagProjection:
  tagFamilies:
    - name: "storage-only"
      tags: ["entity_id"]
fieldProjection:
  names: ["total", "value"]
timeRange:
  begin: 2026-02-25T14:00:00Z
  end: 2026-02-25T15:00:00Z
EOF
```

### Query with Filter
```bash
bydbctl measure query -f - <<EOF
name: "service_cpm_minute"
groups: ["measure-minute"]
tagProjection:
  tagFamilies:
    - name: "storage-only"
      tags: ["entity_id"]
fieldProjection:
  names: ["total", "value"]
criteria:
  condition:
    name: "entity_id"
    op: "BINARY_OP_EQ"
    value:
      str:
        value: "bW9ja19iX3NlcnZpY2U=.1"
EOF
```

### Query with Sorting (Descending)
```bash
bydbctl measure query -f - <<EOF
name: "service_cpm_minute"
groups: ["measure-minute"]
tagProjection:
  tagFamilies:
    - name: "storage-only"
      tags: ["entity_id"]
fieldProjection:
  names: ["total", "value"]
orderBy:
  sort: "SORT_DESC"
EOF
```

### Query with Limit
```bash
bydbctl measure query -f - <<EOF
name: "service_cpm_minute"
groups: ["measure-minute"]
tagProjection:
  tagFamilies:
    - name: "storage-only"
      tags: ["entity_id"]
fieldProjection:
  names: ["total", "value"]
orderBy:
  sort: "SORT_DESC"
limit: 10
offset: 0
EOF
```

### Aggregation - MAX
```bash
bydbctl measure query -f - <<EOF
name: "service_cpm_minute"
groups: ["measure-minute"]
tagProjection:
  tagFamilies:
    - name: "storage-only"
      tags: ["entity_id"]
fieldProjection:
  names: ["total", "value"]
groupBy:
  tagProjection:
    tagFamilies:
    - name: "storage-only"
      tags: ["entity_id"]
  fieldName: "value"
agg:
  function: "AGGREGATION_FUNCTION_MAX"
  fieldName: "value"
EOF
```

### Aggregation - TopN
```bash
bydbctl measure query -f - <<EOF
name: "service_cpm_minute"
groups: ["measure-minute"]
tagProjection:
  tagFamilies:
    - name: "storage-only"
      tags: ["entity_id"]
fieldProjection:
  names: ["value"]
groupBy:
  tagProjection:
    tagFamilies:
    - name: "storage-only"
      tags: ["entity_id"]
  fieldName: "value"
agg:
  function: "AGGREGATION_FUNCTION_MEAN"
  fieldName: "value"
top:
  number: 10
  fieldName: "value"
  fieldValueSort: "SORT_DESC"
EOF
```

---

## 3. Query Streams (Traces/Logs)

> **Docs**: [Query Streams](https://skywalking.apache.org/docs/skywalking-banyandb/next/interacting/bydbctl/query/stream/)

### Query Trace Segments - Last 30 Minutes
```bash
bydbctl stream query --start -30m -f - <<EOF
groups: ["stream-segment"]
name: "segment"
projection:
  tagFamilies:
    - name: "searchable"
      tags: ["trace_id", "segment_id", "latency"]
EOF
```

### Query with Time Range
```bash
bydbctl stream query -f - <<EOF
groups: ["stream-segment"]
name: "segment"
projection:
  tagFamilies:
    - name: "searchable"
      tags: ["trace_id", "latency"]
    - name: "storage-only"
      tags: ["start_time", "data_binary"]
timeRange:
  begin: 2026-02-25T14:00:00Z
  end: 2026-02-25T15:00:00Z
EOF
```

### Query by Service ID
```bash
bydbctl stream query -f - <<EOF
name: "segment"
groups: ["stream-segment"]
projection:
  tagFamilies:
    - name: "searchable"
      tags: ["service_id", "trace_id", "latency"]
criteria:
  condition:
    name: "service_id"
    op: "BINARY_OP_EQ"
    value:
      str:
        value: "<SERVICE_ID_BASE64>"
EOF
```

### Query by Trace ID
```bash
bydbctl stream query -f - <<EOF
name: "segment"
groups: ["stream-segment"]
projection:
  tagFamilies:
    - name: "searchable"
      tags: ["trace_id", "segment_id", "latency", "endpoint_id"]
    - name: "storage-only"
      tags: ["data_binary"]
criteria:
  condition:
    name: "trace_id"
    op: "BINARY_OP_EQ"
    value:
      str:
        value: "<TRACE_ID>"
EOF
```

### Query Ordered by Latency (Slowest First)
```bash
bydbctl stream query -f - <<EOF
name: "segment"
groups: ["stream-segment"]
projection:
  tagFamilies:
    - name: "searchable"
      tags: ["trace_id", "latency"]
orderBy:
  indexRuleName: "latency"
  sort: "SORT_DESC"
limit: 20
EOF
```

### Query Error Traces
```bash
bydbctl stream query -f - <<EOF
name: "segment"
groups: ["stream-segment"]
projection:
  tagFamilies:
    - name: "searchable"
      tags: ["trace_id", "latency"]
    - name: "storage-only"
      tags: ["is_error"]
criteria:
  condition:
    name: "is_error"
    op: "BINARY_OP_EQ"
    value:
      int:
        value: 1
EOF
```

---

## 4. Filter Operations

> **Docs**: [Filter Operations](https://skywalking.apache.org/docs/skywalking-banyandb/next/interacting/bydbctl/query/filter-operation/)

### Binary Operators

| Operator | Description |
|----------|-------------|
| `BINARY_OP_EQ` | Equal |
| `BINARY_OP_NE` | Not equal |
| `BINARY_OP_LT` | Less than |
| `BINARY_OP_GT` | Greater than |
| `BINARY_OP_LE` | Less than or equal |
| `BINARY_OP_GE` | Greater than or equal |
| `BINARY_OP_IN` | In array |
| `BINARY_OP_NOT_IN` | Not in array |
| `BINARY_OP_HAVING` | Contains all values |
| `BINARY_OP_NOT_HAVING` | Does not contain |
| `BINARY_OP_MATCH` | Full-text search |

### Equal Filter
```yaml
criteria:
  condition:
    name: "entity_id"
    op: "BINARY_OP_EQ"
    value:
      str:
        value: "entity_1"
```

### IN Filter (Multiple Values)
```yaml
criteria:
  condition:
    name: "entity_id"
    op: "BINARY_OP_IN"
    value:
      str_array:
        value: ["entity_1", "entity_2", "entity_3"]
```

### Greater Than Filter
```yaml
criteria:
  condition:
    name: "latency"
    op: "BINARY_OP_GT"
    value:
      int:
        value: 1000
```

### Full-Text Match
```yaml
criteria:
  condition:
    name: "name"
    op: "BINARY_OP_MATCH"
    value:
      str:
        value: "service"
    match_option:
      analyzer: "url"
      operator: "OPERATOR_AND"
```

### Logical AND
```yaml
criteria:
  le:
    op: "LOGICAL_OP_AND"
    left:
      condition:
        name: "service_id"
        op: "BINARY_OP_EQ"
        value:
          str:
            value: "service_1"
    right:
      condition:
        name: "latency"
        op: "BINARY_OP_GT"
        value:
          int:
            value: 500
```

### Logical OR
```yaml
criteria:
  le:
    op: "LOGICAL_OP_OR"
    left:
      condition:
        name: "is_error"
        op: "BINARY_OP_EQ"
        value:
          int:
            value: 1
    right:
      condition:
        name: "latency"
        op: "BINARY_OP_GT"
        value:
          int:
            value: 5000
```

---

## 5. Query Properties

> **Docs**: [Property Operations](https://skywalking.apache.org/docs/skywalking-banyandb/next/interacting/bydbctl/property/)

### List Properties in Group
```bash
bydbctl property query -f - <<EOF
groups: ["sw"]
EOF
```

### Query by Container Name
```bash
bydbctl property query -f - <<EOF
groups: ["sw"]
name: temp_data
EOF
```

### Query with Filter
```bash
bydbctl property query -f - <<EOF
groups: ["sw"]
criteria:
  condition:
    name: "state"
    op: "BINARY_OP_EQ"
    value:
      str:
        value: "succeed"
EOF
```

### Query with Limit and Projection
```bash
bydbctl property query -f - <<EOF
groups: ["sw"]
tag_projection: ["name", "state"]
limit: 10
EOF
```

---

## 6. HTTP API Access

> **Docs**: [Client APIs](https://skywalking.apache.org/docs/skywalking-banyandb/next/interacting/client/)

BanyanDB exposes HTTP endpoints at `http://localhost:17913/api`.

### Query Measure via HTTP
```bash
curl -X POST http://localhost:17913/api/v1/measure/query \
  -H "Content-Type: application/json" \
  -d '{
    "name": "service_cpm_minute",
    "groups": ["measure-minute"],
    "tagProjection": {
      "tagFamilies": [{
        "name": "storage-only",
        "tags": ["entity_id"]
      }]
    },
    "fieldProjection": {
      "names": ["value", "total"]
    },
    "timeRange": {
      "begin": "2026-02-25T14:00:00Z",
      "end": "2026-02-25T15:00:00Z"
    }
  }'
```

### Query Stream via HTTP
```bash
curl -X POST http://localhost:17913/api/v1/stream/query \
  -H "Content-Type: application/json" \
  -d '{
    "name": "segment",
    "groups": ["stream-segment"],
    "projection": {
      "tagFamilies": [{
        "name": "searchable",
        "tags": ["trace_id", "latency"]
      }]
    },
    "limit": 10
  }'
```

---

## 7. Web UI

> **Docs**: [Web UI Dashboard](https://skywalking.apache.org/docs/skywalking-banyandb/next/interacting/web-ui/dashboard/)

Access the BanyanDB Web UI at: `http://localhost:17913`

Features:
- Schema browser (Groups, Measures, Streams)
- Query builder
- Data visualization
- Index rule management

---

## 8. Common SkyWalking Data Groups

| Group | Type | Contains |
|-------|------|----------|
| `measure-minute` | Measure | Per-minute metrics (CPM, response time) |
| `measure-hour` | Measure | Hourly aggregated metrics |
| `measure-day` | Measure | Daily aggregated metrics |
| `stream-segment` | Stream | Trace segments |
| `stream-log` | Stream | Application logs |
| `sw` | Property | Service/instance metadata |

---

## 9. Aggregation Functions

| Function | Description |
|----------|-------------|
| `AGGREGATION_FUNCTION_MIN` | Minimum value |
| `AGGREGATION_FUNCTION_MAX` | Maximum value |
| `AGGREGATION_FUNCTION_MEAN` | Average value |
| `AGGREGATION_FUNCTION_COUNT` | Count of records |
| `AGGREGATION_FUNCTION_SUM` | Sum of values |

---

## 10. TopN Aggregation

> **Docs**: [TopN Aggregation](https://skywalking.apache.org/docs/skywalking-banyandb/next/interacting/bydbctl/schema/top-n-aggregation/)

Query pre-calculated TopN results:
```bash
bydbctl measure query -f - <<EOF
name: "endpoint_cpm_minute_top_bottom"
groups: ["measure-minute"]
tagProjection:
  tagFamilies:
    - name: "storage-only"
      tags: ["entity_id"]
fieldProjection:
  names: ["value"]
top:
  number: 10
  fieldName: "value"
  fieldValueSort: "SORT_DESC"
EOF
```

---

## References

| Topic | Documentation Link |
|-------|-------------------|
| BanyanDB Overview | https://skywalking.apache.org/docs/skywalking-banyandb/next/readme/ |
| Data Model | https://skywalking.apache.org/docs/skywalking-banyandb/next/concept/data-model/ |
| bydbctl CLI | https://skywalking.apache.org/docs/skywalking-banyandb/next/interacting/bydbctl/bydbctl/ |
| Query Measures | https://skywalking.apache.org/docs/skywalking-banyandb/next/interacting/bydbctl/query/measure/ |
| Query Streams | https://skywalking.apache.org/docs/skywalking-banyandb/next/interacting/bydbctl/query/stream/ |
| Filter Operations | https://skywalking.apache.org/docs/skywalking-banyandb/next/interacting/bydbctl/query/filter-operation/ |
| Property Operations | https://skywalking.apache.org/docs/skywalking-banyandb/next/interacting/bydbctl/property/ |
| Schema - Group | https://skywalking.apache.org/docs/skywalking-banyandb/next/interacting/bydbctl/schema/group/ |
| Schema - Measure | https://skywalking.apache.org/docs/skywalking-banyandb/next/interacting/bydbctl/schema/measure/ |
| Schema - Stream | https://skywalking.apache.org/docs/skywalking-banyandb/next/interacting/bydbctl/schema/stream/ |
| Schema - Index Rules | https://skywalking.apache.org/docs/skywalking-banyandb/next/interacting/bydbctl/schema/index-rule/ |
| TopN Aggregation | https://skywalking.apache.org/docs/skywalking-banyandb/next/interacting/bydbctl/schema/top-n-aggregation/ |
| Web UI | https://skywalking.apache.org/docs/skywalking-banyandb/next/interacting/web-ui/dashboard/ |
| Client APIs | https://skywalking.apache.org/docs/skywalking-banyandb/next/interacting/client/ |
| Data Lifecycle | https://skywalking.apache.org/docs/skywalking-banyandb/next/interacting/data-lifecycle/ |
| Configuration | https://skywalking.apache.org/docs/skywalking-banyandb/next/operation/configuration/ |
| Troubleshooting | https://skywalking.apache.org/docs/skywalking-banyandb/next/operation/troubleshooting/no-data/ |
| Helm Chart | https://github.com/apache/skywalking-banyandb-helm |
| Proto Definitions | https://github.com/apache/skywalking-banyandb-client-proto |
