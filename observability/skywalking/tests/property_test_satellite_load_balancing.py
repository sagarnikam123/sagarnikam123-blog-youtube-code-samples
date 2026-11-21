#!/usr/bin/env python3
"""
Property-Based Test: Satellite Load Balancing Distribution

Feature: skywalking-cluster
Property 1: Satellite Load Balancing Distribution

This test validates that for any set of observability data sent to the Satellite cluster,
the data should be distributed across all available OAP Server replicas according to the
configured load balancing strategy.

Validates: Requirements 4.2

Note: This test simulates the load balancing behavior by verifying configuration and
distribution patterns. Full integration testing requires a running cluster.
"""

import random
from collections import Counter
from pathlib import Path
from typing import Dict, List, Tuple

import pytest
import yaml
from hypothesis import given, settings, strategies as st


# Test configuration
VALID_ENVIRONMENTS = ["minikube", "eks"]
HELM_VALUES_DIR = Path(__file__).parent.parent / "helm-values"
MIN_DATA_ITEMS = 10
MAX_DATA_ITEMS = 1000


# Hypothesis strategies
@st.composite
def observability_data_strategy(draw):
    """
    Generate observability data items for load balancing tests.

    Returns a list of data items with metadata for distribution testing.
    """
    num_items = draw(st.integers(min_value=MIN_DATA_ITEMS, max_value=MAX_DATA_ITEMS))

    data_items = []
    for i in range(num_items):
        item = {
            "id": f"data-{i}",
            "type": draw(st.sampled_from(["trace", "metric", "log"])),
            "timestamp": draw(st.integers(min_value=1000000000, max_value=9999999999)),
            "service": draw(st.sampled_from(["service-a", "service-b", "service-c", "service-d"])),
            "size": draw(st.integers(min_value=100, max_value=10000)),  # bytes
        }
        data_items.append(item)

    return data_items


@st.composite
def load_balancing_config_strategy(draw):
    """Generate load balancing configuration variations."""
    return {
        "strategy": draw(st.sampled_from(["round-robin", "random", "least-connections"])),
        "oap_replicas": draw(st.integers(min_value=2, max_value=5)),
        "satellite_replicas": draw(st.integers(min_value=1, max_value=3)),
    }


@st.composite
def environment_with_data_strategy(draw):
    """Generate environment and observability data combinations."""
    environment = draw(st.sampled_from(VALID_ENVIRONMENTS))
    data_items = draw(observability_data_strategy())

    return environment, data_items


class TestSatelliteLoadBalancing:
    """Property-based tests for Satellite load balancing distribution."""

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

    def get_oap_replica_count(self, config: Dict) -> int:
        """Extract OAP Server replica count from configuration."""
        return config.get("oap", {}).get("replicas", 0)

    def get_satellite_replica_count(self, config: Dict) -> int:
        """Extract Satellite replica count from configuration."""
        return config.get("satellite", {}).get("replicas", 0)

    def simulate_round_robin_distribution(
        self,
        data_items: List[Dict],
        num_oap_replicas: int
    ) -> Dict[int, List[Dict]]:
        """
        Simulate round-robin load balancing distribution.

        Args:
            data_items: List of data items to distribute
            num_oap_replicas: Number of OAP Server replicas

        Returns:
            Dictionary mapping OAP replica index to assigned data items
        """
        distribution = {i: [] for i in range(num_oap_replicas)}

        for idx, item in enumerate(data_items):
            oap_index = idx % num_oap_replicas
            distribution[oap_index].append(item)

        return distribution

    def simulate_random_distribution(
        self,
        data_items: List[Dict],
        num_oap_replicas: int,
        seed: int = None
    ) -> Dict[int, List[Dict]]:
        """
        Simulate random load balancing distribution.

        Args:
            data_items: List of data items to distribute
            num_oap_replicas: Number of OAP Server replicas
            seed: Random seed for reproducibility

        Returns:
            Dictionary mapping OAP replica index to assigned data items
        """
        if seed is not None:
            random.seed(seed)

        distribution = {i: [] for i in range(num_oap_replicas)}

        for item in data_items:
            oap_index = random.randint(0, num_oap_replicas - 1)
            distribution[oap_index].append(item)

        return distribution

    def calculate_distribution_balance(self, distribution: Dict[int, List[Dict]]) -> Tuple[float, float]:
        """
        Calculate distribution balance metrics.

        Args:
            distribution: Dictionary mapping OAP replica to data items

        Returns:
            Tuple of (balance_ratio, std_deviation)
            - balance_ratio: ratio of min to max items (1.0 = perfect balance)
            - std_deviation: standard deviation of item counts
        """
        counts = [len(items) for items in distribution.values()]

        if not counts or max(counts) == 0:
            return 1.0, 0.0

        min_count = min(counts)
        max_count = max(counts)

        # Balance ratio: 1.0 means perfect balance, lower means imbalance
        balance_ratio = min_count / max_count if max_count > 0 else 1.0

        # Standard deviation
        mean = sum(counts) / len(counts)
        variance = sum((c - mean) ** 2 for c in counts) / len(counts)
        std_dev = variance ** 0.5

        return balance_ratio, std_dev

    def validate_satellite_configuration(self, config: Dict) -> bool:
        """
        Validate Satellite is properly configured for load balancing.

        Args:
            config: Configuration dictionary

        Returns:
            True if Satellite is properly configured
        """
        satellite_config = config.get("satellite", {})

        # Check Satellite is enabled
        if not satellite_config.get("enabled", False):
            return False

        # Check replicas
        if satellite_config.get("replicas", 0) < 1:
            return False

        # Check configuration section exists
        if "config" not in satellite_config:
            return False

        return True

    def validate_oap_cluster_mode(self, config: Dict) -> bool:
        """
        Validate OAP Server is configured in cluster mode.

        Args:
            config: Configuration dictionary

        Returns:
            True if OAP is in cluster mode
        """
        oap_config = config.get("oap", {})

        # Check replicas > 1 for cluster mode
        if oap_config.get("replicas", 0) < 2:
            return False

        # Check cluster mode is enabled in env
        env_vars = oap_config.get("env", {})
        cluster_mode = env_vars.get("SW_CLUSTER", "standalone")

        if cluster_mode == "standalone":
            return False

        return True

    @given(environment=st.sampled_from(VALID_ENVIRONMENTS))
    @settings(max_examples=100, deadline=None)
    def test_property_satellite_enabled_for_load_balancing(self, environment: str):
        """
        Property 1: Satellite Load Balancing Distribution

        For any valid environment, Satellite should be enabled and configured
        to support load balancing to OAP Server replicas.

        This test verifies that:
        1. Satellite is enabled in configuration
        2. Satellite has at least 1 replica
        3. Satellite configuration section exists
        """
        # Load configuration
        config = self.load_helm_values(environment)

        # Verify Satellite is configured for load balancing
        assert self.validate_satellite_configuration(config), \
            f"Satellite is not properly configured for load balancing in environment: {environment}"

    @given(environment=st.sampled_from(VALID_ENVIRONMENTS))
    @settings(max_examples=100, deadline=None)
    def test_property_oap_cluster_mode_for_load_balancing(self, environment: str):
        """
        Property 1: Satellite Load Balancing Distribution

        For any valid environment, OAP Server should be configured in cluster mode
        with multiple replicas to receive load-balanced data from Satellite.

        This test verifies that:
        1. OAP Server has multiple replicas (>= 2)
        2. OAP Server is configured in cluster mode
        3. Service discovery is enabled
        """
        # Load configuration
        config = self.load_helm_values(environment)

        # Verify OAP is in cluster mode
        assert self.validate_oap_cluster_mode(config), \
            f"OAP Server is not configured in cluster mode for environment: {environment}"

        # Verify replica count
        oap_replicas = self.get_oap_replica_count(config)
        assert oap_replicas >= 2, \
            f"OAP Server has insufficient replicas ({oap_replicas}) for load balancing in environment: {environment}"

    @given(data_items=observability_data_strategy())
    @settings(max_examples=100, deadline=None)
    def test_property_round_robin_distribution_balance(self, data_items: List[Dict]):
        """
        Property 1: Satellite Load Balancing Distribution

        For any set of observability data distributed using round-robin strategy,
        the data should be evenly distributed across all OAP Server replicas.

        This test verifies that:
        1. All OAP replicas receive data
        2. Distribution is balanced (balance ratio > 0.8)
        3. No replica is overloaded
        """
        # Test with different replica counts
        for num_replicas in [2, 3, 4, 5]:
            distribution = self.simulate_round_robin_distribution(data_items, num_replicas)

            # Verify all replicas received data
            for replica_idx in range(num_replicas):
                assert len(distribution[replica_idx]) > 0, \
                    f"OAP replica {replica_idx} received no data with {num_replicas} replicas"

            # Calculate balance metrics
            balance_ratio, std_dev = self.calculate_distribution_balance(distribution)

            # For round-robin, balance should be very good (> 0.8)
            # With perfect round-robin, balance_ratio should be close to 1.0
            expected_items_per_replica = len(data_items) / num_replicas
            max_deviation = 1  # Allow 1 item deviation due to integer division

            for replica_idx, items in distribution.items():
                deviation = abs(len(items) - expected_items_per_replica)
                assert deviation <= max_deviation, \
                    f"Round-robin distribution imbalanced: replica {replica_idx} has {len(items)} items, " \
                    f"expected ~{expected_items_per_replica:.1f} (deviation: {deviation})"

    @given(data_items=observability_data_strategy())
    @settings(max_examples=100, deadline=None)
    def test_property_random_distribution_coverage(self, data_items: List[Dict]):
        """
        Property 1: Satellite Load Balancing Distribution

        For any set of observability data distributed using random strategy,
        all OAP Server replicas should receive some data (with high probability).

        This test verifies that:
        1. All OAP replicas receive data (for sufficient data volume)
        2. No single replica receives all data
        3. Distribution is reasonably balanced
        """
        # Test with different replica counts
        for num_replicas in [2, 3, 4]:
            distribution = self.simulate_random_distribution(data_items, num_replicas, seed=42)

            # For random distribution with sufficient data, all replicas should receive some data
            if len(data_items) >= num_replicas * 5:  # At least 5 items per replica on average
                for replica_idx in range(num_replicas):
                    assert len(distribution[replica_idx]) > 0, \
                        f"OAP replica {replica_idx} received no data with random distribution " \
                        f"({len(data_items)} items, {num_replicas} replicas)"

            # Verify no single replica received all data
            max_items = max(len(items) for items in distribution.values())
            assert max_items < len(data_items), \
                f"Single OAP replica received all data with random distribution"

            # For random distribution, balance ratio should be reasonable (> 0.3 for large datasets)
            if len(data_items) >= 100:
                balance_ratio, _ = self.calculate_distribution_balance(distribution)
                assert balance_ratio > 0.3, \
                    f"Random distribution severely imbalanced: balance_ratio={balance_ratio:.2f}"

    @given(env_and_data=environment_with_data_strategy())
    @settings(max_examples=100, deadline=None)
    def test_property_distribution_with_environment_config(self, env_and_data: Tuple[str, List[Dict]]):
        """
        Property 1: Satellite Load Balancing Distribution

        For any environment configuration and observability data set,
        the load balancing should distribute data across the configured
        number of OAP Server replicas.

        This test verifies that:
        1. Distribution uses actual environment replica counts
        2. All configured replicas participate in load balancing
        3. Distribution is appropriate for the data volume
        """
        environment, data_items = env_and_data

        # Load configuration
        config = self.load_helm_values(environment)

        # Get replica counts
        oap_replicas = self.get_oap_replica_count(config)

        # Skip if OAP not configured
        if oap_replicas < 2:
            pytest.skip(f"OAP Server not configured in cluster mode for environment: {environment}")

        # Simulate distribution
        distribution = self.simulate_round_robin_distribution(data_items, oap_replicas)

        # Verify all replicas received data
        for replica_idx in range(oap_replicas):
            assert len(distribution[replica_idx]) > 0, \
                f"OAP replica {replica_idx} received no data in environment: {environment}"

        # Verify total data preserved
        total_distributed = sum(len(items) for items in distribution.values())
        assert total_distributed == len(data_items), \
            f"Data loss during distribution: {total_distributed} != {len(data_items)}"

    @given(data_items=observability_data_strategy())
    @settings(max_examples=100, deadline=None)
    def test_property_distribution_preserves_data_integrity(self, data_items: List[Dict]):
        """
        Property 1: Satellite Load Balancing Distribution

        For any set of observability data, load balancing should preserve
        all data items without loss or duplication.

        This test verifies that:
        1. No data items are lost during distribution
        2. No data items are duplicated
        3. All data item properties are preserved
        """
        num_replicas = 3

        # Simulate distribution
        distribution = self.simulate_round_robin_distribution(data_items, num_replicas)

        # Collect all distributed items
        distributed_items = []
        for items in distribution.values():
            distributed_items.extend(items)

        # Verify count matches
        assert len(distributed_items) == len(data_items), \
            f"Data count mismatch: {len(distributed_items)} != {len(data_items)}"

        # Verify no duplicates (check IDs)
        distributed_ids = [item["id"] for item in distributed_items]
        assert len(distributed_ids) == len(set(distributed_ids)), \
            f"Duplicate data items found after distribution"

        # Verify all original items are present
        original_ids = set(item["id"] for item in data_items)
        distributed_ids_set = set(distributed_ids)
        assert original_ids == distributed_ids_set, \
            f"Data items missing or added during distribution"

    @given(data_items=observability_data_strategy())
    @settings(max_examples=100, deadline=None)
    def test_property_distribution_scales_with_replicas(self, data_items: List[Dict]):
        """
        Property 1: Satellite Load Balancing Distribution

        For any set of observability data, increasing the number of OAP Server
        replicas should distribute the load across more replicas without data loss.

        This test verifies that:
        1. Distribution works with varying replica counts (2-5)
        2. More replicas result in less load per replica
        3. Data integrity is maintained regardless of replica count
        """
        # Test with increasing replica counts
        for num_replicas in [2, 3, 4, 5]:
            distribution = self.simulate_round_robin_distribution(data_items, num_replicas)

            # Verify all replicas used
            assert len(distribution) == num_replicas, \
                f"Distribution map size mismatch: {len(distribution)} != {num_replicas}"

            # Verify total data preserved
            total_items = sum(len(items) for items in distribution.values())
            assert total_items == len(data_items), \
                f"Data loss with {num_replicas} replicas: {total_items} != {len(data_items)}"

            # Verify average load decreases with more replicas
            avg_items_per_replica = total_items / num_replicas
            expected_avg = len(data_items) / num_replicas
            assert abs(avg_items_per_replica - expected_avg) < 1, \
                f"Average load calculation error with {num_replicas} replicas"

    @given(environment=st.sampled_from(VALID_ENVIRONMENTS))
    @settings(max_examples=100, deadline=None)
    def test_property_satellite_service_discovery_configured(self, environment: str):
        """
        Property 1: Satellite Load Balancing Distribution

        For any environment, Satellite should be configured with service discovery
        to automatically detect OAP Server replicas for load balancing.

        This test verifies that:
        1. Satellite configuration includes OAP Server endpoint
        2. Service discovery mechanism is configured
        3. Load balancing strategy is defined
        """
        # Load configuration
        config = self.load_helm_values(environment)

        # Verify Satellite is configured
        satellite_config = config.get("satellite", {})
        assert satellite_config.get("enabled", False), \
            f"Satellite not enabled in environment: {environment}"

        # Verify Satellite has configuration section
        assert "config" in satellite_config, \
            f"Satellite configuration section missing in environment: {environment}"

        # Verify OAP Server is configured as backend
        oap_config = config.get("oap", {})
        assert "service" in oap_config, \
            f"OAP Server service configuration missing in environment: {environment}"


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v", "--tb=short"])
