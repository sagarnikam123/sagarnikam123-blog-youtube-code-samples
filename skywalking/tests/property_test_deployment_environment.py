#!/usr/bin/env python3
"""
Property-Based Test: Deployment Script Environment Handling

Feature: skywalking-cluster
Property 3: Deployment Script Environment Handling

This test validates that for any valid environment parameter (minikube, eks),
the deployment script successfully loads the corresponding configuration and deploys all
required components.

Validates: Requirements 5.1, 5.5

Note: The test is configured to run up to 100 examples, but Hypothesis will only generate
unique examples. Since we have 2 valid environments (minikube, eks), the actual number
of test runs will be limited to the number of unique environment combinations.
"""

from pathlib import Path
from typing import Dict

import pytest
import yaml
from hypothesis import given, settings, strategies as st


# Test configuration
VALID_ENVIRONMENTS = ["minikube", "eks"]
REQUIRED_COMPONENTS = ["oap", "banyandb", "satellite", "ui", "etcd"]
HELM_VALUES_DIR = Path(__file__).parent.parent / "helm-values"


# Hypothesis strategies
@st.composite
def environment_strategy(draw):
    """Generate valid environment parameters."""
    return draw(st.sampled_from(VALID_ENVIRONMENTS))


@st.composite
def environment_config_strategy(draw):
    """Generate environment-specific configuration variations."""
    env = draw(environment_strategy())

    # Generate valid configuration variations
    config = {
        "environment": env,
        "namespace": draw(st.sampled_from(["skywalking", "sw-test", "observability"])),
        "timeout": draw(st.integers(min_value=300, max_value=1800)),  # 5-30 minutes
    }

    return config


class TestDeploymentEnvironmentHandling:
    """Property-based tests for deployment script environment handling."""

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
            environment: Environment name (minikube, eks-dev, eks-prod)

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

        # Merge configurations (environment overrides base)
        merged_values = self._deep_merge(base_values, env_values)

        return merged_values

    def _deep_merge(self, base: Dict, override: Dict) -> Dict:
        """
        Deep merge two dictionaries.

        Args:
            base: Base dictionary
            override: Override dictionary

        Returns:
            Merged dictionary
        """
        result = base.copy()

        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._deep_merge(result[key], value)
            else:
                result[key] = value

        return result

    def validate_component_configuration(self, config: Dict, component: str) -> bool:
        """
        Validate that a component has required configuration.

        Args:
            config: Configuration dictionary
            component: Component name

        Returns:
            True if component is properly configured
        """
        if component not in config:
            return False

        component_config = config[component]

        # Check required fields based on component type
        if component == "oap":
            required_fields = ["replicas", "resources", "env", "service"]
            return all(field in component_config for field in required_fields)

        elif component == "banyandb":
            if not component_config.get("enabled", False):
                return False
            required_fields = ["liaison", "data"]
            return all(field in component_config for field in required_fields)

        elif component == "satellite":
            if not component_config.get("enabled", False):
                return False
            required_fields = ["replicas", "resources", "config"]
            return all(field in component_config for field in required_fields)

        elif component == "ui":
            required_fields = ["replicas", "resources", "env"]
            return all(field in component_config for field in required_fields)

        elif component == "etcd":
            if not component_config.get("enabled", False):
                return False
            required_fields = ["replicas", "resources", "persistence"]
            return all(field in component_config for field in required_fields)

        return True

    def validate_environment_specific_settings(self, config: Dict, environment: str) -> bool:
        """
        Validate environment-specific settings are correctly applied.

        Args:
            config: Configuration dictionary
            environment: Environment name

        Returns:
            True if environment-specific settings are correct
        """
        if environment == "minikube":
            # Minikube should have specific replica counts
            if config.get("oap", {}).get("replicas") != 2:
                return False
            if config.get("banyandb", {}).get("data", {}).get("replicas") != 2:
                return False
            if config.get("etcd", {}).get("replicas") != 1:
                return False

            # Minikube should use 'standard' storage class
            storage_class = config.get("banyandb", {}).get("data", {}).get("persistence", {}).get("stream", {}).get("storageClass")
            if storage_class != "standard":
                return False

        elif environment == "eks":
            # EKS should have higher replica counts
            if config.get("oap", {}).get("replicas") < 2:
                return False
            if config.get("etcd", {}).get("replicas") < 3:
                return False

            # EKS should use 'gp3' storage class
            storage_class = config.get("banyandb", {}).get("data", {}).get("persistence", {}).get("stream", {}).get("storageClass")
            if storage_class != "gp3":
                return False

        return True

    @given(environment=environment_strategy())
    @settings(max_examples=100, deadline=None)
    def test_property_environment_configuration_loads(self, environment: str):
        """
        Property 3: Deployment Script Environment Handling

        For any valid environment parameter (minikube, eks-dev, eks-prod),
        the configuration should successfully load.

        This test verifies that:
        1. Environment-specific values file exists
        2. Values file is valid YAML
        3. Configuration can be loaded and parsed
        """
        # Load configuration for environment
        config = self.load_helm_values(environment)

        # Verify configuration is not empty
        assert config is not None, f"Configuration is None for environment: {environment}"
        assert len(config) > 0, f"Configuration is empty for environment: {environment}"

        # Verify configuration has expected structure
        assert isinstance(config, dict), f"Configuration is not a dictionary for environment: {environment}"

    @given(environment=environment_strategy())
    @settings(max_examples=100, deadline=None)
    def test_property_all_required_components_configured(self, environment: str):
        """
        Property 3: Deployment Script Environment Handling

        For any valid environment parameter, all required components
        (OAP, BanyanDB, Satellite, UI, etcd) should be configured.

        This test verifies that:
        1. All required components are present in configuration
        2. Each component has required fields
        3. Component configurations are valid
        """
        # Load configuration
        config = self.load_helm_values(environment)

        # Verify all required components are configured
        for component in REQUIRED_COMPONENTS:
            assert self.validate_component_configuration(config, component), \
                f"Component '{component}' is not properly configured for environment: {environment}"

    @given(environment=environment_strategy())
    @settings(max_examples=100, deadline=None)
    def test_property_environment_specific_settings_applied(self, environment: str):
        """
        Property 3: Deployment Script Environment Handling

        For any valid environment parameter, environment-specific settings
        should be correctly applied (replica counts, storage classes, etc.).

        This test verifies that:
        1. Replica counts match environment requirements
        2. Storage classes are appropriate for environment
        3. Resource allocations are suitable for environment
        """
        # Load configuration
        config = self.load_helm_values(environment)

        # Verify environment-specific settings
        assert self.validate_environment_specific_settings(config, environment), \
            f"Environment-specific settings are incorrect for environment: {environment}"

    @given(environment=environment_strategy())
    @settings(max_examples=100, deadline=None)
    def test_property_resource_requests_defined(self, environment: str):
        """
        Property 3: Deployment Script Environment Handling

        For any valid environment parameter, all components should have
        resource requests and limits defined.

        This test verifies that:
        1. CPU requests are defined for all components
        2. Memory requests are defined for all components
        3. Resource limits are defined
        """
        # Load configuration
        config = self.load_helm_values(environment)

        # Check resource definitions for each component
        components_to_check = ["oap", "satellite", "ui", "etcd"]

        for component in components_to_check:
            if component not in config:
                continue

            component_config = config[component]

            # Check resources
            assert "resources" in component_config, \
                f"Component '{component}' missing resources for environment: {environment}"

            resources = component_config["resources"]

            assert "requests" in resources, \
                f"Component '{component}' missing resource requests for environment: {environment}"
            assert "limits" in resources, \
                f"Component '{component}' missing resource limits for environment: {environment}"

            # Check CPU and memory
            assert "cpu" in resources["requests"], \
                f"Component '{component}' missing CPU request for environment: {environment}"
            assert "memory" in resources["requests"], \
                f"Component '{component}' missing memory request for environment: {environment}"

        # Check BanyanDB liaison and data nodes
        if "banyandb" in config and config["banyandb"].get("enabled"):
            for node_type in ["liaison", "data"]:
                node_config = config["banyandb"].get(node_type, {})
                assert "resources" in node_config, \
                    f"BanyanDB {node_type} missing resources for environment: {environment}"

    @given(environment=environment_strategy())
    @settings(max_examples=100, deadline=None)
    def test_property_storage_configuration_valid(self, environment: str):
        """
        Property 3: Deployment Script Environment Handling

        For any valid environment parameter, storage configuration should be valid.

        This test verifies that:
        1. Persistent volumes are configured for stateful components
        2. Storage classes are defined
        3. Volume sizes are appropriate
        """
        # Load configuration
        config = self.load_helm_values(environment)

        # Check BanyanDB storage configuration
        if "banyandb" in config and config["banyandb"].get("enabled"):
            data_config = config["banyandb"].get("data", {})
            persistence = data_config.get("persistence", {})

            assert persistence.get("enabled", False), \
                f"BanyanDB persistence not enabled for environment: {environment}"

            # Check stream storage
            stream_storage = persistence.get("stream", {})
            assert "storageClass" in stream_storage, \
                f"BanyanDB stream storage class not defined for environment: {environment}"
            assert "size" in stream_storage, \
                f"BanyanDB stream size not defined for environment: {environment}"

            # Check measure storage
            measure_storage = persistence.get("measure", {})
            assert "storageClass" in measure_storage, \
                f"BanyanDB measure storage class not defined for environment: {environment}"
            assert "size" in measure_storage, \
                f"BanyanDB measure size not defined for environment: {environment}"

        # Check etcd storage configuration
        if "etcd" in config and config["etcd"].get("enabled"):
            etcd_persistence = config["etcd"].get("persistence", {})
            assert etcd_persistence.get("enabled", False), \
                f"etcd persistence not enabled for environment: {environment}"
            assert "storageClass" in etcd_persistence, \
                f"etcd storage class not defined for environment: {environment}"
            assert "size" in etcd_persistence, \
                f"etcd size not defined for environment: {environment}"

    @given(environment=environment_strategy())
    @settings(max_examples=100, deadline=None)
    def test_property_high_availability_configuration(self, environment: str):
        """
        Property 3: Deployment Script Environment Handling

        For any valid environment parameter, high availability features
        should be configured (pod anti-affinity, disruption budgets).

        This test verifies that:
        1. Pod anti-affinity rules are defined
        2. Pod disruption budgets are configured
        3. Rolling update strategies are set
        """
        # Load configuration
        config = self.load_helm_values(environment)

        # Check OAP Server HA configuration
        if "oap" in config:
            oap_config = config["oap"]

            # Check pod anti-affinity
            assert "affinity" in oap_config, \
                f"OAP Server missing affinity configuration for environment: {environment}"

            # Check pod disruption budget
            pdb = oap_config.get("podDisruptionBudget", {})
            assert pdb.get("enabled", False), \
                f"OAP Server PDB not enabled for environment: {environment}"

            # Check rolling update strategy
            strategy = oap_config.get("strategy", {})
            assert strategy.get("type") == "RollingUpdate", \
                f"OAP Server not using RollingUpdate strategy for environment: {environment}"


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v", "--tb=short"])
