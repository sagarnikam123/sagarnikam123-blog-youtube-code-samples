"""
Test Runner for the Prometheus Testing Framework.

This module provides the TestRunner class for executing tests from the Test Runner Host
against local or remote Prometheus deployments. It supports running individual tests,
test suites, parallel execution, and timeout handling.

Requirements: 10.3, 10.5, 10.7, 9.1.1, 9.1.2, 9.1.3, 9.1.4, 9.1.5
"""

import asyncio
import concurrent.futures
import logging
import signal
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Optional

from .config import TestConfig, load_config
from .models import (
    ErrorCategory,
    ErrorSeverity,
    TestError,
    TestResult,
    TestStatus,
    TestSuiteResult,
)

logger = logging.getLogger(__name__)


class TestType(Enum):
    """Supported test types."""

    SANITY = "sanity"
    INTEGRATION = "integration"
    LOAD = "load"
    STRESS = "stress"
    PERFORMANCE = "performance"
    SCALABILITY = "scalability"
    ENDURANCE = "endurance"
    RELIABILITY = "reliability"
    CHAOS = "chaos"
    REGRESSION = "regression"
    SECURITY = "security"


class ExecutionMode(Enum):
    """Test execution modes."""

    SEQUENTIAL = "sequential"
    PARALLEL = "parallel"


@dataclass
class TestSpec:
    """
    Specification for a single test to be executed.

    Attributes:
        name: Unique test name
        test_type: Type of test (sanity, load, etc.)
        test_func: Callable that executes the test
        timeout_seconds: Maximum time allowed for test execution
        dependencies: List of test names that must complete first
        enabled: Whether the test is enabled
        metadata: Additional test metadata
    """

    name: str
    test_type: TestType
    test_func: Callable[..., TestResult]
    timeout_seconds: int = 300
    dependencies: list[str] = field(default_factory=list)
    enabled: bool = True
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class RunnerConfig:
    """
    Configuration for the test runner.

    Requirements: 10.3, 10.5, 10.7

    Attributes:
        execution_mode: Sequential or parallel execution
        max_workers: Maximum parallel workers (for parallel mode)
        default_timeout_seconds: Default timeout for tests
        fail_fast: Stop on first failure
        retry_count: Number of retries for failed tests
        retry_delay_seconds: Delay between retries
        collect_metrics: Whether to collect metrics during tests
        prometheus_url: URL of the Prometheus instance to test
    """

    execution_mode: ExecutionMode = ExecutionMode.SEQUENTIAL
    max_workers: int = 4
    default_timeout_seconds: int = 300
    fail_fast: bool = False
    retry_count: int = 0
    retry_delay_seconds: int = 5
    collect_metrics: bool = True
    prometheus_url: str = "http://localhost:9090"


class TestTimeoutError(Exception):
    """Raised when a test exceeds its timeout."""

    def __init__(self, message: str, timeout_seconds: int = 0):
        super().__init__(message)
        self.timeout_seconds = timeout_seconds


class TestRunner:
    """
    Test runner for executing Prometheus tests from the Test Runner Host.

    This class orchestrates test execution, supporting:
    - Running individual tests or full test suites
    - Sequential and parallel execution modes
    - Timeout handling for long-running tests
    - Execution from Test Runner Host against local/remote targets

    Requirements: 10.3, 10.5, 10.7, 9.1.1, 9.1.2, 9.1.3, 9.1.4, 9.1.5

    Example usage:
        # Create runner with configuration
        config = TestConfig.from_yaml("config/default.yaml")
        runner = TestRunner(config)

        # Run all enabled tests
        results = runner.run_all()

        # Run specific test type
        results = runner.run_test_type(TestType.SANITY)

        # Run single test
        result = runner.run_test("api_accessibility")
    """

    def __init__(
        self,
        config: Optional[TestConfig] = None,
        runner_config: Optional[RunnerConfig] = None,
    ):
        """
        Initialize the test runner.

        Args:
            config: Test configuration (loaded from YAML or defaults)
            runner_config: Runner-specific configuration
        """
        self.config = config or TestConfig()
        self.runner_config = runner_config or RunnerConfig(
            prometheus_url=self.config.prometheus.url
        )
        self._tests: dict[str, TestSpec] = {}
        self._results: dict[str, TestResult] = {}
        self._suite_result: Optional[TestSuiteResult] = None
        self._running = False
        self._cancelled = False

        # Set up signal handlers for graceful shutdown
        self._setup_signal_handlers()

    def _setup_signal_handlers(self) -> None:
        """Set up signal handlers for graceful shutdown."""
        if sys.platform != "win32":
            signal.signal(signal.SIGTERM, self._handle_shutdown)
            signal.signal(signal.SIGINT, self._handle_shutdown)

    def _handle_shutdown(self, signum: int, frame: Any) -> None:  # noqa: ARG002
        """Handle shutdown signals gracefully."""
        logger.info("Received shutdown signal %d, cancelling tests...", signum)
        self._cancelled = True
        _ = frame  # Acknowledge unused parameter

    @property
    def prometheus_url(self) -> str:
        """Get the Prometheus URL being tested."""
        return self.runner_config.prometheus_url

    @prometheus_url.setter
    def prometheus_url(self, url: str) -> None:
        """Set the Prometheus URL to test."""
        self.runner_config.prometheus_url = url

    def register_test(self, spec: TestSpec) -> None:
        """
        Register a test specification.

        Args:
            spec: Test specification to register
        """
        self._tests[spec.name] = spec
        logger.debug("Registered test: %s (%s)", spec.name, spec.test_type.value)

    def register_tests(self, specs: list[TestSpec]) -> None:
        """
        Register multiple test specifications.

        Args:
            specs: List of test specifications to register
        """
        for spec in specs:
            self.register_test(spec)

    def get_test(self, name: str) -> Optional[TestSpec]:
        """
        Get a registered test by name.

        Args:
            name: Test name

        Returns:
            TestSpec if found, None otherwise
        """
        return self._tests.get(name)

    def get_tests_by_type(self, test_type: TestType) -> list[TestSpec]:
        """
        Get all tests of a specific type.

        Args:
            test_type: Type of tests to retrieve

        Returns:
            List of matching test specifications
        """
        return [
            spec for spec in self._tests.values()
            if spec.test_type == test_type and spec.enabled
        ]

    def get_enabled_tests(self) -> list[TestSpec]:
        """
        Get all enabled tests.

        Returns:
            List of enabled test specifications
        """
        return [spec for spec in self._tests.values() if spec.enabled]


    def _check_dependencies(self, spec: TestSpec) -> bool:
        """
        Check if all dependencies for a test have completed successfully.

        Args:
            spec: Test specification to check

        Returns:
            True if all dependencies passed, False otherwise
        """
        for dep_name in spec.dependencies:
            if dep_name not in self._results:
                return False
            if not self._results[dep_name].passed:
                return False
        return True

    def _execute_with_timeout(
        self,
        spec: TestSpec,
        **kwargs: Any,
    ) -> TestResult:
        """
        Execute a test with timeout handling.

        Requirements: 10.7

        Args:
            spec: Test specification
            **kwargs: Additional arguments to pass to test function

        Returns:
            TestResult with execution results
        """
        timeout = spec.timeout_seconds or self.runner_config.default_timeout_seconds
        result = TestResult(
            test_name=spec.name,
            test_type=spec.test_type.value,
            status=TestStatus.RUNNING,
            start_time=datetime.utcnow(),
            metadata=spec.metadata.copy(),
        )

        try:
            # Use concurrent.futures for timeout handling
            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
                future = executor.submit(
                    spec.test_func,
                    prometheus_url=self.runner_config.prometheus_url,
                    config=self.config,
                    **kwargs,
                )

                try:
                    test_result = future.result(timeout=timeout)

                    # Merge results
                    result.status = test_result.status
                    result.message = test_result.message
                    result.errors = test_result.errors
                    result.metrics = test_result.metrics
                    result.metadata.update(test_result.metadata)

                except concurrent.futures.TimeoutExpired:
                    result.status = TestStatus.TIMEOUT
                    result.message = f"Test timed out after {timeout} seconds"
                    result.add_error(TestError(
                        error_code="TEST_TIMEOUT",
                        message=f"Test '{spec.name}' exceeded timeout of {timeout}s",
                        category=ErrorCategory.TIMEOUT,
                        severity=ErrorSeverity.CRITICAL,
                        context={"timeout_seconds": timeout},
                        remediation="Increase timeout or optimize test",
                    ))

                    # Cancel the future
                    future.cancel()

        except Exception as e:
            result.status = TestStatus.ERROR
            result.message = f"Test execution error: {str(e)}"
            result.add_error(TestError(
                error_code="TEST_EXECUTION_ERROR",
                message=str(e),
                category=ErrorCategory.EXECUTION,
                severity=ErrorSeverity.CRITICAL,
                context={"exception_type": type(e).__name__},
            ))

        result.end_time = datetime.utcnow()
        if result.start_time:
            result.duration_seconds = (
                result.end_time - result.start_time
            ).total_seconds()

        return result

    def _execute_test(
        self,
        spec: TestSpec,
        **kwargs: Any,
    ) -> TestResult:
        """
        Execute a single test with retry support.

        Args:
            spec: Test specification
            **kwargs: Additional arguments to pass to test function

        Returns:
            TestResult with execution results
        """
        if self._cancelled:
            return TestResult(
                test_name=spec.name,
                test_type=spec.test_type.value,
                status=TestStatus.SKIPPED,
                message="Test cancelled due to shutdown",
            )

        # Check dependencies
        if not self._check_dependencies(spec):
            return TestResult(
                test_name=spec.name,
                test_type=spec.test_type.value,
                status=TestStatus.SKIPPED,
                message="Skipped due to failed dependencies",
                metadata={"dependencies": spec.dependencies},
            )

        logger.info("Running test: %s", spec.name)

        # Execute with retries
        last_result: Optional[TestResult] = None
        for attempt in range(self.runner_config.retry_count + 1):
            if attempt > 0:
                logger.info(
                    "Retrying test %s (attempt %d/%d)",
                    spec.name,
                    attempt + 1,
                    self.runner_config.retry_count + 1,
                )
                time.sleep(self.runner_config.retry_delay_seconds)

            result = self._execute_with_timeout(spec, **kwargs)
            last_result = result

            if result.passed:
                break

        if last_result:
            self._results[spec.name] = last_result
            logger.info(
                "Test %s completed: %s",
                spec.name,
                last_result.status.value,
            )

        return last_result or TestResult(
            test_name=spec.name,
            test_type=spec.test_type.value,
            status=TestStatus.ERROR,
            message="No result returned",
        )

    def run_test(
        self,
        name: str,
        **kwargs: Any,
    ) -> TestResult:
        """
        Run a single test by name.

        Requirements: 10.3

        Args:
            name: Name of the test to run
            **kwargs: Additional arguments to pass to test function

        Returns:
            TestResult with execution results

        Raises:
            ValueError: If test is not found
        """
        spec = self.get_test(name)
        if not spec:
            raise ValueError(f"Test not found: {name}")

        if not spec.enabled:
            return TestResult(
                test_name=name,
                test_type=spec.test_type.value,
                status=TestStatus.SKIPPED,
                message="Test is disabled",
            )

        return self._execute_test(spec, **kwargs)

    def run_test_type(
        self,
        test_type: TestType,
        **kwargs: Any,
    ) -> list[TestResult]:
        """
        Run all tests of a specific type.

        Requirements: 10.3

        Args:
            test_type: Type of tests to run
            **kwargs: Additional arguments to pass to test functions

        Returns:
            List of TestResult objects
        """
        specs = self.get_tests_by_type(test_type)
        if not specs:
            logger.warning("No tests found for type: %s", test_type.value)
            return []

        return self._run_tests(specs, **kwargs)

    def _run_tests_sequential(
        self,
        specs: list[TestSpec],
        **kwargs: Any,
    ) -> list[TestResult]:
        """
        Run tests sequentially.

        Args:
            specs: List of test specifications to run
            **kwargs: Additional arguments to pass to test functions

        Returns:
            List of TestResult objects
        """
        results: list[TestResult] = []

        for spec in specs:
            if self._cancelled:
                results.append(TestResult(
                    test_name=spec.name,
                    test_type=spec.test_type.value,
                    status=TestStatus.SKIPPED,
                    message="Test cancelled due to shutdown",
                ))
                continue

            result = self._execute_test(spec, **kwargs)
            results.append(result)

            if self.runner_config.fail_fast and result.failed:
                logger.warning(
                    "Fail-fast enabled, stopping after failure: %s",
                    spec.name,
                )
                # Mark remaining tests as skipped
                remaining = specs[specs.index(spec) + 1:]
                for remaining_spec in remaining:
                    results.append(TestResult(
                        test_name=remaining_spec.name,
                        test_type=remaining_spec.test_type.value,
                        status=TestStatus.SKIPPED,
                        message="Skipped due to fail-fast",
                    ))
                break

        return results

    def _run_tests_parallel(
        self,
        specs: list[TestSpec],
        **kwargs: Any,
    ) -> list[TestResult]:
        """
        Run tests in parallel.

        Requirements: 10.5

        Args:
            specs: List of test specifications to run
            **kwargs: Additional arguments to pass to test functions

        Returns:
            List of TestResult objects
        """
        results: list[TestResult] = []

        # Separate tests with and without dependencies
        independent_tests = [s for s in specs if not s.dependencies]
        dependent_tests = [s for s in specs if s.dependencies]

        # Run independent tests in parallel
        with concurrent.futures.ThreadPoolExecutor(
            max_workers=self.runner_config.max_workers
        ) as executor:
            future_to_spec = {
                executor.submit(self._execute_test, spec, **kwargs): spec
                for spec in independent_tests
            }

            for future in concurrent.futures.as_completed(future_to_spec):
                spec = future_to_spec[future]
                try:
                    result = future.result()
                    results.append(result)
                except Exception as e:
                    results.append(TestResult(
                        test_name=spec.name,
                        test_type=spec.test_type.value,
                        status=TestStatus.ERROR,
                        message=f"Parallel execution error: {str(e)}",
                    ))

                if self.runner_config.fail_fast and results[-1].failed:
                    logger.warning("Fail-fast enabled, cancelling remaining tests")
                    self._cancelled = True
                    break

        # Run dependent tests sequentially (they depend on results)
        if not self._cancelled:
            for spec in dependent_tests:
                result = self._execute_test(spec, **kwargs)
                results.append(result)

                if self.runner_config.fail_fast and result.failed:
                    break
        else:
            # Mark dependent tests as skipped
            for spec in dependent_tests:
                results.append(TestResult(
                    test_name=spec.name,
                    test_type=spec.test_type.value,
                    status=TestStatus.SKIPPED,
                    message="Skipped due to fail-fast",
                ))

        return results

    def _run_tests(
        self,
        specs: list[TestSpec],
        **kwargs: Any,
    ) -> list[TestResult]:
        """
        Run a list of tests based on execution mode.

        Args:
            specs: List of test specifications to run
            **kwargs: Additional arguments to pass to test functions

        Returns:
            List of TestResult objects
        """
        if self.runner_config.execution_mode == ExecutionMode.PARALLEL:
            return self._run_tests_parallel(specs, **kwargs)
        return self._run_tests_sequential(specs, **kwargs)


    def run_all(self, **kwargs: Any) -> TestSuiteResult:
        """
        Run all enabled tests.

        Requirements: 10.3

        Args:
            **kwargs: Additional arguments to pass to test functions

        Returns:
            TestSuiteResult with all test results
        """
        self._running = True
        self._cancelled = False
        self._results.clear()

        self._suite_result = TestSuiteResult(
            suite_name=self.config.name,
            platform=self.config.platform,
            prometheus_version=self.config.prometheus.version,
            start_time=datetime.utcnow(),
            metadata={
                "deployment_mode": self.config.deployment_mode,
                "prometheus_url": self.runner_config.prometheus_url,
                "execution_mode": self.runner_config.execution_mode.value,
            },
        )

        try:
            specs = self.get_enabled_tests()

            # Sort by test type to run in logical order
            type_order = [
                TestType.SANITY,
                TestType.INTEGRATION,
                TestType.LOAD,
                TestType.PERFORMANCE,
                TestType.SCALABILITY,
                TestType.STRESS,
                TestType.ENDURANCE,
                TestType.RELIABILITY,
                TestType.CHAOS,
                TestType.REGRESSION,
                TestType.SECURITY,
            ]

            specs.sort(key=lambda s: (
                type_order.index(s.test_type) if s.test_type in type_order else 999,
                s.name,
            ))

            results = self._run_tests(specs, **kwargs)

            for result in results:
                self._suite_result.add_result(result)

        finally:
            self._suite_result.end_time = datetime.utcnow()
            self._running = False

        return self._suite_result

    def run_suite(
        self,
        test_types: list[TestType],
        **kwargs: Any,
    ) -> TestSuiteResult:
        """
        Run a suite of specific test types.

        Requirements: 10.3

        Args:
            test_types: List of test types to run
            **kwargs: Additional arguments to pass to test functions

        Returns:
            TestSuiteResult with all test results
        """
        self._running = True
        self._cancelled = False
        self._results.clear()

        self._suite_result = TestSuiteResult(
            suite_name=f"{self.config.name}-suite",
            platform=self.config.platform,
            prometheus_version=self.config.prometheus.version,
            start_time=datetime.utcnow(),
            metadata={
                "deployment_mode": self.config.deployment_mode,
                "prometheus_url": self.runner_config.prometheus_url,
                "test_types": [t.value for t in test_types],
            },
        )

        try:
            for test_type in test_types:
                if self._cancelled:
                    break

                results = self.run_test_type(test_type, **kwargs)
                for result in results:
                    self._suite_result.add_result(result)

        finally:
            self._suite_result.end_time = datetime.utcnow()
            self._running = False

        return self._suite_result

    def get_exit_code(self) -> int:
        """
        Get the exit code based on test results.

        Requirements: 10.4

        Returns:
            0 if all tests passed, non-zero otherwise
        """
        if not self._suite_result:
            return 1

        if self._suite_result.failed_tests > 0:
            return 1

        return 0

    def cancel(self) -> None:
        """Cancel running tests."""
        self._cancelled = True
        logger.info("Test execution cancelled")

    @property
    def is_running(self) -> bool:
        """Check if tests are currently running."""
        return self._running

    @property
    def is_cancelled(self) -> bool:
        """Check if execution was cancelled."""
        return self._cancelled


class AsyncTestRunner:
    """
    Asynchronous test runner for executing Prometheus tests.

    This class provides async support for test execution, useful for
    I/O-bound tests and better concurrency handling.

    Requirements: 10.3, 10.5, 10.7, 9.1.1, 9.1.2, 9.1.3, 9.1.4, 9.1.5
    """

    def __init__(
        self,
        config: Optional[TestConfig] = None,
        runner_config: Optional[RunnerConfig] = None,
    ):
        """
        Initialize the async test runner.

        Args:
            config: Test configuration
            runner_config: Runner-specific configuration
        """
        self.config = config or TestConfig()
        self.runner_config = runner_config or RunnerConfig(
            prometheus_url=self.config.prometheus.url
        )
        self._tests: dict[str, TestSpec] = {}
        self._results: dict[str, TestResult] = {}
        self._cancelled = False

    def register_test(self, spec: TestSpec) -> None:
        """Register a test specification."""
        self._tests[spec.name] = spec

    async def _execute_with_timeout(
        self,
        spec: TestSpec,
        **kwargs: Any,
    ) -> TestResult:
        """
        Execute a test with async timeout handling.

        Requirements: 10.7

        Args:
            spec: Test specification
            **kwargs: Additional arguments

        Returns:
            TestResult with execution results
        """
        timeout = spec.timeout_seconds or self.runner_config.default_timeout_seconds
        result = TestResult(
            test_name=spec.name,
            test_type=spec.test_type.value,
            status=TestStatus.RUNNING,
            start_time=datetime.utcnow(),
        )

        try:
            # Run test function in executor to avoid blocking
            loop = asyncio.get_event_loop()
            test_result = await asyncio.wait_for(
                loop.run_in_executor(
                    None,
                    lambda: spec.test_func(
                        prometheus_url=self.runner_config.prometheus_url,
                        config=self.config,
                        **kwargs,
                    ),
                ),
                timeout=timeout,
            )

            result.status = test_result.status
            result.message = test_result.message
            result.errors = test_result.errors
            result.metrics = test_result.metrics

        except asyncio.TimeoutError:
            result.status = TestStatus.TIMEOUT
            result.message = f"Test timed out after {timeout} seconds"
            result.add_error(TestError(
                error_code="TEST_TIMEOUT",
                message=f"Test '{spec.name}' exceeded timeout of {timeout}s",
                category=ErrorCategory.TIMEOUT,
                severity=ErrorSeverity.CRITICAL,
            ))

        except Exception as e:
            result.status = TestStatus.ERROR
            result.message = f"Test execution error: {str(e)}"
            result.add_error(TestError(
                error_code="TEST_EXECUTION_ERROR",
                message=str(e),
                category=ErrorCategory.EXECUTION,
                severity=ErrorSeverity.CRITICAL,
            ))

        result.end_time = datetime.utcnow()
        if result.start_time:
            result.duration_seconds = (
                result.end_time - result.start_time
            ).total_seconds()

        return result

    async def run_test(self, name: str, **kwargs: Any) -> TestResult:
        """
        Run a single test asynchronously.

        Args:
            name: Test name
            **kwargs: Additional arguments

        Returns:
            TestResult with execution results
        """
        spec = self._tests.get(name)
        if not spec:
            raise ValueError(f"Test not found: {name}")

        return await self._execute_with_timeout(spec, **kwargs)

    async def run_tests_parallel(
        self,
        specs: list[TestSpec],
        max_concurrent: int = 4,
        **kwargs: Any,
    ) -> list[TestResult]:
        """
        Run tests in parallel with concurrency limit.

        Requirements: 10.5

        Args:
            specs: List of test specifications
            max_concurrent: Maximum concurrent tests
            **kwargs: Additional arguments

        Returns:
            List of TestResult objects
        """
        semaphore = asyncio.Semaphore(max_concurrent)

        async def run_with_semaphore(spec: TestSpec) -> TestResult:
            async with semaphore:
                return await self._execute_with_timeout(spec, **kwargs)

        tasks = [run_with_semaphore(spec) for spec in specs]
        return await asyncio.gather(*tasks)

    async def run_all(self, **kwargs: Any) -> TestSuiteResult:
        """
        Run all enabled tests asynchronously.

        Args:
            **kwargs: Additional arguments

        Returns:
            TestSuiteResult with all results
        """
        suite_result = TestSuiteResult(
            suite_name=self.config.name,
            platform=self.config.platform,
            prometheus_version=self.config.prometheus.version,
            start_time=datetime.utcnow(),
        )

        specs = [s for s in self._tests.values() if s.enabled]

        if self.runner_config.execution_mode == ExecutionMode.PARALLEL:
            results = await self.run_tests_parallel(
                specs,
                max_concurrent=self.runner_config.max_workers,
                **kwargs,
            )
        else:
            results = []
            for spec in specs:
                result = await self._execute_with_timeout(spec, **kwargs)
                results.append(result)

        for result in results:
            suite_result.add_result(result)

        suite_result.end_time = datetime.utcnow()
        return suite_result


def create_runner(
    config_path: Optional[str] = None,
    platform: Optional[str] = None,
    deployment_mode: Optional[str] = None,
    prometheus_url: Optional[str] = None,
    execution_mode: str = "sequential",
    max_workers: int = 4,
    timeout_seconds: int = 300,
    fail_fast: bool = False,
) -> TestRunner:
    """
    Factory function to create a configured test runner.

    Requirements: 10.3, 10.5, 10.7, 9.1.1, 9.1.2, 9.1.3, 9.1.4, 9.1.5

    Args:
        config_path: Path to YAML configuration file
        platform: Target platform override
        deployment_mode: Deployment mode override
        prometheus_url: Prometheus URL override
        execution_mode: "sequential" or "parallel"
        max_workers: Maximum parallel workers
        timeout_seconds: Default test timeout
        fail_fast: Stop on first failure

    Returns:
        Configured TestRunner instance
    """
    # Load configuration
    config = load_config(
        config_path=config_path,
        platform=platform,
        deployment_mode=deployment_mode,
        prometheus_url=prometheus_url,
    )

    # Create runner configuration
    runner_config = RunnerConfig(
        execution_mode=ExecutionMode(execution_mode),
        max_workers=max_workers,
        default_timeout_seconds=timeout_seconds,
        fail_fast=fail_fast,
        prometheus_url=prometheus_url or config.prometheus.url,
    )

    return TestRunner(config=config, runner_config=runner_config)


def run_tests(
    test_types: Optional[list[str]] = None,
    config_path: Optional[str] = None,
    prometheus_url: Optional[str] = None,
    parallel: bool = False,
    timeout_seconds: int = 300,
) -> int:
    """
    Convenience function to run tests and return exit code.

    Requirements: 10.3, 10.4, 10.5, 10.7

    Args:
        test_types: List of test type names to run (None for all)
        config_path: Path to configuration file
        prometheus_url: Prometheus URL to test
        parallel: Whether to run tests in parallel
        timeout_seconds: Default test timeout

    Returns:
        Exit code (0 for success, non-zero for failure)
    """
    runner = create_runner(
        config_path=config_path,
        prometheus_url=prometheus_url,
        execution_mode="parallel" if parallel else "sequential",
        timeout_seconds=timeout_seconds,
    )

    if test_types:
        types = [TestType(t) for t in test_types]
        runner.run_suite(types)
    else:
        runner.run_all()

    return runner.get_exit_code()
