"""
k6 Load Testing Runner for Prometheus Testing Framework.

This module provides a K6Runner class for executing k6 load test scripts
from the Test Runner Host against local or remote Prometheus deployments.

Requirements: 14.8, 14.9, 14.10, 14.11
"""

import json
import os
import shutil
import subprocess
import tempfile
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Optional


class K6TestType(Enum):
    """Types of k6 tests supported."""

    LOAD = "load"
    STRESS = "stress"
    BENCHMARK = "benchmark"
    SOAK = "soak"
    SCALING = "scaling"


@dataclass
class K6Stage:
    """
    Represents a stage in k6 ramping configuration.

    Attributes:
        duration: Duration of the stage (e.g., "5m", "30s")
        target: Target number of VUs at end of stage
    """

    duration: str
    target: int

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation."""
        return {"duration": self.duration, "target": self.target}


@dataclass
class K6Config:
    """
    Configuration for k6 test execution.

    Requirements: 14.8, 14.11

    Attributes:
        prometheus_url: URL of the Prometheus instance to test
        vus: Number of virtual users (for load tests)
        duration: Test duration (e.g., "30m", "1h")
        iterations: Number of iterations (for benchmark tests)
        stages: List of stages for ramping tests
        k6_binary: Path to k6 binary
        script_path: Path to k6 script to execute
        output_dir: Directory for test output
        timeout_seconds: Timeout for k6 execution
        env_vars: Additional environment variables
    """

    prometheus_url: str = "http://localhost:9090"
    vus: int = 100
    duration: str = "30m"
    iterations: int = 100
    stages: list[K6Stage] = field(default_factory=list)
    k6_binary: str = "k6"
    script_path: Optional[str] = None
    output_dir: str = "./results"
    timeout_seconds: Optional[int] = None
    env_vars: dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "prometheus_url": self.prometheus_url,
            "vus": self.vus,
            "duration": self.duration,
            "iterations": self.iterations,
            "stages": [s.to_dict() for s in self.stages],
            "k6_binary": self.k6_binary,
            "script_path": self.script_path,
            "output_dir": self.output_dir,
            "timeout_seconds": self.timeout_seconds,
        }


@dataclass
class K6Metrics:
    """
    Metrics collected from k6 test execution.

    Requirements: 14.8, 14.9, 14.10, 14.11

    Attributes:
        http_req_duration_avg_ms: Average HTTP request duration
        http_req_duration_p50_ms: 50th percentile HTTP request duration
        http_req_duration_p90_ms: 90th percentile HTTP request duration
        http_req_duration_p95_ms: 95th percentile HTTP request duration
        http_req_duration_p99_ms: 99th percentile HTTP request duration
        http_req_failed_rate: Rate of failed HTTP requests
        http_reqs_count: Total number of HTTP requests
        http_reqs_rate: HTTP requests per second
        iterations_count: Total number of iterations
        iterations_rate: Iterations per second
        vus_max: Maximum number of VUs
        data_received_bytes: Total data received
        data_sent_bytes: Total data sent
        custom_metrics: Additional custom metrics from k6 script
    """

    http_req_duration_avg_ms: float = 0.0
    http_req_duration_p50_ms: float = 0.0
    http_req_duration_p90_ms: float = 0.0
    http_req_duration_p95_ms: float = 0.0
    http_req_duration_p99_ms: float = 0.0
    http_req_failed_rate: float = 0.0
    http_reqs_count: int = 0
    http_reqs_rate: float = 0.0
    iterations_count: int = 0
    iterations_rate: float = 0.0
    vus_max: int = 0
    data_received_bytes: int = 0
    data_sent_bytes: int = 0
    custom_metrics: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "http_req_duration_avg_ms": round(self.http_req_duration_avg_ms, 2),
            "http_req_duration_p50_ms": round(self.http_req_duration_p50_ms, 2),
            "http_req_duration_p90_ms": round(self.http_req_duration_p90_ms, 2),
            "http_req_duration_p95_ms": round(self.http_req_duration_p95_ms, 2),
            "http_req_duration_p99_ms": round(self.http_req_duration_p99_ms, 2),
            "http_req_failed_rate": round(self.http_req_failed_rate, 4),
            "http_reqs_count": self.http_reqs_count,
            "http_reqs_rate": round(self.http_reqs_rate, 2),
            "iterations_count": self.iterations_count,
            "iterations_rate": round(self.iterations_rate, 2),
            "vus_max": self.vus_max,
            "data_received_bytes": self.data_received_bytes,
            "data_sent_bytes": self.data_sent_bytes,
            "custom_metrics": self.custom_metrics,
        }


@dataclass
class K6Result:
    """
    Result of a k6 test execution.

    Requirements: 14.8, 14.9, 14.10, 14.11

    Attributes:
        test_type: Type of test executed
        config: Test configuration used
        start_time: When the test started
        end_time: When the test ended
        metrics: Collected metrics
        thresholds_passed: Whether all thresholds passed
        exit_code: k6 process exit code
        stdout: Standard output from k6
        stderr: Standard error from k6
        error_message: Error message if test failed
        passed: Whether the test passed overall
        raw_summary: Raw k6 summary data
    """

    test_type: K6TestType = K6TestType.LOAD
    config: Optional[K6Config] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    metrics: K6Metrics = field(default_factory=K6Metrics)
    thresholds_passed: bool = True
    exit_code: int = 0
    stdout: str = ""
    stderr: str = ""
    error_message: str = ""
    passed: bool = True
    raw_summary: dict[str, Any] = field(default_factory=dict)

    @property
    def duration_seconds(self) -> float:
        """Total test duration in seconds."""
        if self.start_time and self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return 0.0

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "test_type": self.test_type.value,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "duration_seconds": round(self.duration_seconds, 2),
            "metrics": self.metrics.to_dict(),
            "thresholds_passed": self.thresholds_passed,
            "exit_code": self.exit_code,
            "passed": self.passed,
            "error_message": self.error_message,
        }


class K6RunnerError(Exception):
    """Exception raised when k6 runner encounters an error."""

    def __init__(self, message: str, exit_code: int = 1):
        super().__init__(message)
        self.exit_code = exit_code


class K6Runner:
    """
    Runner for k6 load tests against Prometheus.

    This class executes k6 test scripts from the Test Runner Host
    and collects results for load, stress, and benchmark testing.

    Requirements: 14.8, 14.9, 14.10, 14.11

    Example usage:
        runner = K6Runner("http://localhost:9090")

        # Run load test
        result = runner.run_load_test(
            script="k6/query-load.js",
            vus=100,
            duration="30m"
        )

        # Run stress test
        result = runner.run_stress_test(
            script="k6/stress-ramp.js",
            stages=[
                K6Stage("5m", 100),
                K6Stage("10m", 500),
                K6Stage("5m", 1000),
            ]
        )

        # Run benchmark
        result = runner.run_benchmark(
            script="k6/benchmark.js",
            iterations=100
        )
    """

    def __init__(
        self,
        prometheus_url: str,
        k6_binary: str = "k6",
        output_dir: str = "./results",
    ):
        """Initialize the K6Runner.

        Args:
            prometheus_url: URL of the Prometheus instance to test
            k6_binary: Path to k6 binary (default: "k6")
            output_dir: Directory for test output (default: "./results")
        """
        self.prometheus_url = prometheus_url
        self.k6_binary = k6_binary
        self.output_dir = output_dir
        self._scripts_dir = Path(__file__).parent.parent / "k6"

    def _check_k6_available(self) -> bool:
        """Check if k6 binary is available.

        Returns:
            True if k6 is available, False otherwise
        """
        # First check if k6_binary is an absolute path or in PATH
        k6_path = shutil.which(self.k6_binary)
        if k6_path:
            try:
                result = subprocess.run(
                    [k6_path, "version"],
                    capture_output=True,
                    text=True,
                    timeout=10,
                    check=False,
                )
                return result.returncode == 0
            except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
                return False
        return False

    def _resolve_script_path(self, script: str) -> Path:
        """Resolve script path to absolute path.

        Args:
            script: Script path (relative or absolute)

        Returns:
            Resolved absolute path

        Raises:
            FileNotFoundError: If script doesn't exist
        """
        script_path = Path(script)

        # If absolute path, use as-is
        if script_path.is_absolute():
            if script_path.exists():
                return script_path
            raise FileNotFoundError(f"k6 script not found: {script}")

        # Try relative to scripts directory
        relative_to_scripts = self._scripts_dir / script_path.name
        if relative_to_scripts.exists():
            return relative_to_scripts

        # Try relative to current directory
        if script_path.exists():
            return script_path.resolve()

        # Try with k6/ prefix
        if not script.startswith("k6/"):
            k6_prefixed = self._scripts_dir / script
            if k6_prefixed.exists():
                return k6_prefixed

        raise FileNotFoundError(f"k6 script not found: {script}")

    def _build_env_vars(
        self,
        config: K6Config,
    ) -> dict[str, str]:
        """Build environment variables for k6 execution.

        Args:
            config: Test configuration

        Returns:
            Dictionary of environment variables
        """
        env = os.environ.copy()
        env["PROMETHEUS_URL"] = config.prometheus_url
        env["VUS"] = str(config.vus)
        env["DURATION"] = config.duration
        env["ITERATIONS"] = str(config.iterations)

        # Add stages as comma-separated targets for stress tests
        if config.stages:
            stage_targets = ",".join(str(s.target) for s in config.stages)
            env["RAMP_STAGES"] = stage_targets

        # Add any custom environment variables
        env.update(config.env_vars)

        return env

    def _build_k6_command(
        self,
        config: K6Config,
        test_type: K6TestType,
        output_file: str,
    ) -> list[str]:
        """Build the k6 command with all arguments.

        Args:
            config: Test configuration
            test_type: Type of test being run
            output_file: Path to output JSON file

        Returns:
            List of command arguments
        """
        k6_path = shutil.which(self.k6_binary) or self.k6_binary

        cmd = [
            k6_path,
            "run",
            "--out", f"json={output_file}",
        ]

        # Add VUs and duration for load tests
        if test_type == K6TestType.LOAD:
            cmd.extend(["--vus", str(config.vus)])
            cmd.extend(["--duration", config.duration])

        # Add iterations for benchmark tests
        elif test_type == K6TestType.BENCHMARK:
            cmd.extend(["--iterations", str(config.iterations)])

        # Add script path
        cmd.append(str(config.script_path))

        return cmd

    def _parse_k6_json_output(self, output_file: str) -> K6Metrics:
        """Parse k6 JSON output file to extract metrics.

        Args:
            output_file: Path to k6 JSON output file

        Returns:
            K6Metrics with parsed values
        """
        metrics = K6Metrics()
        custom_metrics: dict[str, Any] = {}

        if not os.path.exists(output_file):
            return metrics

        try:
            with open(output_file, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue

                    try:
                        data = json.loads(line)
                        self._process_k6_data_point(data, metrics, custom_metrics)
                    except json.JSONDecodeError:
                        continue

            metrics.custom_metrics = custom_metrics
        except (OSError, IOError):
            pass

        return metrics

    def _process_k6_data_point(
        self,
        data: dict[str, Any],
        metrics: K6Metrics,
        custom_metrics: dict[str, Any],
    ) -> None:
        """Process a single k6 data point.

        Args:
            data: k6 data point
            metrics: K6Metrics to update
            custom_metrics: Custom metrics dict to update
        """
        data_type = data.get("type")
        metric_name = data.get("metric", "")

        if data_type == "Point":
            value = data.get("data", {}).get("value", 0)

            # Standard k6 metrics
            if metric_name == "http_reqs":
                metrics.http_reqs_count += 1
            elif metric_name == "iterations":
                metrics.iterations_count += 1
            elif metric_name == "vus":
                metrics.vus_max = max(metrics.vus_max, int(value))
            elif metric_name == "data_received":
                metrics.data_received_bytes += int(value)
            elif metric_name == "data_sent":
                metrics.data_sent_bytes += int(value)

            # Custom Prometheus metrics
            elif metric_name.startswith("prometheus_"):
                if metric_name not in custom_metrics:
                    custom_metrics[metric_name] = []
                custom_metrics[metric_name].append(value)

        elif data_type == "Metric":
            # Summary metrics at end of test
            contains = data.get("data", {}).get("contains", "")
            values = data.get("data", {}).get("values", {})

            if metric_name == "http_req_duration" and contains == "time":
                metrics.http_req_duration_avg_ms = values.get("avg", 0)
                metrics.http_req_duration_p50_ms = values.get("med", 0)
                metrics.http_req_duration_p90_ms = values.get("p(90)", 0)
                metrics.http_req_duration_p95_ms = values.get("p(95)", 0)
                metrics.http_req_duration_p99_ms = values.get("p(99)", 0)
            elif metric_name == "http_req_failed" and contains == "rate":
                metrics.http_req_failed_rate = values.get("rate", 0)
            elif metric_name == "http_reqs" and contains == "counter":
                metrics.http_reqs_count = int(values.get("count", 0))
                metrics.http_reqs_rate = values.get("rate", 0)
            elif metric_name == "iterations" and contains == "counter":
                metrics.iterations_count = int(values.get("count", 0))
                metrics.iterations_rate = values.get("rate", 0)
            elif metric_name == "vus_max" and contains == "gauge":
                metrics.vus_max = int(values.get("max", 0))

    def _parse_stdout_summary(self, stdout: str) -> tuple[dict[str, Any], bool]:
        """Parse k6 summary from stdout.

        Args:
            stdout: Standard output from k6

        Returns:
            Tuple of (summary_dict, thresholds_passed)
        """
        summary: dict[str, Any] = {}
        thresholds_passed = True

        # Look for JSON summary in output
        for line in stdout.strip().split('\n'):
            line = line.strip()
            if line.startswith('{') and line.endswith('}'):
                try:
                    data = json.loads(line)
                    if isinstance(data, dict):
                        summary = data
                        thresholds_passed = data.get("thresholds_passed", True)
                        break
                except json.JSONDecodeError:
                    continue

        # Check for threshold failures in output
        if "✗" in stdout or "threshold" in stdout.lower() and "failed" in stdout.lower():
            thresholds_passed = False

        return summary, thresholds_passed

    def parse_k6_output(self, output: str) -> dict[str, Any]:
        """Parse k6 JSON output into metrics dictionary.

        This is a public method for parsing k6 output externally.

        Requirements: 14.11

        Args:
            output: Raw k6 JSON output string

        Returns:
            Dictionary with parsed metrics
        """
        metrics: dict[str, Any] = {
            "http_req_duration": {},
            "http_reqs": {},
            "iterations": {},
            "vus": {},
            "custom": {},
        }

        for line in output.strip().split('\n'):
            line = line.strip()
            if not line:
                continue

            try:
                data = json.loads(line)
                data_type = data.get("type")
                metric_name = data.get("metric", "")

                if data_type == "Metric":
                    values = data.get("data", {}).get("values", {})

                    if metric_name == "http_req_duration":
                        metrics["http_req_duration"] = {
                            "avg": values.get("avg", 0),
                            "min": values.get("min", 0),
                            "max": values.get("max", 0),
                            "p50": values.get("med", 0),
                            "p90": values.get("p(90)", 0),
                            "p95": values.get("p(95)", 0),
                            "p99": values.get("p(99)", 0),
                        }
                    elif metric_name == "http_reqs":
                        metrics["http_reqs"] = {
                            "count": values.get("count", 0),
                            "rate": values.get("rate", 0),
                        }
                    elif metric_name == "iterations":
                        metrics["iterations"] = {
                            "count": values.get("count", 0),
                            "rate": values.get("rate", 0),
                        }
                    elif metric_name == "vus":
                        metrics["vus"] = {
                            "min": values.get("min", 0),
                            "max": values.get("max", 0),
                        }
                    elif metric_name.startswith("prometheus_"):
                        metrics["custom"][metric_name] = values

            except json.JSONDecodeError:
                continue

        return metrics

    def _run_k6(
        self,
        config: K6Config,
        test_type: K6TestType,
    ) -> K6Result:
        """Execute k6 test and collect results.

        Args:
            config: Test configuration
            test_type: Type of test to run

        Returns:
            K6Result with test results
        """
        result = K6Result(test_type=test_type, config=config)
        result.start_time = datetime.utcnow()

        # Check prerequisites
        if not self._check_k6_available():
            result.passed = False
            result.error_message = f"k6 binary not found: {self.k6_binary}"
            result.exit_code = 1
            result.end_time = datetime.utcnow()
            return result

        try:
            script_path = self._resolve_script_path(config.script_path or "")
            config.script_path = str(script_path)
        except FileNotFoundError as e:
            result.passed = False
            result.error_message = str(e)
            result.exit_code = 1
            result.end_time = datetime.utcnow()
            return result

        # Create output directory
        os.makedirs(self.output_dir, exist_ok=True)

        # Create temporary file for JSON output
        with tempfile.NamedTemporaryFile(
            mode='w',
            suffix='.json',
            delete=False,
            dir=self.output_dir,
        ) as f:
            output_file = f.name

        try:
            # Build command and environment
            cmd = self._build_k6_command(config, test_type, output_file)
            env = self._build_env_vars(config)

            # Execute k6
            process = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                env=env,
                timeout=config.timeout_seconds,
                check=False,
            )

            result.exit_code = process.returncode
            result.stdout = process.stdout
            result.stderr = process.stderr

            # Parse results
            if os.path.exists(output_file):
                result.metrics = self._parse_k6_json_output(output_file)

            # Parse summary from stdout
            summary, thresholds_passed = self._parse_stdout_summary(process.stdout)
            result.raw_summary = summary
            result.thresholds_passed = thresholds_passed

            # Determine overall pass/fail
            result.passed = process.returncode == 0 and thresholds_passed

            if process.returncode != 0 and not result.error_message:
                result.error_message = process.stderr or "k6 execution failed"

        except subprocess.TimeoutExpired:
            result.passed = False
            result.error_message = f"k6 execution timed out after {config.timeout_seconds}s"
            result.exit_code = 124  # Standard timeout exit code
        except (OSError, IOError) as e:
            result.passed = False
            result.error_message = str(e)
            result.exit_code = 1
        finally:
            # Clean up temporary file
            if os.path.exists(output_file):
                try:
                    os.remove(output_file)
                except OSError:
                    pass

        result.end_time = datetime.utcnow()
        return result

    def run_load_test(
        self,
        script: str,
        vus: int = 100,
        duration: str = "30m",
        timeout_seconds: Optional[int] = None,
        env_vars: Optional[dict[str, str]] = None,
    ) -> K6Result:
        """Run a k6 load test.

        Requirements: 14.8, 14.9, 14.10

        Args:
            script: Path to k6 script (relative or absolute)
            vus: Number of virtual users
            duration: Test duration (e.g., "30m", "1h")
            timeout_seconds: Timeout for k6 execution
            env_vars: Additional environment variables

        Returns:
            K6Result with test results
        """
        config = K6Config(
            prometheus_url=self.prometheus_url,
            vus=vus,
            duration=duration,
            script_path=script,
            k6_binary=self.k6_binary,
            output_dir=self.output_dir,
            timeout_seconds=timeout_seconds,
            env_vars=env_vars or {},
        )

        return self._run_k6(config, K6TestType.LOAD)

    def run_stress_test(
        self,
        script: str,
        stages: list[K6Stage],
        timeout_seconds: Optional[int] = None,
        env_vars: Optional[dict[str, str]] = None,
    ) -> K6Result:
        """Run a k6 stress test with ramping stages.

        Requirements: 14.8, 14.9, 14.10

        Args:
            script: Path to k6 script (relative or absolute)
            stages: List of K6Stage objects defining ramp stages
            timeout_seconds: Timeout for k6 execution
            env_vars: Additional environment variables

        Returns:
            K6Result with test results
        """
        config = K6Config(
            prometheus_url=self.prometheus_url,
            stages=stages,
            script_path=script,
            k6_binary=self.k6_binary,
            output_dir=self.output_dir,
            timeout_seconds=timeout_seconds,
            env_vars=env_vars or {},
        )

        return self._run_k6(config, K6TestType.STRESS)

    def run_benchmark(
        self,
        script: str,
        iterations: int = 100,
        timeout_seconds: Optional[int] = None,
        env_vars: Optional[dict[str, str]] = None,
    ) -> K6Result:
        """Run a k6 benchmark test.

        Requirements: 14.8, 14.9, 14.10

        Args:
            script: Path to k6 script (relative or absolute)
            iterations: Number of iterations to run
            timeout_seconds: Timeout for k6 execution
            env_vars: Additional environment variables

        Returns:
            K6Result with test results
        """
        config = K6Config(
            prometheus_url=self.prometheus_url,
            iterations=iterations,
            script_path=script,
            k6_binary=self.k6_binary,
            output_dir=self.output_dir,
            timeout_seconds=timeout_seconds,
            env_vars=env_vars or {},
        )

        return self._run_k6(config, K6TestType.BENCHMARK)


def run_k6_load_test(
    prometheus_url: str,
    script: str,
    vus: int = 100,
    duration: str = "30m",
) -> K6Result:
    """Convenience function to run a k6 load test.

    Requirements: 14.8, 14.9, 14.10, 14.11

    Args:
        prometheus_url: URL of the Prometheus instance
        script: Path to k6 script
        vus: Number of virtual users
        duration: Test duration

    Returns:
        K6Result with test results
    """
    runner = K6Runner(prometheus_url)
    return runner.run_load_test(script, vus, duration)


def run_k6_stress_test(
    prometheus_url: str,
    script: str,
    stages: list[tuple[str, int]],
) -> K6Result:
    """Convenience function to run a k6 stress test.

    Requirements: 14.8, 14.9, 14.10, 14.11

    Args:
        prometheus_url: URL of the Prometheus instance
        script: Path to k6 script
        stages: List of (duration, target_vus) tuples

    Returns:
        K6Result with test results
    """
    runner = K6Runner(prometheus_url)
    k6_stages = [K6Stage(duration=d, target=t) for d, t in stages]
    return runner.run_stress_test(script, k6_stages)


def run_k6_benchmark(
    prometheus_url: str,
    script: str,
    iterations: int = 100,
) -> K6Result:
    """Convenience function to run a k6 benchmark test.

    Requirements: 14.8, 14.9, 14.10, 14.11

    Args:
        prometheus_url: URL of the Prometheus instance
        script: Path to k6 script
        iterations: Number of iterations

    Returns:
        K6Result with test results
    """
    runner = K6Runner(prometheus_url)
    return runner.run_benchmark(script, iterations)
