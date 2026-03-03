# SkyWalking Tests

This directory contains comprehensive tests for the SkyWalking full cluster mode deployment, including property-based tests, unit tests, and integration tests.

## Test Types

### Property-Based Tests

Property-based tests use Hypothesis to validate universal properties across randomized inputs with minimum 100 iterations per test.

**Files:**
- `property_test_deployment_environment.py` - Tests for deployment script environment handling (Property 3)
- `property_test_satellite_load_balancing.py` - Tests for Satellite load balancing distribution (Property 1)
- `property_test_satellite_service_discovery.py` - Tests for Satellite service discovery (Property 2)
- `property_test_persistent_volume_binding.py` - Tests for persistent volume binding validation (Property 18)

**Features:**
- Validates configuration loading for all environments (minikube, eks-dev, eks-prod)
- Verifies all required components are properly configured
- Checks environment-specific settings (replica counts, storage classes)
- Validates resource requests and limits
- Verifies storage configuration
- Tests high availability features
- Validates Satellite load balancing across OAP Server replicas
- Tests distribution algorithms (round-robin, random)
- Verifies data integrity during load balancing
- Tests service discovery configuration
- Validates automatic detection of OAP Server replica changes
- Tests routing table updates during pod lifecycle events
- Verifies service discovery handles additions and removals correctly

### Unit Tests

Unit tests validate specific scenarios and edge cases.

**Files:**
- `test-installation.sh` - Installation verification script

### Integration Tests

Integration tests validate end-to-end workflows across the complete SkyWalking cluster deployment.

**Files:**
- `integration_test_full_deployment.py` - Full deployment workflow test
- `integration_test_marketplace_features.py` - Marketplace features integration test
- `integration_test_high_availability.py` - High availability test
- `integration_test_data_persistence.py` - Data persistence test
- `run-integration-tests.sh` - Integration test runner script

**Features:**
- Validates complete deployment workflow from start to finish
- Tests all marketplace features (MySQL, Redis, RabbitMQ, Kubernetes, MQ monitoring)
- Validates high availability by simulating pod failures
- Tests data persistence across component restarts
- Verifies cluster recovery and self-healing capabilities
- Tests OAP Server, BanyanDB, Satellite, UI, and etcd components
- Validates connectivity, health checks, and data ingestion
- Tests rolling updates and pod disruption budgets

## Prerequisites

### Python Dependencies

Install Python dependencies:

```bash
pip install -r requirements.txt
```

Or using a virtual environment:

```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### Required Files

The tests expect the following directory structure:

```
skywalking/
├── helm-values/
│   ├── base-values.yaml
│   ├── minikube-values.yaml
│   ├── eks-dev-values.yaml (to be created)
│   └── eks-prod-values.yaml (to be created)
├── scripts/
│   └── (deployment scripts)
└── tests/
    ├── property_test_deployment_environment.py
    ├── pytest.ini
    ├── conftest.py
    ├── requirements.txt
    └── README.md
```

## Running Tests

### Run All Property-Based Tests

```bash
cd skywalking/tests
pytest property_test_*.py -v
```

### Run All Integration Tests

```bash
cd skywalking/tests
./run-integration-tests.sh minikube
```

Or using pytest directly:

```bash
pytest integration_test_*.py -v --environment=minikube
```

### Run Specific Integration Test Suite

```bash
# Full deployment workflow
./run-integration-tests.sh minikube --test-suite full

# Marketplace features
./run-integration-tests.sh minikube --test-suite marketplace

# High availability
./run-integration-tests.sh minikube --test-suite ha

# Data persistence
./run-integration-tests.sh minikube --test-suite persistence
```

### Run Specific Property Test

```bash
pytest property_test_deployment_environment.py -v
```

### Run Tests for Specific Environment

```bash
# Minikube tests only
pytest -m minikube -v

# EKS tests only
pytest -m eks -v
```

### Run with Coverage

```bash
pytest --cov=. --cov-report=html --cov-report=term
```

### Run in Parallel

```bash
pytest -n auto  # Use all available CPU cores
pytest -n 4     # Use 4 workers
```

### Run with Verbose Hypothesis Output

```bash
pytest property_test_*.py -v --hypothesis-verbosity=verbose
```

## Test Configuration

### Pytest Configuration

The `pytest.ini` file contains:
- Test discovery patterns
- Output options
- Custom markers
- Hypothesis settings

### Hypothesis Configuration

Property-based tests use these settings:
- **max_examples**: 100 iterations per test
- **deadline**: None (no time limit per example)
- **verbosity**: normal

To override for debugging:

```bash
pytest --hypothesis-max-examples=10 -v
```

## Test Markers

Tests can be filtered using markers:

- `@pytest.mark.property` - Property-based tests
- `@pytest.mark.unit` - Unit tests
- `@pytest.mark.integration` - Integration tests
- `@pytest.mark.slow` - Slow-running tests
- `@pytest.mark.minikube` - Minikube-specific tests
- `@pytest.mark.eks` - EKS-specific tests

Example:

```bash
# Run only property-based tests
pytest -m property -v

# Run all except slow tests
pytest -m "not slow" -v

# Run property tests for minikube
pytest -m "property and minikube" -v
```

## Property Test Details

### Property 1: Satellite Load Balancing Distribution

**File:** `property_test_satellite_load_balancing.py`

**Validates:** Requirements 4.2

**Tests:**
1. `test_property_satellite_enabled_for_load_balancing` - Satellite configuration validation
2. `test_property_oap_cluster_mode_for_load_balancing` - OAP cluster mode verification
3. `test_property_round_robin_distribution_balance` - Round-robin distribution balance
4. `test_property_random_distribution_coverage` - Random distribution coverage
5. `test_property_distribution_with_environment_config` - Environment-specific distribution
6. `test_property_distribution_preserves_data_integrity` - Data integrity preservation
7. `test_property_distribution_scales_with_replicas` - Scaling behavior validation
8. `test_property_satellite_service_discovery_configured` - Service discovery configuration

**Property Statement:**
> For any set of observability data sent to the Satellite cluster, the data should be distributed across all available OAP Server replicas according to the configured load balancing strategy.

### Property 2: Satellite Service Discovery

**File:** `property_test_satellite_service_discovery.py`

**Validates:** Requirements 4.4

**Tests:**
1. `test_property_service_discovery_configured` - Service discovery configuration validation
2. `test_property_service_discovery_detects_replica_changes` - Replica change detection
3. `test_property_routing_table_updated_correctly` - Routing table update verification
4. `test_property_all_replicas_discoverable` - All replicas discoverable
5. `test_property_service_discovery_handles_lifecycle_events` - Pod lifecycle event handling
6. `test_property_service_discovery_with_environment_config` - Environment-specific discovery
7. `test_property_no_traffic_loss_during_discovery_update` - Traffic continuity during updates
8. `test_property_service_discovery_handles_multiple_updates` - Multiple update handling

**Property Statement:**
> For any OAP Server replica added to or removed from the cluster, Satellite should automatically update its routing table to include or exclude that replica within the service discovery interval.

### Property 3: Deployment Script Environment Handling

**File:** `property_test_deployment_environment.py`

**Validates:** Requirements 5.1, 5.5

**Tests:**
1. `test_property_environment_configuration_loads` - Configuration loading
2. `test_property_all_required_components_configured` - Component presence
3. `test_property_environment_specific_settings_applied` - Environment settings
4. `test_property_resource_requests_defined` - Resource definitions
5. `test_property_storage_configuration_valid` - Storage configuration
6. `test_property_high_availability_configuration` - HA features

**Property Statement:**
> For any valid environment parameter (minikube, eks-dev, eks-prod), the deployment script should successfully load the corresponding configuration and deploy all required components.

### Property 18: Persistent Volume Binding

**File:** `property_test_persistent_volume_binding.py`

**Validates:** Requirements 9.7

**Tests:**
1. `test_property_all_pvcs_configured` - All required PVCs configured
2. `test_property_pvc_storage_class_appropriate` - Storage class appropriateness
3. `test_property_bound_pvc_has_volume` - Bound PVC has volume assigned
4. `test_property_binding_check_detects_state` - Binding check state detection
5. `test_property_error_message_describes_failure` - Error message clarity
6. `test_property_pvc_access_mode_is_valid` - Access mode validation
7. `test_property_pvc_volume_mode_is_filesystem` - Volume mode validation
8. `test_property_pvc_size_is_appropriate` - PVC size appropriateness
9. `test_property_all_pvcs_must_be_bound_for_healthy_cluster` - Cluster health dependency
10. `test_property_pvc_configuration_matches_component_requirements` - Component requirements match

**Property Statement:**
> For any persistent volume claim defined in the configuration, the health check should verify the PVC is bound to an available persistent volume.

## Integration Test Details

### Integration Test 1: Full Deployment Workflow

**File:** `integration_test_full_deployment.py`

**Validates:** All requirements

**Tests:**
1. `test_01_deployment_completes_successfully` - Deployment completion
2. `test_02_all_components_healthy` - Component health validation
3. `test_03_connectivity_tests_pass` - Connectivity validation
4. `test_04_data_ingestion_works` - Data ingestion pipeline
5. `test_05_data_visible_in_ui` - UI data visibility
6. `test_06_self_observability_metrics_visible` - Self-observability metrics
7. `test_07_deployment_is_idempotent` - Idempotency validation

**Description:**
> Validates the complete deployment workflow from cluster deployment through data ingestion and visualization. Ensures all components are healthy, connected, and functioning correctly.

### Integration Test 2: Marketplace Features

**File:** `integration_test_marketplace_features.py`

**Validates:** Requirements 11.1-11.10, 13.1-13.9

**Tests:**
1. `test_01_general_services_monitoring` - General services monitoring
2. `test_02_mysql_metrics_visible` - MySQL metrics collection
3. `test_03_redis_metrics_visible` - Redis metrics collection
4. `test_04_rabbitmq_metrics_visible` - RabbitMQ metrics collection
5. `test_05_message_queue_monitoring` - MQ monitoring validation
6. `test_06_activemq_metrics_visible` - ActiveMQ metrics collection
7. `test_07_kubernetes_monitoring` - Kubernetes monitoring validation
8. `test_08_otel_collector_configured` - OTel Collector configuration
9. `test_09_exporters_deployed` - Exporter deployment validation
10. `test_10_marketplace_features_complete_within_time` - Performance validation

**Description:**
> Validates all SkyWalking marketplace features including general services monitoring (MySQL, Redis, RabbitMQ), Kubernetes monitoring, and message queue monitoring. Ensures metrics are collected and visible in the UI.

### Integration Test 3: High Availability

**File:** `integration_test_high_availability.py`

**Validates:** Requirements 18.1-18.10

**Tests:**
1. `test_01_cluster_has_multiple_replicas` - Multiple replica validation
2. `test_02_pod_anti_affinity_configured` - Anti-affinity configuration
3. `test_03_pod_disruption_budgets_configured` - PDB configuration
4. `test_04_kill_oap_server_pod` - Pod failure simulation
5. `test_05_data_ingestion_continues_after_pod_failure` - Ingestion continuity
6. `test_06_ui_remains_accessible_after_pod_failure` - UI availability
7. `test_07_cluster_recovers_automatically` - Automatic recovery
8. `test_08_rolling_update_strategy_configured` - Rolling update validation
9. `test_09_no_data_loss_during_failure` - Data loss prevention
10. `test_10_etcd_cluster_maintains_quorum` - etcd quorum validation

**Description:**
> Validates high availability features by simulating pod failures and verifying the cluster continues to operate correctly. Tests automatic recovery, data ingestion continuity, and UI accessibility during failures.

### Integration Test 4: Data Persistence

**File:** `integration_test_data_persistence.py`

**Validates:** Requirements 8.7, 8.8

**Tests:**
1. `test_01_data_ingestion_successful` - Initial data ingestion
2. `test_02_pvcs_are_bound` - PVC binding validation
3. `test_03_restart_banyandb_data_pods` - BanyanDB restart
4. `test_04_data_still_queryable_after_restart` - Data persistence after BanyanDB restart
5. `test_05_restart_oap_server_pods` - OAP Server restart
6. `test_06_data_still_queryable_after_oap_restart` - Data persistence after OAP restart
7. `test_07_restart_all_components_sequentially` - Sequential component restarts
8. `test_08_final_health_check_after_all_restarts` - Final health validation
9. `test_09_pvcs_still_bound_after_restarts` - PVC persistence
10. `test_10_no_data_loss_after_multiple_restarts` - Data loss prevention

**Description:**
> Validates data persistence across component restarts. Ingests test data, restarts BanyanDB and OAP Server pods, and verifies data remains queryable. Tests that persistent volumes maintain data integrity.

## Troubleshooting

### Import Errors

If you see import errors:

```bash
# Ensure you're in the tests directory
cd skywalking/tests

# Install dependencies
pip install -r requirements.txt
```

### YAML File Not Found

If tests fail with "file not found":

```bash
# Verify helm-values directory structure
ls -la ../helm-values/

# Ensure required files exist:
# - base-values.yaml
# - minikube-values.yaml
```

### Hypothesis Errors

If Hypothesis tests fail:

```bash
# Run with verbose output to see generated examples
pytest property_test_*.py --hypothesis-verbosity=verbose

# Reduce examples for faster debugging
pytest --hypothesis-max-examples=10
```

### Test Skips

Some tests may be skipped if:
- Environment-specific values files don't exist (eks-dev, eks-prod)
- Required components are not configured
- Test prerequisites are not met

This is expected behavior during incremental development.

## CI/CD Integration

### GitHub Actions Example

```yaml
name: Property-Based Tests

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
      - name: Run property-based tests
        run: |
          cd skywalking/tests
          pytest property_test_*.py -v --tb=short
```

## Contributing

When adding new property-based tests:

1. Follow the naming convention: `property_test_<feature>.py`
2. Include property number and description in docstring
3. Tag with feature name: `Feature: skywalking-cluster`
4. Reference validated requirements
5. Use Hypothesis strategies for input generation
6. Set `max_examples=100` for thorough testing
7. Add appropriate pytest markers

Example:

```python
@given(environment=environment_strategy())
@settings(max_examples=100, deadline=None)
def test_property_my_feature(self, environment: str):
    """
    Property X: My Feature Description

    For any valid input, the system should behave correctly.

    Validates: Requirements X.Y, X.Z
    """
    # Test implementation
    pass
```

## References

- [Hypothesis Documentation](https://hypothesis.readthedocs.io/)
- [Pytest Documentation](https://docs.pytest.org/)
- [Property-Based Testing Guide](https://increment.com/testing/in-praise-of-property-based-testing/)
- [SkyWalking Documentation](https://skywalking.apache.org/docs/)

## Test Execution Times

Approximate execution times:

- Property-based tests: 2-5 minutes per file (100 examples)
- Unit tests: < 1 minute
- Integration tests:
  - Full deployment: 20-30 minutes
  - Marketplace features: 15-25 minutes
  - High availability: 15-20 minutes
  - Data persistence: 20-30 minutes
  - All integration tests: 60-90 minutes

Total test suite: ~90-120 minutes for complete validation.

## Integration Test Prerequisites

### Cluster Requirements

Integration tests require a running Kubernetes cluster:

**Minikube:**
- Minimum 6 CPU cores
- Minimum 12GB memory
- Minimum 50GB disk space
- kubectl configured to access Minikube

**EKS:**
- EKS cluster with sufficient node capacity
- kubectl configured with EKS credentials
- EBS CSI driver installed
- Appropriate IAM permissions

### Running Integration Tests

1. **Ensure cluster is running:**
   ```bash
   kubectl cluster-info
   ```

2. **Install test dependencies:**
   ```bash
   cd skywalking/tests
   pip install -r requirements.txt
   ```

3. **Run integration tests:**
   ```bash
   # Run all integration tests
   ./run-integration-tests.sh minikube

   # Run specific test suite
   ./run-integration-tests.sh minikube --test-suite ha

   # Run with verbose output
   ./run-integration-tests.sh minikube --verbose
   ```

4. **Clean up after tests:**
   Integration tests automatically clean up deployed resources after completion.

### Integration Test Options

The `run-integration-tests.sh` script supports:

- `--test-suite SUITE` - Run specific test suite (full, marketplace, ha, persistence, all)
- `--parallel` - Run tests in parallel (faster but uses more resources)
- `--verbose` - Enable verbose output
- `--help` - Display help message

### Integration Test Workflow

Each integration test follows this workflow:

1. **Setup:** Deploy SkyWalking cluster using deployment script
2. **Stabilization:** Wait for cluster to stabilize (60 seconds)
3. **Test Execution:** Run test scenarios
4. **Validation:** Verify expected outcomes
5. **Cleanup:** Remove deployed resources

### Troubleshooting Integration Tests

**Cluster not accessible:**
```bash
# Check cluster connectivity
kubectl cluster-info

# Check cluster nodes
kubectl get nodes
```

**Deployment timeout:**
- Increase timeout in test fixtures
- Check cluster has sufficient resources
- Review deployment logs

**Test failures:**
- Check pod logs: `kubectl logs -n skywalking <pod-name>`
- Review test output for specific error messages
- Verify all prerequisites are met
- Ensure cluster has sufficient resources
