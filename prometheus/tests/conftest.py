"""
Pytest configuration and fixtures for Prometheus Testing Framework.

This module provides shared fixtures and configuration for all test types.
"""

import pytest
from hypothesis import settings, Verbosity

# Configure Hypothesis profiles
settings.register_profile(
    "default",
    max_examples=100,
    verbosity=Verbosity.normal,
    deadline=None,
)

settings.register_profile(
    "ci",
    max_examples=200,
    verbosity=Verbosity.verbose,
    deadline=None,
)

settings.register_profile(
    "dev",
    max_examples=10,
    verbosity=Verbosity.verbose,
    deadline=None,
)


def pytest_configure(config):
    """Configure pytest with custom settings."""
    # Load the default hypothesis profile
    settings.load_profile("default")


def pytest_addoption(parser):
    """Add custom command line options."""
    parser.addoption(
        "--platform",
        action="store",
        default="docker",
        choices=["minikube", "eks", "gke", "aks", "docker", "binary"],
        help="Target platform for tests",
    )
    parser.addoption(
        "--prometheus-url",
        action="store",
        default="http://localhost:9090",
        help="Prometheus API URL",
    )
    parser.addoption(
        "--prometheus-version",
        action="store",
        default="v3.5.0",
        help="Prometheus version to test",
    )


@pytest.fixture
def platform(request):
    """Get the target platform from command line."""
    return request.config.getoption("--platform")


@pytest.fixture
def prometheus_url(request):
    """Get the Prometheus URL from command line."""
    return request.config.getoption("--prometheus-url")


@pytest.fixture
def prometheus_version(request):
    """Get the Prometheus version from command line."""
    return request.config.getoption("--prometheus-version")
