# Lesson 01-approaches — The API vs. SDK Architectural Boundary

This lesson proves the OpenTelemetry API/SDK split by comparing the exact same instrumentation code running with:

1. **API Only (No SDK)**: Returns a `DefaultTracer`. `is_recording()` returns `False`. The invalid zero-context `00000000000000000000000000000000` is preserved, and zero crashes occur.
2. **Full SDK Registered**: Telemetry is actively processed, enriched with `Resource`, and exported.

---

## Running in Python

```bash
cd python
pip install -r requirements.txt

# Run without SDK (No-Op):
python api_noop.py

# Run with SDK:
python manual_sdk.py
```

---

## Running in Java

```bash
cd java

# Run without SDK (No-Op):
mvn clean compile exec:java -Dexec.mainClass="com.course.ApiNoOp"

# Run with SDK:
mvn compile exec:java -Dexec.mainClass="com.course.ManualSdk"
```
