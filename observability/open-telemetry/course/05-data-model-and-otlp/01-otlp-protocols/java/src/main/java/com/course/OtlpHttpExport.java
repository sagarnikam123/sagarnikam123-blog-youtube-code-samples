package com.course;

import io.opentelemetry.api.common.AttributeKey;
import io.opentelemetry.api.common.Attributes;
import io.opentelemetry.api.trace.Span;
import io.opentelemetry.api.trace.Tracer;
import io.opentelemetry.exporter.logging.LoggingSpanExporter;
import io.opentelemetry.exporter.otlp.http.trace.OtlpHttpSpanExporter;
import io.opentelemetry.sdk.OpenTelemetrySdk;
import io.opentelemetry.sdk.resources.Resource;
import io.opentelemetry.sdk.trace.SdkTracerProvider;
import io.opentelemetry.sdk.trace.export.BatchSpanProcessor;
import io.opentelemetry.sdk.trace.export.SimpleSpanProcessor;

public class OtlpHttpExport {

    public static void main(String[] args) {
        System.out.println("--- Java OTLP / HTTP Exporter (Port 4318) ---");

        Resource resource = Resource.getDefault().merge(
            Resource.create(Attributes.of(AttributeKey.stringKey("service.name"), "http-exporter-java"))
        );

        OtlpHttpSpanExporter httpExporter = OtlpHttpSpanExporter.builder()
            .setEndpoint("http://localhost:4318/v1/traces")
            .build();

        SdkTracerProvider tracerProvider = SdkTracerProvider.builder()
            .setResource(resource)
            .addSpanProcessor(SimpleSpanProcessor.create(LoggingSpanExporter.create()))
            .addSpanProcessor(BatchSpanProcessor.builder(httpExporter).build())
            .build();

        OpenTelemetrySdk sdk = OpenTelemetrySdk.builder()
            .setTracerProvider(tracerProvider)
            .buildAndRegisterGlobal();

        Tracer tracer = sdk.getTracer("http-tracer");
        Span span = tracer.spanBuilder("http_operation").startSpan();
        try {
            span.setAttribute("protocol.name", "http/protobuf");
            span.setAttribute("protocol.port", 4318L);
            System.out.println("Emitted HTTP span: TraceID = " + span.getSpanContext().getTraceId());
        } finally {
            span.end();
        }

        tracerProvider.shutdown();
        System.out.println("--- Java HTTP export flushed! ---\n");
        System.exit(0);
    }
}
