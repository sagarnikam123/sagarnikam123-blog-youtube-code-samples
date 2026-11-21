"""
Report generation for Prometheus load tests.

This module provides functionality to generate reports from load test
results including latency percentiles and throughput metrics.

Requirements: 14.7
"""

import json
import sys
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

# Add parent directory to path for hyphenated package import
_current_dir = Path(__file__).parent
sys.path.insert(0, str(_current_dir))

from generator import LoadGeneratorStats
from metrics import LoadTestMetrics


@dataclass
class LoadTestReport:
    """Complete load test report.

    Attributes:
        test_name: Name of the load test
        start_time: When the test started
        end_time: When the test ended
        config: Test configuration used
        generator_stats: Statistics from load generation
        metrics: Collected metrics during the test
        thresholds: Pass/fail thresholds
        passed: Whether the test passed all thresholds
        failures: List of threshold failures
    """

    test_name: str = "load_test"
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    config: dict[str, Any] = field(default_factory=dict)
    generator_stats: Optional[LoadGeneratorStats] = None
    metrics: Optional[LoadTestMetrics] = None
    thresholds: dict[str, Any] = field(default_factory=dict)
    passed: bool = True
    failures: list[str] = field(default_factory=list)

    @property
    def duration_seconds(self) -> float:
        """Calculate test duration in seconds."""
        if self.start_time and self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return 0.0

    def to_dict(self) -> dict[str, Any]:
        """Convert report to dictionary."""
        return {
            "metadata": {
                "test_name": self.test_name,
                "start_time": (
                    self.start_time.isoformat() if self.start_time else None
                ),
                "end_time": self.end_time.isoformat() if self.end_time else None,
                "duration_seconds": self.duration_seconds,
            },
            "config": self.config,
            "generator_stats": (
                self.generator_stats.to_dict() if self.generator_stats else {}
            ),
            "metrics": self.metrics.to_dict() if self.metrics else {},
            "thresholds": self.thresholds,
            "summary": {
                "passed": self.passed,
                "failures": self.failures,
            },
        }


class LoadTestReporter:
    """
    Generates reports from load test results.

    This class creates comprehensive reports including latency
    percentiles and throughput metrics in various formats.

    Requirements: 14.7
    """

    def __init__(
        self,
        thresholds: Optional[dict[str, Any]] = None,
    ):
        """Initialize the reporter.

        Args:
            thresholds: Pass/fail thresholds for metrics
        """
        self.thresholds = thresholds or self._default_thresholds()

    def _default_thresholds(self) -> dict[str, Any]:
        """Get default thresholds."""
        return {
            "query_latency_p99_ms": 500,
            "scrape_success_rate_percent": 99.0,
            "cpu_utilization_percent": 80,
            "memory_utilization_percent": 85,
        }

    def evaluate_thresholds(
        self,
        metrics: LoadTestMetrics,
    ) -> tuple[bool, list[str]]:
        """Evaluate metrics against thresholds.

        Args:
            metrics: Collected metrics to evaluate

        Returns:
            Tuple of (passed, list of failure messages)
        """
        failures = []

        # Check query latency p99
        if metrics.query_latency.p99 > self.thresholds.get(
            "query_latency_p99_ms", 500
        ):
            failures.append(
                f"Query latency p99 ({metrics.query_latency.p99:.2f}ms) "
                f"exceeds threshold ({self.thresholds['query_latency_p99_ms']}ms)"
            )

        # Check scrape success rate
        if metrics.scrape_metrics.success_rate < self.thresholds.get(
            "scrape_success_rate_percent", 99.0
        ):
            failures.append(
                f"Scrape success rate ({metrics.scrape_metrics.success_rate:.2f}%) "
                f"below threshold ({self.thresholds['scrape_success_rate_percent']}%)"
            )

        # Check CPU utilization
        if metrics.resource_metrics.cpu_avg > self.thresholds.get(
            "cpu_utilization_percent", 80
        ):
            failures.append(
                f"CPU utilization ({metrics.resource_metrics.cpu_avg:.2f}%) "
                f"exceeds threshold ({self.thresholds['cpu_utilization_percent']}%)"
            )

        return len(failures) == 0, failures

    def generate_report(
        self,
        test_name: str,
        config: dict[str, Any],
        generator_stats: LoadGeneratorStats,
        metrics: LoadTestMetrics,
    ) -> LoadTestReport:
        """Generate a complete load test report.

        Args:
            test_name: Name of the test
            config: Test configuration
            generator_stats: Statistics from load generation
            metrics: Collected metrics

        Returns:
            Complete load test report
        """
        passed, failures = self.evaluate_thresholds(metrics)

        return LoadTestReport(
            test_name=test_name,
            start_time=generator_stats.start_time,
            end_time=generator_stats.end_time,
            config=config,
            generator_stats=generator_stats,
            metrics=metrics,
            thresholds=self.thresholds,
            passed=passed,
            failures=failures,
        )

    def generate_latency_report(
        self,
        metrics: LoadTestMetrics,
    ) -> dict[str, Any]:
        """Generate a focused latency percentile report.

        Args:
            metrics: Collected metrics

        Returns:
            Latency report dictionary
        """
        return {
            "latency_percentiles": {
                "p50_ms": round(metrics.query_latency.p50, 2),
                "p90_ms": round(metrics.query_latency.p90, 2),
                "p99_ms": round(metrics.query_latency.p99, 2),
            },
            "latency_stats": {
                "min_ms": round(metrics.query_latency.min_latency, 2),
                "max_ms": round(metrics.query_latency.max_latency, 2),
                "avg_ms": round(metrics.query_latency.avg_latency, 2),
            },
            "sample_count": len(metrics.query_latency.samples),
            "threshold_p99_ms": self.thresholds.get("query_latency_p99_ms", 500),
            "passed": metrics.query_latency.p99 <= self.thresholds.get(
                "query_latency_p99_ms", 500
            ),
        }

    def generate_throughput_report(
        self,
        generator_stats: LoadGeneratorStats,
        metrics: LoadTestMetrics,
    ) -> dict[str, Any]:
        """Generate a focused throughput metrics report.

        Args:
            generator_stats: Statistics from load generation
            metrics: Collected metrics

        Returns:
            Throughput report dictionary
        """
        return {
            "samples_generated": generator_stats.total_samples_generated,
            "samples_per_second": round(generator_stats.samples_per_second, 2),
            "requests_sent": generator_stats.total_requests_sent,
            "successful_requests": generator_stats.successful_requests,
            "failed_requests": generator_stats.failed_requests,
            "request_success_rate": (
                round(
                    (
                        generator_stats.successful_requests
                        / max(1, generator_stats.total_requests_sent)
                    )
                    * 100,
                    2,
                )
            ),
            "scrape_success_rate": round(metrics.scrape_metrics.success_rate, 2),
            "avg_scrape_duration_seconds": round(
                metrics.scrape_metrics.avg_duration, 4
            ),
        }

    def to_json(self, report: LoadTestReport, indent: int = 2) -> str:
        """Convert report to JSON string.

        Args:
            report: Load test report
            indent: JSON indentation

        Returns:
            JSON string representation
        """
        return json.dumps(report.to_dict(), indent=indent, default=str)

    def to_markdown(self, report: LoadTestReport) -> str:
        """Convert report to Markdown format.

        Args:
            report: Load test report

        Returns:
            Markdown string representation
        """
        lines = [
            f"# Load Test Report: {report.test_name}",
            "",
            "## Summary",
            "",
            f"- **Status**: {'✅ PASSED' if report.passed else '❌ FAILED'}",
            f"- **Duration**: {report.duration_seconds:.2f} seconds",
            f"- **Start Time**: {report.start_time}",
            f"- **End Time**: {report.end_time}",
            "",
        ]

        if report.failures:
            lines.extend([
                "### Failures",
                "",
            ])
            for failure in report.failures:
                lines.append(f"- {failure}")
            lines.append("")

        if report.generator_stats:
            lines.extend([
                "## Load Generation",
                "",
                f"- **Targets**: {report.generator_stats.total_targets}",
                f"- **Series**: {report.generator_stats.total_series}",
                f"- **Samples Generated**: {report.generator_stats.total_samples_generated}",
                f"- **Samples/Second**: {report.generator_stats.samples_per_second:.2f}",
                "",
            ])

        if report.metrics:
            lines.extend([
                "## Query Latency",
                "",
                "| Percentile | Latency (ms) |",
                "|------------|--------------|",
                f"| p50 | {report.metrics.query_latency.p50:.2f} |",
                f"| p90 | {report.metrics.query_latency.p90:.2f} |",
                f"| p99 | {report.metrics.query_latency.p99:.2f} |",
                "",
                "## Resource Utilization",
                "",
                f"- **CPU Avg**: {report.metrics.resource_metrics.cpu_avg:.2f}%",
                f"- **CPU Max**: {report.metrics.resource_metrics.cpu_max:.2f}%",
                f"- **Memory Avg**: {report.metrics.resource_metrics.memory_avg / 1024 / 1024:.2f} MB",
                f"- **Memory Max**: {report.metrics.resource_metrics.memory_max / 1024 / 1024:.2f} MB",
                "",
                "## Scrape Metrics",
                "",
                f"- **Success Rate**: {report.metrics.scrape_metrics.success_rate:.2f}%",
                f"- **Avg Duration**: {report.metrics.scrape_metrics.avg_duration:.4f}s",
                "",
            ])

        return "\n".join(lines)

    def save_report(
        self,
        report: LoadTestReport,
        output_dir: Path,
        formats: Optional[list[str]] = None,
    ) -> list[Path]:
        """Save report to files in specified formats.

        Args:
            report: Load test report
            output_dir: Directory to save reports
            formats: List of formats (json, markdown, csv)

        Returns:
            List of saved file paths
        """
        formats = formats or ["json", "markdown"]
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        saved_files = []
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        base_name = f"load_test_report_{timestamp}"

        if "json" in formats:
            json_path = output_dir / f"{base_name}.json"
            json_path.write_text(self.to_json(report))
            saved_files.append(json_path)

        if "markdown" in formats:
            md_path = output_dir / f"{base_name}.md"
            md_path.write_text(self.to_markdown(report))
            saved_files.append(md_path)

        if "csv" in formats:
            csv_path = output_dir / f"{base_name}.csv"
            csv_content = self._to_csv(report)
            csv_path.write_text(csv_content)
            saved_files.append(csv_path)

        return saved_files

    def _to_csv(self, report: LoadTestReport) -> str:
        """Convert report to CSV format.

        Args:
            report: Load test report

        Returns:
            CSV string representation
        """
        lines = ["metric,value"]

        if report.generator_stats:
            lines.extend([
                f"total_targets,{report.generator_stats.total_targets}",
                f"total_series,{report.generator_stats.total_series}",
                f"samples_generated,{report.generator_stats.total_samples_generated}",
                f"samples_per_second,{report.generator_stats.samples_per_second:.2f}",
            ])

        if report.metrics:
            lines.extend([
                f"query_latency_p50_ms,{report.metrics.query_latency.p50:.2f}",
                f"query_latency_p90_ms,{report.metrics.query_latency.p90:.2f}",
                f"query_latency_p99_ms,{report.metrics.query_latency.p99:.2f}",
                f"cpu_avg_percent,{report.metrics.resource_metrics.cpu_avg:.2f}",
                f"memory_avg_bytes,{report.metrics.resource_metrics.memory_avg:.0f}",
                f"scrape_success_rate,{report.metrics.scrape_metrics.success_rate:.2f}",
            ])

        lines.append(f"test_passed,{report.passed}")

        return "\n".join(lines)
