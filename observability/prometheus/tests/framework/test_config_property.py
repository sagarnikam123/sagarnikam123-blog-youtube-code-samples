"""
Property-based tests for configuration parsing.

**Feature: prometheus-installation, Property 9: Test Configuration Parsing**
**Validates: Requirements 10.1, 10.2**

This module tests that for any valid YAML test configuration,
the test framework parses it correctly and produces a configuration
object with all specified values.
"""

import tempfile
from pathlib import Path

import pytest
import yaml
from hypothesis import given, settings
from hypothesis import strategies as st

from framework.config import TestConfig


# Strategies for generating valid configuration values
valid_platforms = st.sampled_from(["minikube", "eks", "gke", "aks", "docker", "binary"])
valid_deployment_modes = st.sampled_from(["monolithic", "distributed"])
valid_versions = st.sampled_from(["v3.4.0", "v3.5.0", "v3.9.0", "v2.45.0"])
valid_namespaces = st.text(
    alphabet="abcdefghijklmnopqrstuvwxyz0123456789-",
    min_size=1,
    max_size=63,
).filter(lambda s: s[0].isalpha() and s[-1].isalnum())
valid_urls = st.sampled_from([
    "http://localhost:9090",
    "http://prometheus:9090",
    "https://prometheus.monitoring.svc:9090",
])
valid_timeouts = st.sampled_from(["30s", "60s", "120s", "5m", "10m"])
valid_durations = st.sampled_from(["15m", "30m", "1h", "6h", "24h"])
valid_components = st.lists(
    st.sampled_from(["node-exporter", "alertmanager", "grafana", "kube-state-metrics"]),
    min_size=1,
    max_size=4,
    unique=True,
)
valid_targets = st.lists(
    st.integers(min_value=10, max_value=100000),
    min_size=1,
    max_size=5,
    unique=True,
)
valid_series = st.lists(
    st.integers(min_value=1000, max_value=10000000),
    min_size=1,
    max_size=5,
    unique=True,
)
valid_dimensions = st.lists(
    st.sampled_from(["targets", "series", "cardinality", "retention", "queries"]),
    min_size=1,
    max_size=5,
    unique=True,
)
valid_chaos_tools = st.sampled_from(["chaos-mesh", "litmus"])
positive_int = st.integers(min_value=1, max_value=10000000)
test_names = st.text(
    alphabet="abcdefghijklmnopqrstuvwxyz0123456789-_",
    min_size=1,
    max_size=50,
).filter(lambda s: s[0].isalpha())
valid_healthcheck_endpoints = st.lists(
    st.sampled_from(["/-/healthy", "/-/ready", "/api/v1/status/runtimeinfo"]),
    min_size=1,
    max_size=3,
    unique=True,
)
valid_k6_scripts = st.lists(
    st.sampled_from(["k6/query-load.js", "k6/query-range-load.js", "k6/remote-write-load.js", "k6/benchmark.js"]),
    min_size=1,
    max_size=4,
    unique=True,
)
valid_api_endpoints = st.lists(
    st.sampled_from(["/api/v1/query", "/api/v1/query_range", "/api/v1/labels", "/api/v1/series"]),
    min_size=1,
    max_size=4,
    unique=True,
)
valid_concurrent_users = st.lists(
    st.integers(min_value=1, max_value=1000),
    min_size=1,
    max_size=5,
    unique=True,
)


@st.composite
def valid_platform_and_mode(draw):
    """Generate valid platform and deployment mode combinations."""
    platform = draw(valid_platforms)
    # docker and binary only support monolithic mode
    if platform in ["docker", "binary"]:
        deployment_mode = "monolithic"
    else:
        deployment_mode = draw(valid_deployment_modes)
    return platform, deployment_mode


@st.composite
def valid_test_config_dict(draw):
    """Generate a valid test configuration dictionary."""
    platform, deployment_mode = draw(valid_platform_and_mode())

    return {
        "test": {
            "name": draw(test_names),
            "platform": platform,
            "deployment_mode": deployment_mode,
            "prometheus": {
                "version": draw(valid_versions),
                "namespace": draw(valid_namespaces),
                "url": draw(valid_urls),
            },
            "runner": {
                "python_version": "3.10+",
                "k6_path": "/usr/local/bin/k6",
                "kubectl_path": "/usr/local/bin/kubectl",
            },
            "credentials": {
                "kubeconfig": "${KUBECONFIG}",
                "aws_profile": "${AWS_PROFILE}",
                "gcp_credentials": "${GOOGLE_APPLICATION_CREDENTIALS}",
                "azure_subscription": "${AZURE_SUBSCRIPTION_ID}",
            },
        },
        "sanity": {
            "enabled": draw(st.booleans()),
            "timeout": draw(valid_timeouts),
            "healthcheck_endpoints": draw(valid_healthcheck_endpoints),
        },
        "integration": {
            "enabled": draw(st.booleans()),
            "components": draw(valid_components),
            "test_federation": draw(st.booleans()),
        },
        "load": {
            "enabled": draw(st.booleans()),
            "duration": draw(valid_durations),
            "targets": draw(valid_targets),
            "series": draw(valid_series),
            "k6": {
                "vus": draw(st.integers(min_value=1, max_value=1000)),
                "scripts": draw(valid_k6_scripts),
            },
        },
        "stress": {
            "enabled": draw(st.booleans()),
            "cardinality": {"max_labels": draw(positive_int)},
            "ingestion": {"max_samples_per_second": draw(positive_int)},
            "queries": {"concurrent": draw(st.integers(min_value=1, max_value=1000))},
            "k6": {
                "stages": [
                    {"duration": "5m", "target": 100},
                    {"duration": "10m", "target": 500},
                ],
            },
        },
        "performance": {
            "enabled": draw(st.booleans()),
            "iterations": draw(st.integers(min_value=1, max_value=1000)),
            "k6": {
                "scripts": ["k6/benchmark.js"],
            },
            "api_endpoints": draw(valid_api_endpoints),
        },
        "scalability": {
            "enabled": draw(st.booleans()),
            "dimensions": draw(valid_dimensions),
            "k6": {
                "concurrent_users": draw(valid_concurrent_users),
            },
            "test_horizontal_scaling": draw(st.booleans()),
        },
        "endurance": {
            "enabled": draw(st.booleans()),
            "duration": draw(valid_durations),
            "k6": {
                "vus": draw(st.integers(min_value=1, max_value=500)),
                "scripts": ["k6/query-load.js"],
            },
            "healthcheck_interval": "5m",
        },
        "reliability": {
            "enabled": draw(st.booleans()),
            "healthcheck_endpoints": draw(valid_healthcheck_endpoints),
            "test_replica_failure": draw(st.booleans()),
        },
        "chaos": {
            "enabled": draw(st.booleans()),
            "tool": draw(valid_chaos_tools),
            "scenarios": {
                "monolithic": ["container_kill", "process_kill"],
                "distributed": ["pod_kill", "replica_failure"],
            },
        },
        "regression": {
            "enabled": draw(st.booleans()),
            "baseline_version": draw(valid_versions),
        },
        "security": {
            "enabled": draw(st.booleans()),
            "scan_vulnerabilities": draw(st.booleans()),
            "test_api_auth": draw(st.booleans()),
        },
    }


@pytest.mark.property
class TestConfigParsing:
    """
    Property-based tests for configuration parsing.

    **Feature: prometheus-installation, Property 9: Test Configuration Parsing**
    **Validates: Requirements 10.1, 10.2**
    """

    @given(config_dict=valid_test_config_dict())
    @settings(max_examples=100)
    def test_from_dict_preserves_all_values(self, config_dict: dict):
        """
        Property: For any valid configuration dictionary, parsing should
        produce a TestConfig with all specified values preserved.

        **Feature: prometheus-installation, Property 9: Test Configuration Parsing**
        **Validates: Requirements 10.1, 10.2**
        """
        config = TestConfig.from_dict(config_dict)

        # Verify test metadata
        assert config.name == config_dict["test"]["name"]
        assert config.platform == config_dict["test"]["platform"]
        assert config.deployment_mode == config_dict["test"]["deployment_mode"]

        # Verify Prometheus config
        assert config.prometheus.version == config_dict["test"]["prometheus"]["version"]
        assert config.prometheus.namespace == config_dict["test"]["prometheus"]["namespace"]
        assert config.prometheus.url == config_dict["test"]["prometheus"]["url"]

        # Verify Runner config
        assert config.runner.python_version == config_dict["test"]["runner"]["python_version"]
        assert config.runner.k6_path == config_dict["test"]["runner"]["k6_path"]
        assert config.runner.kubectl_path == config_dict["test"]["runner"]["kubectl_path"]

        # Verify sanity config
        assert config.sanity.enabled == config_dict["sanity"]["enabled"]
        assert config.sanity.timeout == config_dict["sanity"]["timeout"]
        assert config.sanity.healthcheck_endpoints == config_dict["sanity"]["healthcheck_endpoints"]

        # Verify integration config
        assert config.integration.enabled == config_dict["integration"]["enabled"]
        assert config.integration.components == config_dict["integration"]["components"]
        assert config.integration.test_federation == config_dict["integration"]["test_federation"]

        # Verify load config
        assert config.load.enabled == config_dict["load"]["enabled"]
        assert config.load.duration == config_dict["load"]["duration"]
        assert config.load.targets == config_dict["load"]["targets"]
        assert config.load.series == config_dict["load"]["series"]
        assert config.load.k6.vus == config_dict["load"]["k6"]["vus"]
        assert config.load.k6.scripts == config_dict["load"]["k6"]["scripts"]

        # Verify stress config
        assert config.stress.enabled == config_dict["stress"]["enabled"]
        assert config.stress.cardinality_max_labels == config_dict["stress"]["cardinality"]["max_labels"]
        assert config.stress.ingestion_max_samples_per_second == config_dict["stress"]["ingestion"]["max_samples_per_second"]
        assert config.stress.queries_concurrent == config_dict["stress"]["queries"]["concurrent"]

        # Verify performance config
        assert config.performance.enabled == config_dict["performance"]["enabled"]
        assert config.performance.iterations == config_dict["performance"]["iterations"]
        assert config.performance.api_endpoints == config_dict["performance"]["api_endpoints"]

        # Verify scalability config
        assert config.scalability.enabled == config_dict["scalability"]["enabled"]
        assert config.scalability.dimensions == config_dict["scalability"]["dimensions"]
        assert config.scalability.test_horizontal_scaling == config_dict["scalability"]["test_horizontal_scaling"]

        # Verify endurance config
        assert config.endurance.enabled == config_dict["endurance"]["enabled"]
        assert config.endurance.duration == config_dict["endurance"]["duration"]

        # Verify reliability config
        assert config.reliability.enabled == config_dict["reliability"]["enabled"]
        assert config.reliability.healthcheck_endpoints == config_dict["reliability"]["healthcheck_endpoints"]
        assert config.reliability.test_replica_failure == config_dict["reliability"]["test_replica_failure"]

        # Verify chaos config
        assert config.chaos.enabled == config_dict["chaos"]["enabled"]
        assert config.chaos.tool == config_dict["chaos"]["tool"]

        # Verify regression config
        assert config.regression.enabled == config_dict["regression"]["enabled"]
        assert config.regression.baseline_version == config_dict["regression"]["baseline_version"]

        # Verify security config
        assert config.security.enabled == config_dict["security"]["enabled"]
        assert config.security.scan_vulnerabilities == config_dict["security"]["scan_vulnerabilities"]
        assert config.security.test_api_auth == config_dict["security"]["test_api_auth"]

    @given(config_dict=valid_test_config_dict())
    @settings(max_examples=100)
    def test_yaml_round_trip(self, config_dict: dict):
        """
        Property: For any valid configuration, writing to YAML and reading back
        should produce an equivalent configuration.

        **Feature: prometheus-installation, Property 9: Test Configuration Parsing**
        **Validates: Requirements 10.1, 10.2**
        """
        # Parse the config
        original_config = TestConfig.from_dict(config_dict)

        # Write to YAML file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            yaml.dump(config_dict, f)
            temp_path = Path(f.name)

        try:
            # Read back from YAML
            loaded_config = TestConfig.from_yaml(temp_path)

            # Verify equivalence
            assert loaded_config.name == original_config.name
            assert loaded_config.platform == original_config.platform
            assert loaded_config.deployment_mode == original_config.deployment_mode
            assert loaded_config.prometheus.version == original_config.prometheus.version
            assert loaded_config.prometheus.namespace == original_config.prometheus.namespace
            assert loaded_config.prometheus.url == original_config.prometheus.url
            assert loaded_config.sanity.enabled == original_config.sanity.enabled
            assert loaded_config.integration.enabled == original_config.integration.enabled
            assert loaded_config.load.enabled == original_config.load.enabled
            assert loaded_config.stress.enabled == original_config.stress.enabled
            assert loaded_config.performance.enabled == original_config.performance.enabled
            assert loaded_config.scalability.enabled == original_config.scalability.enabled
            assert loaded_config.endurance.enabled == original_config.endurance.enabled
            assert loaded_config.reliability.enabled == original_config.reliability.enabled
            assert loaded_config.chaos.enabled == original_config.chaos.enabled
            assert loaded_config.regression.enabled == original_config.regression.enabled
            assert loaded_config.security.enabled == original_config.security.enabled
        finally:
            temp_path.unlink()

    @given(config_dict=valid_test_config_dict())
    @settings(max_examples=100)
    def test_to_dict_round_trip(self, config_dict: dict):
        """
        Property: For any valid configuration, converting to dict and back
        should produce an equivalent configuration.

        **Feature: prometheus-installation, Property 9: Test Configuration Parsing**
        **Validates: Requirements 10.1, 10.2**
        """
        # Parse the config
        original_config = TestConfig.from_dict(config_dict)

        # Convert to dict and back
        exported_dict = original_config.to_dict()
        reimported_config = TestConfig.from_dict(exported_dict)

        # Verify equivalence
        assert reimported_config.name == original_config.name
        assert reimported_config.platform == original_config.platform
        assert reimported_config.deployment_mode == original_config.deployment_mode
        assert reimported_config.prometheus.version == original_config.prometheus.version
        assert reimported_config.prometheus.namespace == original_config.prometheus.namespace
        assert reimported_config.prometheus.url == original_config.prometheus.url
        assert reimported_config.sanity.enabled == original_config.sanity.enabled
        assert reimported_config.sanity.timeout == original_config.sanity.timeout
        assert reimported_config.integration.enabled == original_config.integration.enabled
        assert reimported_config.integration.components == original_config.integration.components
        assert reimported_config.load.enabled == original_config.load.enabled
        assert reimported_config.load.duration == original_config.load.duration
        assert reimported_config.load.targets == original_config.load.targets
        assert reimported_config.load.series == original_config.load.series
        assert reimported_config.stress.enabled == original_config.stress.enabled
        assert reimported_config.stress.cardinality_max_labels == original_config.stress.cardinality_max_labels
        assert reimported_config.stress.ingestion_max_samples_per_second == original_config.stress.ingestion_max_samples_per_second
        assert reimported_config.stress.queries_concurrent == original_config.stress.queries_concurrent
        assert reimported_config.performance.enabled == original_config.performance.enabled
        assert reimported_config.performance.iterations == original_config.performance.iterations
        assert reimported_config.scalability.enabled == original_config.scalability.enabled
        assert reimported_config.scalability.dimensions == original_config.scalability.dimensions
        assert reimported_config.endurance.enabled == original_config.endurance.enabled
        assert reimported_config.endurance.duration == original_config.endurance.duration
        assert reimported_config.reliability.enabled == original_config.reliability.enabled
        assert reimported_config.chaos.enabled == original_config.chaos.enabled
        assert reimported_config.chaos.tool == original_config.chaos.tool
        assert reimported_config.regression.enabled == original_config.regression.enabled
        assert reimported_config.regression.baseline_version == original_config.regression.baseline_version
        assert reimported_config.security.enabled == original_config.security.enabled
        assert reimported_config.security.scan_vulnerabilities == original_config.security.scan_vulnerabilities

    @given(
        config_dict=valid_test_config_dict(),
        new_url=valid_urls,
        new_version=valid_versions,
        new_k6_vus=st.integers(min_value=1, max_value=1000),
    )
    @settings(max_examples=100)
    def test_cli_args_override(
        self,
        config_dict: dict,
        new_url: str,
        new_version: str,
        new_k6_vus: int,
    ):
        """
        Property: CLI arguments should override file configuration values.

        **Feature: prometheus-installation, Property 9: Test Configuration Parsing**
        **Validates: Requirements 10.2**
        """
        original_config = TestConfig.from_dict(config_dict)

        # Merge CLI args (keeping same platform and deployment_mode to avoid validation errors)
        merged_config = original_config.merge_cli_args(
            prometheus_url=new_url,
            prometheus_version=new_version,
            k6_vus=new_k6_vus,
        )

        # CLI args should override
        assert merged_config.prometheus.url == new_url
        assert merged_config.prometheus.version == new_version
        assert merged_config.load.k6.vus == new_k6_vus

        # Other values should be preserved
        assert merged_config.name == original_config.name
        assert merged_config.platform == original_config.platform
        assert merged_config.deployment_mode == original_config.deployment_mode
        assert merged_config.sanity.enabled == original_config.sanity.enabled
        assert merged_config.integration.enabled == original_config.integration.enabled

    @given(config_dict=valid_test_config_dict())
    @settings(max_examples=100)
    def test_enabled_test_types_consistency(self, config_dict: dict):
        """
        Property: get_enabled_test_types should return exactly the test types
        that have enabled=True.

        **Feature: prometheus-installation, Property 9: Test Configuration Parsing**
        **Validates: Requirements 10.1**
        """
        config = TestConfig.from_dict(config_dict)
        enabled_types = config.get_enabled_test_types()

        # Check each test type
        expected_enabled = []
        if config.sanity.enabled:
            expected_enabled.append("sanity")
        if config.integration.enabled:
            expected_enabled.append("integration")
        if config.load.enabled:
            expected_enabled.append("load")
        if config.stress.enabled:
            expected_enabled.append("stress")
        if config.performance.enabled:
            expected_enabled.append("performance")
        if config.scalability.enabled:
            expected_enabled.append("scalability")
        if config.endurance.enabled:
            expected_enabled.append("endurance")
        if config.reliability.enabled:
            expected_enabled.append("reliability")
        if config.chaos.enabled:
            expected_enabled.append("chaos")
        if config.regression.enabled:
            expected_enabled.append("regression")
        if config.security.enabled:
            expected_enabled.append("security")

        assert enabled_types == expected_enabled

    @given(config_dict=valid_test_config_dict())
    @settings(max_examples=100)
    def test_deployment_mode_helpers(self, config_dict: dict):
        """
        Property: is_distributed() and is_monolithic() should be mutually exclusive
        and consistent with deployment_mode.

        **Feature: prometheus-installation, Property 9: Test Configuration Parsing**
        **Validates: Requirements 10.9**
        """
        config = TestConfig.from_dict(config_dict)

        # Exactly one should be true
        assert config.is_distributed() != config.is_monolithic()

        # Should match deployment_mode
        if config.deployment_mode == "distributed":
            assert config.is_distributed()
            assert not config.is_monolithic()
        else:
            assert config.is_monolithic()
            assert not config.is_distributed()

    @given(config_dict=valid_test_config_dict())
    @settings(max_examples=100)
    def test_chaos_scenarios_match_deployment_mode(self, config_dict: dict):
        """
        Property: get_chaos_scenarios() should return scenarios appropriate
        for the current deployment mode.

        **Feature: prometheus-installation, Property 9: Test Configuration Parsing**
        **Validates: Requirements 10.9**
        """
        config = TestConfig.from_dict(config_dict)
        scenarios = config.get_chaos_scenarios()

        if config.is_distributed():
            assert scenarios == config.chaos.scenarios_distributed
        else:
            assert scenarios == config.chaos.scenarios_monolithic


@pytest.mark.property
class TestDeploymentModeValidation:
    """
    Property-based tests for deployment mode validation.

    **Feature: prometheus-installation, Property 9: Test Configuration Parsing**
    **Validates: Requirements 10.9**
    """

    def test_docker_only_supports_monolithic(self):
        """
        Test that docker platform only supports monolithic deployment mode.

        **Validates: Requirements 10.9**
        """
        config_dict = {
            "test": {
                "name": "test",
                "platform": "docker",
                "deployment_mode": "distributed",
            }
        }

        with pytest.raises(ValueError, match="only supports monolithic"):
            TestConfig.from_dict(config_dict)

    def test_binary_only_supports_monolithic(self):
        """
        Test that binary platform only supports monolithic deployment mode.

        **Validates: Requirements 10.9**
        """
        config_dict = {
            "test": {
                "name": "test",
                "platform": "binary",
                "deployment_mode": "distributed",
            }
        }

        with pytest.raises(ValueError, match="only supports monolithic"):
            TestConfig.from_dict(config_dict)

    @given(platform=st.sampled_from(["minikube", "eks", "gke", "aks"]))
    @settings(max_examples=20)
    def test_kubernetes_platforms_support_both_modes(self, platform: str):
        """
        Property: Kubernetes platforms should support both monolithic and distributed modes.

        **Validates: Requirements 10.9**
        """
        for mode in ["monolithic", "distributed"]:
            config_dict = {
                "test": {
                    "name": "test",
                    "platform": platform,
                    "deployment_mode": mode,
                }
            }
            config = TestConfig.from_dict(config_dict)
            assert config.deployment_mode == mode
            assert config.platform == platform
