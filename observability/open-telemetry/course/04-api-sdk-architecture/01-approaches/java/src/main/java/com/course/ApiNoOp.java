package com.course;

import io.opentelemetry.api.GlobalOpenTelemetry;
import io.opentelemetry.api.trace.Span;
import io.opentelemetry.api.trace.Tracer;

public class ApiNoOp {

    public static void main(String[] args) {
        System.out.println("=== Running Java with API ONLY (No SDK Registered) ===");

        // GlobalOpenTelemetry returns a DefaultTracer (No-Op) if no SDK is configured
        Tracer tracer = GlobalOpenTelemetry.getTracer("library-sample", "1.0.0");

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

        System.out.println("=== Result: No output, zero overhead, zero errors! ===\n");
    }
}
