# Lesson 01-log-correlation — Trace-Log Correlation

In this lesson, you will configure an OpenTelemetry `LoggerProvider` and verify that log lines emitted within an active span automatically inherit the `trace_id` and `span_id`.

---

## What Is Validated

1. **Active Context Inheritance**: The log record emitted inside a span scope captures the exact active 16-byte `trace_id` and 8-byte `span_id`.
2. **Standard Log Data Model**: Validates severity mapping (`INFO` -> `SeverityNumber: 9`), log body payload, and custom log attributes (`payment.id`).
3. **Decoupled Application Logging**: Developers call familiar logger APIs while the OpenTelemetry bridge enriches the stream behind the scenes.

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
mvn clean test
```
