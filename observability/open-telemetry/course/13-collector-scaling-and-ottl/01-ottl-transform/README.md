# Lesson 01-ottl-transform — In-Flight Transformations with OTTL

This lesson demonstrates using the OpenTelemetry Transformation Language (OTTL) inside the `transform` processor to:

1. Mask sensitive query strings (`password=REDACTED`) using regex replacement.
2. Scrub unwanted sensitive span attributes (`auth.bearer_token`).
3. Promote span attributes to the top-level `Resource` (`resource.attributes["cloud.region"]`).

---

## Running the Collector

```bash
docker compose up -d
docker compose logs -f collector
```

Send a trace with `auth.bearer_token` and `password=secret` to `http://localhost:4318/v1/traces` and observe the redacted output in the Collector's debug logs!
