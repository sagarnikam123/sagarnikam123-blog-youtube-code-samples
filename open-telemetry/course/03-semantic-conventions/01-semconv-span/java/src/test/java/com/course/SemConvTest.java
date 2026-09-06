package com.course;

import io.opentelemetry.api.common.AttributeKey;
import io.opentelemetry.api.trace.Span;
import io.opentelemetry.api.trace.SpanKind;
import io.opentelemetry.api.trace.StatusCode;
import io.opentelemetry.api.trace.Tracer;
import io.opentelemetry.sdk.testing.exporter.InMemorySpanExporter;
import io.opentelemetry.sdk.trace.SdkTracerProvider;
import io.opentelemetry.sdk.trace.data.SpanData;
import io.opentelemetry.sdk.trace.export.SimpleSpanProcessor;
import org.junit.jupiter.api.Test;

import java.util.List;

import static org.assertj.core.api.Assertions.assertThat;

public class SemConvTest {

    @Test
    void testModernSemanticConventions() {
        InMemorySpanExporter exporter = InMemorySpanExporter.create();
        SdkTracerProvider tracerProvider = SdkTracerProvider.builder()
            .addSpanProcessor(SimpleSpanProcessor.create(exporter))
            .build();

        Tracer tracer = tracerProvider.get("test-tracer", "1.0.0");

        // Simulate Inbound HTTP Request
        Span serverSpan = tracer.spanBuilder("GET /api/v1/orders")
            .setSpanKind(SpanKind.SERVER)
            .startSpan();

        try (io.opentelemetry.context.Scope scope = serverSpan.makeCurrent()) {
            serverSpan.setAttribute("http.request.method", "GET");
            serverSpan.setAttribute("http.response.status_code", 200L);
            serverSpan.setAttribute("url.path", "/api/v1/orders");
            serverSpan.setAttribute("server.address", "api.internal");
            serverSpan.setAttribute("server.port", 8080L);
            serverSpan.setStatus(StatusCode.OK);

            // Simulate Child Database Call
            Span dbSpan = tracer.spanBuilder("SELECT orders")
                .setSpanKind(SpanKind.CLIENT)
                .startSpan();
            try {
                dbSpan.setAttribute("db.system", "postgresql");
                dbSpan.setAttribute("db.operation", "SELECT");
                dbSpan.setAttribute("db.collection.name", "orders");
                dbSpan.setAttribute("db.namespace", "ecommerce_db");
                dbSpan.setStatus(StatusCode.OK);
            } finally {
                dbSpan.end();
            }
        } finally {
            serverSpan.end();
        }

        List<SpanData> finishedSpans = exporter.getFinishedSpanItems();
        assertThat(finishedSpans).hasSize(2);

        SpanData dbFinished = finishedSpans.get(0);
        SpanData httpFinished = finishedSpans.get(1);

        // Verify hierarchy
        assertThat(dbFinished.getParentSpanId()).isEqualTo(httpFinished.getSpanId());

        // Verify HTTP Attributes
        assertThat(httpFinished.getAttributes().get(AttributeKey.stringKey("http.request.method"))).isEqualTo("GET");
        assertThat(httpFinished.getAttributes().get(AttributeKey.longKey("http.response.status_code"))).isEqualTo(200L);
        assertThat(httpFinished.getAttributes().get(AttributeKey.stringKey("server.address"))).isEqualTo("api.internal");

        // Verify DB Attributes
        assertThat(dbFinished.getAttributes().get(AttributeKey.stringKey("db.system"))).isEqualTo("postgresql");
        assertThat(dbFinished.getAttributes().get(AttributeKey.stringKey("db.operation"))).isEqualTo("SELECT");
        assertThat(dbFinished.getAttributes().get(AttributeKey.stringKey("db.collection.name"))).isEqualTo("orders");
    }
}
