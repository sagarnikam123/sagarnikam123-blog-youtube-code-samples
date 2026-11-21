package com.course;

import io.opentelemetry.api.baggage.Baggage;
import io.opentelemetry.api.baggage.propagation.W3CBaggagePropagator;
import io.opentelemetry.api.common.AttributeKey;
import io.opentelemetry.api.trace.Span;
import io.opentelemetry.api.trace.SpanKind;
import io.opentelemetry.api.trace.Tracer;
import io.opentelemetry.api.trace.propagation.W3CTraceContextPropagator;
import io.opentelemetry.context.Context;
import io.opentelemetry.context.propagation.ContextPropagators;
import io.opentelemetry.context.propagation.TextMapGetter;
import io.opentelemetry.context.propagation.TextMapPropagator;
import io.opentelemetry.context.propagation.TextMapSetter;
import io.opentelemetry.sdk.OpenTelemetrySdk;
import io.opentelemetry.sdk.testing.exporter.InMemorySpanExporter;
import io.opentelemetry.sdk.trace.SdkTracerProvider;
import io.opentelemetry.sdk.trace.data.SpanData;
import io.opentelemetry.sdk.trace.export.SimpleSpanProcessor;
import org.junit.jupiter.api.Test;

import java.util.HashMap;
import java.util.List;
import java.util.Map;

import static org.assertj.core.api.Assertions.assertThat;

public class PropagationTest {

    private static final TextMapSetter<Map<String, String>> SETTER = Map::put;

    private static final TextMapGetter<Map<String, String>> GETTER = new TextMapGetter<>() {
        @Override
        public Iterable<String> keys(Map<String, String> carrier) {
            return carrier.keySet();
        }

        @Override
        public String get(Map<String, String> carrier, String key) {
            return carrier.get(key);
        }
    };

    @Test
    void testDistributedPropagationAndBaggage() {
        InMemorySpanExporter exporter = InMemorySpanExporter.create();
        SdkTracerProvider tracerProvider = SdkTracerProvider.builder()
            .addSpanProcessor(SimpleSpanProcessor.create(exporter))
            .build();

        TextMapPropagator composite = TextMapPropagator.composite(
            W3CTraceContextPropagator.getInstance(),
            W3CBaggagePropagator.getInstance()
        );

        OpenTelemetrySdk sdk = OpenTelemetrySdk.builder()
            .setTracerProvider(tracerProvider)
            .setPropagators(ContextPropagators.create(composite))
            .build();

        Tracer tracer = sdk.getTracer("propagation-tracer");

        // 1. Client Side Execution
        Map<String, String> carrier = new HashMap<>();
        Span clientSpan = tracer.spanBuilder("client_request")
            .setSpanKind(SpanKind.CLIENT)
            .startSpan();

        try {
            // Attach Baggage to context
            Baggage clientBaggage = Baggage.builder()
                .put("tenant.id", "t-9000")
                .put("user.tier", "platinum")
                .build();

            Context clientContext = Context.current()
                .with(clientSpan)
                .with(clientBaggage);

            // Inject into HTTP headers carrier
            composite.inject(clientContext, carrier, SETTER);
        } finally {
            clientSpan.end();
        }

        // Verify headers were populated
        assertThat(carrier).containsKey("traceparent");
        assertThat(carrier).containsKey("baggage");

        // 2. Server Side Execution
        Context serverContext = composite.extract(Context.current(), carrier, GETTER);
        Baggage extractedBaggage = Baggage.fromContext(serverContext);

        Span serverSpan = tracer.spanBuilder("server_handle")
            .setParent(serverContext)
            .setSpanKind(SpanKind.SERVER)
            .startSpan();

        try {
            String tenantId = extractedBaggage.getEntryValue("tenant.id");
            assertThat(tenantId).isEqualTo("t-9000");

            // Explicitly promote baggage to span attribute
            serverSpan.setAttribute(AttributeKey.stringKey("tenant.id"), tenantId);
        } finally {
            serverSpan.end();
        }

        List<SpanData> spans = exporter.getFinishedSpanItems();
        assertThat(spans).hasSize(2);

        SpanData clientData = spans.get(0);
        SpanData serverData = spans.get(1);

        // Assert shared Trace ID and Parent relationship
        assertThat(serverData.getTraceId()).isEqualTo(clientData.getTraceId());
        assertThat(serverData.getParentSpanId()).isEqualTo(clientData.getSpanId());
        assertThat(serverData.getAttributes().get(AttributeKey.stringKey("tenant.id"))).isEqualTo("t-9000");
    }
}
