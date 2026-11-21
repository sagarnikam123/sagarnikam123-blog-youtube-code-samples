# Property 1: Satellite Load Balancing Distribution - Usage Guide

## Overview

This property test validates that Satellite correctly distributes observability data across all available OAP Server replicas according to the configured load balancing strategy.

**Feature:** skywalking-cluster
**Property:** 1
**Validates:** Requirements 4.2
**File:** `property_test_satellite_load_balancing.py`

## Property Statement

> For any set of observability data sent to the Satellite cluster, the data should be distributed across all available OAP Server replicas according to the configured load balancing strategy.

## Test Coverage

The property test includes 8 test functions covering different aspects of load balancing:

1. **Satellite Configuration** - Verifies Satellite is enabled and configured
2. **OAP Cluster Mode** - Verifies OAP Server is in cluster mode with multiple replicas
3. **Round-Robin Distribution** - Tests even distribution with round-robin strategy
4. **Random Distribution** - Tests coverage with random distribution strategy
5. **Environment-Specific Distribution** - Tests with actual environment configurations
6. **Data Integrity** - Verifies no data loss or duplication during distribution
7. **Scaling Behavior** - Tests distribution with varying replica counts (2-5)
8. **Service Discovery** - Verifies service discovery configuration

## Prerequisites

### Install Dependencies

```bash
cd skywalking/tests
pip install -r requirements.txt
```

### Required Files

Ensure these Helm values files exist:
- `skywalking/helm-values/base-values.yaml`
- `skywalking/helm-values/minikube-values.yaml`
- `skywalking/helm-values/eks-values.yaml`

## Running the Tests

### Run All Property 1 Tests

```bash
cd skywalking/tests
pytest property_test_satellite_load_balancing.py -v
```

### Run Specific Test

```bash
# Test Satellite configuration
pytest property_test_satellite_load_balancing.py::TestSatelliteLoadBalancing::test_property_satellite_enabled_for_load_balancing -v

# Test round-robin distribution
pytest property_test_satellite_load_balancing.py::TestSatelliteLoadBalancing::test_property_round_robin_distribution_balance -v

# Test data integrity
pytest property_test_satellite_load_balancing.py::TestSatelliteLoadBalancing::test_property_distribution_preserves_data_integrity -v
```

### Run with Verbose Hypothesis Output

```bash
pytest property_test_satellite_load_balancing.py -v --hypothesis-verbosity=verbose
```

### Run with Reduced Examples (for faster testing)

```bash
pytest property_test_satellite_load_balancing.py --hypothesis-max-examples=10 -v
```

### Run with Coverage

```bash
pytest property_test_satellite_load_balancing.py --cov=. --cov-report=html --cov-report=term -v
```

## Test Configuration

### Hypothesis Settings

- **max_examples**: 100 iterations per test
- **deadline**: None (no time limit per example)
- **verbosity**: normal

### Data Generation

The tests generate randomized observability data:
- **Data items**: 10-1000 items per test
- **Data types**: trace, metric, log
- **Services**: service-a, service-b, service-c, service-d
- **Timestamps**: Random Unix timestamps
- **Sizes**: 100-10000 bytes

### Load Balancing Strategies

The tests simulate two distribution strategies:
1. **Round-robin**: Sequential distribution across replicas
2. **Random**: Random selection of replica for each item

## Expected Results

### Successful Test Run

```
============================== test session starts ===============================
collected 8 items

property_test_satellite_load_balancing.py::TestSatelliteLoadBalancing::test_property_satellite_enabled_for_load_balancing PASSED
property_test_satellite_load_balancing.py::TestSatelliteLoadBalancing::test_property_oap_cluster_mode_for_load_balancing PASSED
property_test_satellite_load_balancing.py::TestSatelliteLoadBalancing::test_property_round_robin_distribution_balance PASSED
property_test_satellite_load_balancing.py::TestSatelliteLoadBalancing::test_property_random_distribution_coverage PASSED
property_test_satellite_load_balancing.py::TestSatelliteLoadBalancing::test_property_distribution_with_environment_config PASSED
property_test_satellite_load_balancing.py::TestSatelliteLoadBalancing::test_property_distribution_preserves_data_integrity PASSED
property_test_satellite_load_balancing.py::TestSatelliteLoadBalancing::test_property_distribution_scales_with_replicas PASSED
property_test_satellite_load_balancing.py::TestSatelliteLoadBalancing::test_property_satellite_service_discovery_configured PASSED

============================== 8 passed in 15.23s ================================
```

### Test Execution Time

- **Per test**: 1-3 minutes (100 examples)
- **Full suite**: 10-20 minutes
- **Quick run** (10 examples): 1-2 minutes

## Interpreting Results

### Configuration Tests

Tests 1, 2, and 8 validate configuration:
- **PASS**: Satellite and OAP are properly configured for load balancing
- **FAIL**: Configuration missing or incorrect (check Helm values files)

### Distribution Tests

Tests 3, 4, 5, 7 validate distribution algorithms:
- **PASS**: Data is distributed according to strategy
- **FAIL**: Distribution is imbalanced or incorrect

### Data Integrity Tests

Test 6 validates data preservation:
- **PASS**: No data loss or duplication
- **FAIL**: Data integrity issue in distribution logic

## Troubleshooting

### Test Skipped: Environment values file not found

**Issue**: Missing environment-specific Helm values file

**Solution**:
```bash
# Check if files exist
ls -la skywalking/helm-values/

# Create missing files if needed
cp skywalking/helm-values/minikube-values.yaml skywalking/helm-values/eks-values.yaml
```

### Test Failed: Satellite not enabled

**Issue**: Satellite is not enabled in configuration

**Solution**: Edit Helm values file and set:
```yaml
satellite:
  enabled: true
  replicas: 2
  config:
    # ... configuration
```

### Test Failed: OAP not in cluster mode

**Issue**: OAP Server has insufficient replicas or wrong mode

**Solution**: Edit Helm values file and set:
```yaml
oap:
  replicas: 2  # or 3 for production
  env:
    SW_CLUSTER: kubernetes
    # ... other settings
```

### Test Failed: Distribution imbalanced

**Issue**: Distribution algorithm not working correctly

**Solution**: This indicates a logic error in the distribution simulation. Review the test implementation or the actual Satellite configuration.

## Integration with CI/CD

### GitHub Actions Example

```yaml
name: Property Test - Satellite Load Balancing

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: |
          cd skywalking/tests
          pip install -r requirements.txt
      - name: Run Property 1 tests
        run: |
          cd skywalking/tests
          pytest property_test_satellite_load_balancing.py -v --tb=short
```

## Next Steps

After Property 1 tests pass:

1. **Implement Satellite configuration** in Helm values
2. **Configure OAP Server cluster mode** with appropriate replicas
3. **Run integration tests** with actual cluster deployment
4. **Validate with real traffic** using test applications
5. **Monitor distribution** using Satellite metrics

## Related Tests

- **Property 2**: Satellite Service Discovery (optional)
- **Property 3**: Deployment Script Environment Handling
- **Integration Test**: End-to-end data ingestion with load balancing

## References

- [SkyWalking Satellite Documentation](https://skywalking.apache.org/docs/skywalking-satellite/latest/readme/)
- [Hypothesis Documentation](https://hypothesis.readthedocs.io/)
- [Property-Based Testing Guide](https://increment.com/testing/in-praise-of-property-based-testing/)
- Requirements Document: `.kiro/specs/skywalking-cluster/requirements.md` (Requirement 4.2)
- Design Document: `.kiro/specs/skywalking-cluster/design.md` (Property 1)
