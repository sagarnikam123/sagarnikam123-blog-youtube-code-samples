package com.course;

import io.opentelemetry.api.common.AttributeKey;
import io.opentelemetry.api.common.Attributes;
import io.opentelemetry.api.metrics.DoubleHistogram;
import io.opentelemetry.api.metrics.LongCounter;
import io.opentelemetry.api.metrics.LongUpDownCounter;
import io.opentelemetry.api.metrics.Meter;
import io.opentelemetry.sdk.metrics.SdkMeterProvider;
import io.opentelemetry.sdk.metrics.data.LongPointData;
import io.opentelemetry.sdk.metrics.data.MetricData;
import io.opentelemetry.sdk.testing.exporter.InMemoryMetricReader;
import org.junit.jupiter.api.Test;

import java.util.Collection;
import java.util.List;

import static org.assertj.core.api.Assertions.assertThat;

public class MetricsInstrumentsTest {

    @Test
    void testMetricInstrumentsLifecycle() {
        InMemoryMetricReader reader = InMemoryMetricReader.create();
        SdkMeterProvider meterProvider = SdkMeterProvider.builder()
            .registerMetricReader(reader)
            .build();

        Meter meter = meterProvider.get("course-meter");

        // 1. Counter
        LongCounter counter = meter.counterBuilder("http_requests_total")
            .setDescription("Total HTTP requests")
            .setUnit("1")
            .build();
        counter.add(10, Attributes.of(AttributeKey.stringKey("http.request.method"), "GET"));

        // 2. UpDownCounter
        LongUpDownCounter upDownCounter = meter.upDownCounterBuilder("active_connections")
            .setDescription("Active connections")
            .setUnit("1")
            .build();
        upDownCounter.add(5);
        upDownCounter.add(-2); // net 3

        // 3. Histogram
        DoubleHistogram histogram = meter.histogramBuilder("http_request_duration_seconds")
            .setDescription("Request latency")
            .setUnit("s")
            .build();
        histogram.record(0.045);
        histogram.record(0.120);

        // 4. Observable Gauge (Callback)
        meter.gaugeBuilder("jvm_memory_used_megabytes")
            .setDescription("Heap memory used")
            .setUnit("By")
            .buildWithCallback(measurement -> measurement.record(256.5));

        Collection<MetricData> metrics = reader.collectAllMetrics();
        assertThat(metrics).hasSize(4);

        List<String> names = metrics.stream().map(MetricData::getName).toList();
        assertThat(names).containsExactlyInAnyOrder(
            "http_requests_total",
            "active_connections",
            "http_request_duration_seconds",
            "jvm_memory_used_megabytes"
        );

        MetricData connData = metrics.stream().filter(m -> m.getName().equals("active_connections")).findFirst().get();
        LongPointData point = (LongPointData) connData.getLongSumData().getPoints().iterator().next();
        assertThat(point.getValue()).isEqualTo(3L);
    }
}
