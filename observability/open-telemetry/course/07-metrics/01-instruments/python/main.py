from opentelemetry import metrics
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import InMemoryMetricReader
from opentelemetry.sdk.resources import Resource
from opentelemetry.metrics import CallbackOptions, Observation

# Simulated system state for ObservableGauge
CURRENT_HEAP_USAGE_MB = 256.5

def heap_callback(options: CallbackOptions):
    yield Observation(CURRENT_HEAP_USAGE_MB, {"memory.type": "heap"})

def main():
    reader = InMemoryMetricReader()
    provider = MeterProvider(resource=Resource.create({"service.name": "metrics-demo"}), metric_readers=[reader])
    metrics.set_meter_provider(provider)
    meter = metrics.get_meter("course-meter", "1.0.0")

    # 1. Monotonic Counter (e.g. requests count)
    request_counter = meter.create_counter(
        name="http_requests_total",
        description="Total HTTP requests received",
        unit="1"
    )
    request_counter.add(10, {"http.request.method": "GET", "http.response.status_code": 200})
    request_counter.add(2, {"http.request.method": "POST", "http.response.status_code": 500})

    # 2. UpDownCounter (e.g. active websocket connections)
    active_connections = meter.create_up_down_counter(
        name="active_connections",
        description="Current live websocket connections",
        unit="1"
    )
    active_connections.add(5)   # 5 connections opened
    active_connections.add(-2)  # 2 connections closed (net = 3)

    # 3. Histogram (e.g. request duration)
    latency_histogram = meter.create_histogram(
        name="http_request_duration_seconds",
        description="Duration of HTTP requests",
        unit="s"
    )
    latency_histogram.record(0.042, {"http.route": "/api/v1/users"})
    latency_histogram.record(0.125, {"http.route": "/api/v1/users"})
    latency_histogram.record(0.850, {"http.route": "/api/v1/checkout"})

    # 4. Asynchronous Observable Gauge (e.g. memory usage)
    meter.create_observable_gauge(
        name="jvm_memory_used_megabytes",
        callbacks=[heap_callback],
        description="Heap memory currently allocated in megabytes",
        unit="By"
    )

    # Collect data from in-memory reader
    data = reader.get_metrics_data()
    metrics_list = data.resource_metrics[0].scope_metrics[0].metrics
    names = [m.name for m in metrics_list]
    print(f"Captured metrics: {names}")

    assert "http_requests_total" in names
    assert "active_connections" in names
    assert "http_request_duration_seconds" in names
    assert "jvm_memory_used_megabytes" in names

    # Verify UpDownCounter value
    conn_metric = [m for m in metrics_list if m.name == "active_connections"][0]
    assert conn_metric.data.data_points[0].value == 3, f"Expected 3, got {conn_metric.data.data_points[0].value}"

    print("SUCCESS: All 4 instrument types generated and validated!")
    provider.shutdown()

if __name__ == "__main__":
    main()
