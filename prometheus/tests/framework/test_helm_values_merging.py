"""
Property-based tests for Helm values merging.

**Feature: prometheus-installation, Property 4: Helm Values Merging**
**Validates: Requirements 3.4, 3.6**

This module tests that for any combination of valid values files
(base + version + environment), the Helm installation should produce
a deployment where all specified values are correctly applied and
merged in the correct precedence order.

Helm values merging follows this precedence (later files override earlier):
1. base/values.yaml (lowest precedence)
2. versions/<version>/values.yaml
3. environments/<env>/values.yaml (highest precedence)
"""

from pathlib import Path
from typing import Any

import pytest
import yaml
from hypothesis import given, settings, assume
from hypothesis import strategies as st


# Path to Helm values files
HELM_VALUES_DIR = Path(__file__).parent.parent.parent / "install" / "helm" / "kube-prometheus-stack"


def deep_merge(base: dict, override: dict) -> dict:
    """
    Deep merge two dictionaries, with override taking precedence.

    This mimics Helm's values merging behavior where:
    - Scalar values are replaced
    - Dictionaries are recursively merged
    - Lists are replaced (not appended)

    Args:
        base: Base dictionary
        override: Override dictionary (takes precedence)

    Returns:
        Merged dictionary
    """
    result = base.copy()

    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = deep_merge(result[key], value)
        else:
            result[key] = value

    return result


def load_yaml_file(path: Path) -> dict:
    """Load a YAML file and return its contents as a dictionary."""
    if not path.exists():
        return {}
    with open(path, "r", encoding="utf-8") as f:
        content = yaml.safe_load(f)
        return content if content else {}


def get_nested_value(data: dict, path: str, default: Any = None) -> Any:
    """
    Get a nested value from a dictionary using dot notation.

    Args:
        data: Dictionary to search
        path: Dot-separated path (e.g., "prometheus.prometheusSpec.retention")
        default: Default value if path not found

    Returns:
        Value at path or default
    """
    keys = path.split(".")
    current = data

    for key in keys:
        if isinstance(current, dict) and key in current:
            current = current[key]
        else:
            return default

    return current


def merge_helm_values(base_path: Path, version_path: Path, env_path: Path) -> dict:
    """
    Merge Helm values files in the correct precedence order.

    Precedence (later overrides earlier):
    1. base/values.yaml
    2. versions/<version>/values.yaml
    3. environments/<env>/values.yaml

    Args:
        base_path: Path to base values file
        version_path: Path to version-specific values file
        env_path: Path to environment-specific values file

    Returns:
        Merged values dictionary
    """
    base = load_yaml_file(base_path)
    version = load_yaml_file(version_path)
    env = load_yaml_file(env_path)

    # Merge in precedence order
    merged = deep_merge(base, version)
    merged = deep_merge(merged, env)

    return merged


# Available versions and environments
VERSIONS = ["v3.5.0-lts", "v3.9.0-latest"]
ENVIRONMENTS = ["dev", "staging", "prod", "minikube"]


# Strategies for generating valid combinations
valid_versions = st.sampled_from(VERSIONS)
valid_environments = st.sampled_from(ENVIRONMENTS)


@st.composite
def valid_helm_values_combination(draw):
    """Generate a valid combination of version and environment."""
    version = draw(valid_versions)
    environment = draw(valid_environments)
    return {"version": version, "environment": environment}


@pytest.mark.property
class TestHelmValuesMerging:
    """
    Property-based tests for Helm values merging.

    **Feature: prometheus-installation, Property 4: Helm Values Merging**
    **Validates: Requirements 3.4, 3.6**
    """

    @given(combination=valid_helm_values_combination())
    @settings(max_examples=20)
    def test_environment_values_override_version_values(self, combination: dict):
        """
        Property: Environment-specific values should override version-specific values.

        For any combination of version and environment, values specified in the
        environment file should take precedence over values in the version file.

        **Feature: prometheus-installation, Property 4: Helm Values Merging**
        **Validates: Requirements 3.4, 3.6**
        """
        version = combination["version"]
        environment = combination["environment"]

        base_path = HELM_VALUES_DIR / "base" / "values.yaml"
        version_path = HELM_VALUES_DIR / "versions" / version / "values.yaml"
        env_path = HELM_VALUES_DIR / "environments" / environment / "values.yaml"

        # Skip if files don't exist
        assume(base_path.exists())
        assume(version_path.exists())
        assume(env_path.exists())

        # Load individual files
        env_values = load_yaml_file(env_path)

        # Merge values
        merged = merge_helm_values(base_path, version_path, env_path)

        # For any value specified in environment, it should appear in merged
        # Check retention if specified in environment
        env_retention = get_nested_value(env_values, "prometheus.prometheusSpec.retention")
        if env_retention is not None:
            merged_retention = get_nested_value(merged, "prometheus.prometheusSpec.retention")
            assert merged_retention == env_retention, (
                f"Environment retention '{env_retention}' should override in merged config, "
                f"but got '{merged_retention}'"
            )

        # Check resources if specified in environment
        env_cpu_request = get_nested_value(
            env_values, "prometheus.prometheusSpec.resources.requests.cpu"
        )
        if env_cpu_request is not None:
            merged_cpu_request = get_nested_value(
                merged, "prometheus.prometheusSpec.resources.requests.cpu"
            )
            assert merged_cpu_request == env_cpu_request, (
                f"Environment CPU request '{env_cpu_request}' should override in merged config, "
                f"but got '{merged_cpu_request}'"
            )

    @given(combination=valid_helm_values_combination())
    @settings(max_examples=20)
    def test_version_values_override_base_values(self, combination: dict):
        """
        Property: Version-specific values should override base values.

        For any combination, values specified in the version file should take
        precedence over values in the base file.

        **Feature: prometheus-installation, Property 4: Helm Values Merging**
        **Validates: Requirements 3.4, 3.6**
        """
        version = combination["version"]
        environment = combination["environment"]

        base_path = HELM_VALUES_DIR / "base" / "values.yaml"
        version_path = HELM_VALUES_DIR / "versions" / version / "values.yaml"
        env_path = HELM_VALUES_DIR / "environments" / environment / "values.yaml"

        assume(base_path.exists())
        assume(version_path.exists())
        assume(env_path.exists())

        # Load individual files
        version_values = load_yaml_file(version_path)
        env_values = load_yaml_file(env_path)

        # Merge values
        merged = merge_helm_values(base_path, version_path, env_path)

        # Check image tag from version file (if not overridden by env)
        version_image_tag = get_nested_value(
            version_values, "prometheus.prometheusSpec.image.tag"
        )
        env_image_tag = get_nested_value(
            env_values, "prometheus.prometheusSpec.image.tag"
        )

        if version_image_tag is not None and env_image_tag is None:
            merged_image_tag = get_nested_value(
                merged, "prometheus.prometheusSpec.image.tag"
            )
            assert merged_image_tag == version_image_tag, (
                f"Version image tag '{version_image_tag}' should be in merged config, "
                f"but got '{merged_image_tag}'"
            )

    @given(combination=valid_helm_values_combination())
    @settings(max_examples=20)
    def test_base_values_preserved_when_not_overridden(self, combination: dict):
        """
        Property: Base values should be preserved when not overridden.

        For any combination, values specified only in the base file should
        appear in the merged result.

        **Feature: prometheus-installation, Property 4: Helm Values Merging**
        **Validates: Requirements 3.4, 3.6**
        """
        version = combination["version"]
        environment = combination["environment"]

        base_path = HELM_VALUES_DIR / "base" / "values.yaml"
        version_path = HELM_VALUES_DIR / "versions" / version / "values.yaml"
        env_path = HELM_VALUES_DIR / "environments" / environment / "values.yaml"

        assume(base_path.exists())
        assume(version_path.exists())
        assume(env_path.exists())

        # Load individual files
        base_values = load_yaml_file(base_path)
        version_values = load_yaml_file(version_path)
        env_values = load_yaml_file(env_path)

        # Merge values
        merged = merge_helm_values(base_path, version_path, env_path)

        # Check walCompression from base (typically not overridden)
        base_wal_compression = get_nested_value(
            base_values, "prometheus.prometheusSpec.walCompression"
        )
        version_wal_compression = get_nested_value(
            version_values, "prometheus.prometheusSpec.walCompression"
        )
        env_wal_compression = get_nested_value(
            env_values, "prometheus.prometheusSpec.walCompression"
        )

        if base_wal_compression is not None:
            expected = env_wal_compression or version_wal_compression or base_wal_compression
            merged_wal_compression = get_nested_value(
                merged, "prometheus.prometheusSpec.walCompression"
            )
            assert merged_wal_compression == expected, (
                f"Expected walCompression '{expected}' in merged config, "
                f"but got '{merged_wal_compression}'"
            )

    @given(combination=valid_helm_values_combination())
    @settings(max_examples=20)
    def test_merged_config_contains_required_fields(self, combination: dict):
        """
        Property: Merged configuration should contain all required fields.

        For any valid combination, the merged result should contain the
        essential Prometheus configuration fields.

        **Feature: prometheus-installation, Property 4: Helm Values Merging**
        **Validates: Requirements 3.4, 3.6**
        """
        version = combination["version"]
        environment = combination["environment"]

        base_path = HELM_VALUES_DIR / "base" / "values.yaml"
        version_path = HELM_VALUES_DIR / "versions" / version / "values.yaml"
        env_path = HELM_VALUES_DIR / "environments" / environment / "values.yaml"

        assume(base_path.exists())
        assume(version_path.exists())
        assume(env_path.exists())

        # Merge values
        merged = merge_helm_values(base_path, version_path, env_path)

        # Required fields that should always be present after merge
        required_paths = [
            "prometheus.prometheusSpec.retention",
            "prometheus.prometheusSpec.resources.requests.cpu",
            "prometheus.prometheusSpec.resources.requests.memory",
            "prometheus.prometheusSpec.resources.limits.cpu",
            "prometheus.prometheusSpec.resources.limits.memory",
        ]

        for path in required_paths:
            value = get_nested_value(merged, path)
            assert value is not None, (
                f"Required field '{path}' should be present in merged config "
                f"for version={version}, environment={environment}"
            )

    @given(combination=valid_helm_values_combination())
    @settings(max_examples=20)
    def test_merge_is_deterministic(self, combination: dict):
        """
        Property: Merging the same files should always produce the same result.

        For any combination, merging the same files multiple times should
        produce identical results.

        **Feature: prometheus-installation, Property 4: Helm Values Merging**
        **Validates: Requirements 3.4, 3.6**
        """
        version = combination["version"]
        environment = combination["environment"]

        base_path = HELM_VALUES_DIR / "base" / "values.yaml"
        version_path = HELM_VALUES_DIR / "versions" / version / "values.yaml"
        env_path = HELM_VALUES_DIR / "environments" / environment / "values.yaml"

        assume(base_path.exists())
        assume(version_path.exists())
        assume(env_path.exists())

        # Merge multiple times
        merged1 = merge_helm_values(base_path, version_path, env_path)
        merged2 = merge_helm_values(base_path, version_path, env_path)

        assert merged1 == merged2, (
            f"Merging should be deterministic for version={version}, "
            f"environment={environment}"
        )

    @given(combination=valid_helm_values_combination())
    @settings(max_examples=20)
    def test_storage_configuration_properly_merged(self, combination: dict):
        """
        Property: Storage configuration should be properly merged.

        For any combination, storage settings from environment should
        override base storage settings.

        **Feature: prometheus-installation, Property 4: Helm Values Merging**
        **Validates: Requirements 3.4, 3.6**
        """
        version = combination["version"]
        environment = combination["environment"]

        base_path = HELM_VALUES_DIR / "base" / "values.yaml"
        version_path = HELM_VALUES_DIR / "versions" / version / "values.yaml"
        env_path = HELM_VALUES_DIR / "environments" / environment / "values.yaml"

        assume(base_path.exists())
        assume(version_path.exists())
        assume(env_path.exists())

        # Load individual files
        base_values = load_yaml_file(base_path)
        env_values = load_yaml_file(env_path)

        # Merge values
        merged = merge_helm_values(base_path, version_path, env_path)

        # Check storage size
        storage_path = "prometheus.prometheusSpec.storageSpec.volumeClaimTemplate.spec.resources.requests.storage"
        env_storage = get_nested_value(env_values, storage_path)
        base_storage = get_nested_value(base_values, storage_path)
        merged_storage = get_nested_value(merged, storage_path)

        if env_storage is not None:
            assert merged_storage == env_storage, (
                f"Environment storage '{env_storage}' should override base storage, "
                f"but got '{merged_storage}'"
            )
        elif base_storage is not None:
            assert merged_storage == base_storage, (
                f"Base storage '{base_storage}' should be preserved, "
                f"but got '{merged_storage}'"
            )

    @given(combination=valid_helm_values_combination())
    @settings(max_examples=20)
    def test_replicas_configuration_properly_merged(self, combination: dict):
        """
        Property: Replicas configuration should be properly merged.

        For any combination, replica settings from environment should
        override base replica settings (for HA configuration).

        **Feature: prometheus-installation, Property 4: Helm Values Merging**
        **Validates: Requirements 3.4, 3.6**
        """
        version = combination["version"]
        environment = combination["environment"]

        base_path = HELM_VALUES_DIR / "base" / "values.yaml"
        version_path = HELM_VALUES_DIR / "versions" / version / "values.yaml"
        env_path = HELM_VALUES_DIR / "environments" / environment / "values.yaml"

        assume(base_path.exists())
        assume(version_path.exists())
        assume(env_path.exists())

        # Load individual files
        env_values = load_yaml_file(env_path)

        # Merge values
        merged = merge_helm_values(base_path, version_path, env_path)

        # Check replicas if specified in environment
        env_replicas = get_nested_value(env_values, "prometheus.prometheusSpec.replicas")

        if env_replicas is not None:
            merged_replicas = get_nested_value(merged, "prometheus.prometheusSpec.replicas")
            assert merged_replicas == env_replicas, (
                f"Environment replicas '{env_replicas}' should be in merged config, "
                f"but got '{merged_replicas}'"
            )
