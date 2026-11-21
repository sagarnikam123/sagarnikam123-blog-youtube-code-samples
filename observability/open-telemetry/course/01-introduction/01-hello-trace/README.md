# Lesson 01-hello-trace — Your First OpenTelemetry Span

In this lesson, you will configure an OpenTelemetry `TracerProvider`, assign standard resource attributes, emit a trace with span attributes and an in-span event, and export it to both the console (for immediate feedback) and OTLP (for ingestion by Collector/Jaeger).

---

## What This Code Demonstrates

1. **`Resource` creation**: Standard key-value pairs (`service.name`, `service.version`) identifying the entity producing telemetry.
2. **`TracerProvider`**: The central factory that manages Tracer instances and pipeline configuration.
3. **`SpanProcessor`**:
   - `SimpleSpanProcessor`: Synchronous; passes every span immediately to an exporter (ideal for CLI/debugging/local testing).
   - `BatchSpanProcessor`: Asynchronous; batches spans in memory and exports periodically (mandatory for production).
4. **`Span` lifecycle**: Starting a span, setting modern semantic attributes, recording a point-in-time timestamped event, and calling `span.end()`.
5. **Clean `shutdown()`**: Ensuring any in-flight spans in memory buffers are flushed before process exit.

---

## Running the Python Example

```bash
cd python

# 1. (Optional) Create virtual environment
python3 -m venv .venv && source .venv/bin/activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run the script
python main.py
```

**Expected Console Output:**
You will see JSON representing the span attributes, timestamps, and event details printed directly in your terminal, followed by export confirmation.

---

## Running the Java Example

```bash
cd java

# Compile and run via Maven
mvn clean compile exec:java
```

---

## Viewing in Jaeger

If you started the Docker stack in `stack/docker/` (`docker compose up -d`):

1. Open your browser to [http://localhost:16686](http://localhost:16686).
2. Under **Service**, select `hello-service-py` or `hello-service-java`.
3. Click **Find Traces** to view your distributed trace, duration waterfall, and attributes.
