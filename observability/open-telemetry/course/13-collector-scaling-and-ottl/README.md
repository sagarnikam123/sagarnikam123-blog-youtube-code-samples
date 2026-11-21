# Module 13 — Collector Scaling, OTTL & Tail Sampling

> **OTCA Exam Alignment:** Domain 3 — OpenTelemetry Collector (26% Exam Weight)

---

## 1. OpenTelemetry Transformation Language (OTTL)

**OTTL** is a domain-specific language designed for transforming, filtering, and masking telemetry directly within the OpenTelemetry Collector's `transform` processor.

```text
┌─────────────────────────────────────────────────────────────┐
│                    OTTL Pipeline Processing                 │
│                                                             │
│   Context: span                                             │
│   Statements:                                               │
│     1. set(attributes["env"], "production")                 │
│     2. replace_pattern(attributes["url.full"],              │
│            "token=[^&]+", "token=REDACTED")                │
│     3. delete_key(attributes, "http.request.headers.cookie")│
└─────────────────────────────────────────────────────────────┘
```

### Context Targets in OTTL

OTTL statements specify an execution **context**:

- `resource`: attributes describing the host/service (`resource.attributes["service.name"]`).
- `span`: attributes and fields of a trace span (`attributes["http.status_code"]`, `name`).
- `metric` / `datapoint`: metric attributes and values.
- `log`: log body, severity, and attributes (`body`, `attributes["user.id"]`).

### Essential OTTL Functions

| Function | Usage | Description |
| ---------- | ------- | ------------- |
| `set(target, value)` | `set(attributes["env"], "prod")` | Adds or overwrites a field/attribute. |
| `replace_pattern(target, regex, replacement)` | `replace_pattern(attributes["url.full"], "key=[^&]+", "key=REDACTED")` | Regex scrubbing (PII / secrets). |
| `delete_key(map, key)` | `delete_key(attributes, "credit_card")` | Drops an unwanted high-cardinality key. |
| `truncate_all(map, limit)` | `truncate_all(attributes, 255)` | Truncates long string values to prevent memory spikes. |

---

## 2. Tail-Based Sampling in the Collector

Unlike Head-based sampling (which decides at the beginning of a trace), **Tail-Based Sampling** buffers spans in memory until the entire trace finishes.

### Why Tail Sampling Is Powerful

- **Keep 100% of Errors:** Sample all traces containing `http.response.status_code >= 500` or exceptions.
- **Keep 100% of Slow Requests:** Sample all traces where total latency > 1,500ms.
- **Keep 1% of Normal Traffic:** Sample a representative 1% sample of fast `200 OK` requests.

### Configuration Example

```yaml
processors:
  tail_sampling:
    decision_wait: 10s
    num_traces: 10000
    expected_new_traces_per_sec: 2000
    policies:
      # Policy 1: Always keep errors
      - name: sample-errors
        type: numeric_attribute
        numeric_attribute:
          key: http.response.status_code
          min_value: 500
          max_value: 599
      # Policy 2: Always keep slow traces
      - name: sample-latency
        type: latency
        latency:
          threshold_ms: 1000
      # Policy 3: 5% of everything else
      - name: sample-probabilistic
        type: probabilistic
        probabilistic:
          sampling_percentage: 5.0
```

---

## 3. The Load-Balancing Exporter (`loadbalancing`)

> [!IMPORTANT]
> **OTCA Exam Focus: Solving the Distributed Tail Sampling Dilemma**
> If you have 3 Gateway Collector instances, Service A's span might land on Gateway 1, while Service B's child span lands on Gateway 2. If Gateway 1 and Gateway 2 only see partial traces, tail sampling decisions will fail!
>
> **The Solution:** A tier-1 Collector uses the **`loadbalancing` exporter** with `routing_key: "trace_id"`. The exporter hashes the 128-bit Trace ID so that **all spans belonging to the same trace are consistently routed to the exact same Gateway instance**.

---

## 4. Official Documentation Links

- [OTTL Specification & Syntax Reference](https://github.com/open-telemetry/opentelemetry-collector-contrib/tree/main/pkg/ottl)
- [Transform Processor Documentation](https://github.com/open-telemetry/opentelemetry-collector-contrib/tree/main/processor/transformprocessor)
- [Tail Sampling Processor Documentation](https://github.com/open-telemetry/opentelemetry-collector-contrib/tree/main/processor/tailsamplingprocessor)
- [Load-Balancing Exporter](https://github.com/open-telemetry/opentelemetry-collector-contrib/tree/main/exporter/loadbalancingexporter)

---

## 5. Module Exercises & Challenge

| Sub-Lesson | Language | Goal | Run Command |
|------------|----------|------|-------------|
| [`01-ottl-transform`](./01-ottl-transform/) | YAML / Docker | Run a Collector with OTTL expressions masking secrets and promoting resource attributes | `docker compose up` |
| [`challenge`](./challenge/) | YAML | **Hands-on Challenge:** Implement an OTTL rule that scrubs SSNs and drops `/health` probe traces | *(See challenge README)* |
