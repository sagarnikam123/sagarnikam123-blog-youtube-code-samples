"""
Endurance tests for monolithic and distributed Prometheus deployments.

This module implements endurance tests that run against both monolithic
and distributed Prometheus deployment modes to compare stability
characteristics.

Requirements: 18.8
"""

import asyncio
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Optional

from .config import SoakTestConfig, StabilityMonitorConfig
from .k6_soak import K6SoakConfig, K6SoakResult, K6SoakRunner
from .models import StabilityMetrics, StabilityStatus
from .stability_monitor import StabilityMonitor, StabilityMonitorResult
from .test_soak import SoakTestResult, SoakTester


class DeploymentMode(Enum):
    """Prometheus deployment mode."""

    MONOLITHIC = "monolithic"
    DISTRIBUTED = "distributed"


@dataclass
class DeploymentEnduranceConfig:
    """
    Configuration for deployment-specific endurance tests.

    Requirements: 18.8

    Attributes:
        prometheus_url: URL of the Prometheus instance
        deployment_mode: Monolithic or distributed deployment
        duration_hours: Test duration in hours
        vus: Number of virtual users for k6 tests
        use_k6: Whether to use k6 for load generation
        measurement_interval_seconds: Interval between measurements
        memory_growth_threshold_percent_per_hour: Max memory growth rate
        latency_degradation_threshold_percent: Max latency increase
    """

    prometheus_url: str = "http://localhost:9090"
    deployment_mode: DeploymentMode = DeploymentMode.MONOLITHIC
    duration_hours: float = 24.0
    vus: int = 50
    use_k6: bool = True
    measurement_interval_seconds: int = 300
    memory_growth_threshold_percent_per_hour: float = 1.0
    latency_degradation_threshold_percent: float = 20.0


@dataclass
class DeploymentEnduranceResult:
    """
    Result of deployment-specific endurance test.

    Requirements: 18.8

    Attributes:
        config: Test configuration
        deployment_mode: The deployment mode tested
        start_time: When the test started
        end_time: When the test ended
        soak_result: Result from soak test (if run)
        k6_result: Result from k6 test (if run)
        stability_result: Result from stability monitoring
        stability_metrics: Aggregated stability metrics
        status: Overall stability status
        passed: Whether the test passed
        error_messages: Any error messages
    """

    config: Optional[DeploymentEnduranceConfig] = None
    deployment_mode: DeploymentMode = DeploymentMode.MONOLITHIC
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    soak_result: Optional[SoakTestResult] = None
    k6_result: Optional[K6SoakResult] = None
    stability_result: Optional[StabilityMonitorResult] = None
    stability_metrics: StabilityMetrics = field(default_factory=StabilityMetrics)
    status: StabilityStatus = StabilityStatus.STABLE
    passed: bool = True
    error_messages: list[str] = field(default_factory=list)

    @property
    def duration_hours(self) -> float:
        """Total test duration in hours."""
        if self.start_time and self.end_time:
            return (self.end_time - self.start_time).total_seconds() / 3600.0
        return 0.0

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "deployment_mode": self.deployment_mode.value,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "duration_hours": round(self.duration_hours, 2),
            "stability_metrics": self.stability_metrics.to_dict(),
            "status": self.status.value,
            "passed": self.passed,
            "error_messages": self.error_messages,
            "soak_result": self.soak_result.to_dict() if self.soak_result else None,
            "k6_result": self.k6_result.to_dict() if self.k6_result else None,
            "stability_result": (
                self.stability_result.to_dict() if self.stability_result else None
            ),
        }


@dataclass
class ComparisonResult:
    """
    Result of comparing monolithic vs distributed endurance tests.

    Requirements: 18.8

    Attributes:
        monolithic_result: Result from monolithic deployment test
        distributed_result: Result from distributed deployment test
        comparison_metrics: Comparison metrics between modes
        recommendation: Recommendation based on comparison
    """

    monolithic_result: Optional[DeploymentEnduranceResult] = None
    distributed_result: Optional[DeploymentEnduranceResult] = None
    comparison_metrics: dict[str, Any] = field(default_factory=dict)
    recommendation: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "monolithic": (
                self.monolithic_result.to_dict()
                if self.monolithic_result
                else None
            ),
            "distributed": (
                self.distributed_result.to_dict()
                if self.distributed_result
                else None
            ),
            "comparison_metrics": self.comparison_metrics,
            "recommendation": self.recommendation,
        }


class DeploymentEnduranceTester:
    """
    Runs endurance tests against specific deployment modes.

    This class executes endurance tests against either monolithic or
    distributed Prometheus deployments and collects stability metrics.

    Requirements: 18.8
    """

    def __init__(self, config: DeploymentEnduranceConfig):
        """Initialize the deployment endurance tester.

        Args:
            config: Test configuration
        """
        self.config = config

    async def _run_soak_test(self) -> SoakTestResult:
        """Run Python-based soak test.

        Returns:
            SoakTestResult with test results
        """
        soak_config = SoakTestConfig(
            prometheus_url=self.config.prometheus_url,
            duration_seconds=int(self.config.duration_hours * 3600),
            measurement_interval_seconds=self.config.measurement_interval_seconds,
            memory_growth_threshold_percent_per_hour=(
                self.config.memory_growth_threshold_percent_per_hour
            ),
        )
        tester = SoakTester(soak_config)
        return await tester.run()

    def _run_k6_test(self) -> K6SoakResult:
        """Run k6-based soak test.

        Returns:
            K6SoakResult with test results
        """
        k6_config = K6SoakConfig(
            prometheus_url=self.config.prometheus_url,
            vus=self.config.vus,
            duration=f"{int(self.config.duration_hours)}h",
        )
        runner = K6SoakRunner(k6_config)
        return runner.run()

    async def _run_stability_monitoring(
        self,
        duration_seconds: int,
    ) -> StabilityMonitorResult:
        """Run stability monitoring.

        Args:
            duration_seconds: Duration to monitor

        Returns:
            StabilityMonitorResult with monitoring results
        """
        stability_config = StabilityMonitorConfig(
            prometheus_url=self.config.prometheus_url,
            latency_degradation_threshold_percent=(
                self.config.latency_degradation_threshold_percent
            ),
        )
        monitor = StabilityMonitor(stability_config)
        return await monitor.run(duration_seconds)

    async def run(self) -> DeploymentEnduranceResult:
        """Run the deployment-specific endurance test.

        Requirements: 18.8

        Returns:
            DeploymentEnduranceResult with test results
        """
        result = DeploymentEnduranceResult(
            config=self.config,
            deployment_mode=self.config.deployment_mode,
        )
        result.start_time = datetime.utcnow()

        try:
            # Run k6 test if enabled
            if self.config.use_k6:
                result.k6_result = self._run_k6_test()
                if not result.k6_result.passed:
                    result.error_messages.append("k6 soak test failed")

            # Run Python soak test
            result.soak_result = await self._run_soak_test()
            if not result.soak_result.passed:
                result.error_messages.append("Soak test failed")

            # Aggregate stability metrics
            if result.soak_result:
                result.stability_metrics = result.soak_result.stability_metrics
                result.status = result.soak_result.status

            # Determine overall pass/fail
            result.passed = (
                (result.soak_result is None or result.soak_result.passed)
                and (result.k6_result is None or result.k6_result.passed)
            )

        except Exception as e:
            result.passed = False
            result.status = StabilityStatus.FAILED
            result.error_messages.append(str(e))

        result.end_time = datetime.utcnow()
        return result


class MonolithicDistributedComparator:
    """
    Compares endurance test results between deployment modes.

    This class runs endurance tests against both monolithic and distributed
    Prometheus deployments and compares their stability characteristics.

    Requirements: 18.8
    """

    def __init__(
        self,
        monolithic_url: str = "http://localhost:9090",
        distributed_url: str = "http://localhost:9091",
        duration_hours: float = 24.0,
        vus: int = 50,
    ):
        """Initialize the comparator.

        Args:
            monolithic_url: URL of monolithic Prometheus
            distributed_url: URL of distributed Prometheus
            duration_hours: Test duration in hours
            vus: Number of virtual users for k6 tests
        """
        self.monolithic_url = monolithic_url
        self.distributed_url = distributed_url
        self.duration_hours = duration_hours
        self.vus = vus

    async def run_monolithic_test(self) -> DeploymentEnduranceResult:
        """Run endurance test against monolithic deployment.

        Returns:
            DeploymentEnduranceResult for monolithic deployment
        """
        config = DeploymentEnduranceConfig(
            prometheus_url=self.monolithic_url,
            deployment_mode=DeploymentMode.MONOLITHIC,
            duration_hours=self.duration_hours,
            vus=self.vus,
        )
        tester = DeploymentEnduranceTester(config)
        return await tester.run()

    async def run_distributed_test(self) -> DeploymentEnduranceResult:
        """Run endurance test against distributed deployment.

        Returns:
            DeploymentEnduranceResult for distributed deployment
        """
        config = DeploymentEnduranceConfig(
            prometheus_url=self.distributed_url,
            deployment_mode=DeploymentMode.DISTRIBUTED,
            duration_hours=self.duration_hours,
            vus=self.vus,
        )
        tester = DeploymentEnduranceTester(config)
        return await tester.run()

    def _compare_results(
        self,
        monolithic: DeploymentEnduranceResult,
        distributed: DeploymentEnduranceResult,
    ) -> dict[str, Any]:
        """Compare results between deployment modes.

        Args:
            monolithic: Monolithic deployment result
            distributed: Distributed deployment result

        Returns:
            Dictionary of comparison metrics
        """
        comparison = {}

        # Compare stability scores
        mono_score = monolithic.stability_metrics.overall_stability_score
        dist_score = distributed.stability_metrics.overall_stability_score
        comparison["stability_score_difference"] = dist_score - mono_score

        # Compare memory growth rates
        mono_mem = monolithic.stability_metrics.memory_growth_rate_bytes_per_hour
        dist_mem = distributed.stability_metrics.memory_growth_rate_bytes_per_hour
        comparison["memory_growth_difference_bytes_per_hour"] = dist_mem - mono_mem

        # Compare latency trends
        mono_lat = monolithic.stability_metrics.latency_trend_percent_per_hour
        dist_lat = distributed.stability_metrics.latency_trend_percent_per_hour
        comparison["latency_trend_difference_percent_per_hour"] = dist_lat - mono_lat

        # Compare degradation counts
        mono_deg = monolithic.stability_metrics.degradation_count
        dist_deg = distributed.stability_metrics.degradation_count
        comparison["degradation_count_difference"] = dist_deg - mono_deg

        # Compare compaction success rates
        mono_compact = monolithic.stability_metrics.compaction_success_rate
        dist_compact = distributed.stability_metrics.compaction_success_rate
        comparison["compaction_success_rate_difference"] = dist_compact - mono_compact

        return comparison

    def _generate_recommendation(
        self,
        comparison: dict[str, Any],
        monolithic: DeploymentEnduranceResult,
        distributed: DeploymentEnduranceResult,
    ) -> str:
        """Generate recommendation based on comparison.

        Args:
            comparison: Comparison metrics
            monolithic: Monolithic deployment result
            distributed: Distributed deployment result

        Returns:
            Recommendation string
        """
        recommendations = []

        # Check stability scores
        score_diff = comparison.get("stability_score_difference", 0)
        if score_diff > 10:
            recommendations.append(
                "Distributed deployment shows better stability "
                f"(+{score_diff:.1f} points)"
            )
        elif score_diff < -10:
            recommendations.append(
                "Monolithic deployment shows better stability "
                f"({score_diff:.1f} points)"
            )
        else:
            recommendations.append("Both deployments show similar stability")

        # Check memory growth
        mem_diff = comparison.get("memory_growth_difference_bytes_per_hour", 0)
        if abs(mem_diff) > 10_000_000:  # 10MB/hour difference
            if mem_diff > 0:
                recommendations.append(
                    "Monolithic has lower memory growth rate"
                )
            else:
                recommendations.append(
                    "Distributed has lower memory growth rate"
                )

        # Check degradation events
        deg_diff = comparison.get("degradation_count_difference", 0)
        if deg_diff > 2:
            recommendations.append(
                "Monolithic shows fewer degradation events"
            )
        elif deg_diff < -2:
            recommendations.append(
                "Distributed shows fewer degradation events"
            )

        # Overall recommendation
        if monolithic.passed and not distributed.passed:
            recommendations.append(
                "RECOMMENDATION: Use monolithic deployment for this workload"
            )
        elif distributed.passed and not monolithic.passed:
            recommendations.append(
                "RECOMMENDATION: Use distributed deployment for this workload"
            )
        elif score_diff > 5:
            recommendations.append(
                "RECOMMENDATION: Consider distributed deployment for better stability"
            )
        elif score_diff < -5:
            recommendations.append(
                "RECOMMENDATION: Monolithic deployment is sufficient for this workload"
            )
        else:
            recommendations.append(
                "RECOMMENDATION: Either deployment mode is suitable"
            )

        return "; ".join(recommendations)

    async def compare(self) -> ComparisonResult:
        """Run comparison between monolithic and distributed deployments.

        Requirements: 18.8

        Returns:
            ComparisonResult with comparison data
        """
        result = ComparisonResult()

        # Run tests sequentially to avoid resource contention
        result.monolithic_result = await self.run_monolithic_test()
        result.distributed_result = await self.run_distributed_test()

        # Compare results
        if result.monolithic_result and result.distributed_result:
            result.comparison_metrics = self._compare_results(
                result.monolithic_result,
                result.distributed_result,
            )
            result.recommendation = self._generate_recommendation(
                result.comparison_metrics,
                result.monolithic_result,
                result.distributed_result,
            )

        return result


def run_deployment_endurance_test_sync(
    prometheus_url: str = "http://localhost:9090",
    deployment_mode: str = "monolithic",
    duration_hours: float = 24.0,
    vus: int = 50,
) -> DeploymentEnduranceResult:
    """Synchronous wrapper for running deployment endurance test.

    Args:
        prometheus_url: URL of the Prometheus instance
        deployment_mode: "monolithic" or "distributed"
        duration_hours: Test duration in hours
        vus: Number of virtual users for k6 tests

    Returns:
        DeploymentEnduranceResult
    """
    mode = (
        DeploymentMode.DISTRIBUTED
        if deployment_mode == "distributed"
        else DeploymentMode.MONOLITHIC
    )
    config = DeploymentEnduranceConfig(
        prometheus_url=prometheus_url,
        deployment_mode=mode,
        duration_hours=duration_hours,
        vus=vus,
    )
    tester = DeploymentEnduranceTester(config)
    return asyncio.run(tester.run())


def run_comparison_sync(
    monolithic_url: str = "http://localhost:9090",
    distributed_url: str = "http://localhost:9091",
    duration_hours: float = 24.0,
    vus: int = 50,
) -> ComparisonResult:
    """Synchronous wrapper for running deployment comparison.

    Args:
        monolithic_url: URL of monolithic Prometheus
        distributed_url: URL of distributed Prometheus
        duration_hours: Test duration in hours
        vus: Number of virtual users for k6 tests

    Returns:
        ComparisonResult
    """
    comparator = MonolithicDistributedComparator(
        monolithic_url=monolithic_url,
        distributed_url=distributed_url,
        duration_hours=duration_hours,
        vus=vus,
    )
    return asyncio.run(comparator.compare())
