"""
Report generation for the Prometheus Testing Framework.

This module provides functionality to generate comprehensive test reports
in multiple formats (JSON, Markdown, HTML, CSV) with support for
deployment_mode, k6_results, and test_runner_host metadata.

Requirements: 11.3, 11.4, 11.5
"""

import csv
import io
import json
import os
import platform
import sys
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from .models import TestResult, TestSuiteResult, TestStatus


@dataclass
class TestRunnerHostInfo:
    """Information about the Test Runner Host (local laptop/workstation).

    Requirements: 11.3 - Include test_runner_host metadata in reports
    """

    os_name: str = field(default_factory=lambda: platform.system())
    os_version: str = field(default_factory=lambda: platform.release())
    python_version: str = field(default_factory=lambda: platform.python_version())
    hostname: str = field(default_factory=lambda: platform.node())
    k6_version: Optional[str] = None
    kubectl_version: Optional[str] = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "os": self.os_name,
            "os_version": self.os_version,
            "python_version": self.python_version,
            "hostname": self.hostname,
            "k6_version": self.k6_version,
            "kubectl_version": self.kubectl_version,
        }


@dataclass
class K6Results:
    """Results from k6 load testing.

    Requirements: 11.3 - Include k6_results in reports
    """

    vus: int = 0
    iterations: int = 0
    http_req_duration_p50_ms: float = 0.0
    http_req_duration_p90_ms: float = 0.0
    http_req_duration_p99_ms: float = 0.0
    http_req_failed_percent: float = 0.0
    data_received_bytes: int = 0
    data_sent_bytes: int = 0
    max_vus_reached: Optional[int] = None
    failure_point_vus: Optional[int] = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation."""
        result = {
            "vus": self.vus,
            "iterations": self.iterations,
            "http_req_duration_p50_ms": self.http_req_duration_p50_ms,
            "http_req_duration_p90_ms": self.http_req_duration_p90_ms,
            "http_req_duration_p99_ms": self.http_req_duration_p99_ms,
            "http_req_failed_percent": self.http_req_failed_percent,
            "data_received_bytes": self.data_received_bytes,
            "data_sent_bytes": self.data_sent_bytes,
        }
        if self.max_vus_reached is not None:
            result["max_vus_reached"] = self.max_vus_reached
        if self.failure_point_vus is not None:
            result["failure_point_vus"] = self.failure_point_vus
        return result

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "K6Results":
        """Create K6Results from dictionary."""
        return cls(
            vus=data.get("vus", 0),
            iterations=data.get("iterations", 0),
            http_req_duration_p50_ms=data.get("http_req_duration_p50_ms", 0.0),
            http_req_duration_p90_ms=data.get("http_req_duration_p90_ms", 0.0),
            http_req_duration_p99_ms=data.get("http_req_duration_p99_ms", 0.0),
            http_req_failed_percent=data.get("http_req_failed_percent", 0.0),
            data_received_bytes=data.get("data_received_bytes", 0),
            data_sent_bytes=data.get("data_sent_bytes", 0),
            max_vus_reached=data.get("max_vus_reached"),
            failure_point_vus=data.get("failure_point_vus"),
        )


@dataclass
class TestTypeResult:
    """Results for a specific test type (sanity, load, stress, etc.).

    Requirements: 11.3 - Include deployment_mode and k6_results
    """

    test_type: str
    status: str = "not_started"
    duration_seconds: float = 0.0
    deployment_mode: str = "monolithic"
    tests: list[TestResult] = field(default_factory=list)
    k6_results: Optional[K6Results] = None
    metrics: dict[str, Any] = field(default_factory=dict)
    breaking_point: Optional[dict[str, Any]] = None

    @property
    def passed(self) -> bool:
        """Check if all tests in this type passed."""
        return self.status == "passed"

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation."""
        result = {
            "status": self.status,
            "duration_seconds": self.duration_seconds,
            "deployment_mode": self.deployment_mode,
            "tests": [t.to_dict() for t in self.tests],
        }
        if self.k6_results:
            result["k6_results"] = self.k6_results.to_dict()
        if self.metrics:
            result["metrics"] = self.metrics
        if self.breaking_point:
            result["breaking_point"] = self.breaking_point
        return result


@dataclass
class FullTestReport:
    """Complete test report with all metadata and results.

    Requirements: 11.3, 11.4, 11.5
    """

    test_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = field(default_factory=datetime.utcnow)
    platform: str = "minikube"
    deployment_mode: str = "monolithic"
    prometheus_version: str = "v3.5.0"
    duration_seconds: float = 0.0
    test_runner_host: TestRunnerHostInfo = field(default_factory=TestRunnerHostInfo)

    # Summary
    total_tests: int = 0
    passed_tests: int = 0
    failed_tests: int = 0
    skipped_tests: int = 0

    # Results by test type
    results: dict[str, TestTypeResult] = field(default_factory=dict)

    # Collected metrics
    prometheus_metrics: dict[str, Any] = field(default_factory=dict)
    system_metrics: dict[str, Any] = field(default_factory=dict)

    @property
    def success_rate(self) -> float:
        """Calculate success rate as percentage."""
        if self.total_tests == 0:
            return 0.0
        return (self.passed_tests / self.total_tests) * 100

    @property
    def overall_status(self) -> str:
        """Determine overall test status."""
        if self.failed_tests > 0:
            return "failed"
        if self.total_tests == 0:
            return "not_started"
        return "passed"


    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation for JSON export."""
        return {
            "metadata": {
                "test_id": self.test_id,
                "timestamp": self.timestamp.isoformat(),
                "platform": self.platform,
                "deployment_mode": self.deployment_mode,
                "prometheus_version": self.prometheus_version,
                "duration_seconds": self.duration_seconds,
                "test_runner_host": self.test_runner_host.to_dict(),
            },
            "summary": {
                "total_tests": self.total_tests,
                "passed": self.passed_tests,
                "failed": self.failed_tests,
                "skipped": self.skipped_tests,
                "success_rate": round(self.success_rate, 2),
                "status": self.overall_status,
            },
            "results": {
                test_type: result.to_dict()
                for test_type, result in self.results.items()
            },
            "metrics": {
                "prometheus": self.prometheus_metrics,
                "system": self.system_metrics,
            },
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "FullTestReport":
        """Create FullTestReport from dictionary."""
        metadata = data.get("metadata", {})
        summary = data.get("summary", {})
        metrics = data.get("metrics", {})

        host_data = metadata.get("test_runner_host", {})
        test_runner_host = TestRunnerHostInfo(
            os_name=host_data.get("os", platform.system()),
            os_version=host_data.get("os_version", platform.release()),
            python_version=host_data.get("python_version", platform.python_version()),
            hostname=host_data.get("hostname", platform.node()),
            k6_version=host_data.get("k6_version"),
            kubectl_version=host_data.get("kubectl_version"),
        )

        return cls(
            test_id=metadata.get("test_id", str(uuid.uuid4())),
            timestamp=datetime.fromisoformat(metadata["timestamp"])
                if "timestamp" in metadata else datetime.utcnow(),
            platform=metadata.get("platform", "minikube"),
            deployment_mode=metadata.get("deployment_mode", "monolithic"),
            prometheus_version=metadata.get("prometheus_version", "v3.5.0"),
            duration_seconds=metadata.get("duration_seconds", 0.0),
            test_runner_host=test_runner_host,
            total_tests=summary.get("total_tests", 0),
            passed_tests=summary.get("passed", 0),
            failed_tests=summary.get("failed", 0),
            skipped_tests=summary.get("skipped", 0),
            prometheus_metrics=metrics.get("prometheus", {}),
            system_metrics=metrics.get("system", {}),
        )


class ReportGenerator:
    """
    Generates comprehensive test reports in multiple formats.

    This class creates reports from test suite results including:
    - JSON reports with deployment_mode and k6_results
    - Markdown/HTML human-readable reports
    - CSV exports for analysis
    - test_runner_host metadata

    Requirements: 11.3, 11.4, 11.5
    """

    def __init__(
        self,
        output_dir: Optional[Path | str] = None,
        test_runner_host: Optional[TestRunnerHostInfo] = None,
    ):
        """Initialize the report generator.

        Args:
            output_dir: Directory to save reports (default: ./results)
            test_runner_host: Test runner host information
        """
        self.output_dir = Path(output_dir) if output_dir else Path("./results")
        self.test_runner_host = test_runner_host or TestRunnerHostInfo()

    def create_report(
        self,
        suite_result: TestSuiteResult,
        deployment_mode: str = "monolithic",
        k6_results: Optional[dict[str, K6Results]] = None,
        prometheus_metrics: Optional[dict[str, Any]] = None,
        system_metrics: Optional[dict[str, Any]] = None,
    ) -> FullTestReport:
        """Create a full test report from suite results.

        Args:
            suite_result: Test suite execution results
            deployment_mode: Deployment mode (monolithic/distributed)
            k6_results: k6 results by test type
            prometheus_metrics: Collected Prometheus metrics
            system_metrics: Collected system metrics

        Returns:
            Complete test report
        """
        k6_results = k6_results or {}

        # Group results by test type
        results_by_type: dict[str, TestTypeResult] = {}
        for result in suite_result.results:
            test_type = result.test_type
            if test_type not in results_by_type:
                results_by_type[test_type] = TestTypeResult(
                    test_type=test_type,
                    deployment_mode=deployment_mode,
                    k6_results=k6_results.get(test_type),
                )
            results_by_type[test_type].tests.append(result)


        # Calculate status and duration for each test type
        for test_type, type_result in results_by_type.items():
            type_result.duration_seconds = sum(
                t.duration_seconds for t in type_result.tests
            )
            all_passed = all(t.passed for t in type_result.tests)
            any_failed = any(t.failed for t in type_result.tests)
            if any_failed:
                type_result.status = "failed"
            elif all_passed:
                type_result.status = "passed"
            else:
                type_result.status = "partial"

        return FullTestReport(
            timestamp=suite_result.start_time,
            platform=suite_result.platform,
            deployment_mode=deployment_mode,
            prometheus_version=suite_result.prometheus_version,
            duration_seconds=suite_result.duration_seconds,
            test_runner_host=self.test_runner_host,
            total_tests=suite_result.total_tests,
            passed_tests=suite_result.passed_tests,
            failed_tests=suite_result.failed_tests,
            skipped_tests=suite_result.skipped_tests,
            results=results_by_type,
            prometheus_metrics=prometheus_metrics or {},
            system_metrics=system_metrics or {},
        )

    def to_json(self, report: FullTestReport, indent: int = 2) -> str:
        """Convert report to JSON string.

        Requirements: 11.3 - Generate JSON reports

        Args:
            report: Full test report
            indent: JSON indentation level

        Returns:
            JSON string representation
        """
        return json.dumps(report.to_dict(), indent=indent, default=str)


    def to_markdown(self, report: FullTestReport) -> str:
        """Convert report to Markdown format.

        Requirements: 11.4 - Generate human-readable summary reports

        Args:
            report: Full test report

        Returns:
            Markdown string representation
        """
        status_icon = "✅" if report.overall_status == "passed" else "❌"

        lines = [
            f"# Prometheus Test Report",
            "",
            f"**Test ID**: {report.test_id}",
            f"**Timestamp**: {report.timestamp.isoformat()}",
            "",
            "## Summary",
            "",
            f"- **Status**: {status_icon} {report.overall_status.upper()}",
            f"- **Platform**: {report.platform}",
            f"- **Deployment Mode**: {report.deployment_mode}",
            f"- **Prometheus Version**: {report.prometheus_version}",
            f"- **Duration**: {report.duration_seconds:.2f} seconds",
            "",
            "### Test Results",
            "",
            f"| Metric | Value |",
            f"|--------|-------|",
            f"| Total Tests | {report.total_tests} |",
            f"| Passed | {report.passed_tests} |",
            f"| Failed | {report.failed_tests} |",
            f"| Skipped | {report.skipped_tests} |",
            f"| Success Rate | {report.success_rate:.1f}% |",
            "",
            "## Test Runner Host",
            "",
            f"- **OS**: {report.test_runner_host.os_name} {report.test_runner_host.os_version}",
            f"- **Python Version**: {report.test_runner_host.python_version}",
            f"- **Hostname**: {report.test_runner_host.hostname}",
        ]

        if report.test_runner_host.k6_version:
            lines.append(f"- **k6 Version**: {report.test_runner_host.k6_version}")
        if report.test_runner_host.kubectl_version:
            lines.append(f"- **kubectl Version**: {report.test_runner_host.kubectl_version}")

        lines.append("")


        # Results by test type
        if report.results:
            lines.extend([
                "## Results by Test Type",
                "",
            ])

            for test_type, type_result in report.results.items():
                type_icon = "✅" if type_result.passed else "❌"
                lines.extend([
                    f"### {test_type.title()} Tests {type_icon}",
                    "",
                    f"- **Status**: {type_result.status}",
                    f"- **Duration**: {type_result.duration_seconds:.2f}s",
                    f"- **Deployment Mode**: {type_result.deployment_mode}",
                    "",
                ])

                # k6 results if available
                if type_result.k6_results:
                    k6 = type_result.k6_results
                    lines.extend([
                        "#### k6 Load Test Results",
                        "",
                        f"| Metric | Value |",
                        f"|--------|-------|",
                        f"| VUs | {k6.vus} |",
                        f"| Iterations | {k6.iterations} |",
                        f"| p50 Latency | {k6.http_req_duration_p50_ms:.2f}ms |",
                        f"| p90 Latency | {k6.http_req_duration_p90_ms:.2f}ms |",
                        f"| p99 Latency | {k6.http_req_duration_p99_ms:.2f}ms |",
                        f"| Failed Requests | {k6.http_req_failed_percent:.2f}% |",
                        "",
                    ])

                # Individual test results
                if type_result.tests:
                    lines.extend([
                        "#### Individual Tests",
                        "",
                        "| Test | Status | Duration |",
                        "|------|--------|----------|",
                    ])
                    for test in type_result.tests:
                        test_icon = "✅" if test.passed else "❌"
                        lines.append(
                            f"| {test.test_name} | {test_icon} {test.status.value} | "
                            f"{test.duration_seconds:.2f}s |"
                        )
                    lines.append("")


        # Prometheus metrics
        if report.prometheus_metrics:
            lines.extend([
                "## Prometheus Metrics",
                "",
                "```json",
                json.dumps(report.prometheus_metrics, indent=2, default=str),
                "```",
                "",
            ])

        # System metrics
        if report.system_metrics:
            lines.extend([
                "## System Metrics",
                "",
                "```json",
                json.dumps(report.system_metrics, indent=2, default=str),
                "```",
                "",
            ])

        return "\n".join(lines)

    def to_html(self, report: FullTestReport) -> str:
        """Convert report to HTML format.

        Requirements: 11.4 - Generate human-readable summary reports

        Args:
            report: Full test report

        Returns:
            HTML string representation
        """
        status_class = "passed" if report.overall_status == "passed" else "failed"
        status_icon = "✅" if report.overall_status == "passed" else "❌"

        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Prometheus Test Report - {report.test_id}</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; margin: 40px; background: #f5f5f5; }}
        .container {{ max-width: 1200px; margin: 0 auto; background: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        h1 {{ color: #333; border-bottom: 2px solid #e0e0e0; padding-bottom: 10px; }}
        h2 {{ color: #555; margin-top: 30px; }}
        h3 {{ color: #666; }}
        .summary {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin: 20px 0; }}
        .summary-card {{ background: #f8f9fa; padding: 20px; border-radius: 8px; text-align: center; }}
        .summary-card.passed {{ border-left: 4px solid #28a745; }}
        .summary-card.failed {{ border-left: 4px solid #dc3545; }}
        .summary-card h3 {{ margin: 0 0 10px 0; font-size: 14px; color: #666; }}
        .summary-card .value {{ font-size: 24px; font-weight: bold; color: #333; }}
        table {{ width: 100%; border-collapse: collapse; margin: 15px 0; }}
        th, td {{ padding: 12px; text-align: left; border-bottom: 1px solid #e0e0e0; }}
        th {{ background: #f8f9fa; font-weight: 600; }}
        .status-passed {{ color: #28a745; }}
        .status-failed {{ color: #dc3545; }}
        .metadata {{ background: #f8f9fa; padding: 15px; border-radius: 8px; margin: 15px 0; }}
        .metadata dt {{ font-weight: 600; color: #555; }}
        .metadata dd {{ margin: 0 0 10px 0; color: #333; }}
        pre {{ background: #f4f4f4; padding: 15px; border-radius: 4px; overflow-x: auto; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>{status_icon} Prometheus Test Report</h1>
        <p><strong>Test ID:</strong> {report.test_id}</p>
        <p><strong>Timestamp:</strong> {report.timestamp.isoformat()}</p>

        <div class="summary">
            <div class="summary-card {status_class}">
                <h3>Status</h3>
                <div class="value">{report.overall_status.upper()}</div>
            </div>
            <div class="summary-card">
                <h3>Total Tests</h3>
                <div class="value">{report.total_tests}</div>
            </div>
            <div class="summary-card passed">
                <h3>Passed</h3>
                <div class="value">{report.passed_tests}</div>
            </div>
            <div class="summary-card failed">
                <h3>Failed</h3>
                <div class="value">{report.failed_tests}</div>
            </div>
            <div class="summary-card">
                <h3>Success Rate</h3>
                <div class="value">{report.success_rate:.1f}%</div>
            </div>
        </div>

        <h2>Configuration</h2>
        <div class="metadata">
            <dl>
                <dt>Platform</dt><dd>{report.platform}</dd>
                <dt>Deployment Mode</dt><dd>{report.deployment_mode}</dd>
                <dt>Prometheus Version</dt><dd>{report.prometheus_version}</dd>
                <dt>Duration</dt><dd>{report.duration_seconds:.2f} seconds</dd>
            </dl>
        </div>

        <h2>Test Runner Host</h2>
        <div class="metadata">
            <dl>
                <dt>OS</dt><dd>{report.test_runner_host.os_name} {report.test_runner_host.os_version}</dd>
                <dt>Python Version</dt><dd>{report.test_runner_host.python_version}</dd>
                <dt>Hostname</dt><dd>{report.test_runner_host.hostname}</dd>
"""

        if report.test_runner_host.k6_version:
            html += f"                <dt>k6 Version</dt><dd>{report.test_runner_host.k6_version}</dd>\n"
        if report.test_runner_host.kubectl_version:
            html += f"                <dt>kubectl Version</dt><dd>{report.test_runner_host.kubectl_version}</dd>\n"

        html += """            </dl>
        </div>
"""
        return html


    def _html_results_section(self, report: FullTestReport) -> str:
        """Generate HTML for results section."""
        html = ""

        if report.results:
            html += "        <h2>Results by Test Type</h2>\n"

            for test_type, type_result in report.results.items():
                status_class = "passed" if type_result.passed else "failed"
                status_icon = "✅" if type_result.passed else "❌"

                html += f"""
        <h3>{status_icon} {test_type.title()} Tests</h3>
        <div class="metadata">
            <dl>
                <dt>Status</dt><dd class="status-{status_class}">{type_result.status}</dd>
                <dt>Duration</dt><dd>{type_result.duration_seconds:.2f}s</dd>
                <dt>Deployment Mode</dt><dd>{type_result.deployment_mode}</dd>
            </dl>
        </div>
"""

                # k6 results
                if type_result.k6_results:
                    k6 = type_result.k6_results
                    html += f"""
        <h4>k6 Load Test Results</h4>
        <table>
            <tr><th>Metric</th><th>Value</th></tr>
            <tr><td>VUs</td><td>{k6.vus}</td></tr>
            <tr><td>Iterations</td><td>{k6.iterations}</td></tr>
            <tr><td>p50 Latency</td><td>{k6.http_req_duration_p50_ms:.2f}ms</td></tr>
            <tr><td>p90 Latency</td><td>{k6.http_req_duration_p90_ms:.2f}ms</td></tr>
            <tr><td>p99 Latency</td><td>{k6.http_req_duration_p99_ms:.2f}ms</td></tr>
            <tr><td>Failed Requests</td><td>{k6.http_req_failed_percent:.2f}%</td></tr>
        </table>
"""

                # Individual tests
                if type_result.tests:
                    html += """
        <h4>Individual Tests</h4>
        <table>
            <tr><th>Test</th><th>Status</th><th>Duration</th></tr>
"""
                    for test in type_result.tests:
                        status_class = "passed" if test.passed else "failed"
                        status_icon = "✅" if test.passed else "❌"
                        html += f"""            <tr>
                <td>{test.test_name}</td>
                <td class="status-{status_class}">{status_icon} {test.status.value}</td>
                <td>{test.duration_seconds:.2f}s</td>
            </tr>
"""
                    html += "        </table>\n"

        return html


    def to_html_complete(self, report: FullTestReport) -> str:
        """Generate complete HTML report.

        Args:
            report: Full test report

        Returns:
            Complete HTML string
        """
        html = self.to_html(report)
        html += self._html_results_section(report)

        # Metrics sections
        if report.prometheus_metrics:
            html += f"""
        <h2>Prometheus Metrics</h2>
        <pre>{json.dumps(report.prometheus_metrics, indent=2, default=str)}</pre>
"""

        if report.system_metrics:
            html += f"""
        <h2>System Metrics</h2>
        <pre>{json.dumps(report.system_metrics, indent=2, default=str)}</pre>
"""

        html += """
    </div>
</body>
</html>
"""
        return html

    def to_csv(self, report: FullTestReport) -> str:
        """Convert report to CSV format.

        Requirements: 11.5 - Support exporting results to CSV

        Args:
            report: Full test report

        Returns:
            CSV string representation
        """
        output = io.StringIO()
        writer = csv.writer(output)

        # Header
        writer.writerow([
            "test_id", "timestamp", "platform", "deployment_mode",
            "prometheus_version", "test_type", "test_name", "status",
            "duration_seconds", "k6_vus", "k6_iterations",
            "k6_p50_ms", "k6_p90_ms", "k6_p99_ms", "k6_failed_percent"
        ])

        # Data rows
        for test_type, type_result in report.results.items():
            k6 = type_result.k6_results
            for test in type_result.tests:
                writer.writerow([
                    report.test_id,
                    report.timestamp.isoformat(),
                    report.platform,
                    report.deployment_mode,
                    report.prometheus_version,
                    test_type,
                    test.test_name,
                    test.status.value,
                    f"{test.duration_seconds:.2f}",
                    k6.vus if k6 else "",
                    k6.iterations if k6 else "",
                    f"{k6.http_req_duration_p50_ms:.2f}" if k6 else "",
                    f"{k6.http_req_duration_p90_ms:.2f}" if k6 else "",
                    f"{k6.http_req_duration_p99_ms:.2f}" if k6 else "",
                    f"{k6.http_req_failed_percent:.2f}" if k6 else "",
                ])

        return output.getvalue()


    def to_csv_summary(self, report: FullTestReport) -> str:
        """Generate CSV summary with aggregated metrics.

        Args:
            report: Full test report

        Returns:
            CSV string with summary metrics
        """
        output = io.StringIO()
        writer = csv.writer(output)

        # Summary format: metric,value
        writer.writerow(["metric", "value"])
        writer.writerow(["test_id", report.test_id])
        writer.writerow(["timestamp", report.timestamp.isoformat()])
        writer.writerow(["platform", report.platform])
        writer.writerow(["deployment_mode", report.deployment_mode])
        writer.writerow(["prometheus_version", report.prometheus_version])
        writer.writerow(["duration_seconds", f"{report.duration_seconds:.2f}"])
        writer.writerow(["total_tests", report.total_tests])
        writer.writerow(["passed_tests", report.passed_tests])
        writer.writerow(["failed_tests", report.failed_tests])
        writer.writerow(["skipped_tests", report.skipped_tests])
        writer.writerow(["success_rate", f"{report.success_rate:.2f}"])
        writer.writerow(["overall_status", report.overall_status])

        # Test runner host info
        writer.writerow(["host_os", report.test_runner_host.os_name])
        writer.writerow(["host_python_version", report.test_runner_host.python_version])

        # k6 results per test type
        for test_type, type_result in report.results.items():
            if type_result.k6_results:
                k6 = type_result.k6_results
                writer.writerow([f"{test_type}_k6_vus", k6.vus])
                writer.writerow([f"{test_type}_k6_iterations", k6.iterations])
                writer.writerow([f"{test_type}_k6_p50_ms", f"{k6.http_req_duration_p50_ms:.2f}"])
                writer.writerow([f"{test_type}_k6_p90_ms", f"{k6.http_req_duration_p90_ms:.2f}"])
                writer.writerow([f"{test_type}_k6_p99_ms", f"{k6.http_req_duration_p99_ms:.2f}"])

        return output.getvalue()


    def save_report(
        self,
        report: FullTestReport,
        formats: Optional[list[str]] = None,
        base_name: Optional[str] = None,
    ) -> list[Path]:
        """Save report to files in specified formats.

        Requirements: 11.3, 11.4, 11.5

        Args:
            report: Full test report
            formats: List of formats to save (json, markdown, html, csv)
            base_name: Base filename (default: test_report_{timestamp})

        Returns:
            List of saved file paths
        """
        formats = formats or ["json", "markdown", "html", "csv"]
        self.output_dir.mkdir(parents=True, exist_ok=True)

        timestamp = report.timestamp.strftime("%Y%m%d_%H%M%S")
        base_name = base_name or f"test_report_{timestamp}"

        saved_files = []

        if "json" in formats:
            json_path = self.output_dir / f"{base_name}.json"
            json_path.write_text(self.to_json(report))
            saved_files.append(json_path)

        if "markdown" in formats or "md" in formats:
            md_path = self.output_dir / f"{base_name}.md"
            md_path.write_text(self.to_markdown(report))
            saved_files.append(md_path)

        if "html" in formats:
            html_path = self.output_dir / f"{base_name}.html"
            html_path.write_text(self.to_html_complete(report))
            saved_files.append(html_path)

        if "csv" in formats:
            csv_path = self.output_dir / f"{base_name}.csv"
            csv_path.write_text(self.to_csv(report))
            saved_files.append(csv_path)

            # Also save summary CSV
            summary_path = self.output_dir / f"{base_name}_summary.csv"
            summary_path.write_text(self.to_csv_summary(report))
            saved_files.append(summary_path)

        return saved_files


    def load_report(self, path: Path | str) -> FullTestReport:
        """Load a report from a JSON file.

        Args:
            path: Path to JSON report file

        Returns:
            Loaded FullTestReport
        """
        path = Path(path)
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return FullTestReport.from_dict(data)

    @staticmethod
    def get_test_runner_host_info() -> TestRunnerHostInfo:
        """Collect information about the current test runner host.

        Returns:
            TestRunnerHostInfo with current system information
        """
        import subprocess

        k6_version = None
        kubectl_version = None

        # Try to get k6 version
        try:
            result = subprocess.run(
                ["k6", "version"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            if result.returncode == 0:
                # Parse "k6 v0.47.0 (...)"
                version_line = result.stdout.strip().split("\n")[0]
                if "v" in version_line:
                    k6_version = version_line.split()[1] if len(version_line.split()) > 1 else version_line
        except (subprocess.TimeoutExpired, FileNotFoundError, Exception):
            pass

        # Try to get kubectl version
        try:
            result = subprocess.run(
                ["kubectl", "version", "--client", "--short"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            if result.returncode == 0:
                kubectl_version = result.stdout.strip()
        except (subprocess.TimeoutExpired, FileNotFoundError, Exception):
            pass

        return TestRunnerHostInfo(
            k6_version=k6_version,
            kubectl_version=kubectl_version,
        )
