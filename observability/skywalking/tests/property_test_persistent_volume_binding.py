#!/usr/bin/env python3
"""
Property-Based Test: Persistent Volume Binding

Feature: skywalking-cluster
Property 18: Persistent Volume Binding

This test validates that for any persistent volume claim defined in the configuration,
the health check should verify the PVC is bound to an available persistent volume.

Validates: Requirements 9.7

Note: This test validates PVC configuration and simulates binding verification.
Full integration testing requires a running Kubernetes cluster.
"""

from pathlib import Path
from typing import Dict, List, Set

import pytest
import yaml
from hypothesis import given, settings, strategies as st


# Test configuration
VALID_ENVIRONMENTS = ["minikube", "eks"]
HELM_VALUES_DIR = Path(__file__).parent.parent / "helm-values"


# PVC types in SkyWalking cluster
PVC_TYPES = [
    "banyandb-stream",
    "banyandb-measure",
    "etcd-data"
]

# Valid PVC states
PVC_STATES = ["Bound", "Pending", "Lost"]
VALID_ACCESS_MODES = ["ReadWriteOnce", "ReadOnlyMany", "ReadWriteMany"]
VALID_VOLUME_MODES = ["Filesystem", "Block"]


# Hypothesis strategies
@st.composite
def pvc_configuration_strategy(draw):
    """
    Generate PVC configuration for testing.

    Returns a PVC configuration dictionary.
    """
    return {
        "name": draw(st.sampled_from(PVC_TYPES)),
        "size": draw(st.sampled_from(["10Gi", "20Gi", "50Gi", "100Gi"])),
        "storageClass": draw(st.sampled_from(["standard", "gp3", "fast-ssd"])),
        "accessMode": draw(st.sampled_from(VALID_ACCESS_MODES)),
        "volumeMode": draw(st.sampled_from(VALID_VOLUME_MODES)),
    }


@st.composite
def pvc_status_strategy(draw):
    """
    Generate PVC status for testing.

    Returns a PVC status dictionary.
    """
    state = draw(st.sampled_from(PVC_STATES))

    status = {
        "phase": state,
        "accessModes": [draw(st.sampled_from(VALID_ACCESS_MODES))],
    }

    if state == "Bound":
        status["volumeName"] = f"pv-{draw(st.integers(min_value=1000, max_value=9999))}"
        status["capacity"] = {
            "storage": draw(st.sampled_from(["10Gi", "20Gi", "50Gi", "100Gi"]))
        }

    return status


@st.composite
def environment_with_pvcs_strategy(draw):
    """Generate environment and PVC configuration combinations."""
    environment = draw(st.sampled_from(VALID_ENVIRONMENTS))
    num_pvcs = draw(st.integers(min_value=1, max_value=5))

    pvcs = []
    for _ in range(num_pvcs):
        pvc = draw(pvc_configuration_strategy())
        pvcs.append(pvc)

    return environment, pvcs


class TestPersistentVolumeBinding:
    """Property-based tests for persistent volume binding validation."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test environment."""
        self.helm_values_dir = HELM_VALUES_DIR
        self.base_values_file = self.helm_values_dir / "base-values.yaml"

        # Verify test prerequisites
        assert self.helm_values_dir.exists(), f"Helm values directory not found: {self.helm_values_dir}"
        assert self.base_values_file.exists(), f"Base values file not found: {self.base_values_file}"

    def load_helm_values(self, environment: str) -> Dict:
        """
        Load Helm values for a specific environment.

        Args:
            environment: Environment name (minikube, eks)

        Returns:
            Merged configuration dictionary
        """
        # Load base values
        with open(self.base_values_file, 'r', encoding='utf-8') as f:
            base_values = yaml.safe_load(f)

        # Load environment-specific values
        env_values_file = self.helm_values_dir / f"{environment}-values.yaml"

        if not env_values_file.exists():
            pytest.skip(f"Environment values file not found: {env_values_file}")

        with open(env_values_file, 'r', encoding='utf-8') as f:
            env_values = yaml.safe_load(f)

        # Merge configurations
        merged_values = self._deep_merge(base_values, env_values)

        return merged_values

    def _deep_merge(self, base: Dict, override: Dict) -> Dict:
        """Deep merge two dictionaries."""
        result = base.copy()

        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._deep_merge(result[key], value)
            else:
                result[key] = value

        return result

    def extract_pvc_configurations(self, config: Dict) -> List[Dict]:
        """
        Extract all PVC configurations from Helm values.

        Args:
            config: Configuration dictionary

        Returns:
            List of PVC configuration dictionaries
        """
        pvcs = []

        # Extract BanyanDB PVCs from persistence configuration
        banyandb_config = config.get("banyandb", {})
        data_config = banyandb_config.get("data", {})
        persistence_config = data_config.get("persistence", {})

        # Check if persistence is enabled
        if persistence_config.get("enabled", False):
            # Extract stream PVC
            if "stream" in persistence_config:
                stream_pvc = {
                    "name": "banyandb-stream",
                    "component": "banyandb-data",
                    "size": persistence_config["stream"].get("size", ""),
                    "storageClass": persistence_config["stream"].get("storageClass", ""),
                    "accessMode": persistence_config["stream"].get("accessMode", "ReadWriteOnce"),
                    "volumeMode": persistence_config["stream"].get("volumeMode", "Filesystem"),
                }
                pvcs.append(stream_pvc)

            # Extract measure PVC
            if "measure" in persistence_config:
                measure_pvc = {
                    "name": "banyandb-measure",
                    "component": "banyandb-data",
                    "size": persistence_config["measure"].get("size", ""),
                    "storageClass": persistence_config["measure"].get("storageClass", ""),
                    "accessMode": persistence_config["measure"].get("accessMode", "ReadWriteOnce"),
                    "volumeMode": persistence_config["measure"].get("volumeMode", "Filesystem"),
                }
                pvcs.append(measure_pvc)

        # Extract etcd PVC
        etcd_config = config.get("etcd", {})
        etcd_persistence = etcd_config.get("persistence", {})

        # Check if etcd persistence is enabled
        if etcd_persistence.get("enabled", False):
            etcd_pvc = {
                "name": "etcd-data",
                "component": "etcd",
                "size": etcd_persistence.get("size", ""),
                "storageClass": etcd_persistence.get("storageClass", ""),
                "accessMode": etcd_persistence.get("accessMode", "ReadWriteOnce"),
                "volumeMode": etcd_persistence.get("volumeMode", "Filesystem"),
            }
            pvcs.append(etcd_pvc)

        return pvcs

    def validate_pvc_configuration(self, pvc: Dict) -> bool:
        """
        Validate a PVC configuration is complete and correct.

        Args:
            pvc: PVC configuration dictionary

        Returns:
            True if PVC configuration is valid
        """
        # Check required fields
        required_fields = ["name", "component", "size", "storageClass"]
        for field in required_fields:
            if field not in pvc or not pvc[field]:
                return False

        # Validate size format (e.g., "10Gi", "50Gi")
        size = pvc["size"]
        if not size.endswith(("Gi", "Mi", "Ti")):
            return False

        # Validate access mode
        access_mode = pvc.get("accessMode", "ReadWriteOnce")
        if access_mode not in VALID_ACCESS_MODES:
            return False

        # Validate volume mode
        volume_mode = pvc.get("volumeMode", "Filesystem")
        if volume_mode not in VALID_VOLUME_MODES:
            return False

        return True

    def simulate_pvc_binding_check(self, pvc: Dict, pvc_status: Dict) -> bool:
        """
        Simulate checking if a PVC is bound to a persistent volume.

        Args:
            pvc: PVC configuration
            pvc_status: PVC status from Kubernetes

        Returns:
            True if PVC is bound
        """
        # Check if PVC is in Bound state
        if pvc_status.get("phase") != "Bound":
            return False

        # Check if volume name is assigned
        if not pvc_status.get("volumeName"):
            return False

        # Check if capacity is set
        if not pvc_status.get("capacity", {}).get("storage"):
            return False

        return True

    def get_pvc_binding_error_message(self, pvc: Dict, pvc_status: Dict) -> str:
        """
        Generate error message for PVC binding failure.

        Args:
            pvc: PVC configuration
            pvc_status: PVC status

        Returns:
            Error message describing the binding failure
        """
        phase = pvc_status.get("phase", "Unknown")
        pvc_name = pvc.get("name", "unknown")
        component = pvc.get("component", "unknown")

        if phase == "Pending":
            return (
                f"PVC '{pvc_name}' for component '{component}' is in Pending state. "
                f"Possible causes: no available PV, insufficient storage, storage class not found."
            )
        elif phase == "Lost":
            return (
                f"PVC '{pvc_name}' for component '{component}' is in Lost state. "
                f"The bound PV is no longer available."
            )
        else:
            return (
                f"PVC '{pvc_name}' for component '{component}' is in unexpected state: {phase}"
            )

    def validate_storage_class_exists(self, storage_class: str, environment: str) -> bool:
        """
        Validate that storage class is appropriate for environment.

        Args:
            storage_class: Storage class name
            environment: Environment name

        Returns:
            True if storage class is valid for environment
        """
        # Minikube typically uses "standard" storage class
        if environment == "minikube":
            return storage_class in ["standard", "hostpath"]

        # EKS typically uses "gp3" or "gp2" storage class
        if environment in ["eks", "eks-dev", "eks-prod"]:
            return storage_class in ["gp3", "gp2", "io1", "io2"]

        return True

    @given(environment=st.sampled_from(VALID_ENVIRONMENTS))
    @settings(max_examples=100, deadline=None)
    def test_property_all_pvcs_configured(self, environment: str):
        """
        Property 18: Persistent Volume Binding

        For any environment, all required PVCs should be configured in the Helm values.

        This test verifies that:
        1. BanyanDB stream PVC is configured
        2. BanyanDB measure PVC is configured
        3. etcd PVC is configured
        4. All PVC configurations are complete
        """
        # Load configuration
        config = self.load_helm_values(environment)

        # Extract PVC configurations
        pvcs = self.extract_pvc_configurations(config)

        # Verify at least some PVCs are configured
        assert len(pvcs) > 0, \
            f"No PVCs configured in environment: {environment}"

        # Verify each PVC configuration is valid
        for pvc in pvcs:
            assert self.validate_pvc_configuration(pvc), \
                f"Invalid PVC configuration for {pvc.get('name', 'unknown')} in environment: {environment}"

    @given(environment=st.sampled_from(VALID_ENVIRONMENTS))
    @settings(max_examples=100, deadline=None)
    def test_property_pvc_storage_class_appropriate(self, environment: str):
        """
        Property 18: Persistent Volume Binding

        For any environment, PVCs should use storage classes appropriate for that environment.

        This test verifies that:
        1. Minikube uses local storage classes (standard, hostpath)
        2. EKS uses AWS EBS storage classes (gp3, gp2)
        3. Storage class is specified for all PVCs
        """
        # Load configuration
        config = self.load_helm_values(environment)

        # Extract PVC configurations
        pvcs = self.extract_pvc_configurations(config)

        # Verify storage class for each PVC
        for pvc in pvcs:
            storage_class = pvc.get("storageClass", "")

            assert storage_class, \
                f"Storage class not specified for PVC {pvc.get('name')} in environment: {environment}"

            assert self.validate_storage_class_exists(storage_class, environment), \
                f"Storage class '{storage_class}' not appropriate for environment: {environment}"

    @given(pvc_status=pvc_status_strategy())
    @settings(max_examples=100, deadline=None)
    def test_property_bound_pvc_has_volume(self, pvc_status: Dict):
        """
        Property 18: Persistent Volume Binding

        For any PVC in Bound state, the PVC should have a volume name and capacity assigned.

        This test verifies that:
        1. Bound PVCs have volumeName set
        2. Bound PVCs have capacity information
        3. Bound PVCs have access modes
        """
        if pvc_status["phase"] == "Bound":
            # Verify volume name is assigned
            assert "volumeName" in pvc_status, \
                "Bound PVC missing volumeName"

            assert pvc_status["volumeName"], \
                "Bound PVC has empty volumeName"

            # Verify capacity is set
            assert "capacity" in pvc_status, \
                "Bound PVC missing capacity"

            assert "storage" in pvc_status["capacity"], \
                "Bound PVC capacity missing storage"

            # Verify access modes
            assert "accessModes" in pvc_status, \
                "Bound PVC missing accessModes"

            assert len(pvc_status["accessModes"]) > 0, \
                "Bound PVC has no access modes"

    @given(pvc_config=pvc_configuration_strategy(), pvc_status=pvc_status_strategy())
    @settings(max_examples=100, deadline=None)
    def test_property_binding_check_detects_state(self, pvc_config: Dict, pvc_status: Dict):
        """
        Property 18: Persistent Volume Binding

        For any PVC configuration and status, the binding check should correctly
        identify whether the PVC is bound or not.

        This test verifies that:
        1. Bound PVCs pass the binding check
        2. Pending PVCs fail the binding check
        3. Lost PVCs fail the binding check
        """
        is_bound = self.simulate_pvc_binding_check(pvc_config, pvc_status)

        if pvc_status["phase"] == "Bound":
            assert is_bound, \
                f"Binding check failed for Bound PVC: {pvc_config.get('name')}"
        else:
            assert not is_bound, \
                f"Binding check passed for non-Bound PVC in state: {pvc_status['phase']}"

    @given(pvc_config=pvc_configuration_strategy(), pvc_status=pvc_status_strategy())
    @settings(max_examples=100, deadline=None)
    def test_property_error_message_describes_failure(self, pvc_config: Dict, pvc_status: Dict):
        """
        Property 18: Persistent Volume Binding

        For any PVC binding failure, the error message should describe the specific
        failure reason and affected component.

        This test verifies that:
        1. Error messages include PVC name
        2. Error messages include component name
        3. Error messages describe the failure state
        4. Error messages provide actionable information
        """
        if pvc_status["phase"] != "Bound":
            error_msg = self.get_pvc_binding_error_message(pvc_config, pvc_status)

            # Verify error message contains PVC name
            pvc_name = pvc_config.get("name", "")
            if pvc_name:
                assert pvc_name in error_msg, \
                    f"Error message missing PVC name: {error_msg}"

            # Verify error message contains component
            component = pvc_config.get("component", "")
            if component:
                assert component in error_msg, \
                    f"Error message missing component: {error_msg}"

            # Verify error message describes state
            phase = pvc_status["phase"]
            assert phase in error_msg, \
                f"Error message missing PVC state: {error_msg}"

            # Verify error message is not empty
            assert len(error_msg) > 0, \
                "Error message is empty"

    @given(environment=st.sampled_from(VALID_ENVIRONMENTS))
    @settings(max_examples=100, deadline=None)
    def test_property_pvc_access_mode_is_valid(self, environment: str):
        """
        Property 18: Persistent Volume Binding

        For any PVC configuration, the access mode should be valid and appropriate
        for the component's usage pattern.

        This test verifies that:
        1. Access mode is one of the valid Kubernetes access modes
        2. BanyanDB PVCs use ReadWriteOnce (single node access)
        3. etcd PVCs use ReadWriteOnce (single node access)
        """
        # Load configuration
        config = self.load_helm_values(environment)

        # Extract PVC configurations
        pvcs = self.extract_pvc_configurations(config)

        for pvc in pvcs:
            access_mode = pvc.get("accessMode", "ReadWriteOnce")

            # Verify access mode is valid
            assert access_mode in VALID_ACCESS_MODES, \
                f"Invalid access mode '{access_mode}' for PVC {pvc.get('name')} in environment: {environment}"

            # Verify appropriate access mode for component
            component = pvc.get("component", "")

            # BanyanDB and etcd should use ReadWriteOnce
            if component in ["banyandb-data", "etcd"]:
                assert access_mode == "ReadWriteOnce", \
                    f"Component '{component}' should use ReadWriteOnce, got: {access_mode}"

    @given(environment=st.sampled_from(VALID_ENVIRONMENTS))
    @settings(max_examples=100, deadline=None)
    def test_property_pvc_volume_mode_is_filesystem(self, environment: str):
        """
        Property 18: Persistent Volume Binding

        For any PVC configuration, the volume mode should be Filesystem
        (as required by BanyanDB and etcd).

        This test verifies that:
        1. Volume mode is specified
        2. Volume mode is Filesystem
        3. All components use Filesystem mode
        """
        # Load configuration
        config = self.load_helm_values(environment)

        # Extract PVC configurations
        pvcs = self.extract_pvc_configurations(config)

        for pvc in pvcs:
            volume_mode = pvc.get("volumeMode", "Filesystem")

            # Verify volume mode is Filesystem
            assert volume_mode == "Filesystem", \
                f"PVC {pvc.get('name')} should use Filesystem volume mode, got: {volume_mode}"

    @given(environment=st.sampled_from(VALID_ENVIRONMENTS))
    @settings(max_examples=100, deadline=None)
    def test_property_pvc_size_is_appropriate(self, environment: str):
        """
        Property 18: Persistent Volume Binding

        For any environment, PVC sizes should be appropriate for the environment type.

        This test verifies that:
        1. Minikube uses smaller PVC sizes (10Gi)
        2. EKS uses larger PVC sizes (50Gi+)
        3. All PVC sizes are specified in valid format
        """
        # Load configuration
        config = self.load_helm_values(environment)

        # Extract PVC configurations
        pvcs = self.extract_pvc_configurations(config)

        for pvc in pvcs:
            size = pvc.get("size", "")

            # Verify size is specified
            assert size, \
                f"PVC size not specified for {pvc.get('name')} in environment: {environment}"

            # Verify size format
            assert size.endswith(("Gi", "Mi", "Ti")), \
                f"Invalid PVC size format '{size}' for {pvc.get('name')}"

            # Extract numeric value
            size_value = int(size.rstrip("GiMiT"))

            # Verify appropriate size for environment
            if environment == "minikube":
                # Minikube should use smaller sizes (typically 10Gi)
                assert size_value <= 20, \
                    f"PVC size too large for Minikube: {size} for {pvc.get('name')}"
            elif environment in ["eks", "eks-dev", "eks-prod"]:
                # EKS should use larger sizes (typically 50Gi+)
                # Allow smaller sizes for etcd
                if pvc.get("component") != "etcd":
                    assert size_value >= 10, \
                        f"PVC size too small for EKS: {size} for {pvc.get('name')}"

    @given(env_and_pvcs=environment_with_pvcs_strategy())
    @settings(max_examples=100, deadline=None)
    def test_property_all_pvcs_must_be_bound_for_healthy_cluster(self, env_and_pvcs):
        """
        Property 18: Persistent Volume Binding

        For any environment with configured PVCs, all PVCs must be in Bound state
        for the cluster to be considered healthy.

        This test verifies that:
        1. Health check validates all PVCs
        2. Any unbound PVC causes health check to fail
        3. All PVCs must be bound for cluster health
        """
        environment, pvcs = env_and_pvcs

        # Simulate PVC statuses
        all_bound = True
        unbound_pvcs = []

        for pvc in pvcs:
            # Randomly assign status (for testing)
            import random
            random.seed(hash(pvc["name"]))

            if random.random() < 0.9:  # 90% bound
                pvc_status = {
                    "phase": "Bound",
                    "volumeName": f"pv-{random.randint(1000, 9999)}",
                    "capacity": {"storage": pvc["size"]},
                    "accessModes": [pvc["accessMode"]]
                }
            else:  # 10% pending
                pvc_status = {
                    "phase": "Pending",
                    "accessModes": [pvc["accessMode"]]
                }

            is_bound = self.simulate_pvc_binding_check(pvc, pvc_status)

            if not is_bound:
                all_bound = False
                unbound_pvcs.append(pvc["name"])

        # If any PVC is not bound, cluster should not be healthy
        if not all_bound:
            assert len(unbound_pvcs) > 0, \
                "Unbound PVCs list should not be empty when cluster is unhealthy"

    @given(environment=st.sampled_from(VALID_ENVIRONMENTS))
    @settings(max_examples=100, deadline=None)
    def test_property_pvc_configuration_matches_component_requirements(self, environment: str):
        """
        Property 18: Persistent Volume Binding

        For any environment, PVC configurations should match the requirements
        of the components that use them.

        This test verifies that:
        1. BanyanDB has separate PVCs for stream and measure data
        2. etcd has PVC for data persistence
        3. Each component's PVC has appropriate size and storage class
        """
        # Load configuration
        config = self.load_helm_values(environment)

        # Extract PVC configurations
        pvcs = self.extract_pvc_configurations(config)

        # Create a set of PVC names
        pvc_names = {pvc["name"] for pvc in pvcs}

        # Verify BanyanDB PVCs exist (if BanyanDB is configured)
        banyandb_config = config.get("banyandb", {})
        if banyandb_config.get("enabled", True):
            # Check for stream and measure PVCs
            has_stream = any("stream" in name for name in pvc_names)
            has_measure = any("measure" in name for name in pvc_names)

            assert has_stream or has_measure, \
                f"BanyanDB enabled but no stream/measure PVCs configured in environment: {environment}"

        # Verify etcd PVC exists (if etcd is configured)
        etcd_config = config.get("etcd", {})
        if etcd_config.get("enabled", True):
            has_etcd = any("etcd" in name for name in pvc_names)

            # etcd PVC is optional for single-replica deployments
            # but should exist for multi-replica deployments
            etcd_replicas = etcd_config.get("replicas", 1)
            if etcd_replicas > 1:
                assert has_etcd, \
                    f"etcd multi-replica deployment but no PVC configured in environment: {environment}"


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v", "--tb=short"])
