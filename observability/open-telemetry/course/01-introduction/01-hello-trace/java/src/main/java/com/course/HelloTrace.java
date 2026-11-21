package com.course;

import io.opentelemetry.api.GlobalOpenTelemetry;
import io.opentelemetry.api.common.AttributeKey;
import io.opentelemetry.api.common.Attributes;
import io.opentelemetry.api.trace.Span;
import io.opentelemetry.api.trace.Tracer;
import io.opentelemetry.exporter.logging.LoggingSpanExporter;
import io.opentelemetry.exporter.otlp.trace.OtlpGrpcSpanExporter;
import io.opentelemetry.sdk.OpenTelemetrySdk;
import io.opentelemetry.sdk.resources.Resource;
import io.opentelemetry.sdk.trace.SdkTracerProvider;
import io.opentelemetry.sdk.trace.export.BatchSpanProcessor;
import io.opentelemetry.sdk.trace.export.SimpleSpanProcessor;

public class HelloTrace {

    public static void main(String[] args) throws InterruptedException {
        // 1. Define standard resource attributes identifying this Java service
        Resource resource = Resource.getDefault().merge(
            Resource.create(
                Attributes.builder()
                    .put(AttributeKey.stringKey("service.name"), "hello-service-java")
                    .put(AttributeKey.stringKey("service.version"), "1.0.0")
                    .put(AttributeKey.stringKey("deployment.environment"), "development")
                    .build()
            )
        );

        // 2. Setup Exporters: Console/Logging and OTLP gRPC
        LoggingSpanExporter loggingExporter = LoggingSpanExporter.create();
        
        String otlpEndpoint = System.getenv().getOrDefault("OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:4317");
        OtlpGrpcSpanExporter otlpExporter = OtlpGrpcSpanExporter.builder()
            .setEndpoint(otlpEndpoint)
            .build();

        // 3. Build SDK TracerProvider
        SdkTracerProvider tracerProvider = SdkTracerProvider.builder()
            .setResource(resource)
            .addSpanProcessor(SimpleSpanProcessor.create(loggingExporter))
            .addSpanProcessor(BatchSpanProcessor.builder(otlpExporter).build())
            .build();

        // 4. Register OpenTelemetrySdk as Global
        OpenTelemetrySdk openTelemetry = OpenTelemetrySdk.builder()
            .setTracerProvider(tracerProvider)
            .buildAndRegisterGlobal();

        Tracer tracer = openTelemetry.getTracer("hello-tracer-java", "1.0.0");

        System.out.println("\n--- Emitting Java OpenTelemetry Span ---");
        Span span = tracer.spanBuilder("hello-operation-java").startSpan();
        try {
            // Set modern semantic attributes
            span.setAttribute("http.request.method", "GET");
            span.setAttribute("course.module", "01-introduction");
            span.setAttribute("lesson.title", "hello-trace");

            Thread.sleep(50);

            span.addEvent("work_completed", Attributes.of(AttributeKey.longKey("items_processed"), 42L));
            System.out.println("Span executed: Trace ID = " + span.getSpanContext().getTraceId());
        } finally {
            span.end();
        }

        // Flush and shutdown SDK cleanly
        tracerProvider.shutdown();
        System.out.println("--- Java span successfully exported! ---\n");
        System.exit(0);
    }
}
