# Property 2: Satellite Service Discovery - Usage Guide

## Overview

This property-based test validates that Satellite automatically detects and updates its routing table when OAP Server replicas are added or removed from the cluster.

**Property Statement:**
> For any OAP Server replica added to or removed from the cluster, Satellite should automatically update its routing table to include or exclude that replica within the service discovery interval.

**Validates:** Requirements 4.4

## Test File

`property_test_satellite_service_discovery.py`

## What This Test Validates

### 1. Service Discovery Configuration
- Satellite is properly configured with service discovery enabled
- OAP Server backend service is configured in Satellite
- Multiple OAP Server replicas are configured for discovery

### 2. Replica Change Detection
- Added replicas are detected and included in routing
- Removed replicas are detected and excluded from routing
- Routing table updates within the service discovery interval

### 3. Routing Table Consistency
- Routing table includes all current replicas
- Routing table excludes removed replicas
- No duplicate entries in routing table
- Correct replica count maintained

### 4. Pod Lifecycle Handling
- Pod additions are detected
- Pod removals are detected
- Only ready pods are included in routing
- Not-ready pods are excluded from routing

### 5. Traffic Continuity
- At least one replica remains available during updates
- No traffic loss during service discovery updates
- Graceful handling of replica transitions

### 6. Multiple Update Handling
- Consecutive replica changes are handled correctly
- Routing table remains consistent after multiple updates
- No stale entries accumulate

## Running the Tests

### Run All Property 2 Tests

```bash
cd skywalking/tests
pytest property_test_satellite_service_discovery.py -v
```

### Run Specific Test

```bash
# Test service discovery configuration
pytest property_test_satellite_service_discovery.py::TestSatelliteServiceDiscovery::test_property_service_discovery_configured -v

# Test replica change detection
pytest property_test_satellite_service_discovery.py::TestSatelliteServiceDiscovery::test_property_service_discovery_detects_replica_changes -v

# Test routing table updates
pytest property_test_satellite_service_discovery.py::TestSatelliteServiceDiscovery::test_property_routing_table_updated_correctly -v

# Test lifecycle event handling
pytest property_test_satellite_service_discovery.py::TestSatelliteServiceDiscovery::test_property_service_discovery_handles_lifecycle_events -v
```

### Run with Verbose Hypothesis Output

```bash
pytest property_test_satellite_service_discovery.py -v --hypothesis-verbosity=verbose
```

### Run with Reduced Examples (for faster testing)

```bash
pytest property_test_satellite_service_discovery.py --hypothesis-max-examples=10 -v
```

## Test Scenarios

### Scenario 1: Adding OAP Server Replicas

**Input:** Initial replicas: 2, Final replicas: 4
**Expected:**
- 2 new endpoints added to routing table
- No endpoints removed
- All 4 replicas discoverable
- Update completes within discovery interval

### Scenario 2: Removing OAP Server Replicas

**Input:** Initial replicas: 5, Final replicas: 3
**Expected:**
- 2 endpoints removed from routing table
- No endpoints added
- Remaining 3 replicas still discoverable
- At least 1 replica remains available during transition

### Scenario 3: Pod Lifecycle Events

**Input:** Sequence of pod_added, pod_ready, pod_not_ready, pod_removed events
**Expected:**
- Only ready pods included in routing table
- Not-ready pods excluded from routing
- Removed pods excluded from routing
- Routing table stays consistent

### Scenario 4: Multiple Consecutive Updates

**Input:** 5 consecutive replica changes (add/remove)
**Expected:**
- Each update handled correctly
- Final routing table matches final replica count
- No stale entries
- Consistency maintained throughout

## Configuration Requirements

For these tests to pass, your Helm values must include:

```yaml
satellite:
  enabled: true
  replicas: 2  # At least 1
  config:
    forwarder:
      grpc:
        serverAddr: "skywalking-oap:11800"  # OAP Server backend service

oap:
  replicas: 2  # At least 2 for cluster mode
  service:
    name: "oap-server"  # Service name for discovery
```

## Test Strategies

The tests use Hypothesis strategies to generate:

1. **Replica Changes:** Random additions/removals of OAP Server replicas (2-5 replicas)
2. **Service Discovery Configs:** Various discovery mechanisms (kubernetes, dns, static)
3. **Lifecycle Events:** Sequences of pod additions, removals, ready, not-ready events
4. **Environment Combinations:** Tests across minikube and eks environments

## Simulated Behavior

Since these are property-based tests without a live cluster, they simulate:

1. **Service Discovery Updates:** Simulates Kubernetes service discovery detecting replica changes
2. **Routing Table Updates:** Simulates Satellite updating its internal routing table
3. **Endpoint Generation:** Creates realistic Kubernetes service endpoints
4. **Discovery Intervals:** Validates updates complete within expected timeframes

## Integration with Live Cluster

For full integration testing with a live cluster:

1. Deploy SkyWalking cluster with Satellite
2. Scale OAP Server replicas: `kubectl scale deployment oap-server --replicas=4`
3. Monitor Satellite logs for service discovery updates
4. Verify traffic distribution across all replicas
5. Scale down and verify removed replicas are excluded

## Troubleshooting

### Test Fails: "Service discovery is not properly configured"

**Cause:** Satellite or OAP Server not configured correctly

**Solution:**
- Verify `satellite.enabled: true` in Helm values
- Verify `satellite.config.forwarder.grpc.serverAddr` is set
- Verify `oap.replicas >= 2`

### Test Fails: "Routing table size mismatch"

**Cause:** Routing table update logic error

**Solution:**
- Check that added/removed endpoints are calculated correctly
- Verify no duplicate endpoints
- Ensure endpoint format is consistent

### Test Fails: "Not-ready pod found in routing table"

**Cause:** Lifecycle event handling error

**Solution:**
- Verify only ready pods are included in routing
- Check pod readiness status is tracked correctly
- Ensure removed pods are excluded

## Expected Test Execution Time

- All 8 tests: ~5-10 seconds
- Each test runs 100 examples (configurable)
- Total iterations: 800+ property checks

## Related Tests

- **Property 1:** `property_test_satellite_load_balancing.py` - Tests load balancing distribution
- **Property 3:** `property_test_deployment_environment.py` - Tests deployment configuration

## References

- [SkyWalking Satellite Documentation](https://skywalking.apache.org/docs/skywalking-satellite/latest/readme/)
- [Kubernetes Service Discovery](https://kubernetes.io/docs/concepts/services-networking/service/)
- [Hypothesis Documentation](https://hypothesis.readthedocs.io/)
- Requirements Document: `.kiro/specs/skywalking-cluster/requirements.md` (Requirement 4.4)
- Design Document: `.kiro/specs/skywalking-cluster/design.md` (Property 2)
