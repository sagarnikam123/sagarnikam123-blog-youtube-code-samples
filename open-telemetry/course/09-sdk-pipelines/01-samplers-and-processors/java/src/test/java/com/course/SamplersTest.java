package com.course;

import io.opentelemetry.api.trace.Span;
import io.opentelemetry.api.trace.SpanContext;
import io.opentelemetry.api.trace.TraceFlags;
import io.opentelemetry.api.trace.TraceState;
import io.opentelemetry.api.trace.Tracer;
import io.opentelemetry.context.Context;
import io.opentelemetry.sdk.testing.exporter.InMemorySpanExporter;
import io.opentelemetry.sdk.trace.SdkTracerProvider;
import io.opentelemetry.sdk.trace.data.SpanData;
import io.opentelemetry.sdk.trace.export.SimpleSpanProcessor;
import io.opentelemetry.sdk.trace.samplers.Sampler;
import org.junit.jupiter.api.Test;

import java.util.List;

import static org.assertj.core.api.Assertions.assertThat;

public class SamplersTest {

    @Test
    void testParentBasedSampling() {
        InMemorySpanExporter exporter = InMemorySpanExporter.create();

        // Configure ParentBased sampler with root = alwaysOff
        Sampler sampler = Sampler.parentBased(Sampler.alwaysOff());

        SdkTracerProvider tracerProvider = SdkTracerProvider.builder()
            .setSampler(sampler)
            .addSpanProcessor(SimpleSpanProcessor.create(exporter))
            .build();

        Tracer tracer = tracerProvider.get("sampler-tracer");

        // 1. Unparented Root Span -> Should NOT be sampled
        Span rootSpan = tracer.spanBuilder("unparented_root").startSpan();
        try {
            assertThat(rootSpan.getSpanContext().isSampled()).isFalse();
        } finally {
            rootSpan.end();
        }

        // 2. Child Span with Remote Sampled Parent -> MUST be sampled
        SpanContext remoteParent = SpanContext.createFromRemoteParent(
            "4bf92f3577b34da6a3ce929d0e0e4736",
            "00f067aa0ba902b7",
            TraceFlags.getSampled(),
            TraceState.getDefault()
        );

        Span childSpan = tracer.spanBuilder("child_operation")
            .setParent(Context.current().with(Span.wrap(remoteParent)))
            .startSpan();

        try {
            assertThat(childSpan.getSpanContext().isSampled()).isTrue();
        } finally {
            childSpan.end();
        }

        // Verify only the sampled child reached the exporter
        List<SpanData> spans = exporter.getFinishedSpanItems();
        assertThat(spans).hasSize(1);
        assertThat(spans.get(0).getName()).isEqualTo("child_operation");
    }
}
