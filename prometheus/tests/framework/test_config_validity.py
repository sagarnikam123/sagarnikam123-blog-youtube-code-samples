"""
Property-based tests for Prometheus configuration file validity.

**Feature: prometheus-installation, Property 2: Configuration File Validity**
**Validates: Requirements 1.5, 2.1, 2.2**

This module tests that for any generated prometheus.yml configuration file
(from binary, Docker, or Helm installation), the file should be valid YAML
and pass Prometheus configuration validation.
"""

import re
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

import pytest
import yaml
from hypothesis import given, settings, assume
from hypothesis import strategies as st


@dataclass
class ScrapeConfig:
    """Represents a Prometheus scrape configuration."""

    job_name: str
    static_configs: list[dict[str, Any]] = field(default_factory=list)
    scrape_interval: Optional[str] = None
    scrape_timeout: Optional[str] = None
    metrics_path: str = "/metrics"
    scheme: str = "http"
    relabel_configs: list[dict[str, Any]] = field(default_factory=list)
    metric_relabel_configs: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation."""
        config = {
            "job_name": self.job_name,
            "metrics_path": self.metrics_path,
            "scheme": self.scheme,
        }

        if self.static_configs:
            config["static_configs"] = self.static_configs
        if self.scrape_interval:
            config["scrape_interval"] = self.scrape_interval
        if self.scrape_timeout:
            config["scrape_timeout"] = self.scrape_timeout
        if self.relabel_configs:
            config["relabel_configs"] = self.relabel_configs
        if self.metric_relabel_configs:
            config["metric_relabel_configs"] = self.metric_relabel_configs

        return config


@dataclass
class PrometheusConfigFile:
    """Represents a complete Prometheus configuration file."""

    global_config: dict[str, Any] = field(default_factory=dict)
    alerting: Optional[dict[str, Any]] = None
    rule_files: list[str] = field(default_factory=list)
    scrape_configs: list[ScrapeConfig] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation."""
        config = {"global": self.global_config}

        if self.alerting:
            config["alerting"] = self.alerting
        if self.rule_files:
            config["rule_files"] = self.rule_files
        if self.scrape_configs:
            config["scrape_configs"] = [sc.to_dict() for sc in self.scrape_configs]

        return config

    def to_yaml(self) -> str:
        """Convert to YAML string."""
        return yaml.dump(self.to_dict(), default_flow_style=False, sort_keys=False)


def is_valid_duration(duration: str) -> bool:
    """Check if a string is a valid Prometheus duration."""
    pattern = r'^(\d+)(ms|s|m|h|d|w|y)$'
    return bool(re.match(pattern, duration))


def is_valid_job_name(name: str) -> bool:
    """Check if a string is a valid Prometheus job name."""
    # Job names must match [a-zA-Z_][a-zA-Z0-9_]*
    pattern = r'^[a-zA-Z_][a-zA-Z0-9_-]*$'
    return bool(re.match(pattern, name))


def is_valid_label_name(name: str) -> bool:
    """Check if a string is a valid Prometheus label name."""
    # Label names must match [a-zA-Z_][a-zA-Z0-9_]*
    pattern = r'^[a-zA-Z_][a-zA-Z0-9_]*$'
    return bool(re.match(pattern, name))


def is_valid_target(target: str) -> bool:
    """Check if a string is a valid scrape target (host:port)."""
    pattern = r'^[a-zA-Z0-9._-]+:\d+$'
    return bool(re.match(pattern, target))


def validate_prometheus_config(config: dict[str, Any]) -> tuple[bool, list[str]]:
    """
    Validate a Prometheus configuration dictionary.

    Returns:
        Tuple of (is_valid, list of error messages)
    """
    errors = []

    # Check global section
    if "global" not in config:
        errors.append("Missing 'global' section")
    else:
        global_config = config["global"]

        # Validate scrape_interval
        if "scrape_interval" in global_config:
            if not is_valid_duration(global_config["scrape_interval"]):
                errors.append(f"Invalid scrape_interval: {global_config['scrape_interval']}")

        # Validate evaluation_interval
        if "evaluation_interval" in global_config:
            if not is_valid_duration(global_config["evaluation_interval"]):
                errors.append(f"Invalid evaluation_interval: {global_config['evaluation_interval']}")

        # Validate scrape_timeout
        if "scrape_timeout" in global_config:
            if not is_valid_duration(global_config["scrape_timeout"]):
                errors.append(f"Invalid scrape_timeout: {global_config['scrape_timeout']}")

        # Validate external_labels
        if "external_labels" in global_config:
            for label_name in global_config["external_labels"].keys():
                if not is_valid_label_name(label_name):
                    errors.append(f"Invalid external label name: {label_name}")

    # Check scrape_configs section
    if "scrape_configs" in config:
        job_names = set()
        for i, scrape_config in enumerate(config["scrape_configs"]):
            # Validate job_name
            if "job_name" not in scrape_config:
                errors.append(f"scrape_config[{i}]: Missing 'job_name'")
            else:
                job_name = scrape_config["job_name"]
                if not is_valid_job_name(job_name):
                    errors.append(f"scrape_config[{i}]: Invalid job_name: {job_name}")
                if job_name in job_names:
                    errors.append(f"scrape_config[{i}]: Duplicate job_name: {job_name}")
                job_names.add(job_name)

            # Validate scrape_interval
            if "scrape_interval" in scrape_config:
                if not is_valid_duration(scrape_config["scrape_interval"]):
                    errors.append(f"scrape_config[{i}]: Invalid scrape_interval")

            # Validate scrape_timeout
            if "scrape_timeout" in scrape_config:
                if not is_valid_duration(scrape_config["scrape_timeout"]):
                    errors.append(f"scrape_config[{i}]: Invalid scrape_timeout")

            # Validate scheme
            if "scheme" in scrape_config:
                if scrape_config["scheme"] not in ["http", "https"]:
                    errors.append(f"scrape_config[{i}]: Invalid scheme: {scrape_config['scheme']}")

            # Validate static_configs
            if "static_configs" in scrape_config:
                for j, static_config in enumerate(scrape_config["static_configs"]):
                    if "targets" in static_config:
                        for target in static_config["targets"]:
                            if not is_valid_target(target):
                                errors.append(f"scrape_config[{i}].static_configs[{j}]: Invalid target: {target}")

                    # Validate labels
                    if "labels" in static_config:
                        for label_name in static_config["labels"].keys():
                            if not is_valid_label_name(label_name):
                                errors.append(f"scrape_config[{i}].static_configs[{j}]: Invalid label: {label_name}")

    return len(errors) == 0, errors


def validate_yaml_syntax(yaml_content: str) -> tuple[bool, Optional[str]]:
    """
    Validate that a string is valid YAML.

    Returns:
        Tuple of (is_valid, error message if invalid)
    """
    try:
        yaml.safe_load(yaml_content)
        return True, None
    except yaml.YAMLError as e:
        return False, str(e)


# Hypothesis strategies for generating valid Prometheus configurations
valid_durations = st.sampled_from(["5s", "10s", "15s", "30s", "1m", "5m", "10m", "15m", "30m", "1h"])
valid_job_names = st.text(
    alphabet="abcdefghijklmnopqrstuvwxyz_",
    min_size=1,
    max_size=30,
).filter(lambda s: s[0].isalpha() or s[0] == "_")
valid_label_names = st.text(
    alphabet="abcdefghijklmnopqrstuvwxyz_",
    min_size=1,
    max_size=20,
).filter(lambda s: s[0].isalpha() or s[0] == "_")
valid_label_values = st.text(
    alphabet="abcdefghijklmnopqrstuvwxyz0123456789-_",
    min_size=1,
    max_size=30,
)
valid_hosts = st.sampled_from([
    "localhost", "prometheus", "node-exporter", "alertmanager",
    "grafana", "cadvisor", "my-app", "app-server"
])
valid_ports = st.integers(min_value=1024, max_value=65535)
valid_schemes = st.sampled_from(["http", "https"])
valid_metrics_paths = st.sampled_from(["/metrics", "/probe", "/api/metrics", "/-/metrics"])


@st.composite
def valid_target(draw):
    """Generate a valid scrape target (host:port)."""
    host = draw(valid_hosts)
    port = draw(valid_ports)
    return f"{host}:{port}"


@st.composite
def valid_labels(draw):
    """Generate valid labels dictionary."""
    num_labels = draw(st.integers(min_value=0, max_value=5))
    labels = {}
    for _ in range(num_labels):
        name = draw(valid_label_names)
        value = draw(valid_label_values)
        labels[name] = value
    return labels


@st.composite
def valid_static_config(draw):
    """Generate a valid static_config entry."""
    num_targets = draw(st.integers(min_value=1, max_value=5))
    targets = [draw(valid_target()) for _ in range(num_targets)]
    labels = draw(valid_labels())

    config = {"targets": targets}
    if labels:
        config["labels"] = labels
    return config


@st.composite
def valid_scrape_config(draw, job_name: Optional[str] = None):
    """Generate a valid scrape_config entry."""
    if job_name is None:
        job_name = draw(valid_job_names)

    config = {
        "job_name": job_name,
        "static_configs": [draw(valid_static_config()) for _ in range(draw(st.integers(min_value=1, max_value=3)))],
    }

    # Optionally add other fields
    if draw(st.booleans()):
        config["scrape_interval"] = draw(valid_durations)
    if draw(st.booleans()):
        config["scrape_timeout"] = draw(valid_durations)
    if draw(st.booleans()):
        config["metrics_path"] = draw(valid_metrics_paths)
    if draw(st.booleans()):
        config["scheme"] = draw(valid_schemes)

    return config


@st.composite
def valid_global_config(draw):
    """Generate a valid global configuration."""
    config = {
        "scrape_interval": draw(valid_durations),
        "evaluation_interval": draw(valid_durations),
    }

    # Optionally add scrape_timeout
    if draw(st.booleans()):
        config["scrape_timeout"] = draw(valid_durations)

    # Optionally add external_labels
    if draw(st.booleans()):
        config["external_labels"] = draw(valid_labels())

    return config


@st.composite
def valid_prometheus_config(draw):
    """Generate a valid Prometheus configuration dictionary."""
    # Generate unique job names
    num_jobs = draw(st.integers(min_value=1, max_value=5))
    job_names = []
    for i in range(num_jobs):
        base_name = draw(valid_job_names)
        # Ensure uniqueness by appending index if needed
        job_name = f"{base_name}_{i}" if base_name in job_names else base_name
        job_names.append(job_name)

    config = {
        "global": draw(valid_global_config()),
        "scrape_configs": [draw(valid_scrape_config(job_name=name)) for name in job_names],
    }

    # Optionally add rule_files
    if draw(st.booleans()):
        config["rule_files"] = draw(st.lists(
            st.sampled_from([
                "/etc/prometheus/rules/*.yml",
                "/etc/prometheus/alerts/*.yml",
                "rules/*.yml",
            ]),
            min_size=0,
            max_size=3,
            unique=True,
        ))

    # Optionally add alerting
    if draw(st.booleans()):
        config["alerting"] = {
            "alertmanagers": [{
                "static_configs": [{
                    "targets": [draw(valid_target())]
                }]
            }]
        }

    return config


@pytest.mark.property
class TestConfigurationFileValidity:
    """
    Property-based tests for Prometheus configuration file validity.

    **Feature: prometheus-installation, Property 2: Configuration File Validity**
    **Validates: Requirements 1.5, 2.1, 2.2**
    """

    @given(config=valid_prometheus_config())
    @settings(max_examples=100)
    def test_generated_config_is_valid_yaml(self, config: dict[str, Any]):
        """
        Property: For any generated Prometheus configuration, the YAML
        representation should be valid YAML that can be parsed back.

        **Feature: prometheus-installation, Property 2: Configuration File Validity**
        **Validates: Requirements 1.5, 2.1, 2.2**
        """
        # Convert to YAML
        yaml_content = yaml.dump(config, default_flow_style=False, sort_keys=False)

        # Validate YAML syntax
        is_valid, error = validate_yaml_syntax(yaml_content)
        assert is_valid, f"Generated YAML is invalid: {error}"

        # Parse back and verify structure is preserved
        parsed = yaml.safe_load(yaml_content)
        assert "global" in parsed, "Parsed config missing 'global' section"
        assert "scrape_configs" in parsed, "Parsed config missing 'scrape_configs' section"

    @given(config=valid_prometheus_config())
    @settings(max_examples=100)
    def test_generated_config_passes_validation(self, config: dict[str, Any]):
        """
        Property: For any generated Prometheus configuration, it should
        pass Prometheus configuration validation rules.

        **Feature: prometheus-installation, Property 2: Configuration File Validity**
        **Validates: Requirements 1.5, 2.1, 2.2**
        """
        is_valid, errors = validate_prometheus_config(config)
        assert is_valid, f"Configuration validation failed: {errors}"

    @given(config=valid_prometheus_config())
    @settings(max_examples=100)
    def test_yaml_round_trip_preserves_config(self, config: dict[str, Any]):
        """
        Property: For any valid Prometheus configuration, converting to YAML
        and parsing back should produce an equivalent configuration.

        **Feature: prometheus-installation, Property 2: Configuration File Validity**
        **Validates: Requirements 1.5, 2.1, 2.2**
        """
        # Convert to YAML and back
        yaml_content = yaml.dump(config, default_flow_style=False, sort_keys=False)
        parsed = yaml.safe_load(yaml_content)

        # Verify key sections are preserved
        assert parsed["global"]["scrape_interval"] == config["global"]["scrape_interval"]
        assert parsed["global"]["evaluation_interval"] == config["global"]["evaluation_interval"]
        assert len(parsed["scrape_configs"]) == len(config["scrape_configs"])

        # Verify job names are preserved
        original_jobs = {sc["job_name"] for sc in config["scrape_configs"]}
        parsed_jobs = {sc["job_name"] for sc in parsed["scrape_configs"]}
        assert original_jobs == parsed_jobs

    @given(config=valid_prometheus_config())
    @settings(max_examples=100)
    def test_file_write_and_read_preserves_config(self, config: dict[str, Any]):
        """
        Property: For any valid Prometheus configuration, writing to a file
        and reading back should produce an equivalent configuration.

        **Feature: prometheus-installation, Property 2: Configuration File Validity**
        **Validates: Requirements 1.5, 2.1, 2.2**
        """
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yml", delete=False) as f:
            yaml.dump(config, f, default_flow_style=False, sort_keys=False)
            temp_path = Path(f.name)

        try:
            # Read back from file
            with open(temp_path, "r") as f:
                loaded = yaml.safe_load(f)

            # Verify structure is preserved
            assert "global" in loaded
            assert "scrape_configs" in loaded
            assert loaded["global"]["scrape_interval"] == config["global"]["scrape_interval"]
            assert len(loaded["scrape_configs"]) == len(config["scrape_configs"])
        finally:
            temp_path.unlink()

    @given(config=valid_prometheus_config())
    @settings(max_examples=100)
    def test_job_names_are_unique(self, config: dict[str, Any]):
        """
        Property: For any valid Prometheus configuration, all job names
        in scrape_configs should be unique.

        **Feature: prometheus-installation, Property 2: Configuration File Validity**
        **Validates: Requirements 1.5, 2.1, 2.2**
        """
        job_names = [sc["job_name"] for sc in config["scrape_configs"]]
        assert len(job_names) == len(set(job_names)), "Job names must be unique"


@pytest.mark.property
class TestExistingConfigurationFiles:
    """
    Tests for existing Prometheus configuration files in the repository.

    **Feature: prometheus-installation, Property 2: Configuration File Validity**
    **Validates: Requirements 1.5, 2.1, 2.2**
    """

    def test_binary_prometheus_yml_is_valid(self):
        """
        Test that the binary installation prometheus.yml is valid.

        **Feature: prometheus-installation, Property 2: Configuration File Validity**
        **Validates: Requirements 1.5**
        """
        config_file = Path(__file__).parent.parent.parent / "install" / "binary" / "prometheus.yml"

        if config_file.exists():
            content = config_file.read_text()

            # Validate YAML syntax
            is_valid_yaml, error = validate_yaml_syntax(content)
            assert is_valid_yaml, f"Binary prometheus.yml has invalid YAML: {error}"

            # Parse and validate structure
            config = yaml.safe_load(content)
            is_valid, errors = validate_prometheus_config(config)
            assert is_valid, f"Binary prometheus.yml validation failed: {errors}"

            # Verify required sections exist
            assert "global" in config, "Missing 'global' section"
            assert "scrape_configs" in config, "Missing 'scrape_configs' section"

            # Verify self-monitoring job exists
            job_names = [sc["job_name"] for sc in config["scrape_configs"]]
            assert "prometheus" in job_names, "Missing 'prometheus' self-monitoring job"

    def test_docker_prometheus_yml_is_valid(self):
        """
        Test that the Docker installation prometheus.yml is valid.

        **Feature: prometheus-installation, Property 2: Configuration File Validity**
        **Validates: Requirements 2.1, 2.2**
        """
        config_file = Path(__file__).parent.parent.parent / "install" / "docker" / "prometheus.yml"

        if config_file.exists():
            content = config_file.read_text()

            # Validate YAML syntax
            is_valid_yaml, error = validate_yaml_syntax(content)
            assert is_valid_yaml, f"Docker prometheus.yml has invalid YAML: {error}"

            # Parse and validate structure
            config = yaml.safe_load(content)
            is_valid, errors = validate_prometheus_config(config)
            assert is_valid, f"Docker prometheus.yml validation failed: {errors}"

            # Verify required sections exist
            assert "global" in config, "Missing 'global' section"
            assert "scrape_configs" in config, "Missing 'scrape_configs' section"

            # Verify self-monitoring job exists
            job_names = [sc["job_name"] for sc in config["scrape_configs"]]
            assert "prometheus" in job_names, "Missing 'prometheus' self-monitoring job"

            # Docker config should have alerting section
            assert "alerting" in config, "Docker config should have 'alerting' section"

            # Docker config should have rule_files
            assert "rule_files" in config, "Docker config should have 'rule_files' section"

    def test_all_prometheus_yml_files_are_valid(self):
        """
        Test that all prometheus.yml files in the repository are valid.

        **Feature: prometheus-installation, Property 2: Configuration File Validity**
        **Validates: Requirements 1.5, 2.1, 2.2**
        """
        install_dir = Path(__file__).parent.parent.parent / "install"

        # Find all prometheus.yml files, excluding Grafana provisioning files
        # which are datasource configs, not Prometheus configs
        prometheus_files = [
            f for f in install_dir.glob("**/prometheus.yml")
            if "grafana" not in str(f).lower() and "provisioning" not in str(f).lower()
        ]

        for config_file in prometheus_files:
            content = config_file.read_text()

            # Validate YAML syntax
            is_valid_yaml, error = validate_yaml_syntax(content)
            assert is_valid_yaml, f"{config_file} has invalid YAML: {error}"

            # Parse and validate structure
            config = yaml.safe_load(content)
            is_valid, errors = validate_prometheus_config(config)
            assert is_valid, f"{config_file} validation failed: {errors}"
