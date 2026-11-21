"""
Data models for Prometheus regression tests.

This module defines data structures for version comparison,
rule comparison, and configuration compatibility testing.

Requirements: 21.1, 21.2, 21.3, 21.4, 21.5, 21.6, 21.7
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Optional


class RegressionType(Enum):
    """Types of regression tests."""

    QUERY_RESULT = "query_result"
    ALERTING_RULE = "alerting_rule"
    RECORDING_RULE = "recording_rule"
    SCRAPE_CONFIG = "scrape_config"
    REMOTE_WRITE = "remote_write"
    PERFORMANCE = "performance"


class ComparisonStatus(Enum):
    """Status of a comparison result."""

    IDENTICAL = "identical"
    DIFFERENT = "different"
    ERROR = "error"
    SKIPPED = "skipped"


@dataclass
class PrometheusVersion:
    """Represents a Prometheus version for comparison.

    Attributes:
        version: Version string (e.g., "v3.5.0")
        url: URL of the Prometheus instance
        namespace: Kubernetes namespace (if applicable)
    """

    version: str
    url: str
    namespace: str = "monitoring"

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "version": self.version,
            "url": self.url,
            "namespace": self.namespace,
        }


@dataclass
class QueryResult:
    """Result of a PromQL query execution.

    Attributes:
        query: The PromQL query executed
        result_type: Type of result (vector, matrix, scalar, string)
        data: The query result data
        execution_time_ms: Query execution time in milliseconds
        timestamp: When the query was executed
        error: Error message if query failed
    """

    query: str
    result_type: Optional[str] = None
    data: Any = None
    execution_time_ms: float = 0.0
    timestamp: Optional[datetime] = None
    error: Optional[str] = None

    @property
    def success(self) -> bool:
        """Check if query was successful."""
        return self.error is None and self.data is not None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "query": self.query,
            "result_type": self.result_type,
            "data": self.data,
            "execution_time_ms": self.execution_time_ms,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "error": self.error,
        }


@dataclass
class QueryComparison:
    """Comparison of query results between two Prometheus versions.

    Attributes:
        query: The PromQL query compared
        baseline_result: Result from baseline version
        target_result: Result from target version
        status: Comparison status
        differences: List of specific differences found
        tolerance: Numeric tolerance for value comparison
    """

    query: str
    baseline_result: QueryResult
    target_result: QueryResult
    status: ComparisonStatus = ComparisonStatus.IDENTICAL
    differences: list[str] = field(default_factory=list)
    tolerance: float = 0.001

    def compare(self) -> None:
        """Compare the two query results and update status."""
        # Check for errors
        if self.baseline_result.error or self.target_result.error:
            if self.baseline_result.error and self.target_result.error:
                # Both errored - check if same error
                if self.baseline_result.error == self.target_result.error:
                    self.status = ComparisonStatus.IDENTICAL
                else:
                    self.status = ComparisonStatus.DIFFERENT
                    self.differences.append(
                        f"Different errors: baseline='{self.baseline_result.error}', "
                        f"target='{self.target_result.error}'"
                    )
            else:
                self.status = ComparisonStatus.DIFFERENT
                if self.baseline_result.error:
                    self.differences.append(
                        f"Baseline errored: {self.baseline_result.error}"
                    )
                else:
                    self.differences.append(
                        f"Target errored: {self.target_result.error}"
                    )
            return

        # Check result types
        if self.baseline_result.result_type != self.target_result.result_type:
            self.status = ComparisonStatus.DIFFERENT
            self.differences.append(
                f"Different result types: baseline={self.baseline_result.result_type}, "
                f"target={self.target_result.result_type}"
            )
            return

        # Compare data
        self._compare_data(
            self.baseline_result.data,
            self.target_result.data,
            "result"
        )

        if self.differences:
            self.status = ComparisonStatus.DIFFERENT
        else:
            self.status = ComparisonStatus.IDENTICAL

    def _compare_data(
        self,
        baseline: Any,
        target: Any,
        path: str,
    ) -> None:
        """Recursively compare data structures."""
        if type(baseline) != type(target):
            self.differences.append(
                f"{path}: type mismatch (baseline={type(baseline).__name__}, "
                f"target={type(target).__name__})"
            )
            return

        if isinstance(baseline, dict):
            baseline_keys = set(baseline.keys())
            target_keys = set(target.keys())

            for key in baseline_keys - target_keys:
                self.differences.append(f"{path}.{key}: missing in target")
            for key in target_keys - baseline_keys:
                self.differences.append(f"{path}.{key}: extra in target")

            for key in baseline_keys & target_keys:
                self._compare_data(baseline[key], target[key], f"{path}.{key}")

        elif isinstance(baseline, list):
            if len(baseline) != len(target):
                self.differences.append(
                    f"{path}: different lengths (baseline={len(baseline)}, "
                    f"target={len(target)})"
                )
            else:
                for i, (b, t) in enumerate(zip(baseline, target)):
                    self._compare_data(b, t, f"{path}[{i}]")

        elif isinstance(baseline, (int, float)):
            if abs(baseline - target) > self.tolerance:
                self.differences.append(
                    f"{path}: value difference (baseline={baseline}, "
                    f"target={target}, diff={abs(baseline - target)})"
                )

        elif baseline != target:
            self.differences.append(
                f"{path}: value mismatch (baseline={baseline}, target={target})"
            )

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "query": self.query,
            "baseline_result": self.baseline_result.to_dict(),
            "target_result": self.target_result.to_dict(),
            "status": self.status.value,
            "differences": self.differences,
            "tolerance": self.tolerance,
        }


@dataclass
class RuleResult:
    """Result of evaluating an alerting or recording rule.

    Attributes:
        rule_name: Name of the rule
        rule_type: Type of rule (alerting or recording)
        expression: PromQL expression of the rule
        result: Evaluation result
        labels: Labels associated with the rule
        annotations: Annotations (for alerting rules)
        state: Alert state (for alerting rules)
        error: Error message if evaluation failed
    """

    rule_name: str
    rule_type: str  # "alerting" or "recording"
    expression: str
    result: Any = None
    labels: dict[str, str] = field(default_factory=dict)
    annotations: dict[str, str] = field(default_factory=dict)
    state: Optional[str] = None  # "firing", "pending", "inactive"
    error: Optional[str] = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "rule_name": self.rule_name,
            "rule_type": self.rule_type,
            "expression": self.expression,
            "result": self.result,
            "labels": self.labels,
            "annotations": self.annotations,
            "state": self.state,
            "error": self.error,
        }


@dataclass
class RuleComparison:
    """Comparison of rule results between two Prometheus versions.

    Attributes:
        rule_name: Name of the rule compared
        rule_type: Type of rule (alerting or recording)
        baseline_result: Result from baseline version
        target_result: Result from target version
        status: Comparison status
        differences: List of specific differences found
    """

    rule_name: str
    rule_type: str
    baseline_result: RuleResult
    target_result: RuleResult
    status: ComparisonStatus = ComparisonStatus.IDENTICAL
    differences: list[str] = field(default_factory=list)

    def compare(self) -> None:
        """Compare the two rule results and update status."""
        # Check for errors
        if self.baseline_result.error or self.target_result.error:
            if self.baseline_result.error != self.target_result.error:
                self.status = ComparisonStatus.DIFFERENT
                self.differences.append(
                    f"Error mismatch: baseline='{self.baseline_result.error}', "
                    f"target='{self.target_result.error}'"
                )
            return

        # Compare states for alerting rules
        if self.rule_type == "alerting":
            if self.baseline_result.state != self.target_result.state:
                self.status = ComparisonStatus.DIFFERENT
                self.differences.append(
                    f"State mismatch: baseline={self.baseline_result.state}, "
                    f"target={self.target_result.state}"
                )

        # Compare results
        if self.baseline_result.result != self.target_result.result:
            self.status = ComparisonStatus.DIFFERENT
            self.differences.append(
                f"Result mismatch: baseline={self.baseline_result.result}, "
                f"target={self.target_result.result}"
            )

        if self.differences:
            self.status = ComparisonStatus.DIFFERENT
        else:
            self.status = ComparisonStatus.IDENTICAL

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "rule_name": self.rule_name,
            "rule_type": self.rule_type,
            "baseline_result": self.baseline_result.to_dict(),
            "target_result": self.target_result.to_dict(),
            "status": self.status.value,
            "differences": self.differences,
        }


@dataclass
class PerformanceComparison:
    """Comparison of performance metrics between two Prometheus versions.

    Attributes:
        metric_name: Name of the performance metric
        baseline_value: Value from baseline version
        target_value: Value from target version
        unit: Unit of measurement
        threshold_percent: Acceptable difference threshold
        status: Comparison status
        difference_percent: Actual percentage difference
    """

    metric_name: str
    baseline_value: float
    target_value: float
    unit: str = "ms"
    threshold_percent: float = 10.0
    status: ComparisonStatus = ComparisonStatus.IDENTICAL
    difference_percent: float = 0.0

    def compare(self) -> None:
        """Compare the two performance values and update status."""
        if self.baseline_value == 0:
            if self.target_value == 0:
                self.status = ComparisonStatus.IDENTICAL
                self.difference_percent = 0.0
            else:
                self.status = ComparisonStatus.DIFFERENT
                self.difference_percent = 100.0
            return

        self.difference_percent = (
            (self.target_value - self.baseline_value) / self.baseline_value
        ) * 100

        if abs(self.difference_percent) > self.threshold_percent:
            self.status = ComparisonStatus.DIFFERENT
        else:
            self.status = ComparisonStatus.IDENTICAL

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "metric_name": self.metric_name,
            "baseline_value": self.baseline_value,
            "target_value": self.target_value,
            "unit": self.unit,
            "threshold_percent": self.threshold_percent,
            "status": self.status.value,
            "difference_percent": round(self.difference_percent, 2),
        }


@dataclass
class ConfigCompatibilityResult:
    """Result of configuration compatibility testing.

    Attributes:
        config_type: Type of configuration (scrape, remote_write)
        config_name: Name/identifier of the configuration
        baseline_working: Whether config works on baseline version
        target_working: Whether config works on target version
        status: Comparison status
        error: Error message if compatibility check failed
        details: Additional details about the compatibility
    """

    config_type: str
    config_name: str
    baseline_working: bool = False
    target_working: bool = False
    status: ComparisonStatus = ComparisonStatus.IDENTICAL
    error: Optional[str] = None
    details: dict[str, Any] = field(default_factory=dict)

    def compare(self) -> None:
        """Compare compatibility and update status."""
        if self.baseline_working and self.target_working:
            self.status = ComparisonStatus.IDENTICAL
        elif self.baseline_working and not self.target_working:
            self.status = ComparisonStatus.DIFFERENT
        elif not self.baseline_working and self.target_working:
            # Config works on target but not baseline - improvement
            self.status = ComparisonStatus.IDENTICAL
        else:
            # Both not working
            self.status = ComparisonStatus.IDENTICAL

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "config_type": self.config_type,
            "config_name": self.config_name,
            "baseline_working": self.baseline_working,
            "target_working": self.target_working,
            "status": self.status.value,
            "error": self.error,
            "details": self.details,
        }


@dataclass
class RegressionTestReport:
    """Complete report for regression testing.

    Attributes:
        test_name: Name of the regression test
        baseline_version: Baseline Prometheus version
        target_version: Target Prometheus version
        start_time: When the test started
        end_time: When the test ended
        query_comparisons: Query result comparisons
        rule_comparisons: Rule result comparisons
        config_results: Configuration compatibility results
        performance_comparisons: Performance metric comparisons
        passed: Whether all comparisons passed
        regressions: List of detected regressions
    """

    test_name: str
    baseline_version: PrometheusVersion
    target_version: PrometheusVersion
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    query_comparisons: list[QueryComparison] = field(default_factory=list)
    rule_comparisons: list[RuleComparison] = field(default_factory=list)
    config_results: list[ConfigCompatibilityResult] = field(default_factory=list)
    performance_comparisons: list[PerformanceComparison] = field(default_factory=list)
    passed: bool = True
    regressions: list[str] = field(default_factory=list)

    @property
    def duration_seconds(self) -> float:
        """Total test duration."""
        if self.start_time and self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return 0.0

    def analyze_regressions(self) -> None:
        """Analyze all comparisons and identify regressions."""
        self.regressions = []
        self.passed = True

        # Check query comparisons
        for qc in self.query_comparisons:
            if qc.status == ComparisonStatus.DIFFERENT:
                self.passed = False
                self.regressions.append(
                    f"Query regression: '{qc.query}' - {', '.join(qc.differences)}"
                )

        # Check rule comparisons
        for rc in self.rule_comparisons:
            if rc.status == ComparisonStatus.DIFFERENT:
                self.passed = False
                self.regressions.append(
                    f"Rule regression: '{rc.rule_name}' ({rc.rule_type}) - "
                    f"{', '.join(rc.differences)}"
                )

        # Check config compatibility
        for cc in self.config_results:
            if cc.status == ComparisonStatus.DIFFERENT:
                self.passed = False
                self.regressions.append(
                    f"Config regression: '{cc.config_name}' ({cc.config_type}) - "
                    f"worked on baseline but not on target"
                )

        # Check performance comparisons
        for pc in self.performance_comparisons:
            if pc.status == ComparisonStatus.DIFFERENT:
                self.passed = False
                direction = "slower" if pc.difference_percent > 0 else "faster"
                self.regressions.append(
                    f"Performance regression: '{pc.metric_name}' - "
                    f"{abs(pc.difference_percent):.1f}% {direction}"
                )

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "test_name": self.test_name,
            "baseline_version": self.baseline_version.to_dict(),
            "target_version": self.target_version.to_dict(),
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "duration_seconds": round(self.duration_seconds, 2),
            "passed": self.passed,
            "regressions": self.regressions,
            "summary": {
                "total_query_comparisons": len(self.query_comparisons),
                "query_regressions": sum(
                    1 for qc in self.query_comparisons
                    if qc.status == ComparisonStatus.DIFFERENT
                ),
                "total_rule_comparisons": len(self.rule_comparisons),
                "rule_regressions": sum(
                    1 for rc in self.rule_comparisons
                    if rc.status == ComparisonStatus.DIFFERENT
                ),
                "total_config_checks": len(self.config_results),
                "config_regressions": sum(
                    1 for cc in self.config_results
                    if cc.status == ComparisonStatus.DIFFERENT
                ),
                "total_performance_comparisons": len(self.performance_comparisons),
                "performance_regressions": sum(
                    1 for pc in self.performance_comparisons
                    if pc.status == ComparisonStatus.DIFFERENT
                ),
            },
            "query_comparisons": [qc.to_dict() for qc in self.query_comparisons],
            "rule_comparisons": [rc.to_dict() for rc in self.rule_comparisons],
            "config_results": [cc.to_dict() for cc in self.config_results],
            "performance_comparisons": [pc.to_dict() for pc in self.performance_comparisons],
        }
