# Challenge — Custom Latency Bucketing with Metric Views

## The Scenario

Your payment processing microservice records payment duration using a standard `Histogram`:
`payment_latency_seconds`

By default, the OpenTelemetry SDK generates default exponential or wide buckets (e.g. `[0.0, 5.0, 10.0, 25.0, 50.0, 75.0, 100.0, 250.0, 500.0, 1000.0]`).
However, your SLA requires strict monitoring in sub-second ranges:
`[0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0]`

Furthermore, a legacy developer attached a high-cardinality attribute `card_last_four` to the payment metric, which threatens to blow up Prometheus memory cardinality limits.

---

## Your Mission

Configure the SDK using a **Metric View** (in Python or Java) that achieves:

### Requirements

1. Matches instrument name `"payment_latency_seconds"`.
2. Replaces the default bucket boundaries with explicit boundaries:
   `[0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0]`.
3. Filters / drops the `card_last_four` attribute from the aggregated output while retaining `payment_gateway` and `status`.
4. Emits 10 sample data points with varying latencies.

### Verification

- Inspect the exported histogram metrics.
- Verify the exported buckets match the custom boundaries.
- Verify `card_last_four` is **NOT** present in the exported attributes.
