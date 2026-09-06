# Challenge — Configurable Sampler & Batch Processor

## The Scenario

Your company runs a high-traffic e-commerce portal during Black Friday. At peak volume, sampling 100% of traces would overwhelm the network and crash your telemetry backends.

The Platform team requires every service to support dynamic sampling configuration:

- In production, sample strictly 10% of new incoming root traces, but **always honor upstream sampled requests** from internal debug proxies.
- Batch spans and flush at least once every 1,000 milliseconds, with a maximum queue size of 4,096 spans.

---

## Your Mission

Write an application initialization suite (Python or Java) that:

1. Configures a `ParentBased` sampler with an underlying `TraceIdRatioBased(0.10)` root sampler.
2. Configures a `BatchSpanProcessor` with `max_queue_size=4096` and `scheduled_delay_millis=1000`.
3. Emits 100 root spans and verifies that approximately ~10% (between 5% and 20% due to statistical hashing) are sampled and exported.
4. Emits an incoming request containing an explicit upstream sampled header (`traceparent` ending in `-01`) and verifies that this child span is **100% sampled** regardless of the 10% root ratio!

### Expected Verification

- Automated assertions prove that upstream sampled parent spans bypass the 10% ratio and are always recorded.
