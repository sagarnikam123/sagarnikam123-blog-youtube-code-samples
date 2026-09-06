# Lesson 01-python-auto — Python Auto-Instrumentation

This sub-lesson demonstrates running an application with **zero** OpenTelemetry code and having OpenTelemetry automatically generate spans, trace IDs, and HTTP attributes.

---

## 1. Inspect `server.py`

Notice that [server.py](./server.py) has zero OpenTelemetry imports or references. It is a standard Python HTTP server.

---

## 2. Run with `opentelemetry-instrument`

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Run wrapped in the OpenTelemetry agent:
opentelemetry-instrument \
    --traces_exporter console \
    --metrics_exporter none \
    --service_name auto-python-service \
    python server.py
```

---

## 3. Trigger HTTP Requests

In a separate terminal:

```bash
curl http://localhost:8085/orders
```

**Result:**
The server terminal immediately prints a complete JSON span with:

- `http.request.method`: `"GET"`
- `url.path`: `"/orders"`
- `http.response.status_code`: `200`
- Generated `trace_id` and `span_id`
Generated entirely through runtime bytecode/monkey-patching!
