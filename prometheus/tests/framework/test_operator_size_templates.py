"""
Property-based tests for Operator size templates.

**Feature: prometheus-installation, Property 5: Operator Size Templates**
**Validates: Requirements 4.5, 4.6**

This module tests that for any Prometheus CR size template (demo, small, medium, large),
the resulting deployment should have resources within the expected ranges for that size category.

Size templates follow this scaling pattern:
- demo: Minimal resources for development/testing (24h retention, 1 replica)
- small: Small production workloads (15d retention, 2 replicas)
- medium: Medium production workloads (30d retention, 2 replicas)
- large: Large production workloads with HA (90d retention, 3 replicas)
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional

import pytest
import yaml
from hypothesis import given, settings, assume
from hypothesis import strategies as st


# Path to Operator Prometheus CR templates
OPERATOR_PROMETHEUS_DIR = Path(__file__).parent.parent.parent / "install" / "operator" / "prometheus"

# Size template names
SIZE_TEMPLATES = ["demo", "small", "medium", "large"]


@dataclass
class ResourceSpec:
    """Resource specification with CPU and memory values."""
    cpu_request: str
    cpu_limit: str
    memory_request: str
    memory_limit: str


@dataclass
class SizeExpectations:
    """Expected resource ranges for a size template."""
    min_replicas: int
    max_replicas: int
    min_retention_days: int
    max_retention_days: int
    min_storage_gb: int
    max_storage_gb: int
    min_memory_request_gi: float
    max_memory_request_gi: float
    min_memory_limit_gi: float
    max_memory_limit_gi: float


# Expected ranges for each size category
SIZE_EXPECTATIONS = {
    "demo": SizeExpectations(
        min_replicas=1, max_replicas=1,
        min_retention_days=1, max_retention_days=7,
        min_storage_gb=5, max_storage_gb=20,
        min_memory_request_gi=0.25, max_memory_request_gi=1.0,
        min_memory_limit_gi=0.5, max_memory_limit_gi=2.0,
    ),
    "small": SizeExpectations(
        min_replicas=1, max_replicas=2,
        min_retention_days=7, max_retention_days=30,
        min_storage_gb=20, max_storage_gb=100,
        min_memory_request_gi=1.0, max_memory_request_gi=4.0,
        min_memory_limit_gi=2.0, max_memory_limit_gi=8.0,
    ),
    "medium": SizeExpectations(
        min_replicas=2, max_replicas=3,
        min_retention_days=14, max_retention_days=60,
        min_storage_gb=50, max_storage_gb=200,
        min_memory_request_gi=2.0, max_memory_request_gi=8.0,
        min_memory_limit_gi=4.0, max_memory_limit_gi=16.0,
    ),
    "large": SizeExpectations(
        min_replicas=2, max_replicas=5,
        min_retention_days=30, max_retention_days=180,
        min_storage_gb=100, max_storage_gb=1000,
        min_memory_request_gi=4.0, max_memory_request_gi=16.0,
        min_memory_limit_gi=8.0, max_memory_limit_gi=32.0,
    ),
}


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
        path: Dot-separated path (e.g., "spec.resources.requests.memory")
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


def parse_retention(retention: str) -> int:
    """
    Parse retention string to days.

    Args:
        retention: Retention string (e.g., "24h", "15d", "30d")

    Returns:
        Retention in days
    """
    if retention.endswith("h"):
        hours = int(retention[:-1])
        return max(1, hours // 24)  # At least 1 day
    elif retention.endswith("d"):
        return int(retention[:-1])
    elif retention.endswith("w"):
        return int(retention[:-1]) * 7
    elif retention.endswith("y"):
        return int(retention[:-1]) * 365
    else:
        # Assume days if no suffix
        return int(retention)


def parse_storage(storage: str) -> int:
    """
    Parse storage string to GB.

    Args:
        storage: Storage string (e.g., "10Gi", "50Gi", "500Gi")

    Returns:
        Storage in GB
    """
    storage = storage.strip()
    if storage.endswith("Gi"):
        return int(storage[:-2])
    elif storage.endswith("Ti"):
        return int(storage[:-2]) * 1024
    elif storage.endswith("Mi"):
        return max(1, int(storage[:-2]) // 1024)
    elif storage.endswith("G"):
        return int(storage[:-1])
    elif storage.endswith("T"):
        return int(storage[:-1]) * 1024
    else:
        return int(storage)


def parse_memory(memory: str) -> float:
    """
    Parse memory string to GiB.

    Args:
        memory: Memory string (e.g., "400Mi", "2Gi", "8Gi")

    Returns:
        Memory in GiB
    """
    memory = memory.strip()
    if memory.endswith("Gi"):
        return float(memory[:-2])
    elif memory.endswith("Mi"):
        return float(memory[:-2]) / 1024
    elif memory.endswith("Ki"):
        return float(memory[:-2]) / (1024 * 1024)
    elif memory.endswith("G"):
        return float(memory[:-1])
    elif memory.endswith("M"):
        return float(memory[:-1]) / 1024
    else:
        return float(memory)


def get_template_path(size: str) -> Path:
    """Get the path to a size template file."""
    return OPERATOR_PROMETHEUS_DIR / f"prometheus-{size}.yaml"


# Strategies for generating valid size templates
valid_sizes = st.sampled_from(SIZE_TEMPLATES)


@pytest.mark.property
class TestOperatorSizeTemplates:
    """
    Property-based tests for Operator size templates.

    **Feature: prometheus-installation, Property 5: Operator Size Templates**
    **Validates: Requirements 4.5, 4.6**
    """

    @given(size=valid_sizes)
    @settings(max_examples=100)
    def test_size_template_exists(self, size: str):
        """
        Property: Each size template file should exist.

        For any size category (demo, small, medium, large), the corresponding
        Prometheus CR template file should exist.

        **Feature: prometheus-installation, Property 5: Operator Size Templates**
        **Validates: Requirements 4.5, 4.6**
        """
        template_path = get_template_path(size)
        assert template_path.exists(), (
            f"Size template file should exist: {template_path}"
        )

    @given(size=valid_sizes)
    @settings(max_examples=100)
    def test_size_template_is_valid_yaml(self, size: str):
        """
        Property: Each size template should be valid YAML.

        For any size category, the template file should be parseable as valid YAML.

        **Feature: prometheus-installation, Property 5: Operator Size Templates**
        **Validates: Requirements 4.5, 4.6**
        """
        template_path = get_template_path(size)
        assume(template_path.exists())

        template = load_yaml_file(template_path)
        assert template, f"Template for size '{size}' should not be empty"
        assert isinstance(template, dict), f"Template for size '{size}' should be a dictionary"

    @given(size=valid_sizes)
    @settings(max_examples=100)
    def test_size_template_has_required_fields(self, size: str):
        """
        Property: Each size template should have all required fields.

        For any size category, the template should contain:
        - apiVersion
        - kind (Prometheus)
        - metadata.name
        - spec.replicas
        - spec.retention
        - spec.resources
        - spec.storage

        **Feature: prometheus-installation, Property 5: Operator Size Templates**
        **Validates: Requirements 4.5, 4.6**
        """
        template_path = get_template_path(size)
        assume(template_path.exists())

        template = load_yaml_file(template_path)
        assume(template)

        # Check required top-level fields
        assert get_nested_value(template, "apiVersion") is not None, (
            f"Template '{size}' should have apiVersion"
        )
        assert get_nested_value(template, "kind") == "Prometheus", (
            f"Template '{size}' should have kind: Prometheus"
        )
        assert get_nested_value(template, "metadata.name") is not None, (
            f"Template '{size}' should have metadata.name"
        )

        # Check required spec fields
        assert get_nested_value(template, "spec.replicas") is not None, (
            f"Template '{size}' should have spec.replicas"
        )
        assert get_nested_value(template, "spec.retention") is not None, (
            f"Template '{size}' should have spec.retention"
        )
        assert get_nested_value(template, "spec.resources") is not None, (
            f"Template '{size}' should have spec.resources"
        )
        assert get_nested_value(template, "spec.storage") is not None, (
            f"Template '{size}' should have spec.storage"
        )

    @given(size=valid_sizes)
    @settings(max_examples=100)
    def test_replicas_within_expected_range(self, size: str):
        """
        Property: Replicas should be within expected range for size category.

        For any size category, the number of replicas should be within the
        expected range for that category.

        **Feature: prometheus-installation, Property 5: Operator Size Templates**
        **Validates: Requirements 4.5, 4.6**
        """
        template_path = get_template_path(size)
        assume(template_path.exists())

        template = load_yaml_file(template_path)
        assume(template)

        replicas = get_nested_value(template, "spec.replicas")
        assume(replicas is not None)

        expectations = SIZE_EXPECTATIONS[size]
        assert expectations.min_replicas <= replicas <= expectations.max_replicas, (
            f"Size '{size}' replicas ({replicas}) should be between "
            f"{expectations.min_replicas} and {expectations.max_replicas}"
        )

    @given(size=valid_sizes)
    @settings(max_examples=100)
    def test_retention_within_expected_range(self, size: str):
        """
        Property: Retention should be within expected range for size category.

        For any size category, the retention period should be within the
        expected range for that category.

        **Feature: prometheus-installation, Property 5: Operator Size Templates**
        **Validates: Requirements 4.5, 4.6**
        """
        template_path = get_template_path(size)
        assume(template_path.exists())

        template = load_yaml_file(template_path)
        assume(template)

        retention = get_nested_value(template, "spec.retention")
        assume(retention is not None)

        retention_days = parse_retention(retention)
        expectations = SIZE_EXPECTATIONS[size]

        assert expectations.min_retention_days <= retention_days <= expectations.max_retention_days, (
            f"Size '{size}' retention ({retention} = {retention_days}d) should be between "
            f"{expectations.min_retention_days}d and {expectations.max_retention_days}d"
        )

    @given(size=valid_sizes)
    @settings(max_examples=100)
    def test_storage_within_expected_range(self, size: str):
        """
        Property: Storage should be within expected range for size category.

        For any size category, the storage size should be within the
        expected range for that category.

        **Feature: prometheus-installation, Property 5: Operator Size Templates**
        **Validates: Requirements 4.5, 4.6**
        """
        template_path = get_template_path(size)
        assume(template_path.exists())

        template = load_yaml_file(template_path)
        assume(template)

        storage = get_nested_value(
            template,
            "spec.storage.volumeClaimTemplate.spec.resources.requests.storage"
        )
        assume(storage is not None)

        storage_gb = parse_storage(storage)
        expectations = SIZE_EXPECTATIONS[size]

        assert expectations.min_storage_gb <= storage_gb <= expectations.max_storage_gb, (
            f"Size '{size}' storage ({storage} = {storage_gb}GB) should be between "
            f"{expectations.min_storage_gb}GB and {expectations.max_storage_gb}GB"
        )

    @given(size=valid_sizes)
    @settings(max_examples=100)
    def test_memory_request_within_expected_range(self, size: str):
        """
        Property: Memory request should be within expected range for size category.

        For any size category, the memory request should be within the
        expected range for that category.

        **Feature: prometheus-installation, Property 5: Operator Size Templates**
        **Validates: Requirements 4.5, 4.6**
        """
        template_path = get_template_path(size)
        assume(template_path.exists())

        template = load_yaml_file(template_path)
        assume(template)

        memory_request = get_nested_value(template, "spec.resources.requests.memory")
        assume(memory_request is not None)

        memory_gi = parse_memory(memory_request)
        expectations = SIZE_EXPECTATIONS[size]

        assert expectations.min_memory_request_gi <= memory_gi <= expectations.max_memory_request_gi, (
            f"Size '{size}' memory request ({memory_request} = {memory_gi}Gi) should be between "
            f"{expectations.min_memory_request_gi}Gi and {expectations.max_memory_request_gi}Gi"
        )

    @given(size=valid_sizes)
    @settings(max_examples=100)
    def test_memory_limit_within_expected_range(self, size: str):
        """
        Property: Memory limit should be within expected range for size category.

        For any size category, the memory limit should be within the
        expected range for that category.

        **Feature: prometheus-installation, Property 5: Operator Size Templates**
        **Validates: Requirements 4.5, 4.6**
        """
        template_path = get_template_path(size)
        assume(template_path.exists())

        template = load_yaml_file(template_path)
        assume(template)

        memory_limit = get_nested_value(template, "spec.resources.limits.memory")
        assume(memory_limit is not None)

        memory_gi = parse_memory(memory_limit)
        expectations = SIZE_EXPECTATIONS[size]

        assert expectations.min_memory_limit_gi <= memory_gi <= expectations.max_memory_limit_gi, (
            f"Size '{size}' memory limit ({memory_limit} = {memory_gi}Gi) should be between "
            f"{expectations.min_memory_limit_gi}Gi and {expectations.max_memory_limit_gi}Gi"
        )

    @given(size=valid_sizes)
    @settings(max_examples=100)
    def test_memory_limit_greater_than_request(self, size: str):
        """
        Property: Memory limit should be greater than or equal to memory request.

        For any size category, the memory limit should be at least as large
        as the memory request.

        **Feature: prometheus-installation, Property 5: Operator Size Templates**
        **Validates: Requirements 4.5, 4.6**
        """
        template_path = get_template_path(size)
        assume(template_path.exists())

        template = load_yaml_file(template_path)
        assume(template)

        memory_request = get_nested_value(template, "spec.resources.requests.memory")
        memory_limit = get_nested_value(template, "spec.resources.limits.memory")
        assume(memory_request is not None and memory_limit is not None)

        request_gi = parse_memory(memory_request)
        limit_gi = parse_memory(memory_limit)

        assert limit_gi >= request_gi, (
            f"Size '{size}' memory limit ({memory_limit} = {limit_gi}Gi) should be >= "
            f"memory request ({memory_request} = {request_gi}Gi)"
        )

    @given(size=valid_sizes)
    @settings(max_examples=100)
    def test_security_context_configured(self, size: str):
        """
        Property: Security context should be configured for each size template.

        For any size category, the template should have security context
        configured with runAsNonRoot and fsGroup.

        **Feature: prometheus-installation, Property 5: Operator Size Templates**
        **Validates: Requirements 4.5, 4.6**
        """
        template_path = get_template_path(size)
        assume(template_path.exists())

        template = load_yaml_file(template_path)
        assume(template)

        security_context = get_nested_value(template, "spec.securityContext")
        assume(security_context is not None)

        assert get_nested_value(template, "spec.securityContext.runAsNonRoot") is True, (
            f"Size '{size}' should have runAsNonRoot: true"
        )
        assert get_nested_value(template, "spec.securityContext.fsGroup") is not None, (
            f"Size '{size}' should have fsGroup configured"
        )

    @given(size=valid_sizes)
    @settings(max_examples=100)
    def test_service_account_configured(self, size: str):
        """
        Property: Service account should be configured for each size template.

        For any size category, the template should have a service account
        name configured.

        **Feature: prometheus-installation, Property 5: Operator Size Templates**
        **Validates: Requirements 4.5, 4.6**
        """
        template_path = get_template_path(size)
        assume(template_path.exists())

        template = load_yaml_file(template_path)
        assume(template)

        service_account = get_nested_value(template, "spec.serviceAccountName")
        assert service_account is not None, (
            f"Size '{size}' should have serviceAccountName configured"
        )


@pytest.mark.property
class TestOperatorSizeTemplateScaling:
    """
    Property-based tests for Operator size template scaling relationships.

    **Feature: prometheus-installation, Property 5: Operator Size Templates**
    **Validates: Requirements 4.5, 4.6**
    """

    def test_sizes_scale_monotonically(self):
        """
        Property: Larger sizes should have more resources than smaller sizes.

        The size templates should follow a monotonic scaling pattern where
        larger sizes have more resources (replicas, retention, storage, memory).

        **Feature: prometheus-installation, Property 5: Operator Size Templates**
        **Validates: Requirements 4.5, 4.6**
        """
        size_order = ["demo", "small", "medium", "large"]
        templates = {}

        for size in size_order:
            template_path = get_template_path(size)
            if template_path.exists():
                templates[size] = load_yaml_file(template_path)

        # Skip if not all templates exist
        if len(templates) != len(size_order):
            pytest.skip("Not all size templates exist")

        # Check monotonic scaling for each metric
        prev_replicas = 0
        prev_retention = 0
        prev_storage = 0
        prev_memory = 0

        for size in size_order:
            template = templates[size]

            replicas = get_nested_value(template, "spec.replicas", 0)
            retention = parse_retention(get_nested_value(template, "spec.retention", "0d"))
            storage = parse_storage(get_nested_value(
                template,
                "spec.storage.volumeClaimTemplate.spec.resources.requests.storage",
                "0Gi"
            ))
            memory = parse_memory(get_nested_value(
                template,
                "spec.resources.requests.memory",
                "0Gi"
            ))

            assert replicas >= prev_replicas, (
                f"Size '{size}' replicas ({replicas}) should be >= previous size ({prev_replicas})"
            )
            assert retention >= prev_retention, (
                f"Size '{size}' retention ({retention}d) should be >= previous size ({prev_retention}d)"
            )
            assert storage >= prev_storage, (
                f"Size '{size}' storage ({storage}GB) should be >= previous size ({prev_storage}GB)"
            )
            assert memory >= prev_memory, (
                f"Size '{size}' memory ({memory}Gi) should be >= previous size ({prev_memory}Gi)"
            )

            prev_replicas = replicas
            prev_retention = retention
            prev_storage = storage
            prev_memory = memory

    def test_all_size_templates_exist(self):
        """
        Property: All four size templates should exist.

        The operator installation should provide templates for all four
        size categories: demo, small, medium, large.

        **Feature: prometheus-installation, Property 5: Operator Size Templates**
        **Validates: Requirements 4.5, 4.6**
        """
        for size in SIZE_TEMPLATES:
            template_path = get_template_path(size)
            assert template_path.exists(), (
                f"Size template '{size}' should exist at {template_path}"
            )
