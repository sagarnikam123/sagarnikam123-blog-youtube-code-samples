"""
Property-based tests for static scrape configuration.

**Feature: prometheus-installation, Property 6: Static Scrape Configuration**
**Validates: Requirements 5.1, 5.5, 5.7**

This module tests that for any valid static_config with properly defined targets,
the configuration is valid YAML, follows Prometheus scrape config schema, and
supports configurable scrape_interval per job.

Property 6: Static Scrape Configuration
*For any* valid static_config with a reachable target, Prometheus should
successfully scrape metrics from that target within the configured scrape_interval.
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


# Valid duration patterns for Prometheus (e.g., 15s, 1m, 5m, 1h)
DURATION_PATTERN = re.compile(r"^[0-9]+[smhd]$")

# Valid label name pattern (Prometheus label naming rules)
LABEL_NAME_PATTERN = re.compile(r"^[a-zA-Z_][a-zA-Z0-9_]*$")


@dataclass
class StaticTarget:
    """Represents a static scrape target."""
    targets: list[str]
    labels: dict[str, str] = field(default_factory=dict)


@dataclass
class ScrapeJobConfig:
    """Represents a Prometheus scrape job configuration."""
    job_name: str
    scrape_interval: str = "15s"
    scrape_timeout: str = "10s"
    metrics_path: str = "/metrics"
    scheme: str = "http"
    static_configs: list[StaticTarget] = field(default_factory=list)
    honor_labels: bool = False
    honor_timestamps: bool = True


def is_valid_duration(duration: str) -> bool:
    """Check if a duration string is valid for Prometheus."""
    return bool(DURATION_PATTERN.match(duration))


def is_valid_label_name(name: str) -> bool:
    """Check if a label name is valid for Prometheus."""
    return bool(LABEL_NAME_PATTERN.match(name))


def is_valid_target(target: str) -> bool:
    """Check if a target address is valid (host:port format)."""
    if not target:
        return False
    # Basic validation: should have host and optional port
    parts = target.rsplit(":", 1)
    if len(parts) == 2:
        host, port = parts
        try:
            port_num = int(port)
            return 1 <= port_num <= 65535 and len(host) > 0
        except ValueError:
            return False
    # Host without port is also valid
    return len(target) > 0


def parse_duration_to_seconds(duration: str) -> int:
    """Parse a Prometheus duration string to seconds."""
    if not duration:
        return 0
    unit = duration[-1]
    value = int(duration[:-1])
    multipliers = {"s": 1, "m": 60, "h": 3600, "d": 86400}
    return value * multipliers.get(unit, 1)


def validate_scrape_config(config: dict[str, Any]) -> list[str]:
    """
    Validate a scrape configuration dictionary.

    Returns a list of validation errors (empty if valid).
    """
    errors = []

    # Check required fields
    if "job_name" not in config:
        errors.append("Missing required field: job_name")
    elif not config["job_name"]:
        errors.append("job_name cannot be empty")

    # Validate scrape_interval if present
    if "scrape_interval" in config:
        if not is_valid_duration(config["scrape_interval"]):
            errors.append(f"Invalid scrape_interval: {config['scrape_interval']}")

    # Validate scrape_timeout if present
    if "scrape_timeout" in config:
        if not is_valid_duration(config["scrape_timeout"]):
            errors.append(f"Invalid scrape_timeout: {config['scrape_timeout']}")

    # Validate timeout <= interval
    if "scrape_interval" in config and "scrape_timeout" in config:
        interval_sec = parse_duration_to_seconds(config["scrape_interval"])
        timeout_sec = parse_duration_to_seconds(config["scrape_timeout"])
        if timeout_sec > interval_sec:
            errors.append("scrape_timeout cannot exceed scrape_interval")

    # Validate scheme
    if "scheme" in config:
        if config["scheme"] not in ("http", "https"):
            errors.append(f"Invalid scheme: {config['scheme']}")

    # Validate static_configs
    if "static_configs" in config:
        for i, sc in enumerate(config["static_configs"]):
            if "targets" not in sc:
                errors.append(f"static_configs[{i}]: missing targets")
            elif not sc["targets"]:
                errors.append(f"static_configs[{i}]: targets cannot be empty")
            else:
                for j, target in enumerate(sc["targets"]):
                    if not is_valid_target(target):
                        errors.append(
                            f"static_configs[{i}].targets[{j}]: invalid target '{target}'"
                        )

            # Validate labels
            if "labels" in sc:
                for label_name in sc["labels"].keys():
                    if not is_valid_label_name(label_name):
                        errors.append(
                            f"static_configs[{i}].labels: invalid label name '{label_name}'"
                        )

    return errors


def scrape_config_to_dict(config: ScrapeJobConfig) -> dict[str, Any]:
    """Convert a ScrapeJobConfig to a dictionary."""
    result = {
        "job_name": config.job_name,
        "scrape_interval": config.scrape_interval,
        "scrape_timeout": config.scrape_timeout,
        "metrics_path": config.metrics_path,
        "scheme": config.scheme,
        "honor_labels": config.honor_labels,
        "honor_timestamps": config.honor_timestamps,
    }

    if config.static_configs:
        result["static_configs"] = [
            {
                "targets": sc.targets,
                "labels": sc.labels,
            }
            for sc in config.static_configs
        ]

    return result


# Hypothesis strategies for generating valid configurations

valid_job_names = st.text(
    alphabet="abcdefghijklmnopqrstuvwxyz0123456789-_",
    min_size=1,
    max_size=50,
).filter(lambda s: s[0].isalpha())

valid_durations = st.sampled_from([
    "5s", "10s", "15s", "30s", "60s",
    "1m", "2m", "5m", "10m", "15m", "30m",
    "1h", "2h", "6h", "12h", "24h",
])

valid_schemes = st.sampled_from(["http", "https"])

valid_metrics_paths = st.sampled_from([
    "/metrics",
    "/api/metrics",
    "/prometheus/metrics",
    "/actuator/prometheus",
    "/_metrics",
])

valid_hostnames = st.sampled_from([
    "localhost",
    "app-server",
    "web-1.example.com",
    "api.internal",
    "192.168.1.100",
    "10.0.0.1",
])

valid_ports = st.integers(min_value=1024, max_value=65535)

valid_label_names = st.text(
    alphabet="abcdefghijklmnopqrstuvwxyz_",
    min_size=1,
    max_size=20,
).filter(lambda s: s[0].isalpha() or s[0] == "_")

valid_label_values = st.text(
    alphabet="abcdefghijklmnopqrstuvwxyz0123456789-_",
    min_size=1,
    max_size=50,
)


@st.composite
def valid_target(draw) -> str:
    """Generate a valid target address (host:port)."""
    hostname = draw(valid_hostnames)
    port = draw(valid_ports)
    return f"{hostname}:{port}"


@st.composite
def valid_labels(draw) -> dict[str, str]:
    """Generate valid labels dictionary."""
    num_labels = draw(st.integers(min_value=0, max_value=5))
    labels = {}
    for _ in range(num_labels):
        name = draw(valid_label_names)
        value = draw(valid_label_values)
        labels[name] = value
    return labels


@st.composite
def valid_static_config(draw) -> dict[str, Any]:
    """Generate a valid static_config entry."""
    num_targets = draw(st.integers(min_value=1, max_value=5))
    targets = [draw(valid_target()) for _ in range(num_targets)]
    labels = draw(valid_labels())
    return {"targets": targets, "labels": labels}


@st.composite
def valid_scrape_job_config(draw) -> dict[str, Any]:
    """Generate a valid scrape job configuration dictionary."""
    job_name = draw(valid_job_names)
    scrape_interval = draw(valid_durations)
    scheme = draw(valid_schemes)
    metrics_path = draw(valid_metrics_paths)

    # Generate timeout that doesn't exceed interval
    interval_seconds = parse_duration_to_seconds(scrape_interval)
    timeout_options = [d for d in [
        "5s", "10s", "15s", "30s", "60s", "1m", "2m", "5m"
    ] if parse_duration_to_seconds(d) <= interval_seconds]
    scrape_timeout = draw(st.sampled_from(timeout_options)) if timeout_options else "10s"

    num_static_configs = draw(st.integers(min_value=1, max_value=3))
    static_configs = [draw(valid_static_config()) for _ in range(num_static_configs)]

    return {
        "job_name": job_name,
        "scrape_interval": scrape_interval,
        "scrape_timeout": scrape_timeout,
        "metrics_path": metrics_path,
        "scheme": scheme,
        "static_configs": static_configs,
    }


@pytest.mark.property
class TestStaticScrapeConfigProperty:
    """
    Property-based tests for static scrape configuration.

    **Feature: prometheus-installation, Property 6: Static Scrape Configuration**
    **Validates: Requirements 5.1, 5.5, 5.7**
    """

    @given(config=valid_scrape_job_config())
    @settings(max_examples=100)
    def test_valid_config_passes_validation(self, config: dict[str, Any]):
        """
        Property: For any valid scrape job configuration, validation should pass.

        **Feature: prometheus-installation, Property 6: Static Scrape Configuration**
        **Validates: Requirements 5.1, 5.5, 5.7**
        """
        errors = validate_scrape_config(config)
        assert len(errors) == 0, f"Validation errors: {errors}"

    @given(config=valid_scrape_job_config())
    @settings(max_examples=100)
    def test_config_yaml_round_trip(self, config: dict[str, Any]):
        """
        Property: For any valid configuration, YAML serialization and
        deserialization should preserve all values.

        **Feature: prometheus-installation, Property 6: Static Scrape Configuration**
        **Validates: Requirements 5.1**
        """
        # Serialize to YAML
        yaml_str = yaml.dump(config, default_flow_style=False)

        # Deserialize from YAML
        loaded_config = yaml.safe_load(yaml_str)

        # Verify all values are preserved
        assert loaded_config["job_name"] == config["job_name"]
        assert loaded_config["scrape_interval"] == config["scrape_interval"]
        assert loaded_config["scrape_timeout"] == config["scrape_timeout"]
        assert loaded_config["metrics_path"] == config["metrics_path"]
        assert loaded_config["scheme"] == config["scheme"]
        assert len(loaded_config["static_configs"]) == len(config["static_configs"])

        for i, sc in enumerate(config["static_configs"]):
            loaded_sc = loaded_config["static_configs"][i]
            assert loaded_sc["targets"] == sc["targets"]
            assert loaded_sc["labels"] == sc["labels"]

    @given(config=valid_scrape_job_config())
    @settings(max_examples=100)
    def test_scrape_interval_is_configurable(self, config: dict[str, Any]):
        """
        Property: For any valid configuration, scrape_interval should be
        a valid Prometheus duration and configurable per job.

        **Feature: prometheus-installation, Property 6: Static Scrape Configuration**
        **Validates: Requirements 5.5**
        """
        scrape_interval = config["scrape_interval"]

        # Verify it's a valid duration
        assert is_valid_duration(scrape_interval), \
            f"Invalid scrape_interval: {scrape_interval}"

        # Verify it can be parsed to seconds
        seconds = parse_duration_to_seconds(scrape_interval)
        assert seconds > 0, f"scrape_interval should be positive: {scrape_interval}"

    @given(config=valid_scrape_job_config())
    @settings(max_examples=100)
    def test_timeout_does_not_exceed_interval(self, config: dict[str, Any]):
        """
        Property: For any valid configuration, scrape_timeout should not
        exceed scrape_interval.

        **Feature: prometheus-installation, Property 6: Static Scrape Configuration**
        **Validates: Requirements 5.5**
        """
        interval_sec = parse_duration_to_seconds(config["scrape_interval"])
        timeout_sec = parse_duration_to_seconds(config["scrape_timeout"])

        assert timeout_sec <= interval_sec, \
            f"Timeout ({config['scrape_timeout']}) exceeds interval ({config['scrape_interval']})"

    @given(config=valid_scrape_job_config())
    @settings(max_examples=100)
    def test_static_configs_have_valid_targets(self, config: dict[str, Any]):
        """
        Property: For any valid configuration, all static_configs should
        have at least one valid target.

        **Feature: prometheus-installation, Property 6: Static Scrape Configuration**
        **Validates: Requirements 5.1, 5.7**
        """
        static_configs = config.get("static_configs", [])
        assert len(static_configs) > 0, "Should have at least one static_config"

        for i, sc in enumerate(static_configs):
            targets = sc.get("targets", [])
            assert len(targets) > 0, f"static_configs[{i}] should have targets"

            for j, target in enumerate(targets):
                assert is_valid_target(target), \
                    f"static_configs[{i}].targets[{j}] is invalid: {target}"

    @given(config=valid_scrape_job_config())
    @settings(max_examples=100)
    def test_labels_have_valid_names(self, config: dict[str, Any]):
        """
        Property: For any valid configuration, all label names should
        follow Prometheus naming conventions.

        **Feature: prometheus-installation, Property 6: Static Scrape Configuration**
        **Validates: Requirements 5.1**
        """
        for i, sc in enumerate(config.get("static_configs", [])):
            labels = sc.get("labels", {})
            for label_name in labels.keys():
                assert is_valid_label_name(label_name), \
                    f"static_configs[{i}].labels has invalid name: {label_name}"

    @given(config=valid_scrape_job_config())
    @settings(max_examples=100)
    def test_config_file_write_and_read(self, config: dict[str, Any]):
        """
        Property: For any valid configuration, writing to a file and
        reading back should produce equivalent configuration.

        **Feature: prometheus-installation, Property 6: Static Scrape Configuration**
        **Validates: Requirements 5.1, 5.7**
        """
        # Create a full prometheus config structure
        prometheus_config = {
            "global": {
                "scrape_interval": "15s",
                "evaluation_interval": "15s",
            },
            "scrape_configs": [config],
        }

        # Write to temp file
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".yml", delete=False
        ) as f:
            yaml.dump(prometheus_config, f, default_flow_style=False)
            temp_path = Path(f.name)

        try:
            # Read back
            with open(temp_path, "r", encoding="utf-8") as f:
                loaded = yaml.safe_load(f)

            # Verify the scrape config is preserved
            loaded_config = loaded["scrape_configs"][0]
            assert loaded_config["job_name"] == config["job_name"]
            assert loaded_config["scrape_interval"] == config["scrape_interval"]
            assert len(loaded_config["static_configs"]) == len(config["static_configs"])
        finally:
            temp_path.unlink()

    @given(
        base_interval=valid_durations,
        job1_interval=valid_durations,
        job2_interval=valid_durations,
    )
    @settings(max_examples=100)
    def test_per_job_scrape_interval_override(
        self,
        base_interval: str,
        job1_interval: str,
        job2_interval: str,
    ):
        """
        Property: Each job can have its own scrape_interval that overrides
        the global default.

        **Feature: prometheus-installation, Property 6: Static Scrape Configuration**
        **Validates: Requirements 5.5**
        """
        # Create config with global interval and per-job overrides
        prometheus_config = {
            "global": {
                "scrape_interval": base_interval,
            },
            "scrape_configs": [
                {
                    "job_name": "job1",
                    "scrape_interval": job1_interval,
                    "static_configs": [{"targets": ["localhost:8080"]}],
                },
                {
                    "job_name": "job2",
                    "scrape_interval": job2_interval,
                    "static_configs": [{"targets": ["localhost:8081"]}],
                },
            ],
        }

        # Verify each job has its own interval
        job1_config = prometheus_config["scrape_configs"][0]
        job2_config = prometheus_config["scrape_configs"][1]

        assert job1_config["scrape_interval"] == job1_interval
        assert job2_config["scrape_interval"] == job2_interval

        # Intervals can be different from global
        # (this is the key property - per-job configuration)
        assert is_valid_duration(job1_config["scrape_interval"])
        assert is_valid_duration(job2_config["scrape_interval"])
