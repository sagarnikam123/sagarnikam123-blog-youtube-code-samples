# Property 4: Deployment Script Prerequisite Validation - Usage Guide

## Overview

This property-based test validates that the deployment script correctly detects and reports missing prerequisites before making any cluster modifications.

**Feature**: skywalking-cluster
**Property**: Property 4 - Deployment Script Prerequisite Validation
**Validates**: Requirements 5.2, 5.10

## What This Test Validates

The test ensures that for any missing prerequisite (kubectl, helm, cluster connectivity, or insufficient resources), the deployment script:

1. **Detects the missing prerequisite** - Script identifies what is missing
2. **Exits before making changes** - No cluster modifications occur
3. **Reports specific issues** - Clear error messages indicate what failed
4. **Provides actionable guidance** - Error messages include remediation steps

## Test Scenarios

### 1. Missing Command Detection
- **Scenario**: kubectl or helm is not installed or not in PATH
- **Expected**: Script fails with error message naming the missing command
- **Validation**: No namespace or resources created

### 2. Cluster Connectivity Failure
- **Scenario**: Cannot connect to Kubernetes cluster
- **Expected**: Script fails with connectivity error message
- **Validation**: No deployment attempted

### 3. Insufficient Minikube Resources
- **Scenario**: Minikube has less than 6 CPU cores or 12GB memory
- **Expected**: Script fails with resource constraint message
- **Validation**: Provides command to start Minikube with correct resources

### 4. Missing Storage Class
- **Scenario**: Required storage class (standard/gp3) not available
- **Expected**: Script fails with storage class error
- **Validation**: Lists available storage classes or provides creation command

### 5. Kubernetes Version Incompatibility
- **Scenario**: Kubernetes version below v1.19
- **Expected**: Script warns about incompatibility
- **Validation**: Continues with warning (non-blocking)

### 6. Prerequisite Check Order
- **Scenario**: Multiple prerequisites missing
- **Expected**: Script fails at first missing prerequisite
- **Validation**: Checks occur in correct order

## Running the Tests

### Run All Property 4 Tests

```bash
cd skywalking/tests
pytest property_test_prerequisite_validation.py -v
```

### Run Specific Test Scenario

```bash
# Test missing command detection
pytest property_test_prerequisite_validation.py::TestPrerequisiteValidation::test_property_missing_command_detected -v

# Test cluster connectivity failures
pytest property_test_prerequisite_validation.py::TestPrerequisiteValidation::test_property_cluster_connectivity_failure_detected -v

# Test prerequisite check order
pytest property_test_prerequisite_validation.py::TestPrerequisiteValidation::test_property_prerequisite_check_order -v

# Test error message quality
pytest property_test_prerequisite_validation.py::TestPrerequisiteValidation::test_property_error_messages_are_actionable -v
```

### Run with Hypothesis Statistics

```bash
pytest property_test_prerequisite_validation.py -v --hypothesis-show-statistics
```

### Run with Verbose Hypothesis Output

```bash
pytest property_test_prerequisite_validation.py -v --hypothesis-verbosity=verbose
```

## Test Configuration

### Hypothesis Settings
- **Max Examples**: 100 iterations per test
- **Deadline**: None (no time limit per example)
- **Shrinking**: Enabled (finds minimal failing examples)

### Test Data Generation

The tests use Hypothesis strategies to generate:

1. **Missing Command Scenarios**
   - Command: kubectl or helm
   - Environment: minikube, eks-dev, or eks-prod

2. **Connectivity Failure Scenarios**
   - Error types: connection_refused, timeout, authentication_failed, cluster_unreachable
   - Environment: any valid environment

3. **Insufficient Resource Scenarios**
   - CPU: 1-5 cores (below minimum of 6)
   - Memory: 4-11 GB (below minimum of 12)
   - Environment: minikube only

4. **Storage Class Missing Scenarios**
   - Expected class: standard (Minikube) or gp3 (EKS)
   - Environment: any valid environment

## Expected Test Results

### Successful Test Run

```
============================= test session starts ==============================
collected 9 items

property_test_prerequisite_validation.py::TestPrerequisiteValidation::test_property_missing_command_detected PASSED [11%]
property_test_prerequisite_validation.py::TestPrerequisiteValidation::test_property_cluster_connectivity_failure_detected PASSED [22%]
property_test_prerequisite_validation.py::TestPrerequisiteValidation::test_property_insufficient_minikube_resources_detected SKIPPED [33%]
property_test_prerequisite_validation.py::TestPrerequisiteValidation::test_property_storage_class_missing_detected SKIPPED [44%]
property_test_prerequisite_validation.py::TestPrerequisiteValidation::test_property_prerequisite_check_order PASSED [55%]
property_test_prerequisite_validation.py::TestPrerequisiteValidation::test_property_error_messages_are_actionable PASSED [66%]
property_test_prerequisite_validation.py::TestPrerequisiteValidation::test_property_dry_run_skips_prerequisite_failures PASSED [77%]
property_test_prerequisite_validation.py::TestPrerequisiteValidation::test_property_prerequisite_validation_exit_codes PASSED [88%]

======================== 7 passed, 2 skipped in 45.23s =========================
```

### Skipped Tests

Some tests are skipped because they require specific cluster conditions:

- **Insufficient Resources Test**: Requires actual Minikube with constrained resources
- **Storage Class Missing Test**: Requires cluster without required storage class

These tests validate the logic but skip actual execution when conditions cannot be simulated.

## Interpreting Test Failures

### Test Failure: Missing Command Not Detected

```
AssertionError: Script should fail when kubectl is missing, but returned 0
```

**Cause**: Script did not detect missing kubectl command
**Fix**: Verify `check_command` function in deployment script

### Test Failure: Cluster Modifications Made

```
AssertionError: Script should not modify cluster when prerequisites are missing
```

**Cause**: Script created resources despite prerequisite failure
**Fix**: Ensure prerequisite checks occur before deployment steps

### Test Failure: Error Message Not Actionable

```
AssertionError: Error type 'missing_command' should have actionable error messages
```

**Cause**: Error messages lack guidance or remediation steps
**Fix**: Add `print_info` calls with remediation guidance

## Integration with CI/CD

### GitHub Actions Example

```yaml
name: Property Tests - Prerequisites

on: [push, pull_request]

jobs:
  test-prerequisites:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.9'

      - name: Install dependencies
        run: |
          cd skywalking/tests
          pip install -r requirements.txt

      - name: Run Property 4 Tests
        run: |
          cd skywalking/tests
          pytest property_test_prerequisite_validation.py -v --tb=short
```

### Pre-commit Hook

```bash
#!/bin/bash
# .git/hooks/pre-commit

echo "Running prerequisite validation property tests..."
cd skywalking/tests
pytest property_test_prerequisite_validation.py -v --tb=short

if [ $? -ne 0 ]; then
    echo "Property tests failed. Please fix before committing."
    exit 1
fi
```

## Troubleshooting

### Issue: Tests Timeout

**Symptom**: Tests hang or timeout
**Solution**: Increase timeout in `run_deployment_script` method or check cluster connectivity

### Issue: Cannot Simulate Missing Commands

**Symptom**: Test skipped with "Cannot simulate missing command"
**Solution**: This is expected if command is not in PATH. Test validates logic is sound.

### Issue: Cluster Modifications Check Fails

**Symptom**: `check_no_cluster_modifications` returns False
**Solution**: Clean up test namespace before running tests:

```bash
kubectl delete namespace skywalking --ignore-not-found=true
```

### Issue: Hypothesis Finds Unexpected Failure

**Symptom**: Test fails with specific generated input
**Solution**: Hypothesis will shrink to minimal failing example. Review the example and fix the deployment script logic.

## Best Practices

1. **Run tests before committing changes** to deployment script
2. **Review Hypothesis statistics** to understand test coverage
3. **Add new test scenarios** when adding new prerequisites
4. **Keep tests fast** by using dry-run mode and mocking where appropriate
5. **Document skipped tests** and conditions required to run them

## Related Documentation

- [Deployment Script](../scripts/deploy-skywalking-cluster.sh)
- [Requirements Document](../../.kiro/specs/skywalking-cluster/requirements.md) - Requirements 5.2, 5.10
- [Design Document](../../.kiro/specs/skywalking-cluster/design.md) - Property 4
- [Testing Guide](../docs/TESTING.md)

## Property Test Theory

Property-based testing validates universal behaviors across many randomly generated inputs. For prerequisite validation:

- **Property**: "For any missing prerequisite, script fails before making changes"
- **Inputs**: Various combinations of missing commands, connectivity failures, resource constraints
- **Validation**: Script behavior is consistent across all scenarios
- **Benefit**: Catches edge cases that manual testing might miss

## Maintenance

When modifying the deployment script:

1. **Adding new prerequisites**: Add corresponding test scenario
2. **Changing error messages**: Update error pattern assertions
3. **Modifying check order**: Update `test_property_prerequisite_check_order`
4. **Adding new environments**: Add to `VALID_ENVIRONMENTS` list

## Support

For issues or questions:
- Review [FAQ](../docs/FAQ.md)
- Check [Troubleshooting Guide](../docs/TROUBLESHOOTING.md)
- Open an issue with test output and Hypothesis statistics
