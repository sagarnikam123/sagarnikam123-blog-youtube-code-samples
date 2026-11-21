"""
Data models for the Prometheus Testing Framework.

This module defines the core data structures used throughout the test framework
including TestResult, TestError, and related types.

Requirements: 10.1, 11.1
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Optional


class TestStatus(Enum):
    """Status of a test execution."""

    __test__ = False  # Tell pytest this is not a test class

    NOT_STARTED = "not_started"
    RUNNING = "running"
    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"
    ERROR = "error"
    TIMEOUT = "timeout"


class ErrorCategory(Enum):
    """Categories of test errors."""

    DEPLOYMENT = "deployment"
    EXECUTION = "execution"
    VALIDATION = "validation"
    NETWORK = "network"
    TIMEOUT = "timeout"
    CONFIGURATION = "configuration"


class ErrorSeverity(Enum):
    """Severity levels for test errors."""

    CRITICAL = "critical"
    WARNING = "warning"
    INFO = "info"


@dataclass
class TestError:
    """
    Represents an error that occurred during test execution.

    Requirements: 10.1, 11.1

    Attributes:
        error_code: Unique error identifier (e.g., "PROM_UNREACHABLE")
        message: Human-readable error description
        category: Error category (deployment, execution, validation)
        severity: Error severity level
        context: Additional context information
        remediation: Suggested fix for the error
        timestamp: When the error occurred
    """

    __test__ = False  # Tell pytest this is not a test class

    error_code: str
    message: str
    category: ErrorCategory
    severity: ErrorSeverity = ErrorSeverity.WARNING
    context: dict[str, Any] = field(default_factory=dict)
    remediation: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> dict[str, Any]:
        """Convert error to dictionary representation."""
        return {
            "error_code": self.error_code,
            "message": self.message,
            "category": self.category.value,
            "severity": self.severity.value,
            "context": self.context,
            "remediation": self.remediation,
            "timestamp": self.timestamp.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "TestError":
        """Create TestError from dictionary."""
        return cls(
            error_code=data["error_code"],
            message=data["message"],
            category=ErrorCategory(data["category"]),
            severity=ErrorSeverity(data.get("severity", "warning")),
            context=data.get("context", {}),
            remediation=data.get("remediation"),
            timestamp=datetime.fromisoformat(data["timestamp"])
                if "timestamp" in data else datetime.utcnow(),
        )


@dataclass
class MetricSnapshot:
    """
    A snapshot of metrics collected during test execution.

    Requirements: 11.1, 11.2
    """

    timestamp: datetime
    prometheus_metrics: dict[str, Any] = field(default_factory=dict)
    system_metrics: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "timestamp": self.timestamp.isoformat(),
            "prometheus_metrics": self.prometheus_metrics,
            "system_metrics": self.system_metrics,
        }


@dataclass
class TestResult:
    """
    Represents the result of a single test execution.

    Requirements: 10.1, 11.1

    Attributes:
        test_name: Name of the test
        test_type: Type of test (sanity, load, stress, etc.)
        status: Test execution status
        duration_seconds: How long the test took
        start_time: When the test started
        end_time: When the test ended
        message: Optional result message
        errors: List of errors encountered
        metrics: Collected metrics during test
        metadata: Additional test metadata
    """

    __test__ = False  # Tell pytest this is not a test class

    test_name: str
    test_type: str
    status: TestStatus = TestStatus.NOT_STARTED
    duration_seconds: float = 0.0
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    message: Optional[str] = None
    errors: list[TestError] = field(default_factory=list)
    metrics: list[MetricSnapshot] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def passed(self) -> bool:
        """Check if the test passed."""
        return self.status == TestStatus.PASSED

    @property
    def failed(self) -> bool:
        """Check if the test failed."""
        return self.status in (TestStatus.FAILED, TestStatus.ERROR, TestStatus.TIMEOUT)

    def add_error(self, error: TestError) -> None:
        """Add an error to the result."""
        self.errors.append(error)
        if error.severity == ErrorSeverity.CRITICAL:
            self.status = TestStatus.ERROR

    def add_metric_snapshot(self, snapshot: MetricSnapshot) -> None:
        """Add a metric snapshot to the result."""
        self.metrics.append(snapshot)

    def to_dict(self) -> dict[str, Any]:
        """Convert result to dictionary representation."""
        return {
            "test_name": self.test_name,
            "test_type": self.test_type,
            "status": self.status.value,
            "duration_seconds": self.duration_seconds,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "message": self.message,
            "errors": [e.to_dict() for e in self.errors],
            "metrics": [m.to_dict() for m in self.metrics],
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "TestResult":
        """Create TestResult from dictionary."""
        return cls(
            test_name=data["test_name"],
            test_type=data["test_type"],
            status=TestStatus(data.get("status", "not_started")),
            duration_seconds=data.get("duration_seconds", 0.0),
            start_time=datetime.fromisoformat(data["start_time"])
                if data.get("start_time") else None,
            end_time=datetime.fromisoformat(data["end_time"])
                if data.get("end_time") else None,
            message=data.get("message"),
            errors=[TestError.from_dict(e) for e in data.get("errors", [])],
            metadata=data.get("metadata", {}),
        )


@dataclass
class TestSuiteResult:
    """
    Represents the result of a complete test suite execution.

    Requirements: 11.3, 11.4, 11.5
    """

    __test__ = False  # Tell pytest this is not a test class

    suite_name: str
    platform: str
    prometheus_version: str
    start_time: datetime = field(default_factory=datetime.utcnow)
    end_time: Optional[datetime] = None
    results: list[TestResult] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def total_tests(self) -> int:
        """Total number of tests in the suite."""
        return len(self.results)

    @property
    def passed_tests(self) -> int:
        """Number of passed tests."""
        return sum(1 for r in self.results if r.passed)

    @property
    def failed_tests(self) -> int:
        """Number of failed tests."""
        return sum(1 for r in self.results if r.failed)

    @property
    def skipped_tests(self) -> int:
        """Number of skipped tests."""
        return sum(1 for r in self.results if r.status == TestStatus.SKIPPED)

    @property
    def duration_seconds(self) -> float:
        """Total duration of the test suite."""
        if self.end_time and self.start_time:
            return (self.end_time - self.start_time).total_seconds()
        return sum(r.duration_seconds for r in self.results)

    @property
    def success_rate(self) -> float:
        """Success rate as a percentage."""
        if self.total_tests == 0:
            return 0.0
        return (self.passed_tests / self.total_tests) * 100

    def add_result(self, result: TestResult) -> None:
        """Add a test result to the suite."""
        self.results.append(result)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "metadata": {
                "suite_name": self.suite_name,
                "platform": self.platform,
                "prometheus_version": self.prometheus_version,
                "start_time": self.start_time.isoformat(),
                "end_time": self.end_time.isoformat() if self.end_time else None,
                "duration_seconds": self.duration_seconds,
                **self.metadata,
            },
            "summary": {
                "total_tests": self.total_tests,
                "passed": self.passed_tests,
                "failed": self.failed_tests,
                "skipped": self.skipped_tests,
                "success_rate": self.success_rate,
            },
            "results": [r.to_dict() for r in self.results],
        }
