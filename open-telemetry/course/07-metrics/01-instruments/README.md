# Lesson 01-instruments — Working with OpenTelemetry Metric Instruments

In this lesson, you will configure and record values using the four primary metric instruments:

1. **Counter (`http_requests_total`)**: Monotonically increasing requests counter.
2. **UpDownCounter (`active_connections`)**: Additive gauge that tracks concurrent connections (+5, -2 = 3).
3. **Histogram (`http_request_duration_seconds`)**: Statistical distribution of request latencies.
4. **ObservableGauge (`jvm_memory_used_megabytes`)**: Asynchronous callback reporting instantaneous memory usage.

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
