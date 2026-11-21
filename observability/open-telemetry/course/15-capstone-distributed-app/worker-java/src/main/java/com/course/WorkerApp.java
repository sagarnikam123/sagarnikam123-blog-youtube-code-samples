package com.course;

import com.sun.net.httpserver.Headers;
import com.sun.net.httpserver.HttpExchange;
import com.sun.net.httpserver.HttpHandler;
import com.sun.net.httpserver.HttpServer;
import io.opentelemetry.api.baggage.Baggage;
import io.opentelemetry.api.baggage.propagation.W3CBaggagePropagator;
import io.opentelemetry.api.common.AttributeKey;
import io.opentelemetry.api.common.Attributes;
import io.opentelemetry.api.metrics.DoubleHistogram;
import io.opentelemetry.api.metrics.Meter;
import io.opentelemetry.api.trace.Span;
import io.opentelemetry.api.trace.SpanKind;
import io.opentelemetry.api.trace.Tracer;
import io.opentelemetry.api.trace.propagation.W3CTraceContextPropagator;
import io.opentelemetry.context.Context;
import io.opentelemetry.context.Scope;
import io.opentelemetry.context.propagation.ContextPropagators;
import io.opentelemetry.context.propagation.TextMapGetter;
import io.opentelemetry.context.propagation.TextMapPropagator;
import io.opentelemetry.exporter.logging.LoggingSpanExporter;
import io.opentelemetry.exporter.otlp.trace.OtlpGrpcSpanExporter;
import io.opentelemetry.sdk.OpenTelemetrySdk;
import io.opentelemetry.sdk.metrics.SdkMeterProvider;
import io.opentelemetry.sdk.resources.Resource;
import io.opentelemetry.sdk.trace.SdkTracerProvider;
import io.opentelemetry.sdk.trace.export.BatchSpanProcessor;
import io.opentelemetry.sdk.trace.export.SimpleSpanProcessor;

import java.io.IOException;
import java.io.OutputStream;
import java.net.InetSocketAddress;

public class WorkerApp {

    private static final TextMapGetter<Headers> GETTER = new TextMapGetter<>() {
        @Override
        public Iterable<String> keys(Headers carrier) {
            return carrier.keySet();
        }

        @Override
        public String get(Headers carrier, String key) {
            return carrier.getFirst(key);
        }
    };

    public static void main(String[] args) throws IOException {
        int port = 8090;

        Resource resource = Resource.getDefault().merge(
            Resource.create(Attributes.of(AttributeKey.stringKey("service.name"), "worker-service-java"))
        );

        TextMapPropagator propagator = TextMapPropagator.composite(
            W3CTraceContextPropagator.getInstance(),
            W3CBaggagePropagator.getInstance()
        );

        String otlpEndpoint = System.getenv().getOrDefault("OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:4317");
        OtlpGrpcSpanExporter otlpExporter = OtlpGrpcSpanExporter.builder().setEndpoint(otlpEndpoint).build();

        SdkTracerProvider tracerProvider = SdkTracerProvider.builder()
            .setResource(resource)
            .addSpanProcessor(SimpleSpanProcessor.create(LoggingSpanExporter.create()))
            .addSpanProcessor(BatchSpanProcessor.builder(otlpExporter).build())
            .build();

        SdkMeterProvider meterProvider = SdkMeterProvider.builder().setResource(resource).build();

        OpenTelemetrySdk sdk = OpenTelemetrySdk.builder()
            .setTracerProvider(tracerProvider)
            .setMeterProvider(meterProvider)
            .setPropagators(ContextPropagators.create(propagator))
            .buildAndRegisterGlobal();

        Tracer tracer = sdk.getTracer("worker-tracer");
        Meter meter = sdk.getMeter("worker-meter");
        DoubleHistogram paymentLatency = meter.histogramBuilder("payment_duration_seconds")
            .setDescription("Payment processing duration")
            .setUnit("s")
            .build();

        HttpServer server = HttpServer.create(new InetSocketAddress(port), 0);

        server.createContext("/process-payment", new HttpHandler() {
            @Override
            public void handle(HttpExchange exchange) throws IOException {
                long startTime = System.currentTimeMillis();

                // 1. Extract context from inbound headers
                Context extractedContext = propagator.extract(Context.current(), exchange.getRequestHeaders(), GETTER);
                Baggage baggage = Baggage.fromContext(extractedContext);

                // 2. Start child span linked to parent
                Span span = tracer.spanBuilder("process-payment")
                    .setParent(extractedContext)
                    .setSpanKind(SpanKind.SERVER)
                    .startSpan();

                try (Scope scope = span.makeCurrent()) {
                    String tenantId = baggage.getEntryValue("tenant.id");
                    if (tenantId == null) tenantId = "unknown";

                    span.setAttribute("tenant.id", tenantId);
                    span.setAttribute("payment.processor", "stripe_gateway");

                    // Correlated log
                    System.out.printf("[WORKER LOG] [trace_id=%s] Processed payment for tenant=%s\n",
                        span.getSpanContext().getTraceId(), tenantId);

                    long durationMs = System.currentTimeMillis() - startTime;
                    paymentLatency.record(durationMs / 1000.0, Attributes.of(AttributeKey.stringKey("tenant.id"), tenantId));

                    String response = "{\"status\": \"payment_settled\", \"tenant\": \"" + tenantId + "\"}";
                    exchange.getResponseHeaders().set("Content-Type", "application/json");
                    exchange.sendResponseHeaders(200, response.getBytes().length);
                    try (OutputStream os = exchange.getResponseBody()) {
                        os.write(response.getBytes());
                    }
                } finally {
                    span.end();
                }
            }
        });

        System.out.println("Payment Worker running on http://0.0.0.0:" + port + "...");
        server.start();
    }
}
