# Lesson 01-propagation — Cross-Service Context & Baggage Propagation

This lesson demonstrates how distributed trace continuity and baggage propagation operate across service boundaries.

---

## Key Steps Demonstrated

1. **Composite Propagator:** Combining `W3CTraceContextPropagator` and `W3CBaggagePropagator`.
2. **Context Injection:** Serializing trace ID, span ID, trace flags, and baggage into an outbound HTTP carrier (`traceparent` and `baggage` headers).
3. **Context Extraction:** Restoring the parent Context in the downstream server.
4. **Baggage Promotion:** Promoting cross-cutting baggage (`tenant.id`) to a searchable span attribute.

---

## Running in Python

```bash
cd python
pip install -r requirements.txt
python client_server_demo.py
```

## Running in Java

```bash
cd java
mvn clean test
```
