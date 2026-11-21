package com.course;

import io.opentelemetry.api.common.AttributeKey;
import io.opentelemetry.api.common.Attributes;
import io.opentelemetry.api.metrics.LongCounter;
import io.opentelemetry.api.metrics.Meter;
import io.opentelemetry.api.trace.Span;
import io.opentelemetry.api.trace.Tracer;
import io.opentelemetry.exporter.logging.LoggingSpanExporter;
import io.opentelemetry.sdk.OpenTelemetrySdk;
import io.opentelemetry.sdk.metrics.SdkMeterProvider;
import io.opentelemetry.sdk.resources.Resource;
import io.opentelemetry.sdk.trace.SdkTracerProvider;
import io.opentelemetry.sdk.trace.export.SimpleSpanProcessor;

public class SignalsComparison {

    public static void main(String[] args) throws Exception {
        Resource resource = Resource.getDefault().merge(
            Resource.create(Attributes.of(AttributeKey.stringKey("service.name"), "signals-demo-java"))
        );

        // 1. Traces Provider
        SdkTracerProvider tracerProvider = SdkTracerProvider.builder()
            .setResource(resource)
            .addSpanProcessor(SimpleSpanProcessor.create(LoggingSpanExporter.create()))
            .build();

        // 2. Metrics Provider
        SdkMeterProvider meterProvider = SdkMeterProvider.builder()
            .setResource(resource)
            .build();

        OpenTelemetrySdk sdk = OpenTelemetrySdk.builder()
            .setTracerProvider(tracerProvider)
            .setMeterProvider(meterProvider)
            .buildAndRegisterGlobal();

        Tracer tracer = sdk.getTracer("signals-tracer");
        Meter meter = sdk.getMeter("signals-meter");

        LongCounter checkoutCounter = meter.counterBuilder("checkout_requests_total")
            .setDescription("Total checkout requests")
            .setUnit("1")
            .build();

        // 3. Correlated Transaction
        Span span = tracer.spanBuilder("checkout_transaction").startSpan();
        try {
            String traceId = span.getSpanContext().getTraceId();
            span.setAttribute("customer.tier", "gold");
            span.setAttribute("cart.value_usd", 89.50);

            // Correlated log output with TraceID
            System.out.printf("[LOG] [trace_id=%s] Payment processed successfully for customer\n", traceId);

            checkoutCounter.add(1, Attributes.of(AttributeKey.stringKey("status"), "success"));
        } finally {
            span.end();
        }

        tracerProvider.shutdown();
        meterProvider.shutdown();
        System.exit(0);
    }
}
