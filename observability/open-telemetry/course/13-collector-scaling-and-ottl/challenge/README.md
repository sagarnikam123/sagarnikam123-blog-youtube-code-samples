# Challenge — PII Redaction & Noise Filtering with OTTL

## The Scenario

Your security compliance audit flagged that:

1. Legacy checkout spans occasionally include an attribute `payment.card_number` containing unmasked credit card digits.
2. Inbound requests to `/healthz` and `/ready` flood your tracing backend with 15,000 useless spans per minute.

---

## Your Mission

Write an OpenTelemetry Collector configuration using the `transform` and/or `filter` processors that satisfies:

### Requirements

1. **PII Scrubbing with OTTL:**
   - Any span attribute named `payment.card_number` must be masked so that only the last 4 digits remain visible, prefixed by `XXXX-XXXX-XXXX-` (e.g. `XXXX-XXXX-XXXX-4123`).
   - If an attribute `db.statement` contains `password=[^&]+`, replace the password with `password=REDACTED`.
2. **Health Check Noise Filtering:**
   - Drop all traces where `url.path == "/healthz"` or `url.path == "/ready"`.
3. **Attribute Promotion:**
   - Promote span attribute `cloud.zone` to a top-level `resource.attributes["cloud.zone"]`.

### Verification

- Validate configuration syntax using the Collector container:

  ```bash
  docker run --rm -v $(pwd)/config.yaml:/etc/otelcol/config.yaml \
    otel/opentelemetry-collector-contrib:0.160.0 \
    validate --config=/etc/otelcol/config.yaml
  ```

- Send a test span carrying a raw credit card number and verify in the debug log that only the masked version is printed.
