from opentelemetry import trace
from opentelemetry.trace import SpanKind, StatusCode
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter
from opentelemetry.sdk.resources import Resource

def test_semantic_conventions():
    # 1. Initialize In-Memory Test Tracer
    memory_exporter = InMemorySpanExporter()
    provider = TracerProvider(resource=Resource.create({"service.name": "order-api"}))
    provider.add_span_processor(SimpleSpanProcessor(memory_exporter))
    tracer = provider.get_tracer("test-tracer", "1.0.0")

    # 2. Simulate Inbound HTTP Server Request
    with tracer.start_as_current_span("GET /api/v1/orders", kind=SpanKind.SERVER) as server_span:
        # Modern stable HTTP conventions (v1.28+)
        server_span.set_attribute("http.request.method", "GET")
        server_span.set_attribute("http.response.status_code", 200)
        server_span.set_attribute("url.path", "/api/v1/orders")
        server_span.set_attribute("server.address", "api.internal")
        server_span.set_attribute("server.port", 8080)
        server_span.set_status(StatusCode.OK)

        # 3. Simulate Downstream Database Client Call
        with tracer.start_as_current_span("SELECT orders", kind=SpanKind.CLIENT) as db_span:
            # Modern Database conventions
            db_span.set_attribute("db.system", "postgresql")
            db_span.set_attribute("db.operation", "SELECT")
            db_span.set_attribute("db.collection.name", "orders")
            db_span.set_attribute("db.namespace", "ecommerce_db")
            db_span.set_status(StatusCode.OK)

    spans = memory_exporter.get_finished_spans()
    assert len(spans) == 2, f"Expected 2 spans, got {len(spans)}"

    db_finished = spans[0]
    http_finished = spans[1]

    # Verify Child -> Parent hierarchy
    assert db_finished.parent.span_id == http_finished.context.span_id

    # Assert modern HTTP attributes
    http_attrs = http_finished.attributes
    assert http_attrs["http.request.method"] == "GET"
    assert http_attrs["http.response.status_code"] == 200
    assert http_attrs["url.path"] == "/api/v1/orders"
    assert http_attrs["server.address"] == "api.internal"
    assert http_attrs["server.port"] == 8080

    # Assert modern DB attributes
    db_attrs = db_finished.attributes
    assert db_attrs["db.system"] == "postgresql"
    assert db_attrs["db.operation"] == "SELECT"
    assert db_attrs["db.collection.name"] == "orders"
    assert db_attrs["db.namespace"] == "ecommerce_db"

    print("SUCCESS: All semantic convention assertions passed!")

if __name__ == "__main__":
    test_semantic_conventions()
