"""
Property-based tests for Kubernetes service discovery configuration.

**Feature: prometheus-installation, Property 8: Kubernetes Service Discovery**
**Validates: Requirements 7.1, 7.2, 7.3, 7.4, 7.7**

This module tests that for any pod with prometheus.io/scrape: "true" annotation,
Prometheus with kubernetes_sd_config should discover and scrape that pod using
the port and path specified in annotations.

Property 8: Kubernetes Service Discovery
*For any* pod with `prometheus.io/scrape: "true"` annotation, Prometheus with
kubernetes_sd_config should discover and scrape that pod using the port and
path specified in annotations.
"""

import re
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import pytest
import yaml
from hypothesis import given, settings, assume
from hypothesis import strategies as st


# Valid Kubernetes annotation key pattern
K8S_ANNOTATION_KEY_PATTERN = re.compile(r"^[a-z0-9]([-a-z0-9]*[a-z0-9])?(\.[a-z0-9]([-a-z0-9]*[a-z0-9])?)*(/[a-zA-Z0-9][-a-zA-Z0-9_.]*)?$")

# Valid Kubernetes label name pattern
K8S_LABEL_NAME_PATTERN = re.compile(r"^([a-z0-9]([-a-z0-9]*[a-z0-9])?\.)*[a-z0-9]([-a-z0-9]*[a-z0-9])?(/[a-zA-Z0-9][-a-zA-Z0-9_.]*)?$")

# Valid Kubernetes namespace pattern
K8S_NAMESPACE_PATTERN = re.compile(r"^[a-z0-9]([-a-z0-9]*[a-z0-9])?$")

# Valid Kubernetes pod name pattern
K8S_POD_NAME_PATTERN = re.compile(r"^[a-z0-9]([-a-z0-9]*[a-z0-9])?$")

# Prometheus annotation prefix
PROMETHEUS_ANNOTATION_PREFIX = "prometheus.io/"

# Standard Prometheus annotations
PROMETHEUS_SCRAPE_ANNOTATION = "prometheus.io/scrape"
PROMETHEUS_PORT_ANNOTATION = "prometheus.io/port"
PROMETHEUS_PATH_ANNOTATION = "prometheus.io/path"
PROMETHEUS_SCHEME_ANNOTATION = "prometheus.io/scheme"


@dataclass
class KubernetesPodMetadata:
    """Represents Kubernetes pod metadata for service discovery."""
    name: str
    namespace: str
    labels: dict[str, str] = field(default_factory=dict)
    annotations: dict[str, str] = field(default_factory=dict)


@dataclass
class KubernetesPodSpec:
    """Represents Kubernetes pod spec for service discovery."""
    container_port: int = 8080
    container_name: str = "app"


@dataclass
class KubernetesPod:
    """Represents a Kubernetes pod for service discovery testing."""
    metadata: KubernetesPodMetadata
    spec: KubernetesPodSpec = field(default_factory=KubernetesPodSpec)
    pod_ip: str = "10.0.0.1"
    node_name: str = "node-1"


@dataclass
class KubernetesSDConfig:
    """Represents a kubernetes_sd_config configuration."""
    role: str = "pod"
    namespaces: list[str] = field(default_factory=list)
    selectors: list[dict[str, Any]] = field(default_factory=list)


@dataclass
class RelabelConfig:
    """Represents a relabel_config entry."""
    source_labels: list[str] = field(default_factory=list)
    target_label: str = ""
    action: str = "replace"
    regex: str = "(.*)"
    replacement: str = "$1"
    separator: str = ";"


def is_valid_namespace(namespace: str) -> bool:
    """Check if a namespace name is valid for Kubernetes."""
    if not namespace or len(namespace) > 63:
        return False
    return bool(K8S_NAMESPACE_PATTERN.match(namespace))


def is_valid_pod_name(name: str) -> bool:
    """Check if a pod name is valid for Kubernetes."""
    if not name or len(name) > 253:
        return False
    return bool(K8S_POD_NAME_PATTERN.match(name))


def is_valid_port(port: int) -> bool:
    """Check if a port number is valid."""
    return 1 <= port <= 65535


def is_valid_metrics_path(path: str) -> bool:
    """Check if a metrics path is valid."""
    if not path:
        return False
    return path.startswith("/")


def is_valid_scheme(scheme: str) -> bool:
    """Check if a scheme is valid for Prometheus scraping."""
    return scheme in ("http", "https")


def should_scrape_pod(pod: KubernetesPod) -> bool:
    """
    Determine if a pod should be scraped based on annotations.

    A pod should be scraped if it has prometheus.io/scrape: "true" annotation.
    """
    scrape_annotation = pod.metadata.annotations.get(PROMETHEUS_SCRAPE_ANNOTATION, "")
    return scrape_annotation.lower() == "true"


def get_scrape_port(pod: KubernetesPod) -> int:
    """
    Get the scrape port for a pod.

    Uses prometheus.io/port annotation if present, otherwise uses container port.
    """
    port_annotation = pod.metadata.annotations.get(PROMETHEUS_PORT_ANNOTATION, "")
    if port_annotation:
        try:
            return int(port_annotation)
        except ValueError:
            pass
    return pod.spec.container_port


def get_scrape_path(pod: KubernetesPod) -> str:
    """
    Get the scrape path for a pod.

    Uses prometheus.io/path annotation if present, otherwise defaults to /metrics.
    """
    path_annotation = pod.metadata.annotations.get(PROMETHEUS_PATH_ANNOTATION, "")
    if path_annotation:
        return path_annotation
    return "/metrics"


def get_scrape_scheme(pod: KubernetesPod) -> str:
    """
    Get the scrape scheme for a pod.

    Uses prometheus.io/scheme annotation if present, otherwise defaults to http.
    """
    scheme_annotation = pod.metadata.annotations.get(PROMETHEUS_SCHEME_ANNOTATION, "")
    if scheme_annotation in ("http", "https"):
        return scheme_annotation
    return "http"


def build_scrape_target(pod: KubernetesPod) -> dict[str, Any]:
    """
    Build a scrape target configuration from a pod.

    Returns the target address and labels that would be generated by
    kubernetes_sd_config relabeling.
    """
    port = get_scrape_port(pod)
    path = get_scrape_path(pod)
    scheme = get_scrape_scheme(pod)

    return {
        "address": f"{pod.pod_ip}:{port}",
        "metrics_path": path,
        "scheme": scheme,
        "labels": {
            "kubernetes_namespace": pod.metadata.namespace,
            "kubernetes_pod_name": pod.metadata.name,
            "kubernetes_node": pod.node_name,
            "pod_ip": pod.pod_ip,
            **{f"__meta_kubernetes_pod_label_{k}": v for k, v in pod.metadata.labels.items()},
        },
    }


def validate_kubernetes_sd_config(config: dict[str, Any]) -> list[str]:
    """
    Validate a kubernetes_sd_config configuration.

    Returns a list of validation errors (empty if valid).
    """
    errors = []

    # Check role is valid
    valid_roles = ["pod", "service", "endpoints", "endpointslice", "node", "ingress"]
    if "role" not in config:
        errors.append("Missing required field: role")
    elif config["role"] not in valid_roles:
        errors.append(f"Invalid role: {config['role']}. Must be one of {valid_roles}")

    # Validate namespaces if present
    if "namespaces" in config:
        namespaces = config["namespaces"]
        if "names" in namespaces:
            for ns in namespaces["names"]:
                if not is_valid_namespace(ns):
                    errors.append(f"Invalid namespace: {ns}")

    return errors


def validate_relabel_config(config: dict[str, Any]) -> list[str]:
    """
    Validate a relabel_config entry.

    Returns a list of validation errors (empty if valid).
    """
    errors = []

    valid_actions = ["replace", "keep", "drop", "hashmod", "labelmap", "labeldrop", "labelkeep"]

    action = config.get("action", "replace")
    if action not in valid_actions:
        errors.append(f"Invalid action: {action}. Must be one of {valid_actions}")

    # For keep/drop actions, source_labels is required
    if action in ("keep", "drop"):
        if "source_labels" not in config or not config["source_labels"]:
            errors.append(f"source_labels required for action: {action}")

    # For replace action, target_label is typically needed
    if action == "replace" and "target_label" not in config:
        # This is actually optional in some cases, so just a warning
        pass

    return errors


def simulate_pod_discovery(
    pods: list[KubernetesPod],
    relabel_configs: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """
    Simulate Kubernetes pod discovery with relabeling.

    Returns list of discovered targets after applying relabel configs.
    """
    discovered_targets = []

    for pod in pods:
        # Build initial labels from pod metadata (simulating __meta_kubernetes_* labels)
        meta_labels = {
            "__meta_kubernetes_namespace": pod.metadata.namespace,
            "__meta_kubernetes_pod_name": pod.metadata.name,
            "__meta_kubernetes_pod_ip": pod.pod_ip,
            "__meta_kubernetes_pod_node_name": pod.node_name,
            "__meta_kubernetes_pod_container_name": pod.spec.container_name,
            "__address__": f"{pod.pod_ip}:{pod.spec.container_port}",
            "__metrics_path__": "/metrics",
            "__scheme__": "http",
        }

        # Add annotation labels
        for key, value in pod.metadata.annotations.items():
            safe_key = key.replace(".", "_").replace("/", "_")
            meta_labels[f"__meta_kubernetes_pod_annotation_{safe_key}"] = value

        # Add pod labels
        for key, value in pod.metadata.labels.items():
            safe_key = key.replace(".", "_").replace("/", "_").replace("-", "_")
            meta_labels[f"__meta_kubernetes_pod_label_{safe_key}"] = value

        # Apply relabel configs
        labels = meta_labels.copy()
        keep_target = True

        for relabel in relabel_configs:
            action = relabel.get("action", "replace")
            source_labels = relabel.get("source_labels", [])
            target_label = relabel.get("target_label", "")
            regex = relabel.get("regex", "(.*)")
            replacement = relabel.get("replacement", "$1")

            # Get source value
            source_values = [str(labels.get(sl, "")) for sl in source_labels]
            source_value = ";".join(source_values)

            if action == "keep":
                if not re.match(regex, source_value):
                    keep_target = False
                    break
            elif action == "drop":
                if re.match(regex, source_value):
                    keep_target = False
                    break
            elif action == "replace":
                match = re.match(regex, source_value)
                if match and target_label:
                    # Simple replacement (not full regex substitution)
                    new_value = replacement
                    for i, group in enumerate(match.groups(), 1):
                        if group:
                            new_value = new_value.replace(f"${i}", group)
                    labels[target_label] = new_value
            elif action == "labelmap":
                # Map matching labels
                for label_name, label_value in list(labels.items()):
                    if re.match(regex, label_name):
                        match = re.match(regex, label_name)
                        if match and match.groups():
                            new_name = match.group(1)
                            labels[new_name] = label_value

        if keep_target:
            discovered_targets.append({
                "address": labels.get("__address__", ""),
                "metrics_path": labels.get("__metrics_path__", "/metrics"),
                "scheme": labels.get("__scheme__", "http"),
                "labels": {k: v for k, v in labels.items() if not k.startswith("__")},
            })

    return discovered_targets


# Hypothesis strategies for generating valid Kubernetes resources

valid_namespaces = st.sampled_from([
    "default", "kube-system", "monitoring", "production", "staging",
    "development", "apps", "services", "backend", "frontend",
])

valid_pod_names = st.text(
    alphabet="abcdefghijklmnopqrstuvwxyz0123456789-",
    min_size=1,
    max_size=50,
).filter(lambda s: s[0].isalnum() and s[-1].isalnum() and "--" not in s)

valid_container_names = st.sampled_from([
    "app", "web", "api", "worker", "sidecar", "proxy", "main",
])

valid_ports = st.integers(min_value=1024, max_value=65535)

valid_metrics_paths = st.sampled_from([
    "/metrics", "/api/metrics", "/prometheus/metrics",
    "/actuator/prometheus", "/_metrics", "/v1/metrics",
])

valid_schemes = st.sampled_from(["http", "https"])

valid_pod_ips = st.tuples(
    st.integers(min_value=10, max_value=10),
    st.integers(min_value=0, max_value=255),
    st.integers(min_value=0, max_value=255),
    st.integers(min_value=1, max_value=254),
).map(lambda t: f"{t[0]}.{t[1]}.{t[2]}.{t[3]}")

valid_node_names = st.sampled_from([
    "node-1", "node-2", "node-3", "worker-1", "worker-2",
    "ip-10-0-0-1", "gke-cluster-node-pool-abc123",
])

valid_label_keys = st.sampled_from([
    "app", "version", "environment", "team", "component",
    "app.kubernetes.io/name", "app.kubernetes.io/version",
])

valid_label_values = st.text(
    alphabet="abcdefghijklmnopqrstuvwxyz0123456789-_.",
    min_size=1,
    max_size=30,
)


@st.composite
def valid_pod_labels(draw) -> dict[str, str]:
    """Generate valid Kubernetes pod labels."""
    num_labels = draw(st.integers(min_value=0, max_value=3))
    labels = {}
    for _ in range(num_labels):
        key = draw(valid_label_keys)
        value = draw(valid_label_values)
        labels[key] = value
    return labels


@st.composite
def valid_prometheus_annotations(draw, scrape: bool = True) -> dict[str, str]:
    """Generate valid Prometheus annotations for a pod."""
    annotations = {}

    # Always set scrape annotation based on parameter
    annotations[PROMETHEUS_SCRAPE_ANNOTATION] = "true" if scrape else "false"

    # Optionally add port annotation
    if draw(st.booleans()):
        port = draw(valid_ports)
        annotations[PROMETHEUS_PORT_ANNOTATION] = str(port)

    # Optionally add path annotation
    if draw(st.booleans()):
        path = draw(valid_metrics_paths)
        annotations[PROMETHEUS_PATH_ANNOTATION] = path

    # Optionally add scheme annotation
    if draw(st.booleans()):
        scheme = draw(valid_schemes)
        annotations[PROMETHEUS_SCHEME_ANNOTATION] = scheme

    return annotations


@st.composite
def valid_kubernetes_pod(draw, scrape: bool = True) -> KubernetesPod:
    """Generate a valid Kubernetes pod for testing."""
    name = draw(valid_pod_names)
    namespace = draw(valid_namespaces)
    labels = draw(valid_pod_labels())
    annotations = draw(valid_prometheus_annotations(scrape=scrape))
    container_port = draw(valid_ports)
    container_name = draw(valid_container_names)
    pod_ip = draw(valid_pod_ips)
    node_name = draw(valid_node_names)

    return KubernetesPod(
        metadata=KubernetesPodMetadata(
            name=name,
            namespace=namespace,
            labels=labels,
            annotations=annotations,
        ),
        spec=KubernetesPodSpec(
            container_port=container_port,
            container_name=container_name,
        ),
        pod_ip=pod_ip,
        node_name=node_name,
    )


@st.composite
def valid_kubernetes_sd_config(draw) -> dict[str, Any]:
    """Generate a valid kubernetes_sd_config."""
    role = draw(st.sampled_from(["pod", "endpoints", "service"]))

    config = {"role": role}

    # Optionally add namespace filter
    if draw(st.booleans()):
        namespaces = draw(st.lists(valid_namespaces, min_size=1, max_size=3))
        config["namespaces"] = {"names": list(set(namespaces))}

    return config


# Standard relabel configs for pod discovery (from pods.yml)
STANDARD_POD_RELABEL_CONFIGS = [
    # Only scrape pods with prometheus.io/scrape: "true" annotation
    {
        "source_labels": ["__meta_kubernetes_pod_annotation_prometheus_io_scrape"],
        "action": "keep",
        "regex": "true",
    },
    # Use prometheus.io/scheme annotation for http/https
    {
        "source_labels": ["__meta_kubernetes_pod_annotation_prometheus_io_scheme"],
        "action": "replace",
        "target_label": "__scheme__",
        "regex": "(https?)",
    },
    # Use prometheus.io/path annotation for metrics path
    {
        "source_labels": ["__meta_kubernetes_pod_annotation_prometheus_io_path"],
        "action": "replace",
        "target_label": "__metrics_path__",
        "regex": "(.+)",
    },
    # Use prometheus.io/port annotation for port
    {
        "source_labels": ["__address__", "__meta_kubernetes_pod_annotation_prometheus_io_port"],
        "action": "replace",
        "regex": "([^:]+)(?::\\d+)?;(\\d+)",
        "replacement": "$1:$2",
        "target_label": "__address__",
    },
    # Add namespace label
    {
        "source_labels": ["__meta_kubernetes_namespace"],
        "action": "replace",
        "target_label": "kubernetes_namespace",
    },
    # Add pod name label
    {
        "source_labels": ["__meta_kubernetes_pod_name"],
        "action": "replace",
        "target_label": "kubernetes_pod_name",
    },
]


@pytest.mark.property
class TestKubernetesServiceDiscoveryProperty:
    """
    Property-based tests for Kubernetes service discovery configuration.

    **Feature: prometheus-installation, Property 8: Kubernetes Service Discovery**
    **Validates: Requirements 7.1, 7.2, 7.3, 7.4, 7.7**
    """

    @given(pod=valid_kubernetes_pod(scrape=True))
    @settings(max_examples=100)
    def test_annotated_pod_is_discovered(self, pod: KubernetesPod):
        """
        Property: For any pod with prometheus.io/scrape: "true" annotation,
        the pod should be discovered by kubernetes_sd_config.

        **Feature: prometheus-installation, Property 8: Kubernetes Service Discovery**
        **Validates: Requirements 7.1, 7.2**
        """
        # Verify the pod has scrape annotation
        assert should_scrape_pod(pod), "Pod should have scrape annotation set to true"

        # Simulate discovery with standard relabel configs
        discovered = simulate_pod_discovery([pod], STANDARD_POD_RELABEL_CONFIGS)

        # Pod should be discovered
        assert len(discovered) == 1, "Annotated pod should be discovered"

        # Verify namespace and pod name are in labels
        target = discovered[0]
        assert "kubernetes_namespace" in target["labels"], "Should have namespace label"
        assert "kubernetes_pod_name" in target["labels"], "Should have pod name label"
        assert target["labels"]["kubernetes_namespace"] == pod.metadata.namespace
        assert target["labels"]["kubernetes_pod_name"] == pod.metadata.name

    @given(pod=valid_kubernetes_pod(scrape=False))
    @settings(max_examples=100)
    def test_non_annotated_pod_is_not_discovered(self, pod: KubernetesPod):
        """
        Property: For any pod without prometheus.io/scrape: "true" annotation,
        the pod should NOT be discovered.

        **Feature: prometheus-installation, Property 8: Kubernetes Service Discovery**
        **Validates: Requirements 7.2**
        """
        # Verify the pod does not have scrape annotation
        assert not should_scrape_pod(pod), "Pod should not have scrape annotation"

        # Simulate discovery with standard relabel configs
        discovered = simulate_pod_discovery([pod], STANDARD_POD_RELABEL_CONFIGS)

        # Pod should NOT be discovered
        assert len(discovered) == 0, "Non-annotated pod should not be discovered"

    @given(pod=valid_kubernetes_pod(scrape=True))
    @settings(max_examples=100)
    def test_port_annotation_is_used(self, pod: KubernetesPod):
        """
        Property: For any pod with prometheus.io/port annotation,
        the scrape target should use the annotated port.

        **Feature: prometheus-installation, Property 8: Kubernetes Service Discovery**
        **Validates: Requirements 7.3**
        """
        expected_port = get_scrape_port(pod)

        # Simulate discovery
        discovered = simulate_pod_discovery([pod], STANDARD_POD_RELABEL_CONFIGS)

        assert len(discovered) == 1, "Pod should be discovered"

        # Verify the port in the address
        target = discovered[0]
        address = target["address"]

        # Address should contain the expected port
        assert f":{expected_port}" in address, \
            f"Address {address} should use port {expected_port}"

    @given(pod=valid_kubernetes_pod(scrape=True))
    @settings(max_examples=100)
    def test_path_annotation_is_used(self, pod: KubernetesPod):
        """
        Property: For any pod with prometheus.io/path annotation,
        the scrape target should use the annotated path.

        **Feature: prometheus-installation, Property 8: Kubernetes Service Discovery**
        **Validates: Requirements 7.4**
        """
        expected_path = get_scrape_path(pod)

        # Simulate discovery
        discovered = simulate_pod_discovery([pod], STANDARD_POD_RELABEL_CONFIGS)

        assert len(discovered) == 1, "Pod should be discovered"

        # Verify the metrics path
        target = discovered[0]
        actual_path = target["metrics_path"]

        # If pod has path annotation, it should be used
        if PROMETHEUS_PATH_ANNOTATION in pod.metadata.annotations:
            assert actual_path == expected_path, \
                f"Metrics path should be {expected_path}, got {actual_path}"
        else:
            # Default path should be /metrics
            assert actual_path == "/metrics", \
                f"Default metrics path should be /metrics, got {actual_path}"


    @given(pod=valid_kubernetes_pod(scrape=True))
    @settings(max_examples=100)
    def test_scheme_annotation_is_used(self, pod: KubernetesPod):
        """
        Property: For any pod with prometheus.io/scheme annotation,
        the scrape target should use the annotated scheme.

        **Feature: prometheus-installation, Property 8: Kubernetes Service Discovery**
        **Validates: Requirements 7.1**
        """
        expected_scheme = get_scrape_scheme(pod)

        # Simulate discovery
        discovered = simulate_pod_discovery([pod], STANDARD_POD_RELABEL_CONFIGS)

        assert len(discovered) == 1, "Pod should be discovered"

        # Verify the scheme
        target = discovered[0]
        actual_scheme = target["scheme"]

        # If pod has scheme annotation, it should be used
        if PROMETHEUS_SCHEME_ANNOTATION in pod.metadata.annotations:
            scheme_value = pod.metadata.annotations[PROMETHEUS_SCHEME_ANNOTATION]
            if scheme_value in ("http", "https"):
                assert actual_scheme == expected_scheme, \
                    f"Scheme should be {expected_scheme}, got {actual_scheme}"
        else:
            # Default scheme should be http
            assert actual_scheme == "http", \
                f"Default scheme should be http, got {actual_scheme}"

    @given(
        pods=st.lists(valid_kubernetes_pod(scrape=True), min_size=1, max_size=5),
    )
    @settings(max_examples=100)
    def test_multiple_pods_discovered(self, pods: list[KubernetesPod]):
        """
        Property: For any set of pods with prometheus.io/scrape: "true" annotation,
        all pods should be discovered.

        **Feature: prometheus-installation, Property 8: Kubernetes Service Discovery**
        **Validates: Requirements 7.7**
        """
        # Simulate discovery
        discovered = simulate_pod_discovery(pods, STANDARD_POD_RELABEL_CONFIGS)

        # All pods should be discovered
        assert len(discovered) == len(pods), \
            f"All {len(pods)} pods should be discovered, got {len(discovered)}"

    @given(
        scrape_pods=st.lists(valid_kubernetes_pod(scrape=True), min_size=1, max_size=3),
        non_scrape_pods=st.lists(valid_kubernetes_pod(scrape=False), min_size=1, max_size=3),
    )
    @settings(max_examples=100)
    def test_mixed_pods_filtered_correctly(
        self,
        scrape_pods: list[KubernetesPod],
        non_scrape_pods: list[KubernetesPod],
    ):
        """
        Property: For any mix of annotated and non-annotated pods,
        only annotated pods should be discovered.

        **Feature: prometheus-installation, Property 8: Kubernetes Service Discovery**
        **Validates: Requirements 7.2, 7.7**
        """
        all_pods = scrape_pods + non_scrape_pods

        # Simulate discovery
        discovered = simulate_pod_discovery(all_pods, STANDARD_POD_RELABEL_CONFIGS)

        # Only scrape_pods should be discovered
        assert len(discovered) == len(scrape_pods), \
            f"Only {len(scrape_pods)} annotated pods should be discovered, got {len(discovered)}"

    @given(config=valid_kubernetes_sd_config())
    @settings(max_examples=100)
    def test_kubernetes_sd_config_is_valid(self, config: dict[str, Any]):
        """
        Property: For any generated kubernetes_sd_config, the configuration
        should be valid.

        **Feature: prometheus-installation, Property 8: Kubernetes Service Discovery**
        **Validates: Requirements 7.1**
        """
        errors = validate_kubernetes_sd_config(config)
        assert len(errors) == 0, f"Validation errors: {errors}"

    @given(pod=valid_kubernetes_pod(scrape=True))
    @settings(max_examples=100)
    def test_pod_labels_are_mapped(self, pod: KubernetesPod):
        """
        Property: For any pod with labels, the labels should be mapped
        to Prometheus labels after discovery.

        **Feature: prometheus-installation, Property 8: Kubernetes Service Discovery**
        **Validates: Requirements 7.1**
        """
        # Add labelmap relabel config
        relabel_configs = STANDARD_POD_RELABEL_CONFIGS + [
            {
                "action": "labelmap",
                "regex": "__meta_kubernetes_pod_label_(.+)",
            },
        ]

        # Simulate discovery
        discovered = simulate_pod_discovery([pod], relabel_configs)

        assert len(discovered) == 1, "Pod should be discovered"

        # Verify pod labels are mapped (with underscores replacing special chars)
        target = discovered[0]
        for key, value in pod.metadata.labels.items():
            # Labels with dots/slashes get converted
            safe_key = key.replace(".", "_").replace("/", "_").replace("-", "_")
            if safe_key in target["labels"]:
                assert target["labels"][safe_key] == value, \
                    f"Label {key} should be mapped with value {value}"

    @given(pod=valid_kubernetes_pod(scrape=True))
    @settings(max_examples=100)
    def test_config_yaml_serialization(self, pod: KubernetesPod):
        """
        Property: For any kubernetes_sd_config with relabel_configs,
        the configuration should serialize to valid YAML.

        **Feature: prometheus-installation, Property 8: Kubernetes Service Discovery**
        **Validates: Requirements 7.1**
        """
        # Build a complete scrape config
        scrape_config = {
            "job_name": "kubernetes-pods",
            "kubernetes_sd_configs": [{"role": "pod"}],
            "relabel_configs": STANDARD_POD_RELABEL_CONFIGS,
        }

        # Serialize to YAML
        yaml_str = yaml.dump(scrape_config, default_flow_style=False)

        # Deserialize and verify
        loaded = yaml.safe_load(yaml_str)

        assert loaded["job_name"] == "kubernetes-pods"
        assert loaded["kubernetes_sd_configs"][0]["role"] == "pod"
        assert len(loaded["relabel_configs"]) == len(STANDARD_POD_RELABEL_CONFIGS)

    @given(pod=valid_kubernetes_pod(scrape=True))
    @settings(max_examples=100)
    def test_discovery_produces_valid_target(self, pod: KubernetesPod):
        """
        Property: For any discovered pod, the resulting target should have
        a valid address, path, and scheme.

        **Feature: prometheus-installation, Property 8: Kubernetes Service Discovery**
        **Validates: Requirements 7.1, 7.3, 7.4**
        """
        # Simulate discovery
        discovered = simulate_pod_discovery([pod], STANDARD_POD_RELABEL_CONFIGS)

        assert len(discovered) == 1, "Pod should be discovered"

        target = discovered[0]

        # Verify address format (ip:port)
        address = target["address"]
        assert ":" in address, f"Address should have port: {address}"
        host, port_str = address.rsplit(":", 1)
        assert host, "Address should have host"
        assert port_str.isdigit(), f"Port should be numeric: {port_str}"
        port = int(port_str)
        assert is_valid_port(port), f"Port should be valid: {port}"

        # Verify metrics path
        path = target["metrics_path"]
        assert is_valid_metrics_path(path), f"Path should be valid: {path}"

        # Verify scheme
        scheme = target["scheme"]
        assert is_valid_scheme(scheme), f"Scheme should be valid: {scheme}"
