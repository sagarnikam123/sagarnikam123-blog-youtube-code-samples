# Challenge — Multi-Hop Context & Baggage Relay

## The Scenario

Your organization has a 3-tier microservice architecture:
`Gateway API` ──► `Order Service` ──► `Payment Worker`

A high-priority enterprise customer identified by `tenant.id = enterprise-corp` reports sporadic timeouts. The SRE team needs the `tenant.id` attribute visible in traces emitted by the downstream `Payment Worker` without changing the database schema or passing custom query parameters through every internal function signature.

---

## Your Mission

Write an end-to-end simulation (in either Python or Java) that satisfies the following requirements:

### Requirements

1. **Gateway API:**
   - Starts a root span (`kind=SERVER`, name `"POST /orders"`).
   - Sets standard W3C Baggage containing `tenant.id = enterprise-corp`.
   - Injects the active context (TraceContext + Baggage) into an HTTP headers carrier dictionary.
2. **Order Service:**
   - Extracts the context from the carrier.
   - Starts a child span with the extracted context as parent.
   - Reads the baggage and verifies `tenant.id` is present.
   - Injects the context into a second outbound carrier targeting the Payment Worker.
3. **Payment Worker:**
   - Extracts the context from the second carrier.
   - Starts a child span.
   - **Crucial Step:** Explicitly copies the `tenant.id` from Baggage into the span's **Span Attributes**.
   - Ends the span.

### Expected Behavior & Verification

- All three spans share the exact same `TraceID`.
- `Order Service` span's `parent_span_id` matches `Gateway API` span's `span_id`.
- `Payment Worker` span's `parent_span_id` matches `Order Service` span's `span_id`.
- The `Payment Worker` finished span has attribute `tenant.id` = `"enterprise-corp"`.
- If an assertion fails, the test suite must fail with a descriptive message.
