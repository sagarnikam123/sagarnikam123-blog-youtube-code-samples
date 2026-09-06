package com.course;

import io.opentelemetry.api.common.AttributeKey;
import io.opentelemetry.api.common.Attributes;
import io.opentelemetry.api.trace.Span;
import io.opentelemetry.api.trace.Tracer;
import io.opentelemetry.exporter.logging.LoggingSpanExporter;
import io.opentelemetry.sdk.OpenTelemetrySdk;
import io.opentelemetry.sdk.resources.Resource;
import io.opentelemetry.sdk.trace.SdkTracerProvider;
import io.opentelemetry.sdk.trace.export.SimpleSpanProcessor;

public class ManualSdk {

    public static void main(String[] args) {
        System.out.println("=== Running Java with FULL SDK Registered ===");

        Resource resource = Resource.getDefault().merge(
            Resource.create(Attributes.of(AttributeKey.stringKey("service.name"), "order-service"))
        );

        SdkTracerProvider tracerProvider = SdkTracerProvider.builder()
            .setResource(resource)
            .addSpanProcessor(SimpleSpanProcessor.create(LoggingSpanExporter.create()))
            .build();

        OpenTelemetrySdk sdk = OpenTelemetrySdk.builder()
            .setTracerProvider(tracerProvider)
            .buildAndRegisterGlobal();

        Tracer tracer = sdk.getTracer("library-sample", "1.0.0");

        Span span = tracer.spanBuilder("library_operation").startSpan();
        try {
            System.out.println("Span isRecording: " + span.isRecording());
            System.out.println("Is valid span context: " + span.getSpanContext().isValid());
            System.out.println("Trace ID: " + span.getSpanContext().getTraceId());

            span.setAttribute("data.processed", 100L);
            span.addEvent("completed");
        } finally {
            span.end();
        }

        tracerProvider.shutdown();
        System.out.println("=== Result: Telemetry exported to logs! ===\n");
        System.exit(0);
    }
}
