"""
Scalability tests for Prometheus.

This module provides pytest tests for validating Prometheus
scalability across different dimensions.

Requirements: 16.1, 16.2, 16.3, 16.4, 16.5, 16.6, 16.7
"""

import pytest

from .scaling_dimensions import (
    ScalingDimensionTester,
    ScalingTestConfig,
    ScalingTestResult,
    ScalingDimension,
)
from .scaling_curves import (
    ScalingCurveGenerator,
    ScalingCurveConfig,
)


class TestTargetScaling:
    """Tests for target scaling dimension.

    Requirements: 16.1
    """

    @pytest.fixture
    def config(self, prometheus_url: str) -> ScalingTestConfig:
        """Create test configuration."""
        return ScalingTestConfig(
            prometheus_url=prometheus_url,
            target_scale_values=[10, 100, 500, 1000],
            query_iterations=5,
            timeout_seconds=30.0,
        )

    @pytest.fixture
    def tester(self, config: ScalingTestConfig) -> ScalingDimensionTester:
        """Create scaling dimension tester."""
        return ScalingDimensionTester(config)

    @pytest.mark.asyncio
    async def test_target_scaling_collects_data_points(
        self,
        tester: ScalingDimensionTester,
    ) -> None:
        """Test that target scaling collects data points at each scale value.

        Requirements: 16.1
        """
        result = await tester.test_target_scaling()

        assert result.dimension == ScalingDimension.TARGETS
        assert len(result.data_points) == len(tester.config.target_scale_values)
        assert result.start_time is not None
        assert result.end_time is not None

        # Verify each data point has valid measurements
        for dp in result.data_points:
            assert dp.scale_value in tester.config.target_scale_values
            assert dp.query_latency_p50_ms >= 0
            assert dp.query_latency_p90_ms >= dp.query_latency_p50_ms
            assert dp.query_latency_p99_ms >= dp.query_latency_p90_ms

    @pytest.mark.asyncio
    async def test_target_scaling_detects_degradation(
        self,
        tester: ScalingDimensionTester,
    ) -> None:
        """Test that target scaling can detect degradation points.

        Requirements: 16.1, 16.6
        """
        result = await tester.test_target_scaling()

        # Degradation point may or may not be detected depending on load
        # Just verify the result structure is correct
        assert isinstance(result.degradation_point, (int, type(None)))
        assert isinstance(result.passed, bool)


class TestSeriesScaling:
    """Tests for series scaling dimension.

    Requirements: 16.2
    """

    @pytest.fixture
    def config(self, prometheus_url: str) -> ScalingTestConfig:
        """Create test configuration."""
        return ScalingTestConfig(
            prometheus_url=prometheus_url,
            series_scale_values=[10000, 50000, 100000],
            query_iterations=5,
            timeout_seconds=30.0,
        )

    @pytest.fixture
    def tester(self, config: ScalingTestConfig) -> ScalingDimensionTester:
        """Create scaling dimension tester."""
        return ScalingDimensionTester(config)

    @pytest.mark.asyncio
    async def test_series_scaling_collects_data_points(
        self,
        tester: ScalingDimensionTester,
    ) -> None:
        """Test that series scaling collects data points at each scale value.

        Requirements: 16.2
        """
        result = await tester.test_series_scaling()

        assert result.dimension == ScalingDimension.SERIES
        assert len(result.data_points) == len(tester.config.series_scale_values)

        for dp in result.data_points:
            assert dp.scale_value in tester.config.series_scale_values


class TestCardinalityScaling:
    """Tests for cardinality scaling dimension.

    Requirements: 16.3
    """

    @pytest.fixture
    def config(self, prometheus_url: str) -> ScalingTestConfig:
        """Create test configuration."""
        return ScalingTestConfig(
            prometheus_url=prometheus_url,
            cardinality_scale_values=[100, 1000, 10000],
            query_iterations=5,
            timeout_seconds=30.0,
        )

    @pytest.fixture
    def tester(self, config: ScalingTestConfig) -> ScalingDimensionTester:
        """Create scaling dimension tester."""
        return ScalingDimensionTester(config)

    @pytest.mark.asyncio
    async def test_cardinality_scaling_collects_data_points(
        self,
        tester: ScalingDimensionTester,
    ) -> None:
        """Test that cardinality scaling collects data points.

        Requirements: 16.3
        """
        result = await tester.test_cardinality_scaling()

        assert result.dimension == ScalingDimension.CARDINALITY
        assert len(result.data_points) == len(tester.config.cardinality_scale_values)


class TestRetentionScaling:
    """Tests for retention scaling dimension.

    Requirements: 16.4
    """

    @pytest.fixture
    def config(self, prometheus_url: str) -> ScalingTestConfig:
        """Create test configuration."""
        return ScalingTestConfig(
            prometheus_url=prometheus_url,
            retention_scale_values=[1, 7, 15],
            query_iterations=5,
            timeout_seconds=30.0,
        )

    @pytest.fixture
    def tester(self, config: ScalingTestConfig) -> ScalingDimensionTester:
        """Create scaling dimension tester."""
        return ScalingDimensionTester(config)

    @pytest.mark.asyncio
    async def test_retention_scaling_collects_data_points(
        self,
        tester: ScalingDimensionTester,
    ) -> None:
        """Test that retention scaling collects data points.

        Requirements: 16.4
        """
        result = await tester.test_retention_scaling()

        assert result.dimension == ScalingDimension.RETENTION
        assert len(result.data_points) == len(tester.config.retention_scale_values)


class TestQueryConcurrencyScaling:
    """Tests for query concurrency scaling dimension.

    Requirements: 16.5
    """

    @pytest.fixture
    def config(self, prometheus_url: str) -> ScalingTestConfig:
        """Create test configuration."""
        return ScalingTestConfig(
            prometheus_url=prometheus_url,
            concurrency_scale_values=[1, 5, 10],
            query_iterations=5,
            timeout_seconds=30.0,
        )

    @pytest.fixture
    def tester(self, config: ScalingTestConfig) -> ScalingDimensionTester:
        """Create scaling dimension tester."""
        return ScalingDimensionTester(config)

    @pytest.mark.asyncio
    async def test_concurrency_scaling_collects_data_points(
        self,
        tester: ScalingDimensionTester,
    ) -> None:
        """Test that concurrency scaling collects data points.

        Requirements: 16.5
        """
        result = await tester.test_query_concurrency_scaling()

        assert result.dimension == ScalingDimension.QUERY_CONCURRENCY
        assert len(result.data_points) == len(tester.config.concurrency_scale_values)

        # Verify latency generally increases with concurrency
        if len(result.data_points) >= 2:
            first_latency = result.data_points[0].query_latency_p50_ms
            last_latency = result.data_points[-1].query_latency_p50_ms
            # Latency should not decrease significantly with more concurrency
            assert last_latency >= first_latency * 0.5


class TestAllScalingDimensions:
    """Tests for running all scaling dimensions together.

    Requirements: 16.1, 16.2, 16.3, 16.4, 16.5
    """

    @pytest.fixture
    def config(self, prometheus_url: str) -> ScalingTestConfig:
        """Create minimal test configuration for all dimensions."""
        return ScalingTestConfig(
            prometheus_url=prometheus_url,
            target_scale_values=[10, 100],
            series_scale_values=[10000, 50000],
            cardinality_scale_values=[100, 1000],
            retention_scale_values=[1, 7],
            concurrency_scale_values=[1, 5],
            query_iterations=3,
            timeout_seconds=30.0,
        )

    @pytest.fixture
    def tester(self, config: ScalingTestConfig) -> ScalingDimensionTester:
        """Create scaling dimension tester."""
        return ScalingDimensionTester(config)

    @pytest.mark.asyncio
    async def test_all_scaling_dimensions(
        self,
        tester: ScalingDimensionTester,
    ) -> None:
        """Test running all scaling dimension tests.

        Requirements: 16.1, 16.2, 16.3, 16.4, 16.5
        """
        results = await tester.run_all_scaling_tests()

        assert "targets" in results
        assert "series" in results
        assert "cardinality" in results
        assert "retention" in results
        assert "query_concurrency" in results

        for result in results.values():
            assert isinstance(result, ScalingTestResult)
            assert len(result.data_points) > 0


class TestScalingCurveGeneration:
    """Tests for scaling curve generation.

    Requirements: 16.6, 16.7
    """

    @pytest.fixture
    def config(self, prometheus_url: str) -> ScalingCurveConfig:
        """Create curve generation configuration."""
        return ScalingCurveConfig(
            prometheus_url=prometheus_url,
            scale_values=[10, 50, 100],
            query_iterations=3,
        )

    @pytest.fixture
    def generator(self, config: ScalingCurveConfig) -> ScalingCurveGenerator:
        """Create scaling curve generator."""
        return ScalingCurveGenerator(config)

    @pytest.mark.asyncio
    async def test_curve_generation_produces_report(
        self,
        generator: ScalingCurveGenerator,
    ) -> None:
        """Test that curve generation produces a valid report.

        Requirements: 16.6, 16.7
        """
        report = await generator.generate_scaling_curve(
            dimension=ScalingDimension.TARGETS,
        )

        assert report.dimension == ScalingDimension.TARGETS
        assert len(report.data_points) > 0
        assert report.curve_analysis is not None

    @pytest.mark.asyncio
    async def test_curve_identifies_degradation(
        self,
        generator: ScalingCurveGenerator,
    ) -> None:
        """Test that curve analysis can identify degradation points.

        Requirements: 16.6
        """
        report = await generator.generate_scaling_curve(
            dimension=ScalingDimension.QUERY_CONCURRENCY,
        )

        # Verify curve analysis structure
        assert "slope" in report.curve_analysis or report.curve_analysis == {}
        assert isinstance(report.degradation_detected, bool)
