"""
Performance test runner for Prometheus.

This module provides a unified interface for running all
performance benchmarks and generating comprehensive reports.

Requirements: 15.1, 15.2, 15.3, 15.4, 15.5, 15.6, 15.7
"""

import asyncio
import json
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from .test_query_latency import (
    QueryLatencyBenchmarkRunner,
    QueryLatencyReport,
)
from .test_remote_write import (
    RemoteWriteBenchmarkRunner,
    RemoteWriteReport,
)
from .test_tsdb import (
    TSDBBenchmarkRunner,
    TSDBBenchmarkReport,
)


@dataclass
class PerformanceTestReport:
    """Comprehensive performance test report.

    Attributes:
        test_name: Name of the test suite
        prometheus_url: URL of the Prometheus instance
        start_time: When the test started
        end_time: When the test ended
        query_latency: Query latency benchmark results
        remote_write: Remote write benchmark results
        tsdb: TSDB benchmark results
        passed: Whether all benchmarks passed
        failures: List of failures
    """

    test_name: str = "performance_benchmark_suite"
    prometheus_url: str = "http://localhost:9090"
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    query_latency: Optional[QueryLatencyReport] = None
    remote_write: list[RemoteWriteReport] = field(default_factory=list)
    tsdb: Optional[TSDBBenchmarkReport] = None
    passed: bool = True
    failures: list[str] = field(default_factory=list)

    @property
    def duration_seconds(self) -> float:
        """Total test duration."""
        if self.start_time and self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return 0.0

    def check_all_passed(self) -> None:
        """Check if all benchmarks passed."""
        self.passed = True
        self.failures = []

        if self.query_latency and not self.query_latency.passed:
            self.passed = False
            self.failures.extend(self.query_latency.failures)

        for rw_report in self.remote_write:
            if not rw_report.passed:
                self.passed = False
                self.failures.extend(rw_report.failures)

        if self.tsdb and not self.tsdb.passed:
            self.passed = False
            self.failures.extend(self.tsdb.failures)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "test_name": self.test_name,
            "prometheus_url": self.prometheus_url,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "duration_seconds": round(self.duration_seconds, 2),
            "passed": self.passed,
            "failures": self.failures,
            "results": {
                "query_latency": (
                    self.query_latency.to_dict() if self.query_latency else None
                ),
                "remote_write": [r.to_dict() for r in self.remote_write],
                "tsdb": self.tsdb.to_dict() if self.tsdb else None,
            },
        }

    def to_json(self, indent: int = 2) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict(), indent=indent)

    def to_markdown(self) -> str:
        """Generate markdown report."""
        lines = [
            f"# Performance Benchmark Report: {self.test_name}",
            "",
            f"**Prometheus URL:** {self.prometheus_url}",
            f"**Start Time:** {self.start_time.isoformat() if self.start_time else 'N/A'}",
            f"**End Time:** {self.end_time.isoformat() if self.end_time else 'N/A'}",
            f"**Duration:** {self.duration_seconds:.2f} seconds",
            f"**Status:** {'✅ PASSED' if self.passed else '❌ FAILED'}",
            "",
        ]

        if self.failures:
            lines.extend([
                "## Failures",
                "",
            ])
            for failure in self.failures:
                lines.append(f"- {failure}")
            lines.append("")

        # Query Latency Results
        if self.query_latency:
            lines.extend([
                "## Query Latency Benchmarks",
                "",
            ])
            summary = self.query_latency.to_dict().get("summary", {})

            if summary.get("simple_queries"):
                sq = summary["simple_queries"]
                lines.extend([
                    "### Simple Queries",
                    f"- P50: {sq.get('p50_ms', 0):.2f}ms",
                    f"- P90: {sq.get('p90_ms', 0):.2f}ms",
                    f"- P99: {sq.get('p99_ms', 0):.2f}ms",
                    "",
                ])

            if summary.get("complex_queries"):
                cq = summary["complex_queries"]
                lines.extend([
                    "### Complex Queries",
                    f"- P50: {cq.get('p50_ms', 0):.2f}ms",
                    f"- P90: {cq.get('p90_ms', 0):.2f}ms",
                    f"- P99: {cq.get('p99_ms', 0):.2f}ms",
                    "",
                ])

            if summary.get("range_queries"):
                lines.append("### Range Queries")
                for name, metrics in summary["range_queries"].items():
                    lines.append(
                        f"- {name}: P50={metrics.get('p50_ms', 0):.2f}ms, "
                        f"P90={metrics.get('p90_ms', 0):.2f}ms, "
                        f"P99={metrics.get('p99_ms', 0):.2f}ms"
                    )
                lines.append("")

        # Remote Write Results
        if self.remote_write:
            lines.extend([
                "## Remote Write Benchmarks",
                "",
            ])
            for rw in self.remote_write:
                metrics = rw.metrics.to_dict()
                lines.extend([
                    f"### {rw.test_name}",
                    f"- Throughput: {metrics['throughput']['samples_per_sec']:.2f} samples/sec",
                    f"- Latency P99: {metrics['latency']['p99_ms']:.2f}ms",
                    f"- Success Rate: {metrics['success_rate_percent']:.2f}%",
                    "",
                ])

        # TSDB Results
        if self.tsdb:
            lines.extend([
                "## TSDB Benchmarks",
                "",
            ])
            metrics = self.tsdb.metrics.to_dict()

            comp = metrics.get("compaction", {})
            lines.extend([
                "### Compaction",
                f"- Total Compactions: {comp.get('compactions_total', 0)}",
                f"- Avg Duration: {comp.get('compaction_duration', {}).get('avg_seconds', 0):.4f}s",
                f"- Head Series: {comp.get('head_series', 0)}",
                "",
            ])

            wal = metrics.get("wal", {})
            lines.extend([
                "### WAL",
                f"- Storage Size: {wal.get('wal_storage_size_bytes', 0) / (1024*1024):.2f} MB",
                f"- Estimated Replay Time: {wal.get('estimated_replay_time_seconds', 0):.2f}s",
                f"- Corruptions: {wal.get('wal_corruptions_total', 0)}",
                "",
            ])

        return "\n".join(lines)


class PerformanceTestRunner:
    """
    Unified runner for all performance benchmarks.

    Requirements: 15.1, 15.2, 15.3, 15.4, 15.5, 15.6, 15.7
    """

    def __init__(
        self,
        prometheus_url: str = "http://localhost:9090",
        query_iterations: int = 100,
        remote_write_iterations: int = 100,
        tsdb_duration_seconds: int = 60,
        thresholds: Optional[dict[str, float]] = None,
    ):
        """Initialize the performance test runner.

        Args:
            prometheus_url: URL of the Prometheus instance
            query_iterations: Iterations for query benchmarks
            remote_write_iterations: Iterations for remote write benchmarks
            tsdb_duration_seconds: Duration for TSDB benchmarks
            thresholds: Pass/fail thresholds
        """
        self.prometheus_url = prometheus_url
        self.query_iterations = query_iterations
        self.remote_write_iterations = remote_write_iterations
        self.tsdb_duration_seconds = tsdb_duration_seconds
        self.thresholds = thresholds

    async def run_query_latency_benchmarks(self) -> QueryLatencyReport:
        """Run query latency benchmarks.

        Returns:
            Query latency report
        """
        runner = QueryLatencyBenchmarkRunner(
            prometheus_url=self.prometheus_url,
            iterations=self.query_iterations,
            thresholds=self.thresholds,
        )
        return await runner.run_all_benchmarks()

    async def run_remote_write_benchmarks(self) -> list[RemoteWriteReport]:
        """Run remote write benchmarks.

        Returns:
            List of remote write reports
        """
        runner = RemoteWriteBenchmarkRunner(
            prometheus_url=self.prometheus_url,
            iterations=self.remote_write_iterations,
        )
        return await runner.run_all_benchmarks()

    async def run_tsdb_benchmarks(self) -> TSDBBenchmarkReport:
        """Run TSDB benchmarks.

        Returns:
            TSDB benchmark report
        """
        runner = TSDBBenchmarkRunner(
            prometheus_url=self.prometheus_url,
            measurement_duration_seconds=self.tsdb_duration_seconds,
        )
        return await runner.run_all_benchmarks()

    async def run_all_benchmarks(
        self,
        include_query_latency: bool = True,
        include_remote_write: bool = True,
        include_tsdb: bool = True,
    ) -> PerformanceTestReport:
        """Run all performance benchmarks.

        Args:
            include_query_latency: Include query latency benchmarks
            include_remote_write: Include remote write benchmarks
            include_tsdb: Include TSDB benchmarks

        Returns:
            Comprehensive performance report
        """
        report = PerformanceTestReport(
            prometheus_url=self.prometheus_url,
        )
        report.start_time = datetime.utcnow()

        if include_query_latency:
            report.query_latency = await self.run_query_latency_benchmarks()

        if include_remote_write:
            report.remote_write = await self.run_remote_write_benchmarks()

        if include_tsdb:
            report.tsdb = await self.run_tsdb_benchmarks()

        report.end_time = datetime.utcnow()
        report.check_all_passed()

        return report

    def save_report(
        self,
        report: PerformanceTestReport,
        output_dir: Path,
        formats: Optional[list[str]] = None,
    ) -> list[Path]:
        """Save report to files.

        Args:
            report: Report to save
            output_dir: Output directory
            formats: List of formats (json, markdown)

        Returns:
            List of saved file paths
        """
        formats = formats or ["json", "markdown"]
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        saved_files = []
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")

        if "json" in formats:
            json_path = output_dir / f"performance_report_{timestamp}.json"
            with open(json_path, "w", encoding="utf-8") as f:
                f.write(report.to_json())
            saved_files.append(json_path)

        if "markdown" in formats:
            md_path = output_dir / f"performance_report_{timestamp}.md"
            with open(md_path, "w", encoding="utf-8") as f:
                f.write(report.to_markdown())
            saved_files.append(md_path)

        return saved_files


def run_performance_tests_sync(
    prometheus_url: str = "http://localhost:9090",
    query_iterations: int = 100,
    remote_write_iterations: int = 100,
    tsdb_duration_seconds: int = 60,
    output_dir: Optional[str] = None,
    thresholds: Optional[dict[str, float]] = None,
) -> PerformanceTestReport:
    """Synchronous wrapper for running all performance tests.

    Args:
        prometheus_url: URL of the Prometheus instance
        query_iterations: Iterations for query benchmarks
        remote_write_iterations: Iterations for remote write benchmarks
        tsdb_duration_seconds: Duration for TSDB benchmarks
        output_dir: Directory to save reports
        thresholds: Pass/fail thresholds

    Returns:
        Comprehensive performance report
    """
    runner = PerformanceTestRunner(
        prometheus_url=prometheus_url,
        query_iterations=query_iterations,
        remote_write_iterations=remote_write_iterations,
        tsdb_duration_seconds=tsdb_duration_seconds,
        thresholds=thresholds,
    )

    report = asyncio.run(runner.run_all_benchmarks())

    if output_dir:
        runner.save_report(report, Path(output_dir))

    return report
