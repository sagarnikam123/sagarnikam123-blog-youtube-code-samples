package com.course;

import io.opentelemetry.api.common.AttributeKey;
import io.opentelemetry.api.common.Attributes;
import io.opentelemetry.api.logs.Logger;
import io.opentelemetry.api.logs.Severity;
import io.opentelemetry.api.trace.Span;
import io.opentelemetry.api.trace.Tracer;
import io.opentelemetry.context.Scope;
import io.opentelemetry.sdk.logs.SdkLoggerProvider;
import io.opentelemetry.sdk.logs.data.LogRecordData;
import io.opentelemetry.sdk.logs.export.SimpleLogRecordProcessor;
import io.opentelemetry.sdk.resources.Resource;
import io.opentelemetry.sdk.testing.exporter.InMemoryLogRecordExporter;
import io.opentelemetry.sdk.trace.SdkTracerProvider;
import org.junit.jupiter.api.Test;

import java.util.List;

import static org.assertj.core.api.Assertions.assertThat;

public class LogCorrelationTest {

    @Test
    void testTraceLogCorrelation() {
        Resource resource = Resource.getDefault().merge(
            Resource.create(Attributes.of(AttributeKey.stringKey("service.name"), "order-service"))
        );

        // 1. Setup Tracing
        SdkTracerProvider tracerProvider = SdkTracerProvider.builder().setResource(resource).build();
        Tracer tracer = tracerProvider.get("order-tracer");

        // 2. Setup Logging Provider & In-Memory Exporter
        InMemoryLogRecordExporter logExporter = InMemoryLogRecordExporter.create();
        SdkLoggerProvider loggerProvider = SdkLoggerProvider.builder()
            .setResource(resource)
            .addLogRecordProcessor(SimpleLogRecordProcessor.create(logExporter))
            .build();
        Logger logger = loggerProvider.get("order-logger");

        // 3. Emit Log within active Span Scope
        Span span = tracer.spanBuilder("process_payment").startSpan();
        try (Scope scope = span.makeCurrent()) {
            logger.logRecordBuilder()
                .setSeverity(Severity.INFO)
                .setSeverityText("INFO")
                .setBody("Payment processed by gateway")
                .setAttribute(AttributeKey.stringKey("payment.id"), "pay_12345")
                .emit();
        } finally {
            span.end();
        }

        // 4. Assert Correlated Log Record
        List<LogRecordData> logs = logExporter.getFinishedLogRecordItems();
        assertThat(logs).hasSize(1);

        LogRecordData record = logs.get(0);
        assertThat(record.getSpanContext().getTraceId()).isEqualTo(span.getSpanContext().getTraceId());
        assertThat(record.getSpanContext().getSpanId()).isEqualTo(span.getSpanContext().getSpanId());
        assertThat(record.getBody().asString()).isEqualTo("Payment processed by gateway");
        assertThat(record.getSeverity()).isEqualTo(Severity.INFO);
    }
}
