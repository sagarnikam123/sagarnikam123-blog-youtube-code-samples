"""
Configuration compatibility tests for Prometheus regression testing.

This module implements tests to verify that scrape configurations
and remote write configurations work correctly after Prometheus upgrades.

Requirements: 21.4, 21.5, 21.7
"""

import time
from datetime import datetime
from typing import Any, Optional

import httpx
import pytest
import yaml

from framework.models import (
    ErrorCategory,
    ErrorSeverity,
    TestError,
    TestResult,
    TestStatus,
)

from .config import ConfigCompatibilityConfig, RegressionTestConfig
from .models import (
    ComparisonStatus,
    ConfigCompatibilityResult,
    PrometheusVersion,
    RegressionTestReport,
)


class PrometheusConfigClient:
    """Client for checking Prometheus configuration compatibility.

    Provides methods to verify scrape configs and remote write
    configurations work correctly.
    """

    def __init__(self, base_url: str, timeout: float = 30.0):
        """Initialize the config client.

        Args:
            base_url: Base URL of the Prometheus instance
            timeout: Request timeout in seconds
        """
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self._client: Optional[httpx.Client] = None

    @property
    def client(self) -> httpx.Client:
        """Get or create the HTTP client."""
        if self._client is None:
            self._client = httpx.Client(timeout=self.timeout)
        return self._client

    def close(self) -> None:
        """Close the HTTP client."""
        if self._client is not None:
            self._client.close()
            self._client = None

    def is_healthy(self) -> bool:
        """Check if Prometheus is healthy."""
        url = f"{self.base_url}/-/healthy"
        try:
            response = self.client.get(url)
            return response.status_code == 200
        except Exception:
            return False

    def get_config(self) -> Optional[dict[str, Any]]:
        """Get the current Prometheus configuration.

        Returns:
            Parsed configuration dictionary or None
        """
        url = f"{self.base_url}/api/v1/status/config"
        try:
            response = self.client.get(url)
            if response.status_code == 200:
                data = response.json()
                if data.get("status") == "success":
                    yaml_config = data.get("data", {}).get("yaml", "")
                    return yaml.safe_load(yaml_config)
        except Exception:
            pass
        return None

    def get_targets(self) -> list[dict[str, Any]]:
        """Get all scrape targets.

        Returns:
            List of target information
        """
        url = f"{self.base_url}/api/v1/targets"
        try:
            response = self.client.get(url)
            if response.status_code == 200:
                data = response.json()
                if data.get("status") == "success":
                    return data.get("data", {}).get("activeTargets", [])
        except Exception:
            pass
        return []

    def get_scrape_pools(self) -> dict[str, list[dict[str, Any]]]:
        """Get targets grouped by scrape pool (job).

        Returns:
            Dictionary mapping job names to target lists
        """
        targets = self.get_targets()
        pools: dict[str, list[dict[str, Any]]] = {}

        for target in targets:
            job = target.get("labels", {}).get("job", "unknown")
            if job not in pools:
                pools[job] = []
            pools[job].append(target)

        return pools

    def check_scrape_config_working(self, job_name: str) -> tuple[bool, dict[str, Any]]:
        """Check if a scrape configuration is working.

        Args:
            job_name: Name of the scrape job to check

        Returns:
            Tuple of (working, details)
        """
        pools = self.get_scrape_pools()

        if job_name not in pools:
            return False, {"error": f"Job '{job_name}' not found in targets"}

        targets = pools[job_name]
        total = len(targets)
        up_count = sum(1 for t in targets if t.get("health") == "up")
        down_count = sum(1 for t in targets if t.get("health") == "down")

        details = {
            "total_targets": total,
            "up": up_count,
            "down": down_count,
            "targets": [
                {
                    "instance": t.get("labels", {}).get("instance", ""),
                    "health": t.get("health", ""),
                    "last_error": t.get("lastError", ""),
                }
                for t in targets
            ],
        }

        # Consider working if at least one target is up
        working = up_count > 0
        return working, details

    def check_remote_write_working(self) -> tuple[bool, dict[str, Any]]:
        """Check if remote write is working.

        Returns:
            Tuple of (working, details)
        """
        # Query remote write metrics
        url = f"{self.base_url}/api/v1/query"

        try:
            # Check for remote write success metrics
            response = self.client.get(
                url,
                params={"query": "prometheus_remote_storage_samples_total"},
            )

            if response.status_code != 200:
                return False, {"error": "Failed to query remote write metrics"}

            data = response.json()
            if data.get("status") != "success":
                return False, {"error": "Query failed"}

            results = data.get("data", {}).get("result", [])

            if not results:
                # No remote write configured
                return True, {"status": "no_remote_write_configured"}

            # Check for failed samples
            failed_response = self.client.get(
                url,
                params={"query": "prometheus_remote_storage_samples_failed_total"},
            )

            failed_results = []
            if failed_response.status_code == 200:
                failed_data = failed_response.json()
                if failed_data.get("status") == "success":
                    failed_results = failed_data.get("data", {}).get("result", [])

            total_samples = sum(
                float(r.get("value", [0, 0])[1])
                for r in results
            )
            failed_samples = sum(
                float(r.get("value", [0, 0])[1])
                for r in failed_results
            )

            details = {
                "total_samples": total_samples,
                "failed_samples": failed_samples,
                "success_rate": (
                    (total_samples - failed_samples) / total_samples * 100
                    if total_samples > 0 else 100
                ),
            }

            # Consider working if success rate > 95%
            working = details["success_rate"] > 95
            return working, details

        except Exception as e:
            return False, {"error": str(e)}


class ConfigCompatibilityTest:
    """
    Test class for verifying configuration compatibility between versions.

    This class checks that scrape configurations and remote write
    configurations continue to work after Prometheus upgrades.

    Requirements: 21.4, 21.5, 21.7
    """

    def __init__(
        self,
        regression_config: RegressionTestConfig,
        config_config: Optional[ConfigCompatibilityConfig] = None,
    ):
        """Initialize the config compatibility test.

        Args:
            regression_config: Regression test configuration
            config_config: Configuration compatibility settings
        """
        self.regression_config = regression_config
        self.config_config = config_config or ConfigCompatibilityConfig()
        self.baseline_client: Optional[PrometheusConfigClient] = None
        self.target_client: Optional[PrometheusConfigClient] = None

    def setup(self) -> tuple[bool, Optional[str]]:
        """Set up the test clients.

        Returns:
            Tuple of (success, error_message)
        """
        try:
            self.baseline_client = PrometheusConfigClient(
                self.regression_config.baseline_url,
                timeout=self.regression_config.timeout_seconds,
            )
            self.target_client = PrometheusConfigClient(
                self.regression_config.target_url,
                timeout=self.regression_config.timeout_seconds,
            )

            if not self.baseline_client.is_healthy():
                return False, f"Baseline Prometheus not healthy"

            if not self.target_client.is_healthy():
                return False, f"Target Prometheus not healthy"

            return True, None

        except Exception as e:
            return False, f"Setup failed: {str(e)}"

    def teardown(self) -> None:
        """Clean up test resources."""
        if self.baseline_client:
            self.baseline_client.close()
        if self.target_client:
            self.target_client.close()

    def check_scrape_configs(self) -> list[ConfigCompatibilityResult]:
        """Check scrape configuration compatibility.

        Returns:
            List of ConfigCompatibilityResult
        """
        results = []

        # Get all scrape jobs from baseline
        baseline_pools = self.baseline_client.get_scrape_pools()
        target_pools = self.target_client.get_scrape_pools()

        # Determine which jobs to check
        job_names = set(baseline_pools.keys())
        if self.config_config.scrape_configs and not self.config_config.test_all_configs:
            job_names = set(self.config_config.scrape_configs) & job_names

        for job_name in job_names:
            baseline_working, baseline_details = self.baseline_client.check_scrape_config_working(job_name)
            target_working, target_details = self.target_client.check_scrape_config_working(job_name)

            result = ConfigCompatibilityResult(
                config_type="scrape",
                config_name=job_name,
                baseline_working=baseline_working,
                target_working=target_working,
                details={
                    "baseline": baseline_details,
                    "target": target_details,
                },
            )
            result.compare()

            if not target_working and baseline_working:
                result.error = f"Scrape job '{job_name}' stopped working after upgrade"

            results.append(result)

        return results

    def check_remote_write_configs(self) -> list[ConfigCompatibilityResult]:
        """Check remote write configuration compatibility.

        Returns:
            List of ConfigCompatibilityResult
        """
        results = []

        baseline_working, baseline_details = self.baseline_client.check_remote_write_working()
        target_working, target_details = self.target_client.check_remote_write_working()

        result = ConfigCompatibilityResult(
            config_type="remote_write",
            config_name="default",
            baseline_working=baseline_working,
            target_working=target_working,
            details={
                "baseline": baseline_details,
                "target": target_details,
            },
        )
        result.compare()

        if not target_working and baseline_working:
            result.error = "Remote write stopped working after upgrade"

        results.append(result)

        return results

    def run(self) -> RegressionTestReport:
        """Run the configuration compatibility test.

        Returns:
            RegressionTestReport with all compatibility results
        """
        baseline_version = PrometheusVersion(
            version=self.regression_config.baseline_version,
            url=self.regression_config.baseline_url,
        )
        target_version = PrometheusVersion(
            version=self.regression_config.target_version,
            url=self.regression_config.target_url,
        )

        report = RegressionTestReport(
            test_name="config_compatibility",
            baseline_version=baseline_version,
            target_version=target_version,
            start_time=datetime.utcnow(),
        )

        success, error = self.setup()
        if not success:
            report.end_time = datetime.utcnow()
            report.passed = False
            report.regressions = [f"Setup failed: {error}"]
            return report

        try:
            # Check scrape configs
            scrape_results = self.check_scrape_configs()
            report.config_results.extend(scrape_results)

            # Check remote write configs
            remote_write_results = self.check_remote_write_configs()
            report.config_results.extend(remote_write_results)

            # Analyze regressions
            report.analyze_regressions()

        finally:
            self.teardown()
            report.end_time = datetime.utcnow()

        return report


def run_config_compatibility_test(
    baseline_url: str = "http://localhost:9090",
    target_url: str = "http://localhost:9091",
    baseline_version: str = "v3.4.0",
    target_version: str = "v3.5.0",
) -> TestResult:
    """
    Run configuration compatibility test and return a TestResult.

    Requirements: 21.4, 21.5

    Args:
        baseline_url: URL of the baseline Prometheus instance
        target_url: URL of the target Prometheus instance
        baseline_version: Expected baseline version
        target_version: Expected target version

    Returns:
        TestResult with pass/fail status and details
    """
    result = TestResult(
        test_name="config_compatibility",
        test_type="regression",
        status=TestStatus.RUNNING,
        start_time=datetime.utcnow(),
    )

    regression_config = RegressionTestConfig(
        baseline_version=baseline_version,
        baseline_url=baseline_url,
        target_version=target_version,
        target_url=target_url,
    )

    test = ConfigCompatibilityTest(regression_config)

    try:
        report = test.run()

        result.duration_seconds = report.duration_seconds
        result.end_time = datetime.utcnow()
        result.metadata["report"] = report.to_dict()

        scrape_count = sum(
            1 for cr in report.config_results if cr.config_type == "scrape"
        )
        remote_write_count = sum(
            1 for cr in report.config_results if cr.config_type == "remote_write"
        )

        if report.passed:
            result.status = TestStatus.PASSED
            result.message = (
                f"Config compatibility passed: {scrape_count} scrape configs, "
                f"{remote_write_count} remote write configs checked"
            )
        else:
            result.status = TestStatus.FAILED
            result.message = (
                f"Config compatibility failed: {len(report.regressions)} "
                f"regression(s) detected"
            )
            for regression in report.regressions:
                result.add_error(TestError(
                    error_code="CONFIG_REGRESSION_DETECTED",
                    message=regression,
                    category=ErrorCategory.VALIDATION,
                    severity=ErrorSeverity.WARNING,
                ))

    except Exception as e:
        result.status = TestStatus.ERROR
        result.end_time = datetime.utcnow()
        result.message = f"Test execution error: {str(e)}"
        result.add_error(TestError(
            error_code="TEST_EXECUTION_ERROR",
            message=str(e),
            category=ErrorCategory.EXECUTION,
            severity=ErrorSeverity.CRITICAL,
        ))

    return result


class TestConfigCompatibility:
    """
    Pytest test class for configuration compatibility tests.

    Requirements: 21.4, 21.5
    """

    @pytest.fixture
    def regression_config(self) -> RegressionTestConfig:
        """Create a regression test configuration fixture."""
        return RegressionTestConfig()

    @pytest.fixture
    def baseline_client(
        self,
        regression_config: RegressionTestConfig,
    ) -> PrometheusConfigClient:
        """Create a baseline Prometheus config client fixture."""
        client = PrometheusConfigClient(
            regression_config.baseline_url,
            timeout=regression_config.timeout_seconds,
        )
        yield client
        client.close()

    @pytest.fixture
    def target_client(
        self,
        regression_config: RegressionTestConfig,
    ) -> PrometheusConfigClient:
        """Create a target Prometheus config client fixture."""
        client = PrometheusConfigClient(
            regression_config.target_url,
            timeout=regression_config.timeout_seconds,
        )
        yield client
        client.close()

    def test_scrape_configs_work_after_upgrade(
        self,
        baseline_client: PrometheusConfigClient,
        target_client: PrometheusConfigClient,
    ):
        """
        Test that scrape configurations work after upgrade.

        Requirements: 21.4

        Verifies:
        - All scrape jobs from baseline exist in target
        - Scrape jobs that worked in baseline still work in target
        """
        if not baseline_client.is_healthy():
            pytest.skip("Baseline Prometheus not available")
        if not target_client.is_healthy():
            pytest.skip("Target Prometheus not available")

        baseline_pools = baseline_client.get_scrape_pools()
        target_pools = target_client.get_scrape_pools()

        # All baseline jobs should exist in target
        missing_jobs = set(baseline_pools.keys()) - set(target_pools.keys())
        assert not missing_jobs, (
            f"Scrape jobs missing in target: {missing_jobs}"
        )

        # Check each job is working
        broken_jobs = []
        for job_name in baseline_pools.keys():
            baseline_working, _ = baseline_client.check_scrape_config_working(job_name)
            target_working, target_details = target_client.check_scrape_config_working(job_name)

            if baseline_working and not target_working:
                broken_jobs.append(f"{job_name}: {target_details}")

        assert not broken_jobs, (
            f"Scrape jobs broken after upgrade: {broken_jobs}"
        )

    def test_remote_write_works_after_upgrade(
        self,
        baseline_client: PrometheusConfigClient,
        target_client: PrometheusConfigClient,
    ):
        """
        Test that remote write continues working after upgrade.

        Requirements: 21.5

        Verifies:
        - Remote write that worked in baseline still works in target
        - Success rate remains acceptable
        """
        if not baseline_client.is_healthy():
            pytest.skip("Baseline Prometheus not available")
        if not target_client.is_healthy():
            pytest.skip("Target Prometheus not available")

        baseline_working, baseline_details = baseline_client.check_remote_write_working()
        target_working, target_details = target_client.check_remote_write_working()

        # If baseline had remote write working, target should too
        if baseline_working:
            assert target_working, (
                f"Remote write stopped working after upgrade. "
                f"Baseline: {baseline_details}, Target: {target_details}"
            )

    def test_target_health_maintained(
        self,
        baseline_client: PrometheusConfigClient,
        target_client: PrometheusConfigClient,
    ):
        """
        Test that target health is maintained after upgrade.

        Requirements: 21.4

        Verifies:
        - Targets that were healthy in baseline are healthy in target
        """
        if not baseline_client.is_healthy():
            pytest.skip("Baseline Prometheus not available")
        if not target_client.is_healthy():
            pytest.skip("Target Prometheus not available")

        baseline_targets = baseline_client.get_targets()
        target_targets = target_client.get_targets()

        # Create lookup by instance
        baseline_by_instance = {
            t.get("labels", {}).get("instance", ""): t
            for t in baseline_targets
        }
        target_by_instance = {
            t.get("labels", {}).get("instance", ""): t
            for t in target_targets
        }

        degraded_targets = []
        for instance, baseline_target in baseline_by_instance.items():
            if instance in target_by_instance:
                target_target = target_by_instance[instance]

                # If baseline was up but target is down
                if (baseline_target.get("health") == "up" and
                    target_target.get("health") == "down"):
                    degraded_targets.append({
                        "instance": instance,
                        "error": target_target.get("lastError", "Unknown"),
                    })

        assert not degraded_targets, (
            f"Targets degraded after upgrade: {degraded_targets}"
        )
