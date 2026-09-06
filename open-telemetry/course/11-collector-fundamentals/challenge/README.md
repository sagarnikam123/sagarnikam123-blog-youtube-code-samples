# Challenge — Multi-Pipeline Collector with Metrics Scraping

## The Scenario

Your organization has legacy services exposing standard Prometheus `/metrics` endpoints, alongside modern services emitting OTLP gRPC telemetry.

You must configure an OpenTelemetry Collector that:

1. Receives OTLP Traces and Metrics on `0.0.0.0:4317`.
2. Scrapes a local Prometheus metrics endpoint every 10 seconds.
3. Protects the Collector from OOM crashes using the `memory_limiter` processor.
4. Batches telemetry with a send batch size of `512`.
5. Exposes a health check extension on port `13133`.
6. Exports all traces and scraped metrics to the `debug` exporter with detailed verbosity.

---

## Your Mission

Create a valid OpenTelemetry Collector configuration file (`otel-collector.yaml`) meeting all specifications above.

### Verification Steps

```bash
# Validate your configuration using docker and the collector binary
docker run --rm -v $(pwd)/otel-collector.yaml:/etc/otelcol/config.yaml \
  otel/opentelemetry-collector-contrib:0.160.0 \
  validate --config=/etc/otelcol/config.yaml
```

- If the configuration is valid, the command exits with return code 0.
- If invalid or if processor order is reversed, the validator reports the syntax or schema error.
