package com.course;

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

public class OtlpGrpcExport {

    public static void main(String[] args) {
        System.out.println("--- Java OTLP / gRPC Exporter (Port 4317) ---");

        Resource resource = Resource.getDefault().merge(
            Resource.create(Attributes.of(AttributeKey.stringKey("service.name"), "grpc-exporter-java"))
        );

        OtlpGrpcSpanExporter grpcExporter = OtlpGrpcSpanExporter.builder()
            .setEndpoint("http://localhost:4317")
            .build();

        SdkTracerProvider tracerProvider = SdkTracerProvider.builder()
            .setResource(resource)
            .addSpanProcessor(SimpleSpanProcessor.create(LoggingSpanExporter.create()))
            .addSpanProcessor(BatchSpanProcessor.builder(grpcExporter).build())
            .build();

        OpenTelemetrySdk sdk = OpenTelemetrySdk.builder()
            .setTracerProvider(tracerProvider)
            .buildAndRegisterGlobal();

        Tracer tracer = sdk.getTracer("grpc-tracer");
        Span span = tracer.spanBuilder("grpc_operation").startSpan();
        try {
            span.setAttribute("protocol.name", "grpc");
            span.setAttribute("protocol.port", 4317L);
            System.out.println("Emitted gRPC span: TraceID = " + span.getSpanContext().getTraceId());
        } finally {
            span.end();
        }

        tracerProvider.shutdown();
        System.out.println("--- Java gRPC export flushed! ---\n");
        System.exit(0);
    }
}
