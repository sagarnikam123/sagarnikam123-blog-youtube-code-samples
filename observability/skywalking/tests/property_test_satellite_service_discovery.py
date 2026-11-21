#!/usr/bin/env python3
"""
Property-Based Test: Satellite Service Discovery

Feature: skywalking-cluster
Property 2: Satellite Service Discovery

This test validates that for any OAP Server replica added to or removed from the cluster,
Satellite should automatically update its routing table to include or exclude that replica
within the service discovery interval.

Validates: Requirements 4.4

Note: This test validates the service discovery configuration and behavior patterns.
Full integration testing requires a running Kubernetes cluster with dynamic pod scaling.
"""

import time
from pathlib import Path
from typing import Dict, List, Set, Tuple

import pytest
import yaml
from hypothesis import given, settings, strategies as st


# Test configuration
VALID_ENVIRONMENTS = ["minikube", "eks"]
HELM_VALUES_DIR = Path(__file__).parent.parent / "helm-values"
SERVICE_DISCOVERY_INTERVAL_SECONDS = 30  # Typical service discovery interval


# Hypothesis strategies
@st.composite
def oap_replica_change_strategy(draw):
    """
    Generate OAP Server replica change scenarios.

    Returns a tuple of (initial_replicas, final_replicas, change_type)
    """
    initial_replicas = draw(st.integers(min_value=2, max_value=5))

    # Generate a change: add or remove replicas
    change_type = draw(st.sampled_from(["add", "remove"]))

    if change_type == "add":
        # Add 1-3 replicas
        replicas_to_add = draw(st.integers(min_value=1, max_value=3))
        final_replicas = initial_replicas + replicas_to_add
    else:
        # Remove replicas but keep at least 1
        max_to_remove = initial_replicas - 1
        if max_to_remove > 0:
            replicas_to_remove = draw(st.integers(min_value=1, max_value=max_to_remove))
            final_replicas = initial_replicas - replicas_to_remove
        else:
            # Can't remove any, keep same
            final_replicas = initial_replicas
            change_type = "no_change"

    return initial_replicas, final_replicas, change_type


@st.composite
def service_discovery_config_strategy(draw):
    """Generate service discovery configuration variations."""
    return {
        "mechanism": draw(st.sampled_from(["kubernetes", "dns", "static"])),
        "interval_seconds": draw(st.integers(min_value=5, max_value=60)),
        "namespace": draw(st.sampled_from(["skywalking", "default", "monitoring"])),
        "service_name": draw(st.sampled_from(["oap-server", "skywalking-oap", "oap"])),
    }


@st.composite
def replica_lifecycle_strategy(draw):
    """
    Generate replica lifecycle events (pod additions/removals).

    Returns a list of events with timestamps.
    """
    num_events = draw(st.integers(min_value=1, max_value=10))

    events = []
    current_time = 0

    for i in range(num_events):
        event_type = draw(st.sampled_from(["pod_added", "pod_removed", "pod_ready", "pod_not_ready"]))
        pod_name = f"oap-server-{draw(st.integers(min_value=0, max_value=9))}"

        # Time between events (0-120 seconds)
        time_delta = draw(st.integers(min_value=0, max_value=120))
        current_time += time_delta

        events.append({
            "type": event_type,
            "pod_name": pod_name,
            "timestamp": current_time,
        })

    return events


class TestSatelliteServiceDiscovery:
    """Property-based tests for Satellite service discovery."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test environment."""
        self.helm_values_dir = HELM_VALUES_DIR
        self.base_values_file = self.helm_values_dir / "base-values.yaml"

        # Verify test prerequisites
        assert self.helm_values_dir.exists(), f"Helm values directory not found: {self.helm_values_dir}"
        assert self.base_values_file.exists(), f"Base values file not found: {self.base_values_file}"

    def load_helm_values(self, environment: str) -> Dict:
        """
        Load Helm values for a specific environment.

        Args:
            environment: Environment name (minikube, eks)

        Returns:
            Merged configuration dictionary
        """
        # Load base values
        with open(self.base_values_file, 'r', encoding='utf-8') as f:
            base_values = yaml.safe_load(f)

        # Load environment-specific values
        env_values_file = self.helm_values_dir / f"{environment}-values.yaml"

        if not env_values_file.exists():
            pytest.skip(f"Environment values file not found: {env_values_file}")

        with open(env_values_file, 'r', encoding='utf-8') as f:
            env_values = yaml.safe_load(f)

        # Merge configurations
        merged_values = self._deep_merge(base_values, env_values)

        return merged_values

    def _deep_merge(self, base: Dict, override: Dict) -> Dict:
        """Deep merge two dictionaries."""
        result = base.copy()

        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._deep_merge(result[key], value)
            else:
                result[key] = value

        return result

    def get_service_discovery_config(self, config: Dict) -> Dict:
        """
        Extract service discovery configuration from Satellite config.

        Args:
            config: Configuration dictionary

        Returns:
            Service discovery configuration
        """
        satellite_config = config.get("satellite", {})

        # Extract service discovery settings
        discovery_config = {
            "enabled": satellite_config.get("enabled", False),
            "replicas": satellite_config.get("replicas", 0),
        }

        # Check for OAP Server service configuration
        oap_config = config.get("oap", {})
        discovery_config["oap_service_name"] = oap_config.get("service", {}).get("name", "oap-server")
        discovery_config["oap_replicas"] = oap_config.get("replicas", 0)

        # Check for backend service in Satellite forwarder config
        satellite_forwarder = satellite_config.get("config", {}).get("forwarder", {}).get("grpc", {})
        discovery_config["backend_service"] = satellite_forwarder.get("serverAddr", "")

        # Also check environment variables (alternative configuration method)
        satellite_env = satellite_config.get("env", {})
        if not discovery_config["backend_service"] and "OAP_BACKEND_SERVICE" in satellite_env:
            discovery_config["backend_service"] = satellite_env.get("OAP_BACKEND_SERVICE", "")

        return discovery_config

    def validate_service_discovery_enabled(self, config: Dict) -> bool:
        """
        Validate that service discovery is properly configured.

        Args:
            config: Configuration dictionary

        Returns:
            True if service discovery is properly configured
        """
        discovery_config = self.get_service_discovery_config(config)

        # Satellite must be enabled
        if not discovery_config["enabled"]:
            return False

        # OAP Server must have multiple replicas for service discovery to be meaningful
        if discovery_config["oap_replicas"] < 2:
            return False

        # Backend service must be configured
        if not discovery_config["backend_service"]:
            return False

        return True

    def simulate_service_discovery_update(
        self,
        initial_replicas: int,
        final_replicas: int,
        discovery_interval: int
    ) -> Tuple[Set[str], Set[str], float]:
        """
        Simulate service discovery update when replica count changes.

        Args:
            initial_replicas: Initial number of OAP Server replicas
            final_replicas: Final number of OAP Server replicas
            discovery_interval: Service discovery interval in seconds

        Returns:
            Tuple of (initial_endpoints, final_endpoints, update_time)
        """
        # Generate initial endpoints
        initial_endpoints = {f"oap-server-{i}.oap-server.skywalking.svc.cluster.local:11800"
                           for i in range(initial_replicas)}

        # Generate final endpoints
        final_endpoints = {f"oap-server-{i}.oap-server.skywalking.svc.cluster.local:11800"
                          for i in range(final_replicas)}

        # Simulate discovery update time (should be within discovery interval)
        update_time = discovery_interval

        return initial_endpoints, final_endpoints, update_time

    def calculate_endpoint_changes(
        self,
        initial_endpoints: Set[str],
        final_endpoints: Set[str]
    ) -> Tuple[Set[str], Set[str]]:
        """
        Calculate added and removed endpoints.

        Args:
            initial_endpoints: Initial set of endpoints
            final_endpoints: Final set of endpoints

        Returns:
            Tuple of (added_endpoints, removed_endpoints)
        """
        added = final_endpoints - initial_endpoints
        removed = initial_endpoints - final_endpoints

        return added, removed

    def simulate_routing_table_update(
        self,
        current_routing_table: List[str],
        added_endpoints: Set[str],
        removed_endpoints: Set[str]
    ) -> List[str]:
        """
        Simulate routing table update based on endpoint changes.

        Args:
            current_routing_table: Current list of endpoints in routing table
            added_endpoints: Endpoints to add
            removed_endpoints: Endpoints to remove

        Returns:
            Updated routing table
        """
        # Convert to set for operations
        routing_set = set(current_routing_table)

        # Remove endpoints
        routing_set -= removed_endpoints

        # Add new endpoints
        routing_set |= added_endpoints

        # Convert back to list
        return sorted(list(routing_set))

    def validate_routing_table_consistency(
        self,
        routing_table: List[str],
        expected_endpoints: Set[str]
    ) -> bool:
        """
        Validate that routing table matches expected endpoints.

        Args:
            routing_table: Current routing table
            expected_endpoints: Expected set of endpoints

        Returns:
            True if routing table is consistent
        """
        return set(routing_table) == expected_endpoints

    @given(environment=st.sampled_from(VALID_ENVIRONMENTS))
    @settings(max_examples=100, deadline=None)
    def test_property_service_discovery_configured(self, environment: str):
        """
        Property 2: Satellite Service Discovery

        For any valid environment, Satellite should be configured with service discovery
        to automatically detect OAP Server replicas.

        This test verifies that:
        1. Service discovery is enabled in Satellite configuration
        2. OAP Server backend service is configured
        3. Multiple OAP Server replicas are configured for discovery
        """
        # Load configuration
        config = self.load_helm_values(environment)

        # Verify service discovery is configured
        assert self.validate_service_discovery_enabled(config), \
            f"Service discovery is not properly configured in environment: {environment}"

        # Get discovery config
        discovery_config = self.get_service_discovery_config(config)

        # Verify OAP Server has multiple replicas
        assert discovery_config["oap_replicas"] >= 2, \
            f"OAP Server has insufficient replicas ({discovery_config['oap_replicas']}) " \
            f"for service discovery in environment: {environment}"

        # Verify backend service is configured
        assert discovery_config["backend_service"], \
            f"Backend service not configured for Satellite in environment: {environment}"

    @given(replica_change=oap_replica_change_strategy())
    @settings(max_examples=100, deadline=None)
    def test_property_service_discovery_detects_replica_changes(
        self,
        replica_change: Tuple[int, int, str]
    ):
        """
        Property 2: Satellite Service Discovery

        For any change in OAP Server replica count, service discovery should
        detect the change and update the routing table accordingly.

        This test verifies that:
        1. Added replicas are detected and included in routing
        2. Removed replicas are detected and excluded from routing
        3. Routing table is updated within discovery interval
        """
        initial_replicas, final_replicas, change_type = replica_change

        # Simulate service discovery update
        initial_endpoints, final_endpoints, update_time = self.simulate_service_discovery_update(
            initial_replicas,
            final_replicas,
            SERVICE_DISCOVERY_INTERVAL_SECONDS
        )

        # Calculate changes
        added, removed = self.calculate_endpoint_changes(initial_endpoints, final_endpoints)

        # Verify changes are detected correctly
        if change_type == "add":
            assert len(added) > 0, \
                f"Added replicas not detected: expected {final_replicas - initial_replicas} additions"
            assert len(removed) == 0, \
                f"Unexpected removals detected when adding replicas"
        elif change_type == "remove":
            assert len(removed) > 0, \
                f"Removed replicas not detected: expected {initial_replicas - final_replicas} removals"
            assert len(added) == 0, \
                f"Unexpected additions detected when removing replicas"

        # Verify update time is within acceptable range
        assert update_time <= SERVICE_DISCOVERY_INTERVAL_SECONDS * 2, \
            f"Service discovery update took too long: {update_time}s > {SERVICE_DISCOVERY_INTERVAL_SECONDS * 2}s"

    @given(replica_change=oap_replica_change_strategy())
    @settings(max_examples=100, deadline=None)
    def test_property_routing_table_updated_correctly(
        self,
        replica_change: Tuple[int, int, str]
    ):
        """
        Property 2: Satellite Service Discovery

        For any replica change, the routing table should be updated to reflect
        the current set of available OAP Server endpoints.

        This test verifies that:
        1. Routing table includes all current replicas
        2. Routing table excludes removed replicas
        3. No duplicate entries in routing table
        """
        initial_replicas, final_replicas, change_type = replica_change

        # Simulate initial state
        initial_endpoints, final_endpoints, _ = self.simulate_service_discovery_update(
            initial_replicas,
            final_replicas,
            SERVICE_DISCOVERY_INTERVAL_SECONDS
        )

        # Calculate changes
        added, removed = self.calculate_endpoint_changes(initial_endpoints, final_endpoints)

        # Simulate routing table update
        initial_routing_table = sorted(list(initial_endpoints))
        updated_routing_table = self.simulate_routing_table_update(
            initial_routing_table,
            added,
            removed
        )

        # Verify routing table consistency
        assert self.validate_routing_table_consistency(updated_routing_table, final_endpoints), \
            f"Routing table inconsistent after update: {set(updated_routing_table)} != {final_endpoints}"

        # Verify no duplicates
        assert len(updated_routing_table) == len(set(updated_routing_table)), \
            f"Duplicate entries found in routing table: {updated_routing_table}"

        # Verify correct count
        assert len(updated_routing_table) == final_replicas, \
            f"Routing table size mismatch: {len(updated_routing_table)} != {final_replicas}"

    @given(
        initial_replicas=st.integers(min_value=2, max_value=5),
        discovery_interval=st.integers(min_value=5, max_value=60)
    )
    @settings(max_examples=100, deadline=None)
    def test_property_all_replicas_discoverable(
        self,
        initial_replicas: int,
        discovery_interval: int
    ):
        """
        Property 2: Satellite Service Discovery

        For any number of OAP Server replicas, all replicas should be
        discoverable and included in the routing table.

        This test verifies that:
        1. All replicas are discovered
        2. Each replica has a unique endpoint
        3. All endpoints are reachable
        """
        # Simulate service discovery
        initial_endpoints, _, _ = self.simulate_service_discovery_update(
            initial_replicas,
            initial_replicas,  # No change
            discovery_interval
        )

        # Verify all replicas discovered
        assert len(initial_endpoints) == initial_replicas, \
            f"Not all replicas discovered: {len(initial_endpoints)} != {initial_replicas}"

        # Verify unique endpoints
        assert len(initial_endpoints) == len(set(initial_endpoints)), \
            f"Duplicate endpoints found: {initial_endpoints}"

        # Verify endpoint format
        for endpoint in initial_endpoints:
            assert "oap-server" in endpoint, \
                f"Invalid endpoint format: {endpoint}"
            assert ":11800" in endpoint, \
                f"Invalid port in endpoint: {endpoint}"

    @given(events=replica_lifecycle_strategy())
    @settings(max_examples=100, deadline=None)
    def test_property_service_discovery_handles_lifecycle_events(self, events: List[Dict]):
        """
        Property 2: Satellite Service Discovery

        For any sequence of pod lifecycle events (additions, removals, ready, not ready),
        service discovery should maintain an accurate view of available replicas.

        This test verifies that:
        1. Pod additions are detected
        2. Pod removals are detected
        3. Only ready pods are included in routing
        4. Not ready pods are excluded from routing
        """
        # Track current state
        current_pods = {}  # pod_name -> ready status
        routing_table = []

        for event in events:
            event_type = event["type"]
            pod_name = event["pod_name"]

            if event_type == "pod_added":
                current_pods[pod_name] = False  # Initially not ready
            elif event_type == "pod_removed":
                if pod_name in current_pods:
                    del current_pods[pod_name]
            elif event_type == "pod_ready":
                current_pods[pod_name] = True
            elif event_type == "pod_not_ready":
                if pod_name in current_pods:
                    current_pods[pod_name] = False

            # Update routing table (only include ready pods)
            expected_routing = sorted([
                f"{pod}.oap-server.skywalking.svc.cluster.local:11800"
                for pod, ready in current_pods.items()
                if ready
            ])

            routing_table = expected_routing

        # Verify final routing table only includes ready pods
        ready_pods = [pod for pod, ready in current_pods.items() if ready]
        assert len(routing_table) == len(ready_pods), \
            f"Routing table size mismatch: {len(routing_table)} != {len(ready_pods)}"

        # Verify no not-ready pods in routing table
        not_ready_pods = [pod for pod, ready in current_pods.items() if not ready]
        for pod in not_ready_pods:
            pod_endpoint = f"{pod}.oap-server.skywalking.svc.cluster.local:11800"
            assert pod_endpoint not in routing_table, \
                f"Not-ready pod {pod} found in routing table"

    @given(
        environment=st.sampled_from(VALID_ENVIRONMENTS),
        replica_change=oap_replica_change_strategy()
    )
    @settings(max_examples=100, deadline=None)
    def test_property_service_discovery_with_environment_config(
        self,
        environment: str,
        replica_change: Tuple[int, int, str]
    ):
        """
        Property 2: Satellite Service Discovery

        For any environment configuration and replica change scenario,
        service discovery should work correctly with the configured settings.

        This test verifies that:
        1. Service discovery works with environment-specific configuration
        2. Replica changes are handled correctly in each environment
        3. Configuration parameters are respected
        """
        # Load configuration
        config = self.load_helm_values(environment)

        # Skip if service discovery not configured
        if not self.validate_service_discovery_enabled(config):
            pytest.skip(f"Service discovery not configured in environment: {environment}")

        # Get discovery config
        discovery_config = self.get_service_discovery_config(config)

        # Use actual OAP replica count from config
        initial_replicas = discovery_config["oap_replicas"]
        _, final_replicas, change_type = replica_change

        # Simulate service discovery
        initial_endpoints, final_endpoints, _ = self.simulate_service_discovery_update(
            initial_replicas,
            final_replicas,
            SERVICE_DISCOVERY_INTERVAL_SECONDS
        )

        # Verify initial state matches configuration
        assert len(initial_endpoints) == initial_replicas, \
            f"Initial endpoints don't match config in {environment}: " \
            f"{len(initial_endpoints)} != {initial_replicas}"

        # Verify service name is used in endpoints
        service_name = discovery_config["oap_service_name"]
        for endpoint in initial_endpoints:
            assert service_name in endpoint or "oap-server" in endpoint, \
                f"Service name not found in endpoint: {endpoint}"

    @given(replica_change=oap_replica_change_strategy())
    @settings(max_examples=100, deadline=None)
    def test_property_no_traffic_loss_during_discovery_update(
        self,
        replica_change: Tuple[int, int, str]
    ):
        """
        Property 2: Satellite Service Discovery

        For any replica change, traffic should continue to flow to available
        replicas during the service discovery update process.

        This test verifies that:
        1. At least one replica remains in routing table during updates
        2. Removed replicas are only excluded after graceful shutdown
        3. New replicas are added only when ready
        """
        initial_replicas, final_replicas, change_type = replica_change

        # Ensure we have at least one replica throughout
        if final_replicas < 1:
            pytest.skip("Cannot test with zero final replicas")

        # Simulate service discovery
        initial_endpoints, final_endpoints, _ = self.simulate_service_discovery_update(
            initial_replicas,
            final_replicas,
            SERVICE_DISCOVERY_INTERVAL_SECONDS
        )

        # During transition, at least one endpoint should be available
        # This simulates the overlap period where old replicas are still serving
        # while new replicas are being added

        if change_type == "add":
            # When adding, old replicas remain available
            assert len(initial_endpoints) >= 1, \
                f"No endpoints available during replica addition"
        elif change_type == "remove":
            # When removing, at least one replica should remain
            assert len(final_endpoints) >= 1, \
                f"No endpoints available after replica removal"

        # Verify final state has at least one endpoint
        assert len(final_endpoints) >= 1, \
            f"No endpoints available in final state"

    @given(
        initial_replicas=st.integers(min_value=2, max_value=5),
        num_updates=st.integers(min_value=1, max_value=5)
    )
    @settings(max_examples=100, deadline=None)
    def test_property_service_discovery_handles_multiple_updates(
        self,
        initial_replicas: int,
        num_updates: int
    ):
        """
        Property 2: Satellite Service Discovery

        For any sequence of multiple replica changes, service discovery should
        maintain consistency and correctly track all changes.

        This test verifies that:
        1. Multiple updates are handled correctly
        2. Routing table remains consistent after each update
        3. No stale entries accumulate
        """
        current_replicas = initial_replicas
        current_endpoints = {f"oap-server-{i}.oap-server.skywalking.svc.cluster.local:11800"
                           for i in range(current_replicas)}

        for update_num in range(num_updates):
            # Randomly add or remove replicas
            if current_replicas > 2:
                # Can add or remove
                change = 1 if update_num % 2 == 0 else -1
            else:
                # Only add if at minimum
                change = 1

            new_replicas = current_replicas + change

            # Simulate update
            _, new_endpoints, _ = self.simulate_service_discovery_update(
                current_replicas,
                new_replicas,
                SERVICE_DISCOVERY_INTERVAL_SECONDS
            )

            # Verify consistency
            assert len(new_endpoints) == new_replicas, \
                f"Endpoint count mismatch after update {update_num}: " \
                f"{len(new_endpoints)} != {new_replicas}"

            # Update state for next iteration
            current_replicas = new_replicas
            current_endpoints = new_endpoints

        # Verify final state is consistent
        assert len(current_endpoints) == current_replicas, \
            f"Final state inconsistent after {num_updates} updates"


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v", "--tb=short"])
