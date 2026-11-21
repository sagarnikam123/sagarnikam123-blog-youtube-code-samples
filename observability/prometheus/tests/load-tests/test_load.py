"""
Load test implementation for Prometheus.

This module provides the main load test runner that combines
load generation, metrics collection, and report generation.

Requirements: 14.1, 14.2, 14.3, 14.4, 14.5, 14.6, 14.7
"""

import asyncio
from pathlib import Path
from typing import Any, Optional

import sys
from pathlib import Path

# Add parent directory to path for hyphenated package import
_current_dir = Path(__file__).parent
sys.path.insert(0, str(_current_dir))

from generator import LoadGenerator, LoadGeneratorConfig, parse_duration
from metrics import LoadTestMetricsCollector
from reporter import LoadTestReport, LoadTestReporter


class LoadTestRunner:
    """
    Runs complete load tests against Prometheus.

    This class orchestrates load generation, metrics collection,
    and report generation for comprehensive load testing.

    Requirements: 14.1, 14.2, 14.3, 14.4, 14.5, 14.6, 14.7
    """

    def __init__(
        self,
        prometheus_url: str = "http://localhost:9090",
        thresholds: Optional[dict[str, Any]] = None,
    ):
        """Initialize the load test runner.

        Args:
            prometheus_url: URL of the Prometheus instance
            thresholds: Pass/fail thresholds for metrics
        """
        self.prometheus_url = prometheus_url
        self.thresholds = thresholds
        self.reporter = LoadTestReporter(thresholds=thresholds)

    async def run_load_test(
        self,
        num_targets: int = 100,
        num_series: int = 10000,
        duration: str = "30m",
        scrape_interval: float = 15.0,
    ) -> LoadTestReport:
        """Run a complete load test.

        Args:
            num_targets: Number of simulated scrape targets
            num_series: Number of unique time series
            duration: Test duration (e.g., "30m", "1h")
            scrape_interval: Interval between metric pushes

        Returns:
            Complete load test report
        """
        duration_seconds = parse_duration(duration)

        # Configure load generator
        generator_config = LoadGeneratorConfig(
            num_targets=num_targets,
            num_series=num_series,
            duration_seconds=duration_seconds,
            scrape_interval_seconds=scrape_interval,
            prometheus_url=self.prometheus_url,
        )

        generator = LoadGenerator(generator_config)
        metrics_collector = LoadTestMetricsCollector(
            prometheus_url=self.prometheus_url,
            collection_interval=5.0,
        )

        # Run load generation and metrics collection concurrently
        generator_task = asyncio.create_task(generator.run())
        metrics_task = asyncio.create_task(
            metrics_collector.run(duration_seconds)
        )

        # Wait for both to complete
        generator_stats, metrics = await asyncio.gather(
            generator_task,
            metrics_task,
        )

        # Generate report
        config = {
            "num_targets": num_targets,
            "num_series": num_series,
            "duration": duration,
            "scrape_interval": scrape_interval,
            "prometheus_url": self.prometheus_url,
        }

        report = self.reporter.generate_report(
            test_name=f"load_test_{num_targets}t_{num_series}s",
            config=config,
            generator_stats=generator_stats,
            metrics=metrics,
        )

        return report

    async def run_scaling_test(
        self,
        target_levels: Optional[list[int]] = None,
        series_levels: Optional[list[int]] = None,
        duration_per_level: str = "5m",
    ) -> list[LoadTestReport]:
        """Run scaling tests at multiple load levels.

        Args:
            target_levels: List of target counts to test
            series_levels: List of series counts to test
            duration_per_level: Duration for each level

        Returns:
            List of reports for each level
        """
        target_levels = target_levels or [100, 1000, 10000]
        series_levels = series_levels or [10000, 100000, 1000000]

        reports = []

        for targets, series in zip(target_levels, series_levels):
            report = await self.run_load_test(
                num_targets=targets,
                num_series=series,
                duration=duration_per_level,
            )
            reports.append(report)

        return reports


def run_load_test_sync(
    prometheus_url: str = "http://localhost:9090",
    num_targets: int = 100,
    num_series: int = 10000,
    duration: str = "30m",
    output_dir: Optional[str] = None,
    thresholds: Optional[dict[str, Any]] = None,
) -> LoadTestReport:
    """Synchronous wrapper for running load tests.

    Args:
        prometheus_url: URL of the Prometheus instance
        num_targets: Number of simulated scrape targets
        num_series: Number of unique time series
        duration: Test duration
        output_dir: Directory to save reports
        thresholds: Pass/fail thresholds

    Returns:
        Load test report
    """
    runner = LoadTestRunner(
        prometheus_url=prometheus_url,
        thresholds=thresholds,
    )

    report = asyncio.run(
        runner.run_load_test(
            num_targets=num_targets,
            num_series=num_series,
            duration=duration,
        )
    )

    if output_dir:
        runner.reporter.save_report(
            report,
            Path(output_dir),
            formats=["json", "markdown"],
        )

    return report
