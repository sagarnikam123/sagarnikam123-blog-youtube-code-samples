"""
k6 Soak Test Runner for Prometheus Endurance Testing.

This module provides a Python wrapper for executing k6 soak tests
against Prometheus for extended periods (24h+).

Requirements: 18.8, 18.9
"""

import json
import os
import subprocess
import tempfile
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Optional


@dataclass
class K6SoakConfig:
    """
    Configuration for k6 soak tests.

    Requirements: 18.8, 18.9

    Attributes:
        prometheus_url: URL of the Prometheus instance
        vus: Number of virtual users
        duration: Test duration (e.g., "24h", "1h", "30m")
        ramp_up_time: Time to ramp up to target VUs
        ramp_down_time: Time to ramp down at end
        healthcheck_interval: Interval for health checks in seconds
        k6_binary: Path to k6 binary
        script_path: Path to k6 soak script
        output_dir: Directory for test output
    """

    prometheus_url: str = "http://localhost:9090"
    vus: int = 50
    duration: str = "24h"
    ramp_up_time: str = "5m"
    ramp_down_time: str = "5m"
    healthcheck_interval: int = 300
    k6_binary: str = "k6"
    script_path: Optional[str] = None
    output_dir: str = "./results"

    def __post_init__(self):
        """Set default script path if not provided."""
        if self.script_path is None:
            # Default to the k6/soak.js relative to this file
            module_dir = Path(__file__).parent.parent
            self.script_path = str(module_dir / "k6" / "soak.js")


@dataclass
class K6SoakMetrics:
    """
    Metrics collected from k6 soak test execution.

    Requirements: 18.8, 18.9

    Attributes:
        total_queries: Total number of queries executed
        failed_queries: Number of failed queries
        query_success_rate: Percentage of successful queries
        query_latency_p50_ms: 50th percentile query latency
        query_latency_p95_ms: 95th percentile query latency
        query_latency_p99_ms: 99th percentile query latency
        range_query_latency_p95_ms: 95th percentile range query latency
        healthcheck_success_rate: Percentage of successful health checks
        memory_bytes_final: Final memory usage in bytes
        active_series_final: Final active series count
        goroutines_final: Final goroutine count
    """

    total_queries: int = 0
    failed_queries: int = 0
    query_success_rate: float = 0.0
    query_latency_p50_ms: float = 0.0
    query_latency_p95_ms: float = 0.0
    query_latency_p99_ms: float = 0.0
    range_query_latency_p95_ms: float = 0.0
    healthcheck_success_rate: float = 0.0
    memory_bytes_final: float = 0.0
    active_series_final: int = 0
    goroutines_final: int = 0

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "total_queries": self.total_queries,
            "failed_queries": self.failed_queries,
            "query_success_rate": round(self.query_success_rate, 4),
            "query_latency_p50_ms": round(self.query_latency_p50_ms, 2),
            "query_latency_p95_ms": round(self.query_latency_p95_ms, 2),
            "query_latency_p99_ms": round(self.query_latency_p99_ms, 2),
            "range_query_latency_p95_ms": round(self.range_query_latency_p95_ms, 2),
            "healthcheck_success_rate": round(self.healthcheck_success_rate, 4),
            "memory_bytes_final": round(self.memory_bytes_final, 0),
            "active_series_final": self.active_series_final,
            "goroutines_final": self.goroutines_final,
        }


@dataclass
class K6SoakResult:
    """
    Result of a k6 soak test execution.

    Requirements: 18.8, 18.9

    Attributes:
        config: Test configuration used
        start_time: When the test started
        end_time: When the test ended
        metrics: Collected metrics
        thresholds_passed: Whether all thresholds passed
        exit_code: k6 process exit code
        raw_output: Raw k6 output
        error_message: Error message if test failed
        passed: Whether the test passed overall
    """

    config: Optional[K6SoakConfig] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    metrics: K6SoakMetrics = field(default_factory=K6SoakMetrics)
    thresholds_passed: bool = True
    exit_code: int = 0
    raw_output: str = ""
    error_message: str = ""
    passed: bool = True

    @property
    def duration_seconds(self) -> float:
        """Total test duration in seconds."""
        if self.start_time and self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return 0.0

    @property
    def duration_hours(self) -> float:
        """Total test duration in hours."""
        return self.duration_seconds / 3600.0

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "duration_hours": round(self.duration_hours, 2),
            "metrics": self.metrics.to_dict(),
            "thresholds_passed": self.thresholds_passed,
            "exit_code": self.exit_code,
            "passed": self.passed,
            "error_message": self.error_message,
        }


class K6SoakRunner:
    """
    Runner for k6 soak tests against Prometheus.

    This class executes k6 soak test scripts and collects results
    for endurance testing of Prometheus deployments.

    Requirements: 18.8, 18.9
    """

    def __init__(self, config: K6SoakConfig):
        """Initialize the k6 soak runner.

        Args:
            config: Test configuration
        """
        self.config = config

    def _check_k6_available(self) -> bool:
        """Check if k6 binary is available.

        Returns:
            True if k6 is available, False otherwise
        """
        try:
            result = subprocess.run(
                [self.config.k6_binary, "version"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False

    def _check_script_exists(self) -> bool:
        """Check if the k6 script exists.

        Returns:
            True if script exists, False otherwise
        """
        if self.config.script_path:
            return Path(self.config.script_path).exists()
        return False

    def _build_k6_command(self, output_file: str) -> list[str]:
        """Build the k6 command with all arguments.

        Args:
            output_file: Path to output JSON file

        Returns:
            List of command arguments
        """
        cmd = [
            self.config.k6_binary,
            "run",
            "--out", f"json={output_file}",
            "--env", f"PROMETHEUS_URL={self.config.prometheus_url}",
            "--env", f"VUS={self.config.vus}",
            "--env", f"DURATION={self.config.duration}",
            "--env", f"RAMP_UP_TIME={self.config.ramp_up_time}",
            "--env", f"RAMP_DOWN_TIME={self.config.ramp_down_time}",
            "--env", f"HEALTHCHECK_INTERVAL={self.config.healthcheck_interval}",
            self.config.script_path,
        ]
        return cmd

    def _parse_k6_output(self, output: str) -> K6SoakMetrics:
        """Parse k6 JSON output to extract metrics.

        Args:
            output: Raw k6 output string

        Returns:
            K6SoakMetrics with parsed values
        """
        metrics = K6SoakMetrics()

        try:
            # Try to parse as JSON summary
            data = json.loads(output)

            if "metrics" in data:
                m = data["metrics"]
                metrics.total_queries = m.get("total_queries", 0)
                metrics.failed_queries = m.get("failed_queries", 0)
                metrics.query_success_rate = m.get("query_success_rate", 0)
                metrics.query_latency_p50_ms = m.get("query_latency_p50", 0)
                metrics.query_latency_p95_ms = m.get("query_latency_p95", 0)
                metrics.query_latency_p99_ms = m.get("query_latency_p99", 0)
                metrics.range_query_latency_p95_ms = m.get("range_query_latency_p95", 0)
                metrics.healthcheck_success_rate = m.get("healthcheck_success_rate", 0)
        except json.JSONDecodeError:
            # Try to parse line-by-line JSON output
            for line in output.strip().split('\n'):
                try:
                    data = json.loads(line)
                    if data.get("type") == "Point":
                        metric_name = data.get("metric", "")
                        value = data.get("data", {}).get("value", 0)

                        if metric_name == "prometheus_total_queries":
                            metrics.total_queries = int(value)
                        elif metric_name == "prometheus_failed_queries":
                            metrics.failed_queries = int(value)
                        elif metric_name == "prometheus_query_success_rate":
                            metrics.query_success_rate = float(value)
                        elif metric_name == "prometheus_memory_bytes":
                            metrics.memory_bytes_final = float(value)
                        elif metric_name == "prometheus_active_series":
                            metrics.active_series_final = int(value)
                        elif metric_name == "prometheus_goroutines":
                            metrics.goroutines_final = int(value)
                except json.JSONDecodeError:
                    continue

        return metrics

    def _parse_summary_output(self, stdout: str) -> tuple[K6SoakMetrics, bool]:
        """Parse k6 summary output from stdout.

        Args:
            stdout: Standard output from k6

        Returns:
            Tuple of (metrics, thresholds_passed)
        """
        metrics = K6SoakMetrics()
        thresholds_passed = True

        try:
            # Look for JSON summary in output
            for line in stdout.strip().split('\n'):
                line = line.strip()
                if line.startswith('{') and line.endswith('}'):
                    try:
                        data = json.loads(line)
                        if "metrics" in data:
                            m = data["metrics"]
                            metrics.total_queries = m.get("total_queries", 0)
                            metrics.failed_queries = m.get("failed_queries", 0)
                            metrics.query_success_rate = m.get("query_success_rate", 0)
                            metrics.query_latency_p50_ms = m.get("query_latency_p50", 0)
                            metrics.query_latency_p95_ms = m.get("query_latency_p95", 0)
                            metrics.query_latency_p99_ms = m.get("query_latency_p99", 0)
                            metrics.range_query_latency_p95_ms = m.get(
                                "range_query_latency_p95", 0
                            )
                            metrics.healthcheck_success_rate = m.get(
                                "healthcheck_success_rate", 0
                            )
                        thresholds_passed = data.get("thresholds_passed", True)
                        break
                    except json.JSONDecodeError:
                        continue
        except Exception:
            pass

        return metrics, thresholds_passed

    def run(self) -> K6SoakResult:
        """Run the k6 soak test.

        Requirements: 18.8, 18.9

        Returns:
            K6SoakResult with test results
        """
        result = K6SoakResult(config=self.config)
        result.start_time = datetime.utcnow()

        # Check prerequisites
        if not self._check_k6_available():
            result.passed = False
            result.error_message = f"k6 binary not found at: {self.config.k6_binary}"
            result.end_time = datetime.utcnow()
            return result

        if not self._check_script_exists():
            result.passed = False
            result.error_message = f"k6 script not found at: {self.config.script_path}"
            result.end_time = datetime.utcnow()
            return result

        # Create output directory
        os.makedirs(self.config.output_dir, exist_ok=True)

        # Create temporary file for JSON output
        with tempfile.NamedTemporaryFile(
            mode='w',
            suffix='.json',
            delete=False,
            dir=self.config.output_dir,
        ) as f:
            output_file = f.name

        try:
            # Build and execute k6 command
            cmd = self._build_k6_command(output_file)

            process = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
            )

            result.exit_code = process.returncode
            result.raw_output = process.stdout

            # Parse results
            if process.returncode == 0:
                # Read JSON output file
                if os.path.exists(output_file):
                    with open(output_file, 'r') as f:
                        json_output = f.read()
                    result.metrics = self._parse_k6_output(json_output)

                # Parse summary from stdout
                metrics, thresholds_passed = self._parse_summary_output(process.stdout)
                if metrics.total_queries > 0:
                    result.metrics = metrics
                result.thresholds_passed = thresholds_passed
                result.passed = thresholds_passed
            else:
                result.passed = False
                result.error_message = process.stderr or "k6 execution failed"

        except subprocess.TimeoutExpired:
            result.passed = False
            result.error_message = "k6 execution timed out"
        except Exception as e:
            result.passed = False
            result.error_message = str(e)
        finally:
            # Clean up temporary file
            if os.path.exists(output_file):
                try:
                    os.remove(output_file)
                except OSError:
                    pass

        result.end_time = datetime.utcnow()
        return result


def run_k6_soak_test(
    prometheus_url: str = "http://localhost:9090",
    vus: int = 50,
    duration: str = "24h",
) -> K6SoakResult:
    """Convenience function to run a k6 soak test.

    Args:
        prometheus_url: URL of the Prometheus instance
        vus: Number of virtual users
        duration: Test duration (e.g., "24h", "1h")

    Returns:
        K6SoakResult with test results
    """
    config = K6SoakConfig(
        prometheus_url=prometheus_url,
        vus=vus,
        duration=duration,
    )
    runner = K6SoakRunner(config)
    return runner.run()
