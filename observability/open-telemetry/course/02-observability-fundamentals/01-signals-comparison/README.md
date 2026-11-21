# Lesson 01-signals-comparison — Correlating Traces, Metrics, and Logs

This lesson demonstrates how OpenTelemetry links three distinct signals to a single business transaction:

1. **Trace**: Captures the exact request path and latency with high-cardinality attributes (`cart.value_usd`).
2. **Metric**: Aggregates a counter (`checkout_requests_total`) with low-cardinality dimensions (`status=success`) suitable for dashboards and alerts.
3. **Log**: Records an event containing the active `trace_id` for instant bidirectional search in log aggregators (e.g., Loki).

---

## Running in Python

```bash
cd python
pip install -r requirements.txt
python main.py
```

## Running in Java

```bash
cd java
mvn clean compile exec:java
```
