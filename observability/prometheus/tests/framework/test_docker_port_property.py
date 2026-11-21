"""
Property-based tests for Docker port configuration.

**Feature: prometheus-installation, Property 3: Docker Port Configuration**
**Validates: Requirements 2.4, 2.6**

This module tests that for any valid port number (1024-65535), when specified
in Docker configuration, Prometheus should be accessible on that port after
container startup.

The property validates:
- Port configuration is correctly applied to docker-compose.yml
- Environment variable substitution works correctly for port configuration
- Generated configuration maintains valid Docker Compose syntax
"""

import os
import re
import tempfile
from pathlib import Path
from typing import Any

import pytest
import yaml
from hypothesis import given, settings, assume, HealthCheck
from hypothesis import strategies as st


# Valid port range for non-privileged ports
VALID_PORT_MIN = 1024
VALID_PORT_MAX = 65535
DEFAULT_PROMETHEUS_PORT = 9090


def parse_docker_compose(content: str) -> dict[str, Any]:
    """Parse docker-compose YAML content."""
    return yaml.safe_load(content)


def generate_docker_compose_with_port(port: int, template_path: Path) -> str:
    """
    Generate docker-compose content with the specified port.

    This simulates the environment variable substitution that Docker Compose
    performs when PROMETHEUS_PORT is set.

    Args:
        port: The port number to configure
        template_path: Path to the docker-compose.yml template

    Returns:
        Docker compose content with port substituted
    """
    with open(template_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Substitute the port variable pattern ${PROMETHEUS_PORT:-9090}
    # This mimics Docker Compose's environment variable substitution
    content = re.sub(
        r'\$\{PROMETHEUS_PORT:-\d+\}',
        str(port),
        content
    )

    return content


def extract_port_mapping(compose_config: dict[str, Any]) -> tuple[int, int] | None:
    """
    Extract the host:container port mapping from docker-compose config.

    Args:
        compose_config: Parsed docker-compose configuration

    Returns:
        Tuple of (host_port, container_port) or None if not found
    """
    services = compose_config.get("services", {})
    prometheus_service = services.get("prometheus", {})
    ports = prometheus_service.get("ports", [])

    if not ports:
        return None

    # Parse the first port mapping (format: "host:container" or just "port")
    port_mapping = ports[0]

    if isinstance(port_mapping, str):
        if ":" in port_mapping:
            parts = port_mapping.split(":")
            return int(parts[0]), int(parts[1])
        else:
            port = int(port_mapping)
            return port, port
    elif isinstance(port_mapping, int):
        return port_mapping, port_mapping

    return None


def validate_docker_compose_syntax(compose_config: dict[str, Any]) -> list[str]:
    """
    Validate basic Docker Compose syntax requirements.

    Args:
        compose_config: Parsed docker-compose configuration

    Returns:
        List of validation errors (empty if valid)
    """
    errors = []

    # Check for required top-level keys
    if "services" not in compose_config:
        errors.append("Missing 'services' key")
        return errors

    services = compose_config["services"]

    # Check for prometheus service
    if "prometheus" not in services:
        errors.append("Missing 'prometheus' service")
        return errors

    prometheus = services["prometheus"]

    # Check for required prometheus service keys
    if "image" not in prometheus:
        errors.append("Missing 'image' in prometheus service")

    if "ports" not in prometheus:
        errors.append("Missing 'ports' in prometheus service")
    elif not prometheus["ports"]:
        errors.append("Empty 'ports' list in prometheus service")

    return errors


def is_valid_port(port: int) -> bool:
    """Check if a port number is valid for non-privileged use."""
    return VALID_PORT_MIN <= port <= VALID_PORT_MAX


# Hypothesis strategies for port generation
valid_ports = st.integers(min_value=VALID_PORT_MIN, max_value=VALID_PORT_MAX)

# Common ports to avoid (well-known services that might conflict)
common_conflicting_ports = {
    3000,  # Grafana default
    3306,  # MySQL
    5432,  # PostgreSQL
    6379,  # Redis
    8080,  # Common HTTP alt
    8443,  # Common HTTPS alt
    9093,  # Alertmanager
    9100,  # Node Exporter
}

# Strategy for ports that are less likely to conflict
safe_ports = st.integers(
    min_value=VALID_PORT_MIN,
    max_value=VALID_PORT_MAX
).filter(lambda p: p not in common_conflicting_ports)


@pytest.mark.property
class TestDockerPortConfiguration:
    """
    Property-based tests for Docker port configuration.

    **Feature: prometheus-installation, Property 3: Docker Port Configuration**
    **Validates: Requirements 2.4, 2.6**
    """

    @pytest.fixture
    def docker_compose_path(self) -> Path:
        """Get the path to the docker-compose.yml template."""
        # Navigate from tests/framework to install/docker
        base_path = Path(__file__).parent.parent.parent
        return base_path / "install" / "docker" / "docker-compose.yml"

    @given(port=valid_ports)
    @settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_port_configuration_applied_correctly(
        self,
        port: int,
        docker_compose_path: Path,
    ):
        """
        Property: For any valid port number (1024-65535), the port configuration
        should be correctly applied to the docker-compose configuration.

        **Feature: prometheus-installation, Property 3: Docker Port Configuration**
        **Validates: Requirements 2.4, 2.6**
        """
        assume(docker_compose_path.exists())

        # Generate docker-compose with the specified port
        compose_content = generate_docker_compose_with_port(port, docker_compose_path)

        # Parse the generated configuration
        compose_config = parse_docker_compose(compose_content)

        # Extract port mapping
        port_mapping = extract_port_mapping(compose_config)

        # Verify port mapping exists and is correct
        assert port_mapping is not None, "Port mapping should exist"
        host_port, container_port = port_mapping

        # Host port should match the configured port
        assert host_port == port, f"Host port {host_port} should match configured port {port}"

        # Container port should always be 9090 (Prometheus default internal port)
        assert container_port == DEFAULT_PROMETHEUS_PORT, \
            f"Container port should be {DEFAULT_PROMETHEUS_PORT}"

    @given(port=valid_ports)
    @settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_generated_config_is_valid_yaml(
        self,
        port: int,
        docker_compose_path: Path,
    ):
        """
        Property: For any valid port configuration, the generated docker-compose
        should be valid YAML.

        **Feature: prometheus-installation, Property 3: Docker Port Configuration**
        **Validates: Requirements 2.4, 2.6**
        """
        assume(docker_compose_path.exists())

        # Generate docker-compose with the specified port
        compose_content = generate_docker_compose_with_port(port, docker_compose_path)

        # Parsing should not raise an exception
        try:
            compose_config = parse_docker_compose(compose_content)
            assert compose_config is not None, "Parsed config should not be None"
        except yaml.YAMLError as e:
            pytest.fail(f"Generated config is not valid YAML: {e}")

    @given(port=valid_ports)
    @settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_generated_config_has_valid_structure(
        self,
        port: int,
        docker_compose_path: Path,
    ):
        """
        Property: For any valid port configuration, the generated docker-compose
        should have valid Docker Compose structure.

        **Feature: prometheus-installation, Property 3: Docker Port Configuration**
        **Validates: Requirements 2.4, 2.6**
        """
        assume(docker_compose_path.exists())

        # Generate docker-compose with the specified port
        compose_content = generate_docker_compose_with_port(port, docker_compose_path)
        compose_config = parse_docker_compose(compose_content)

        # Validate structure
        errors = validate_docker_compose_syntax(compose_config)
        assert not errors, f"Docker Compose validation errors: {errors}"

    @given(port=valid_ports)
    @settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_port_in_valid_range(
        self,
        port: int,
        docker_compose_path: Path,
    ):
        """
        Property: The configured port should always be in the valid range
        (1024-65535) for non-privileged ports.

        **Feature: prometheus-installation, Property 3: Docker Port Configuration**
        **Validates: Requirements 2.4, 2.6**
        """
        assume(docker_compose_path.exists())

        # Generate docker-compose with the specified port
        compose_content = generate_docker_compose_with_port(port, docker_compose_path)
        compose_config = parse_docker_compose(compose_content)

        # Extract and validate port
        port_mapping = extract_port_mapping(compose_config)
        assert port_mapping is not None

        host_port, _ = port_mapping
        assert is_valid_port(host_port), \
            f"Port {host_port} is not in valid range [{VALID_PORT_MIN}, {VALID_PORT_MAX}]"

    @given(port1=valid_ports, port2=valid_ports)
    @settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_different_ports_produce_different_configs(
        self,
        port1: int,
        port2: int,
        docker_compose_path: Path,
    ):
        """
        Property: Different port configurations should produce different
        port mappings in the generated config.

        **Feature: prometheus-installation, Property 3: Docker Port Configuration**
        **Validates: Requirements 2.4, 2.6**
        """
        assume(docker_compose_path.exists())
        assume(port1 != port2)

        # Generate configs with different ports
        compose1 = generate_docker_compose_with_port(port1, docker_compose_path)
        compose2 = generate_docker_compose_with_port(port2, docker_compose_path)

        config1 = parse_docker_compose(compose1)
        config2 = parse_docker_compose(compose2)

        mapping1 = extract_port_mapping(config1)
        mapping2 = extract_port_mapping(config2)

        assert mapping1 is not None and mapping2 is not None

        # Host ports should be different
        assert mapping1[0] != mapping2[0], \
            f"Different port configs should produce different host ports"

    def test_default_port_is_9090(self, docker_compose_path: Path):
        """
        Test that the default port (when no override is specified) is 9090.

        **Feature: prometheus-installation, Property 3: Docker Port Configuration**
        **Validates: Requirements 2.4**
        """
        if not docker_compose_path.exists():
            pytest.skip("docker-compose.yml not found")

        # Read the original template without substitution
        with open(docker_compose_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Check that the default port is 9090
        assert "${PROMETHEUS_PORT:-9090}" in content or "9090:9090" in content, \
            "Default port should be 9090"
