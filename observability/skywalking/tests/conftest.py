"""
Pytest configuration and fixtures for SkyWalking tests.

This module provides shared fixtures and configuration for all test types:
- Property-based tests
- Unit tests
- Integration tests
"""

import os
import sys
from pathlib import Path

import pytest


# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))


@pytest.fixture(scope="session")
def project_root():
    """Return the project root directory."""
    return Path(__file__).parent.parent


@pytest.fixture(scope="session")
def helm_values_dir(project_root):
    """Return the Helm values directory."""
    return project_root / "helm-values"


@pytest.fixture(scope="session")
def scripts_dir(project_root):
    """Return the scripts directory."""
    return project_root / "scripts"


@pytest.fixture(scope="session")
def test_data_dir(project_root):
    """Return the test data directory."""
    test_data = project_root / "tests" / "data"
    test_data.mkdir(exist_ok=True)
    return test_data


@pytest.fixture
def valid_environments():
    """Return list of valid environment names."""
    return ["minikube", "eks-dev", "eks-prod"]


@pytest.fixture
def required_components():
    """Return list of required SkyWalking components."""
    return ["oap", "banyandb", "satellite", "ui", "etcd"]


def pytest_configure(config):
    """Configure pytest with custom settings."""
    # Register custom markers
    config.addinivalue_line(
        "markers", "property: Property-based tests using Hypothesis"
    )
    config.addinivalue_line(
        "markers", "unit: Unit tests for specific scenarios"
    )
    config.addinivalue_line(
        "markers", "integration: Integration tests requiring cluster"
    )
    config.addinivalue_line(
        "markers", "slow: Tests that take significant time to run"
    )
    config.addinivalue_line(
        "markers", "minikube: Tests specific to Minikube environment"
    )
    config.addinivalue_line(
        "markers", "eks: Tests specific to EKS environment"
    )


def pytest_collection_modifyitems(config, items):
    """Modify test collection to add markers automatically."""
    for item in items:
        # Add property marker to property-based tests
        if "property_test_" in item.nodeid:
            item.add_marker(pytest.mark.property)

        # Add environment-specific markers
        if "minikube" in item.nodeid.lower():
            item.add_marker(pytest.mark.minikube)
        if "eks" in item.nodeid.lower():
            item.add_marker(pytest.mark.eks)
