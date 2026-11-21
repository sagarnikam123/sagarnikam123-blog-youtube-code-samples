import os
import json
import logging
from http.server import HTTPServer, BaseHTTPRequestHandler
import urllib.request
from opentelemetry import trace, metrics, baggage, propagate
from opentelemetry.trace import SpanKind
from opentelemetry.trace.propagation.tracecontext import TraceContextTextMapPropagator
from opentelemetry.baggage.propagation import W3CBaggagePropagator
from opentelemetry.propagators.composite import CompositePropagator
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter, SimpleSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter as OTLPGrpcSpanExporter
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader, ConsoleMetricExporter
from opentelemetry.sdk.resources import Resource

# 1. Telemetry Setup
resource = Resource.create({"service.name": "frontend-service-py", "service.version": "1.0.0"})

# Propagator
propagate.set_global_textmap(CompositePropagator([TraceContextTextMapPropagator(), W3CBaggagePropagator()]))

# Tracer
tracer_provider = TracerProvider(resource=resource)
tracer_provider.add_span_processor(SimpleSpanProcessor(ConsoleSpanExporter()))
otlp_endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:4317")
try:
    tracer_provider.add_span_processor(BatchSpanProcessor(OTLPGrpcSpanExporter(endpoint=otlp_endpoint, insecure=True)))
except Exception as e:
    print(f"OTLP trace warning: {e}")
trace.set_tracer_provider(tracer_provider)
tracer = trace.get_tracer("frontend-tracer")

# Metrics
metric_reader = PeriodicExportingMetricReader(ConsoleMetricExporter(), export_interval_millis=10000)
meter_provider = MeterProvider(resource=resource, metric_readers=[metric_reader])
metrics.set_meter_provider(meter_provider)
meter = metrics.get_meter("frontend-meter")
checkout_counter = meter.create_counter("frontend_checkout_requests_total", description="Total checkouts", unit="1")

# Logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] [trace_id=%(trace_id)s] %(message)s")
logger = logging.getLogger("frontend")

WORKER_URL = os.getenv("WORKER_URL", "http://localhost:8090/process-payment")

class FrontendHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        if self.path == "/checkout":
            with tracer.start_as_current_span("POST /checkout", kind=SpanKind.SERVER) as span:
                ctx = span.get_span_context()
                trace_id_hex = trace.format_trace_id(ctx.trace_id)

                span.set_attribute("http.request.method", "POST")
                span.set_attribute("url.path", "/checkout")
                span.set_attribute("server.port", 8000)

                # Set Baggage
                tenant_id = self.headers.get("X-Tenant-Id", "enterprise-corp")
                active_ctx = baggage.set_baggage("tenant.id", tenant_id)

                logger.info(f"Received checkout request for tenant={tenant_id}", extra={"trace_id": trace_id_hex})
                checkout_counter.add(1, {"http.response.status_code": 200, "tenant": tenant_id})

                # Inject Context into outbound HTTP headers to Worker
                carrier = {}
                propagate.inject(carrier, context=active_ctx)

                worker_status = 200
                try:
                    req = urllib.request.Request(WORKER_URL, data=b"{}", headers=carrier, method="POST")
                    with urllib.request.urlopen(req, timeout=3) as resp:
                        worker_status = resp.status
                except Exception as ex:
                    logger.warning(f"Worker downstream call noted (simulated or offline): {ex}", extra={"trace_id": trace_id_hex})

                span.set_attribute("http.response.status_code", 200)

                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                resp_payload = {
                    "status": "order_confirmed",
                    "trace_id": trace_id_hex,
                    "tenant_id": tenant_id,
                    "worker_status": worker_status
                }
                self.wfile.write(json.dumps(resp_payload).encode("utf-8"))
        else:
            self.send_response(404)
            self.end_headers()

def run(port=8000):
    server = HTTPServer(("0.0.0.0", port), FrontendHandler)
    print(f"Frontend Service running on http://0.0.0.0:{port}...")
    server.serve_forever()

if __name__ == "__main__":
    run()
