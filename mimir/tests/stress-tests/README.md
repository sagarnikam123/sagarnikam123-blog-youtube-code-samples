# Mimir Stress Tests

Find Mimir's **breaking point** and failure modes.

## Goal
Discover system limits, degradation patterns, and recovery behavior.

## Test Scenarios

### 1. High Cardinality
- Push metrics with extreme label combinations
- Test: 10M+ unique series
- Goal: Find cardinality limits

### 2. Burst Traffic
- Sudden traffic spikes (10x-100x normal)
- Test: Ingester buffer overflow
- Goal: Validate backpressure handling

### 3. Component Failure
- Kill pods during load
- Test: Ingester/Distributor failures
- Goal: Verify HA and recovery

### 4. Resource Exhaustion
- Push until OOM/CPU throttling
- Test: Memory/CPU limits
- Goal: Find resource bottlenecks

## Tools

| Tool | Purpose | Use Case |
|------|---------|----------|
| **Avalanche** | Cardinality bomb | High series count |
| **k6** | Burst testing | Traffic spikes |
| **Chaos Mesh** | Pod failures | Resilience testing |
| **kubectl** | Resource limits | Exhaustion testing |

## Failure Indicators

- ❌ Pod OOMKilled
- ❌ Ingester drops metrics
- ❌ Query timeouts
- ❌ Ring instability
- ❌ Kafka lag increases

## Quick Start

```bash
# Run cardinality stress test
cd high-cardinality
./cardinality-bomb.sh

# Monitor for failures
kubectl get pods -n mimir-test -w
```
