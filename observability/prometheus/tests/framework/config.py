"""
Configuration management for the Prometheus Testing Framework.

This module handles loading, parsing, and validating test configurations
from YAML files and command-line arguments.

Requirements: 10.1, 10.2, 10.9
"""

import os
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Optional

import yaml
from jsonschema import Draft7Validator


class DeploymentMode(Enum):
    """Deployment mode for Prometheus."""

    MONOLITHIC = "monolithic"
    DISTRIBUTED = "distributed"


# Valid platforms - using string constants to avoid circular imports with deployer.py
VALID_PLATFORMS = ["minikube", "eks", "gke", "aks", "docker", "binary"]
MONOLITHIC_ONLY_PLATFORMS = ["docker", "binary"]


# JSON Schema for configuration validation
CONFIG_SCHEMA = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "type": "object",
    "properties": {
        "test": {
            "type": "object",
            "properties": {
                "name": {"type": "string", "minLength": 1},
                "platform": {
                    "type": "string",
                    "enum": ["minikube", "eks", "gke", "aks", "docker", "binary"]
                },
                "deployment_mode": {
                    "type": "string",
                    "enum": ["monolithic", "distributed"]
                },
                "prometheus": {
                    "type": "object",
                    "properties": {
                        "version": {"type": "string", "pattern": "^v?[0-9]+\\.[0-9]+\\.[0-9]+"},
                        "namespace": {"type": "string", "minLength": 1},
                        "url": {"type": "string"}
                    }
                },
                "runner": {
                    "type": "object",
                    "properties": {
                        "python_version": {"type": "string"},
                        "k6_path": {"type": "string"},
                        "kubectl_path": {"type": "string"}
                    }
                },
                "credentials": {
                    "type": "object",
                    "properties": {
                        "kubeconfig": {"type": "string"},
                        "aws_profile": {"type": "string"},
                        "gcp_credentials": {"type": "string"},
                        "azure_subscription": {"type": "string"}
                    }
                }
            }
        },
        "sanity": {
            "type": "object",
            "properties": {
                "enabled": {"type": "boolean"},
                "timeout": {"type": "string", "pattern": "^[0-9]+[smh]$"},
                "healthcheck_endpoints": {
                    "type": "array",
                    "items": {"type": "string"}
                }
            }
        },
        "integration": {
            "type": "object",
            "properties": {
                "enabled": {"type": "boolean"},
                "components": {
                    "type": "array",
                    "items": {"type": "string"}
                },
                "test_federation": {"type": "boolean"}
            }
        },
        "load": {
            "type": "object",
            "properties": {
                "enabled": {"type": "boolean"},
                "duration": {"type": "string", "pattern": "^[0-9]+[smh]$"},
                "targets": {
                    "type": "array",
                    "items": {"type": "integer", "minimum": 1}
                },
                "series": {
                    "type": "array",
                    "items": {"type": "integer", "minimum": 1}
                },
                "k6": {
                    "type": "object",
                    "properties": {
                        "vus": {"type": "integer", "minimum": 1},
                        "scripts": {
                            "type": "array",
                            "items": {"type": "string"}
                        }
                    }
                }
            }
        },
        "stress": {
            "type": "object",
            "properties": {
                "enabled": {"type": "boolean"},
                "cardinality": {
                    "type": "object",
                    "properties": {
                        "max_labels": {"type": "integer", "minimum": 1}
                    }
                },
                "ingestion": {
                    "type": "object",
                    "properties": {
                        "max_samples_per_second": {"type": "integer", "minimum": 1}
                    }
                },
                "queries": {
                    "type": "object",
                    "properties": {
                        "concurrent": {"type": "integer", "minimum": 1}
                    }
                },
                "k6": {
                    "type": "object",
                    "properties": {
                        "stages": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "duration": {"type": "string"},
                                    "target": {"type": "integer"}
                                }
                            }
                        }
                    }
                }
            }
        },
        "performance": {
            "type": "object",
            "properties": {
                "enabled": {"type": "boolean"},
                "iterations": {"type": "integer", "minimum": 1},
                "k6": {
                    "type": "object",
                    "properties": {
                        "scripts": {
                            "type": "array",
                            "items": {"type": "string"}
                        }
                    }
                },
                "api_endpoints": {
                    "type": "array",
                    "items": {"type": "string"}
                }
            }
        },
        "scalability": {
            "type": "object",
            "properties": {
                "enabled": {"type": "boolean"},
                "dimensions": {
                    "type": "array",
                    "items": {"type": "string"}
                },
                "k6": {
                    "type": "object",
                    "properties": {
                        "concurrent_users": {
                            "type": "array",
                            "items": {"type": "integer"}
                        }
                    }
                },
                "test_horizontal_scaling": {"type": "boolean"}
            }
        },
        "endurance": {
            "type": "object",
            "properties": {
                "enabled": {"type": "boolean"},
                "duration": {"type": "string", "pattern": "^[0-9]+[smhd]$"},
                "k6": {
                    "type": "object",
                    "properties": {
                        "vus": {"type": "integer", "minimum": 1},
                        "scripts": {
                            "type": "array",
                            "items": {"type": "string"}
                        }
                    }
                },
                "healthcheck_interval": {"type": "string"}
            }
        },
        "reliability": {
            "type": "object",
            "properties": {
                "enabled": {"type": "boolean"},
                "healthcheck_endpoints": {
                    "type": "array",
                    "items": {"type": "string"}
                },
                "test_replica_failure": {"type": "boolean"}
            }
        },
        "chaos": {
            "type": "object",
            "properties": {
                "enabled": {"type": "boolean"},
                "tool": {"type": "string", "enum": ["chaos-mesh", "litmus"]},
                "scenarios": {
                    "type": "object",
                    "properties": {
                        "monolithic": {
                            "type": "array",
                            "items": {"type": "string"}
                        },
                        "distributed": {
                            "type": "array",
                            "items": {"type": "string"}
                        }
                    }
                }
            }
        },
        "regression": {
            "type": "object",
            "properties": {
                "enabled": {"type": "boolean"},
                "baseline_version": {"type": "string"}
            }
        },
        "security": {
            "type": "object",
            "properties": {
                "enabled": {"type": "boolean"},
                "scan_vulnerabilities": {"type": "boolean"},
                "test_api_auth": {"type": "boolean"}
            }
        }
    }
}


class ConfigValidationError(Exception):
    """Raised when configuration validation fails."""

    def __init__(self, message: str, errors: list[str] | None = None):
        super().__init__(message)
        self.errors = errors or []


def validate_config(data: dict[str, Any]) -> list[str]:
    """
    Validate configuration data against the schema.

    Args:
        data: Configuration dictionary to validate

    Returns:
        List of validation error messages (empty if valid)
    """
    validator = Draft7Validator(CONFIG_SCHEMA)
    errors = []
    for error in validator.iter_errors(data):
        path = ".".join(str(p) for p in error.path) if error.path else "root"
        errors.append(f"{path}: {error.message}")
    return errors


def expand_env_vars(value: str) -> str:
    """
    Expand environment variables in a string.

    Supports ${VAR_NAME} syntax.

    Args:
        value: String potentially containing environment variable references

    Returns:
        String with environment variables expanded
    """
    if not isinstance(value, str):
        return value

    # Handle ${VAR_NAME} syntax
    import re
    pattern = r'\$\{([^}]+)\}'

    def replace_env(match):
        var_name = match.group(1)
        return os.environ.get(var_name, "")

    return re.sub(pattern, replace_env, value)


@dataclass
class RunnerConfig:
    """Configuration for the Test Runner Host."""

    python_version: str = "3.10+"
    k6_path: str = "/usr/local/bin/k6"
    kubectl_path: str = "/usr/local/bin/kubectl"


@dataclass
class CredentialsConfig:
    """Configuration for remote cluster credentials."""

    kubeconfig: str = ""
    aws_profile: str = ""
    gcp_credentials: str = ""
    azure_subscription: str = ""

    def resolve(self) -> "CredentialsConfig":
        """Resolve environment variables in credential paths."""
        return CredentialsConfig(
            kubeconfig=expand_env_vars(self.kubeconfig) or os.environ.get("KUBECONFIG", ""),
            aws_profile=expand_env_vars(self.aws_profile) or os.environ.get("AWS_PROFILE", ""),
            gcp_credentials=expand_env_vars(self.gcp_credentials) or os.environ.get("GOOGLE_APPLICATION_CREDENTIALS", ""),
            azure_subscription=expand_env_vars(self.azure_subscription) or os.environ.get("AZURE_SUBSCRIPTION_ID", ""),
        )


@dataclass
class PrometheusConfig:
    """Configuration for the Prometheus instance under test."""

    version: str = "v3.5.0"
    namespace: str = "monitoring"
    url: str = "http://localhost:9090"


@dataclass
class K6Config:
    """Configuration for k6 load testing."""

    vus: int = 100
    scripts: list[str] = field(default_factory=list)
    stages: list[dict[str, Any]] = field(default_factory=list)
    concurrent_users: list[int] = field(default_factory=lambda: [10, 50, 100, 200, 500])


@dataclass
class SanityTestConfig:
    """Configuration for sanity tests."""

    enabled: bool = True
    timeout: str = "60s"
    healthcheck_endpoints: list[str] = field(default_factory=lambda: [
        "/-/healthy", "/-/ready", "/api/v1/status/runtimeinfo"
    ])


@dataclass
class IntegrationTestConfig:
    """Configuration for integration tests."""

    enabled: bool = True
    components: list[str] = field(default_factory=lambda: [
        "node-exporter", "alertmanager", "grafana"
    ])
    test_federation: bool = True


@dataclass
class LoadTestConfig:
    """Configuration for load tests."""

    enabled: bool = True
    duration: str = "30m"
    targets: list[int] = field(default_factory=lambda: [100, 1000, 10000])
    series: list[int] = field(default_factory=lambda: [10000, 100000, 1000000])
    k6: K6Config = field(default_factory=lambda: K6Config(
        vus=100,
        scripts=["k6/query-load.js", "k6/query-range-load.js", "k6/remote-write-load.js"]
    ))


@dataclass
class StressTestConfig:
    """Configuration for stress tests."""

    enabled: bool = True
    cardinality_max_labels: int = 1000000
    ingestion_max_samples_per_second: int = 1000000
    queries_concurrent: int = 100
    k6: K6Config = field(default_factory=lambda: K6Config(
        stages=[
            {"duration": "5m", "target": 100},
            {"duration": "10m", "target": 500},
            {"duration": "5m", "target": 1000}
        ]
    ))


@dataclass
class PerformanceTestConfig:
    """Configuration for performance tests."""

    enabled: bool = True
    iterations: int = 100
    k6: K6Config = field(default_factory=lambda: K6Config(
        scripts=["k6/benchmark.js"]
    ))
    api_endpoints: list[str] = field(default_factory=lambda: [
        "/api/v1/query", "/api/v1/query_range", "/api/v1/labels",
        "/api/v1/label/__name__/values", "/api/v1/series"
    ])


@dataclass
class ScalabilityTestConfig:
    """Configuration for scalability tests."""

    enabled: bool = True
    dimensions: list[str] = field(default_factory=lambda: [
        "targets", "series", "cardinality", "retention", "queries"
    ])
    k6: K6Config = field(default_factory=lambda: K6Config(
        concurrent_users=[10, 50, 100, 200, 500]
    ))
    test_horizontal_scaling: bool = True


@dataclass
class EnduranceTestConfig:
    """Configuration for endurance (soak) tests."""

    enabled: bool = False
    duration: str = "24h"
    k6: K6Config = field(default_factory=lambda: K6Config(
        vus=50,
        scripts=["k6/query-load.js"]
    ))
    healthcheck_interval: str = "5m"


@dataclass
class ReliabilityTestConfig:
    """Configuration for reliability tests."""

    enabled: bool = True
    healthcheck_endpoints: list[str] = field(default_factory=lambda: [
        "/-/healthy", "/-/ready"
    ])
    test_replica_failure: bool = True


@dataclass
class ChaosTestConfig:
    """Configuration for chaos tests."""

    enabled: bool = False
    tool: str = "chaos-mesh"  # chaos-mesh, litmus
    scenarios_monolithic: list[str] = field(default_factory=lambda: [
        "container_kill", "process_kill"
    ])
    scenarios_distributed: list[str] = field(default_factory=lambda: [
        "pod_kill", "replica_failure"
    ])


@dataclass
class RegressionTestConfig:
    """Configuration for regression tests."""

    enabled: bool = False
    baseline_version: str = "v3.4.0"


@dataclass
class SecurityTestConfig:
    """Configuration for security tests."""

    enabled: bool = True
    scan_vulnerabilities: bool = True
    test_api_auth: bool = True




@dataclass
class TestConfig:
    """
    Main configuration class for the Prometheus Testing Framework.

    Requirements: 10.1, 10.2, 10.9

    This class holds all configuration for test execution including:
    - Test suite metadata
    - Platform configuration
    - Deployment mode (monolithic/distributed)
    - Prometheus instance configuration
    - Test Runner Host configuration
    - Remote cluster credentials
    - Individual test type configurations

    Attributes:
        name: Name of the test suite
        platform: Target platform (minikube, eks, gke, aks, docker, binary)
        deployment_mode: Deployment mode (monolithic, distributed)
        prometheus: Prometheus instance configuration
        runner: Test Runner Host configuration
        credentials: Remote cluster credentials
        sanity: Sanity test configuration
        integration: Integration test configuration
        load: Load test configuration
        stress: Stress test configuration
        performance: Performance test configuration
        scalability: Scalability test configuration
        endurance: Endurance test configuration
        reliability: Reliability test configuration
        chaos: Chaos test configuration
        regression: Regression test configuration
        security: Security test configuration
    """

    __test__ = False  # Tell pytest this is not a test class

    name: str = "prometheus-test-suite"
    platform: str = "minikube"
    deployment_mode: str = "monolithic"
    prometheus: PrometheusConfig = field(default_factory=PrometheusConfig)
    runner: RunnerConfig = field(default_factory=RunnerConfig)
    credentials: CredentialsConfig = field(default_factory=CredentialsConfig)
    sanity: SanityTestConfig = field(default_factory=SanityTestConfig)
    integration: IntegrationTestConfig = field(default_factory=IntegrationTestConfig)
    load: LoadTestConfig = field(default_factory=LoadTestConfig)
    stress: StressTestConfig = field(default_factory=StressTestConfig)
    performance: PerformanceTestConfig = field(default_factory=PerformanceTestConfig)
    scalability: ScalabilityTestConfig = field(default_factory=ScalabilityTestConfig)
    endurance: EnduranceTestConfig = field(default_factory=EnduranceTestConfig)
    reliability: ReliabilityTestConfig = field(default_factory=ReliabilityTestConfig)
    chaos: ChaosTestConfig = field(default_factory=ChaosTestConfig)
    regression: RegressionTestConfig = field(default_factory=RegressionTestConfig)
    security: SecurityTestConfig = field(default_factory=SecurityTestConfig)

    def __post_init__(self):
        """Validate deployment mode after initialization."""
        valid_modes = ["monolithic", "distributed"]
        if self.deployment_mode not in valid_modes:
            raise ValueError(f"Invalid deployment_mode: {self.deployment_mode}. Must be one of {valid_modes}")

        if self.platform not in VALID_PLATFORMS:
            raise ValueError(f"Invalid platform: {self.platform}. Must be one of {VALID_PLATFORMS}")

        # Validate deployment mode compatibility with platform
        if self.platform in MONOLITHIC_ONLY_PLATFORMS and self.deployment_mode == "distributed":
            raise ValueError(
                f"Platform '{self.platform}' only supports monolithic deployment mode"
            )

    @classmethod
    def from_yaml(cls, path: Path | str, validate: bool = True) -> "TestConfig":
        """
        Load configuration from a YAML file.

        Args:
            path: Path to the YAML configuration file
            validate: Whether to validate the configuration against schema

        Returns:
            TestConfig instance with loaded values

        Raises:
            FileNotFoundError: If the config file doesn't exist
            yaml.YAMLError: If the YAML is invalid
            ConfigValidationError: If validation fails
        """
        path = Path(path)
        if not path.exists():
            raise FileNotFoundError(f"Configuration file not found: {path}")

        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)

        if validate:
            errors = validate_config(data)
            if errors:
                raise ConfigValidationError(
                    f"Configuration validation failed with {len(errors)} error(s)",
                    errors=errors
                )

        return cls.from_dict(data)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "TestConfig":
        """
        Create configuration from a dictionary.

        Args:
            data: Dictionary containing configuration values

        Returns:
            TestConfig instance with loaded values
        """
        test_data = data.get("test", {})

        # Parse Prometheus config
        prom_data = test_data.get("prometheus", {})
        prometheus = PrometheusConfig(
            version=prom_data.get("version", "v3.5.0"),
            namespace=prom_data.get("namespace", "monitoring"),
            url=prom_data.get("url", "http://localhost:9090"),
        )

        # Parse Runner config
        runner_data = test_data.get("runner", {})
        runner = RunnerConfig(
            python_version=runner_data.get("python_version", "3.10+"),
            k6_path=runner_data.get("k6_path", "/usr/local/bin/k6"),
            kubectl_path=runner_data.get("kubectl_path", "/usr/local/bin/kubectl"),
        )

        # Parse Credentials config
        creds_data = test_data.get("credentials", {})
        credentials = CredentialsConfig(
            kubeconfig=creds_data.get("kubeconfig", ""),
            aws_profile=creds_data.get("aws_profile", ""),
            gcp_credentials=creds_data.get("gcp_credentials", ""),
            azure_subscription=creds_data.get("azure_subscription", ""),
        )

        # Parse test type configs
        sanity_data = data.get("sanity", {})
        sanity = SanityTestConfig(
            enabled=sanity_data.get("enabled", True),
            timeout=sanity_data.get("timeout", "60s"),
            healthcheck_endpoints=sanity_data.get("healthcheck_endpoints", [
                "/-/healthy", "/-/ready", "/api/v1/status/runtimeinfo"
            ]),
        )

        integration_data = data.get("integration", {})
        integration = IntegrationTestConfig(
            enabled=integration_data.get("enabled", True),
            components=integration_data.get("components", [
                "node-exporter", "alertmanager", "grafana"
            ]),
            test_federation=integration_data.get("test_federation", True),
        )

        load_data = data.get("load", {})
        load_k6_data = load_data.get("k6", {})
        load = LoadTestConfig(
            enabled=load_data.get("enabled", True),
            duration=load_data.get("duration", "30m"),
            targets=load_data.get("targets", [100, 1000, 10000]),
            series=load_data.get("series", [10000, 100000, 1000000]),
            k6=K6Config(
                vus=load_k6_data.get("vus", 100),
                scripts=load_k6_data.get("scripts", [
                    "k6/query-load.js", "k6/query-range-load.js", "k6/remote-write-load.js"
                ]),
            ),
        )

        stress_data = data.get("stress", {})
        stress_k6_data = stress_data.get("k6", {})
        stress = StressTestConfig(
            enabled=stress_data.get("enabled", True),
            cardinality_max_labels=stress_data.get("cardinality", {}).get(
                "max_labels", 1000000
            ),
            ingestion_max_samples_per_second=stress_data.get("ingestion", {}).get(
                "max_samples_per_second", 1000000
            ),
            queries_concurrent=stress_data.get("queries", {}).get("concurrent", 100),
            k6=K6Config(
                stages=stress_k6_data.get("stages", [
                    {"duration": "5m", "target": 100},
                    {"duration": "10m", "target": 500},
                    {"duration": "5m", "target": 1000}
                ]),
            ),
        )

        performance_data = data.get("performance", {})
        perf_k6_data = performance_data.get("k6", {})
        performance = PerformanceTestConfig(
            enabled=performance_data.get("enabled", True),
            iterations=performance_data.get("iterations", 100),
            k6=K6Config(
                scripts=perf_k6_data.get("scripts", ["k6/benchmark.js"]),
            ),
            api_endpoints=performance_data.get("api_endpoints", [
                "/api/v1/query", "/api/v1/query_range", "/api/v1/labels",
                "/api/v1/label/__name__/values", "/api/v1/series"
            ]),
        )

        scalability_data = data.get("scalability", {})
        scale_k6_data = scalability_data.get("k6", {})
        scalability = ScalabilityTestConfig(
            enabled=scalability_data.get("enabled", True),
            dimensions=scalability_data.get("dimensions", [
                "targets", "series", "cardinality", "retention", "queries"
            ]),
            k6=K6Config(
                concurrent_users=scale_k6_data.get("concurrent_users", [10, 50, 100, 200, 500]),
            ),
            test_horizontal_scaling=scalability_data.get("test_horizontal_scaling", True),
        )

        endurance_data = data.get("endurance", {})
        endurance_k6_data = endurance_data.get("k6", {})
        endurance = EnduranceTestConfig(
            enabled=endurance_data.get("enabled", False),
            duration=endurance_data.get("duration", "24h"),
            k6=K6Config(
                vus=endurance_k6_data.get("vus", 50),
                scripts=endurance_k6_data.get("scripts", ["k6/query-load.js"]),
            ),
            healthcheck_interval=endurance_data.get("healthcheck_interval", "5m"),
        )

        reliability_data = data.get("reliability", {})
        reliability = ReliabilityTestConfig(
            enabled=reliability_data.get("enabled", True),
            healthcheck_endpoints=reliability_data.get("healthcheck_endpoints", [
                "/-/healthy", "/-/ready"
            ]),
            test_replica_failure=reliability_data.get("test_replica_failure", True),
        )

        chaos_data = data.get("chaos", {})
        chaos_scenarios = chaos_data.get("scenarios", {})
        chaos = ChaosTestConfig(
            enabled=chaos_data.get("enabled", False),
            tool=chaos_data.get("tool", "chaos-mesh"),
            scenarios_monolithic=chaos_scenarios.get("monolithic", [
                "container_kill", "process_kill"
            ]),
            scenarios_distributed=chaos_scenarios.get("distributed", [
                "pod_kill", "replica_failure"
            ]),
        )

        regression_data = data.get("regression", {})
        regression = RegressionTestConfig(
            enabled=regression_data.get("enabled", False),
            baseline_version=regression_data.get("baseline_version", "v3.4.0"),
        )

        security_data = data.get("security", {})
        security = SecurityTestConfig(
            enabled=security_data.get("enabled", True),
            scan_vulnerabilities=security_data.get("scan_vulnerabilities", True),
            test_api_auth=security_data.get("test_api_auth", True),
        )

        return cls(
            name=test_data.get("name", "prometheus-test-suite"),
            platform=test_data.get("platform", "minikube"),
            deployment_mode=test_data.get("deployment_mode", "monolithic"),
            prometheus=prometheus,
            runner=runner,
            credentials=credentials,
            sanity=sanity,
            integration=integration,
            load=load,
            stress=stress,
            performance=performance,
            scalability=scalability,
            endurance=endurance,
            reliability=reliability,
            chaos=chaos,
            regression=regression,
            security=security,
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert configuration to dictionary representation."""
        return {
            "test": {
                "name": self.name,
                "platform": self.platform,
                "deployment_mode": self.deployment_mode,
                "prometheus": {
                    "version": self.prometheus.version,
                    "namespace": self.prometheus.namespace,
                    "url": self.prometheus.url,
                },
                "runner": {
                    "python_version": self.runner.python_version,
                    "k6_path": self.runner.k6_path,
                    "kubectl_path": self.runner.kubectl_path,
                },
                "credentials": {
                    "kubeconfig": self.credentials.kubeconfig,
                    "aws_profile": self.credentials.aws_profile,
                    "gcp_credentials": self.credentials.gcp_credentials,
                    "azure_subscription": self.credentials.azure_subscription,
                },
            },
            "sanity": {
                "enabled": self.sanity.enabled,
                "timeout": self.sanity.timeout,
                "healthcheck_endpoints": self.sanity.healthcheck_endpoints,
            },
            "integration": {
                "enabled": self.integration.enabled,
                "components": self.integration.components,
                "test_federation": self.integration.test_federation,
            },
            "load": {
                "enabled": self.load.enabled,
                "duration": self.load.duration,
                "targets": self.load.targets,
                "series": self.load.series,
                "k6": {
                    "vus": self.load.k6.vus,
                    "scripts": self.load.k6.scripts,
                },
            },
            "stress": {
                "enabled": self.stress.enabled,
                "cardinality": {"max_labels": self.stress.cardinality_max_labels},
                "ingestion": {
                    "max_samples_per_second": self.stress.ingestion_max_samples_per_second
                },
                "queries": {"concurrent": self.stress.queries_concurrent},
                "k6": {
                    "stages": self.stress.k6.stages,
                },
            },
            "performance": {
                "enabled": self.performance.enabled,
                "iterations": self.performance.iterations,
                "k6": {
                    "scripts": self.performance.k6.scripts,
                },
                "api_endpoints": self.performance.api_endpoints,
            },
            "scalability": {
                "enabled": self.scalability.enabled,
                "dimensions": self.scalability.dimensions,
                "k6": {
                    "concurrent_users": self.scalability.k6.concurrent_users,
                },
                "test_horizontal_scaling": self.scalability.test_horizontal_scaling,
            },
            "endurance": {
                "enabled": self.endurance.enabled,
                "duration": self.endurance.duration,
                "k6": {
                    "vus": self.endurance.k6.vus,
                    "scripts": self.endurance.k6.scripts,
                },
                "healthcheck_interval": self.endurance.healthcheck_interval,
            },
            "reliability": {
                "enabled": self.reliability.enabled,
                "healthcheck_endpoints": self.reliability.healthcheck_endpoints,
                "test_replica_failure": self.reliability.test_replica_failure,
            },
            "chaos": {
                "enabled": self.chaos.enabled,
                "tool": self.chaos.tool,
                "scenarios": {
                    "monolithic": self.chaos.scenarios_monolithic,
                    "distributed": self.chaos.scenarios_distributed,
                },
            },
            "regression": {
                "enabled": self.regression.enabled,
                "baseline_version": self.regression.baseline_version,
            },
            "security": {
                "enabled": self.security.enabled,
                "scan_vulnerabilities": self.security.scan_vulnerabilities,
                "test_api_auth": self.security.test_api_auth,
            },
        }

    def merge_cli_args(
        self,
        platform: Optional[str] = None,
        deployment_mode: Optional[str] = None,
        prometheus_url: Optional[str] = None,
        prometheus_version: Optional[str] = None,
        k6_vus: Optional[int] = None,
        k6_duration: Optional[str] = None,
    ) -> "TestConfig":
        """
        Merge command-line arguments into the configuration.

        CLI arguments take precedence over file configuration.

        Args:
            platform: Target platform override
            deployment_mode: Deployment mode override (monolithic/distributed)
            prometheus_url: Prometheus URL override
            prometheus_version: Prometheus version override
            k6_vus: k6 virtual users override
            k6_duration: k6 test duration override

        Returns:
            New TestConfig with merged values
        """
        # Create a copy with updated values
        new_config = TestConfig.from_dict(self.to_dict())

        if platform:
            new_config.platform = platform
        if deployment_mode:
            new_config.deployment_mode = deployment_mode
        if prometheus_url:
            new_config.prometheus.url = prometheus_url
        if prometheus_version:
            new_config.prometheus.version = prometheus_version
        if k6_vus:
            new_config.load.k6.vus = k6_vus
            new_config.endurance.k6.vus = k6_vus
        if k6_duration:
            new_config.load.duration = k6_duration

        # Re-validate after merging
        new_config.__post_init__()

        return new_config

    def get_enabled_test_types(self) -> list[str]:
        """Get list of enabled test types."""
        enabled = []
        if self.sanity.enabled:
            enabled.append("sanity")
        if self.integration.enabled:
            enabled.append("integration")
        if self.load.enabled:
            enabled.append("load")
        if self.stress.enabled:
            enabled.append("stress")
        if self.performance.enabled:
            enabled.append("performance")
        if self.scalability.enabled:
            enabled.append("scalability")
        if self.endurance.enabled:
            enabled.append("endurance")
        if self.reliability.enabled:
            enabled.append("reliability")
        if self.chaos.enabled:
            enabled.append("chaos")
        if self.regression.enabled:
            enabled.append("regression")
        if self.security.enabled:
            enabled.append("security")
        return enabled

    def is_distributed(self) -> bool:
        """Check if deployment mode is distributed."""
        return self.deployment_mode == "distributed"

    def is_monolithic(self) -> bool:
        """Check if deployment mode is monolithic."""
        return self.deployment_mode == "monolithic"

    def get_resolved_credentials(self) -> CredentialsConfig:
        """Get credentials with environment variables resolved."""
        return self.credentials.resolve()

    def get_chaos_scenarios(self) -> list[str]:
        """Get chaos scenarios appropriate for the current deployment mode."""
        if self.is_distributed():
            return self.chaos.scenarios_distributed
        return self.chaos.scenarios_monolithic


def load_config(
    config_path: Optional[Path | str] = None,
    platform: Optional[str] = None,
    deployment_mode: Optional[str] = None,
    prometheus_url: Optional[str] = None,
    prometheus_version: Optional[str] = None,
    k6_vus: Optional[int] = None,
    k6_duration: Optional[str] = None,
    validate: bool = True,
) -> TestConfig:
    """
    Load and merge configuration from file and CLI arguments.

    This is the main entry point for loading configuration.

    Args:
        config_path: Path to YAML configuration file (optional)
        platform: Target platform override
        deployment_mode: Deployment mode override
        prometheus_url: Prometheus URL override
        prometheus_version: Prometheus version override
        k6_vus: k6 virtual users override
        k6_duration: k6 test duration override
        validate: Whether to validate configuration

    Returns:
        TestConfig with merged values
    """
    if config_path:
        config = TestConfig.from_yaml(config_path, validate=validate)
    else:
        config = TestConfig()

    # Merge CLI arguments
    return config.merge_cli_args(
        platform=platform,
        deployment_mode=deployment_mode,
        prometheus_url=prometheus_url,
        prometheus_version=prometheus_version,
        k6_vus=k6_vus,
        k6_duration=k6_duration,
    )
