# Property 18: Persistent Volume Binding - Usage Guide

## Overview

This property test validates that all persistent volume claims (PVCs) defined in the SkyWalking cluster configuration are properly configured and can be bound to persistent volumes.

**Property Statement:**
> For any persistent volume claim defined in the configuration, the health check should verify the PVC is bound to an available persistent volume.

**Validates:** Requirements 9.7

## What This Test Validates

### PVC Configuration Validation
- All required PVCs are configured (BanyanDB stream, BanyanDB measure, etcd data)
- PVC configurations are complete with all required fields
- Storage classes are appropriate for the environment
- Access modes are valid and appropriate for components
- Volume modes are set to Filesystem
- PVC sizes are appropriate for the environment

### PVC Binding Verification
- Bound PVCs have volume names assigned
- Bound PVCs have capacity information
- Bound PVCs have access modes configured
- Binding check correctly identifies PVC states
- Error messages describe binding failures clearly

### Component Requirements
- BanyanDB has separate PVCs for stream and measure data
- etcd has PVC for data persistence
- Multi-replica deployments have appropriate PVC configurations

## Running the Tests

### Run All Property 18 Tests

```bash
cd skywalking/tests
pytest property_test_persistent_volume_binding.py -v
```

### Run Specific Test

```bash
# Test PVC configuration
pytest property_test_persistent_volume_binding.py::TestPersistentVolumeBinding::test_property_all_pvcs_configured -v

# Test storage class appropriateness
pytest property_test_persistent_volume_binding.py::TestPersistentVolumeBinding::test_property_pvc_storage_class_appropriate -v

# Test binding check
pytest property_test_persistent_volume_binding.py::TestPersistentVolumeBinding::test_property_binding_check_detects_state -v
```

### Run for Specific Environment

```bash
# Minikube tests only
pytest property_test_persistent_volume_binding.py -v -k minikube

# EKS tests only
pytest property_test_persistent_volume_binding.py -v -k eks
```

### Run with Verbose Hypothesis Output

```bash
pytest property_test_persistent_volume_binding.py -v --hypothesis-verbosity=verbose
```

## Test Cases

### 1. All PVCs Configured
**Test:** `test_property_all_pvcs_configured`

Validates that all required PVCs are configured in the Helm values for each environment.

**Checks:**
- BanyanDB stream PVC exists
- BanyanDB measure PVC exists
- etcd PVC exists
- All PVC configurations are complete

**Example Output:**
```
PASSED property_test_persistent_volume_binding.py::TestPersistentVolumeBinding::test_property_all_pvcs_configured[minikube]
PASSED property_test_persistent_volume_binding.py::TestPersistentVolumeBinding::test_property_all_pvcs_configured[eks]
```

### 2. Storage Class Appropriateness
**Test:** `test_property_pvc_storage_class_appropriate`

Validates that PVCs use storage classes appropriate for the environment.

**Checks:**
- Minikube uses local storage classes (standard, hostpath)
- EKS uses AWS EBS storage classes (gp3, gp2)
- Storage class is specified for all PVCs

**Example Output:**
```
PASSED property_test_persistent_volume_binding.py::TestPersistentVolumeBinding::test_property_pvc_storage_class_appropriate[minikube]
PASSED property_test_persistent_volume_binding.py::TestPersistentVolumeBinding::test_property_pvc_storage_class_appropriate[eks]
```

### 3. Bound PVC Has Volume
**Test:** `test_property_bound_pvc_has_volume`

Validates that PVCs in Bound state have volume name and capacity assigned.

**Checks:**
- Bound PVCs have volumeName set
- Bound PVCs have capacity information
- Bound PVCs have access modes

**Example Output:**
```
PASSED property_test_persistent_volume_binding.py::TestPersistentVolumeBinding::test_property_bound_pvc_has_volume
```

### 4. Binding Check Detects State
**Test:** `test_property_binding_check_detects_state`

Validates that the binding check correctly identifies whether a PVC is bound.

**Checks:**
- Bound PVCs pass the binding check
- Pending PVCs fail the binding check
- Lost PVCs fail the binding check

**Example Output:**
```
PASSED property_test_persistent_volume_binding.py::TestPersistentVolumeBinding::test_property_binding_check_detects_state
```

### 5. Error Message Describes Failure
**Test:** `test_property_error_message_describes_failure`

Validates that error messages for binding failures are clear and actionable.

**Checks:**
- Error messages include PVC name
- Error messages include component name
- Error messages describe the failure state
- Error messages provide actionable information

**Example Output:**
```
PASSED property_test_persistent_volume_binding.py::TestPersistentVolumeBinding::test_property_error_message_describes_failure
```

### 6. Access Mode Validation
**Test:** `test_property_pvc_access_mode_is_valid`

Validates that PVC access modes are valid and appropriate for components.

**Checks:**
- Access mode is one of the valid Kubernetes access modes
- BanyanDB PVCs use ReadWriteOnce
- etcd PVCs use ReadWriteOnce

**Example Output:**
```
PASSED property_test_persistent_volume_binding.py::TestPersistentVolumeBinding::test_property_pvc_access_mode_is_valid[minikube]
PASSED property_test_persistent_volume_binding.py::TestPersistentVolumeBinding::test_property_pvc_access_mode_is_valid[eks]
```

### 7. Volume Mode is Filesystem
**Test:** `test_property_pvc_volume_mode_is_filesystem`

Validates that all PVCs use Filesystem volume mode.

**Checks:**
- Volume mode is specified
- Volume mode is Filesystem
- All components use Filesystem mode

**Example Output:**
```
PASSED property_test_persistent_volume_binding.py::TestPersistentVolumeBinding::test_property_pvc_volume_mode_is_filesystem[minikube]
PASSED property_test_persistent_volume_binding.py::TestPersistentVolumeBinding::test_property_pvc_volume_mode_is_filesystem[eks]
```

### 8. PVC Size Appropriateness
**Test:** `test_property_pvc_size_is_appropriate`

Validates that PVC sizes are appropriate for the environment type.

**Checks:**
- Minikube uses smaller PVC sizes (10Gi)
- EKS uses larger PVC sizes (50Gi+)
- All PVC sizes are in valid format

**Example Output:**
```
PASSED property_test_persistent_volume_binding.py::TestPersistentVolumeBinding::test_property_pvc_size_is_appropriate[minikube]
PASSED property_test_persistent_volume_binding.py::TestPersistentVolumeBinding::test_property_pvc_size_is_appropriate[eks]
```

### 9. All PVCs Must Be Bound
**Test:** `test_property_all_pvcs_must_be_bound_for_healthy_cluster`

Validates that all PVCs must be bound for cluster health.

**Checks:**
- Health check validates all PVCs
- Any unbound PVC causes health check to fail
- All PVCs must be bound for cluster health

**Example Output:**
```
PASSED property_test_persistent_volume_binding.py::TestPersistentVolumeBinding::test_property_all_pvcs_must_be_bound_for_healthy_cluster
```

### 10. Component Requirements Match
**Test:** `test_property_pvc_configuration_matches_component_requirements`

Validates that PVC configurations match component requirements.

**Checks:**
- BanyanDB has separate PVCs for stream and measure data
- etcd has PVC for data persistence
- Each component's PVC has appropriate configuration

**Example Output:**
```
PASSED property_test_persistent_volume_binding.py::TestPersistentVolumeBinding::test_property_pvc_configuration_matches_component_requirements[minikube]
PASSED property_test_persistent_volume_binding.py::TestPersistentVolumeBinding::test_property_pvc_configuration_matches_component_requirements[eks]
```

## Expected Test Results

### Successful Run

```bash
$ pytest property_test_persistent_volume_binding.py -v

property_test_persistent_volume_binding.py::TestPersistentVolumeBinding::test_property_all_pvcs_configured[minikube] PASSED
property_test_persistent_volume_binding.py::TestPersistentVolumeBinding::test_property_all_pvcs_configured[eks] PASSED
property_test_persistent_volume_binding.py::TestPersistentVolumeBinding::test_property_pvc_storage_class_appropriate[minikube] PASSED
property_test_persistent_volume_binding.py::TestPersistentVolumeBinding::test_property_pvc_storage_class_appropriate[eks] PASSED
property_test_persistent_volume_binding.py::TestPersistentVolumeBinding::test_property_bound_pvc_has_volume PASSED
property_test_persistent_volume_binding.py::TestPersistentVolumeBinding::test_property_binding_check_detects_state PASSED
property_test_persistent_volume_binding.py::TestPersistentVolumeBinding::test_property_error_message_describes_failure PASSED
property_test_persistent_volume_binding.py::TestPersistentVolumeBinding::test_property_pvc_access_mode_is_valid[minikube] PASSED
property_test_persistent_volume_binding.py::TestPersistentVolumeBinding::test_property_pvc_access_mode_is_valid[eks] PASSED
property_test_persistent_volume_binding.py::TestPersistentVolumeBinding::test_property_pvc_volume_mode_is_filesystem[minikube] PASSED
property_test_persistent_volume_binding.py::TestPersistentVolumeBinding::test_property_pvc_volume_mode_is_filesystem[eks] PASSED
property_test_persistent_volume_binding.py::TestPersistentVolumeBinding::test_property_pvc_size_is_appropriate[minikube] PASSED
property_test_persistent_volume_binding.py::TestPersistentVolumeBinding::test_property_pvc_size_is_appropriate[eks] PASSED
property_test_persistent_volume_binding.py::TestPersistentVolumeBinding::test_property_all_pvcs_must_be_bound_for_healthy_cluster PASSED
property_test_persistent_volume_binding.py::TestPersistentVolumeBinding::test_property_pvc_configuration_matches_component_requirements[minikube] PASSED
property_test_persistent_volume_binding.py::TestPersistentVolumeBinding::test_property_pvc_configuration_matches_component_requirements[eks] PASSED

============================== 16 passed in 45.23s ==============================
```

## Troubleshooting

### Test Failures

#### Missing PVC Configuration

**Error:**
```
AssertionError: No PVCs configured in environment: minikube
```

**Solution:**
- Verify `helm-values/minikube-values.yaml` has BanyanDB and etcd storage configuration
- Check that storage sections are not commented out
- Ensure storage sizes and storage classes are specified

#### Invalid Storage Class

**Error:**
```
AssertionError: Storage class 'gp3' not appropriate for environment: minikube
```

**Solution:**
- Minikube should use `standard` or `hostpath` storage class
- EKS should use `gp3`, `gp2`, or other AWS EBS storage classes
- Update the environment-specific values file with correct storage class

#### Invalid Access Mode

**Error:**
```
AssertionError: Invalid access mode 'ReadWriteMany' for PVC banyandb-stream in environment: eks
```

**Solution:**
- BanyanDB and etcd should use `ReadWriteOnce` access mode
- Update the PVC configuration to use correct access mode

#### Invalid Volume Mode

**Error:**
```
AssertionError: PVC banyandb-stream should use Filesystem volume mode, got: Block
```

**Solution:**
- All PVCs should use `Filesystem` volume mode
- Update the PVC configuration to use Filesystem mode

#### Inappropriate PVC Size

**Error:**
```
AssertionError: PVC size too large for Minikube: 100Gi for banyandb-stream
```

**Solution:**
- Minikube should use smaller PVC sizes (typically 10Gi)
- EKS should use larger PVC sizes (typically 50Gi+)
- Update the environment-specific values file with appropriate sizes

### Test Skips

Some tests may be skipped if:
- Environment-specific values files don't exist
- Components are not enabled in configuration
- Required storage configuration is missing

This is expected during incremental development.

## Integration with Health Check Script

This property test validates the configuration that will be used by the health check script (`test-health.sh`).

The health check script should:
1. List all PVCs in the namespace
2. Check each PVC status
3. Verify all PVCs are in Bound state
4. Report any unbound PVCs with details

Example health check implementation:

```bash
#!/bin/bash

# Check PVC binding status
check_pvc_binding() {
    local namespace=$1

    echo "Checking PVC binding status..."

    # Get all PVCs
    pvcs=$(kubectl get pvc -n "$namespace" -o json)

    # Check each PVC
    unbound_pvcs=()

    while IFS= read -r pvc_name; do
        phase=$(kubectl get pvc "$pvc_name" -n "$namespace" -o jsonpath='{.status.phase}')

        if [ "$phase" != "Bound" ]; then
            unbound_pvcs+=("$pvc_name:$phase")
        fi
    done < <(kubectl get pvc -n "$namespace" -o jsonpath='{.items[*].metadata.name}')

    # Report results
    if [ ${#unbound_pvcs[@]} -eq 0 ]; then
        echo "✓ All PVCs are bound"
        return 0
    else
        echo "✗ Unbound PVCs found:"
        for pvc in "${unbound_pvcs[@]}"; do
            echo "  - $pvc"
        done
        return 1
    fi
}
```

## References

- [Kubernetes Persistent Volumes](https://kubernetes.io/docs/concepts/storage/persistent-volumes/)
- [Kubernetes Storage Classes](https://kubernetes.io/docs/concepts/storage/storage-classes/)
- [BanyanDB Storage Requirements](https://skywalking.apache.org/docs/skywalking-banyandb/latest/readme/)
- [SkyWalking Helm Chart](https://github.com/apache/skywalking-kubernetes)

## Related Tests

- **Property 16**: Component Health Validation - Validates pod health including PVC usage
- **Property 17**: etcd Cluster Quorum - Validates etcd cluster health which depends on PVC binding
- **Property 19**: Service API Responsiveness - Validates services that depend on persistent storage

## Contributing

When modifying this test:

1. Maintain the property-based testing approach with 100 examples
2. Keep test cases focused on PVC configuration and binding validation
3. Update this usage guide with any new test cases
4. Ensure error messages are clear and actionable
5. Test with both Minikube and EKS configurations
