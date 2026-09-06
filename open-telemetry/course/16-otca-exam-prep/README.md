# Module 16 — Linux Foundation OTCA Exam Guide & Preparation

> **Target:** OpenTelemetry Certified Associate (OTCA) Certification

---

## 1. Exam Blueprint & Overview

The **OpenTelemetry Certified Associate (OTCA)** certification demonstrates foundational knowledge of OpenTelemetry, its architecture, signals, SDK pipelines, Collector configuration, and troubleshooting techniques.

| Detail | Specification |
| -------- | --------------- |
| **Exam Format** | 60 Multiple-Choice Questions (Single and Multi-select) |
| **Duration** | 90 Minutes |
| **Passing Score** | 70% |
| **Delivery Mode** | Online Proctored (Linux Foundation Portal) |
| **Prerequisites** | None |
| **Validity** | 2 Years |

---

## 2. Official Domain Weightings & Cross-Course Reference

```text
┌─────────────────────────────────────────────────────────────┬────────┐
│ Exam Domain                                                 │ Weight │
├─────────────────────────────────────────────────────────────┼────────┤
│ 1. OpenTelemetry Fundamentals (Modules 01, 02, 03)          │  18%   │
│ 2. OpenTelemetry API and SDK (Modules 04, 05, 06, 07, 08, 09│  46%   │
│ 3. OpenTelemetry Collector (Modules 11, 12, 13)             │  26%   │
│ 4. Maintaining and Debugging (Module 14)                    │  10%   │
└─────────────────────────────────────────────────────────────┴────────┘
```

---

## 3. High-Value Study Artifacts in [`otca-prep/`](../otca-prep/)

We provide a dedicated exam prep suite located in the [`otca-prep/`](../otca-prep/) directory:

- [**Domain 1 Review & Quiz (18%):** `otca-prep/01-domain-fundamentals.md`](../otca-prep/01-domain-fundamentals.md) — Signals, semantic conventions, reliability metrics (MTTD/MTTR), SLI/SLO/SLA, and 10 domain quiz questions.
- [**Domain 2 Review & Quiz (46%):** `otca-prep/02-domain-api-sdk.md`](../otca-prep/02-domain-api-sdk.md) — API vs SDK split, No-Op default, OTLP (4317/4318), Span lifecycle, Baggage, 6 Metric instruments, Views, Log Appender Bridge, Samplers, and 25 domain quiz questions.
- [**Domain 3 Review & Quiz (26%):** `otca-prep/03-domain-collector.md`](../otca-prep/03-domain-collector.md) — Receivers, Processor ordering (Memory limiter first!), Exporters, Extensions, Connectors, Agent vs Gateway topologies, OTTL, Tail sampling, Load-balancing, and 15 domain quiz questions.
- [**Domain 4 Review & Quiz (10%):** `otca-prep/04-domain-maintaining.md`](../otca-prep/04-domain-maintaining.md) — Context loss across thread boundaries, Header stripping, Buffer overflow metrics, Schema evolution, zPages, and 10 domain quiz questions.
- [**Full 60-Question Mock Exam:** `otca-prep/mock-exam.md`](../otca-prep/mock-exam.md) — Timed simulation featuring 60 weighted questions with a complete answer key and technical rationales.

---

## 4. Emerging Topics Preview: Continuous Profiling & eBPF

While not yet heavily tested on current OTCA exams, OpenTelemetry is actively standardizing:

1. **Profiling (Fourth Core Signal):** Continuous profiling based on pprof data model to sample CPU stack traces alongside distributed spans.
2. **eBPF Zero-Code Telemetry (Grafana Beyla / OTel eBPF):** Ingesting HTTP and gRPC spans directly from Linux kernel network sockets without any runtime agent or JVM modification.
