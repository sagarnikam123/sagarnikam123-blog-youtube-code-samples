"""
Scaling curve generation for Prometheus scalability testing.

This module provides functionality to generate scaling curves
and identify non-linear degradation points in Prometheus performance.

Requirements: 16.6, 16.7
"""

import json
import statistics
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from .scaling_dimensions import (
    ScalingDataPoint,
    ScalingDimension,
    ScalingDimensionTester,
    ScalingTestConfig,
    ScalingTestResult,
)


@dataclass
class CurveAnalysis:
    """Analysis of a scaling curve.

    Attributes:
        slope: Average slope of the curve
        r_squared: R-squared value for linear fit
        is_linear: Whether the curve is approximately linear
        degradation_point: Scale value where degradation starts
        degradation_severity: How severe the degradation is (0-1)
        inflection_points: Points where curve behavior changes
    """

    slope: float = 0.0
    r_squared: float = 0.0
    is_linear: bool = True
    degradation_point: Optional[int] = None
    degradation_severity: float = 0.0
    inflection_points: list[int] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "slope": round(self.slope, 6),
            "r_squared": round(self.r_squared, 4),
            "is_linear": self.is_linear,
            "degradation_point": self.degradation_point,
            "degradation_severity": round(self.degradation_severity, 4),
            "inflection_points": self.inflection_points,
        }


@dataclass
class ScalingCurveReport:
    """Report for a scaling curve analysis.

    Attributes:
        dimension: The scaling dimension analyzed
        data_points: Collected data points
        curve_analysis: Analysis of the scaling curve
        degradation_detected: Whether degradation was detected
        recommendations: Recommendations based on analysis
        start_time: When the analysis started
        end_time: When the analysis ended
    """

    dimension: ScalingDimension
    data_points: list[ScalingDataPoint] = field(default_factory=list)
    curve_analysis: dict[str, Any] = field(default_factory=dict)
    degradation_detected: bool = False
    recommendations: list[str] = field(default_factory=list)
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None

    @property
    def duration_seconds(self) -> float:
        """Total analysis duration."""
        if self.start_time and self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return 0.0

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "dimension": self.dimension.value,
            "data_points": [dp.to_dict() for dp in self.data_points],
            "curve_analysis": self.curve_analysis,
            "degradation_detected": self.degradation_detected,
            "recommendations": self.recommendations,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "duration_seconds": round(self.duration_seconds, 2),
        }

    def to_json(self, indent: int = 2) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict(), indent=indent)

    def to_markdown(self) -> str:
        """Generate markdown report."""
        lines = [
            f"# Scaling Curve Report: {self.dimension.value}",
            "",
            f"**Start Time:** {self.start_time.isoformat() if self.start_time else 'N/A'}",
            f"**End Time:** {self.end_time.isoformat() if self.end_time else 'N/A'}",
            f"**Duration:** {self.duration_seconds:.2f} seconds",
            f"**Degradation Detected:** {'Yes' if self.degradation_detected else 'No'}",
            "",
            "## Data Points",
            "",
            "| Scale Value | P50 (ms) | P90 (ms) | P99 (ms) | CPU % | Memory (MB) |",
            "|-------------|----------|----------|----------|-------|-------------|",
        ]

        for dp in self.data_points:
            memory_mb = dp.memory_utilization_bytes / (1024 * 1024)
            lines.append(
                f"| {dp.scale_value} | {dp.query_latency_p50_ms:.2f} | "
                f"{dp.query_latency_p90_ms:.2f} | {dp.query_latency_p99_ms:.2f} | "
                f"{dp.cpu_utilization_percent:.2f} | {memory_mb:.2f} |"
            )

        lines.extend(["", "## Curve Analysis", ""])

        if self.curve_analysis:
            for key, value in self.curve_analysis.items():
                lines.append(f"- **{key}:** {value}")

        if self.recommendations:
            lines.extend(["", "## Recommendations", ""])
            for rec in self.recommendations:
                lines.append(f"- {rec}")

        return "\n".join(lines)


@dataclass
class ScalingCurveConfig:
    """Configuration for scaling curve generation.

    Attributes:
        prometheus_url: URL of the Prometheus instance
        scale_values: Scale values to test
        query_iterations: Number of queries per measurement
        timeout_seconds: Query timeout
        linear_threshold: R-squared threshold for linear classification
        degradation_threshold: Slope increase threshold for degradation
    """

    prometheus_url: str = "http://localhost:9090"
    scale_values: list[int] = field(
        default_factory=lambda: [10, 50, 100, 500, 1000, 5000, 10000]
    )
    query_iterations: int = 10
    timeout_seconds: float = 30.0
    linear_threshold: float = 0.95
    degradation_threshold: float = 2.0


class ScalingCurveGenerator:
    """
    Generates scaling curves and identifies degradation points.

    This class analyzes Prometheus performance across scaling dimensions
    to produce scaling curves and identify non-linear degradation.

    Requirements: 16.6, 16.7
    """

    def __init__(self, config: ScalingCurveConfig):
        """Initialize the scaling curve generator.

        Args:
            config: Configuration for curve generation
        """
        self.config = config

    def _calculate_linear_regression(
        self,
        x_values: list[float],
        y_values: list[float],
    ) -> tuple[float, float, float]:
        """Calculate linear regression parameters.

        Args:
            x_values: Independent variable values
            y_values: Dependent variable values

        Returns:
            Tuple of (slope, intercept, r_squared)
        """
        if len(x_values) < 2 or len(y_values) < 2:
            return 0.0, 0.0, 0.0

        n = len(x_values)
        sum_x = sum(x_values)
        sum_y = sum(y_values)
        sum_xy = sum(x * y for x, y in zip(x_values, y_values))
        sum_x2 = sum(x * x for x in x_values)

        denominator = n * sum_x2 - sum_x * sum_x
        if denominator == 0:
            return 0.0, 0.0, 0.0

        slope = (n * sum_xy - sum_x * sum_y) / denominator
        intercept = (sum_y - slope * sum_x) / n

        # Calculate R-squared
        y_mean = sum_y / n
        ss_tot = sum((y - y_mean) ** 2 for y in y_values)
        ss_res = sum((y - (slope * x + intercept)) ** 2 for x, y in zip(x_values, y_values))

        r_squared = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0.0

        return slope, intercept, r_squared

    def _find_inflection_points(
        self,
        data_points: list[ScalingDataPoint],
    ) -> list[int]:
        """Find inflection points in the scaling curve.

        An inflection point is where the second derivative changes sign,
        indicating a change in the curve's concavity.

        Args:
            data_points: List of scaling data points

        Returns:
            List of scale values where inflection occurs
        """
        if len(data_points) < 3:
            return []

        inflection_points = []

        # Calculate first derivatives (rate of change)
        first_derivatives = []
        for i in range(1, len(data_points)):
            dx = data_points[i].scale_value - data_points[i-1].scale_value
            dy = data_points[i].query_latency_p99_ms - data_points[i-1].query_latency_p99_ms
            if dx > 0:
                first_derivatives.append(dy / dx)
            else:
                first_derivatives.append(0)

        # Calculate second derivatives
        for i in range(1, len(first_derivatives)):
            d2y = first_derivatives[i] - first_derivatives[i-1]

            # Check for sign change in second derivative
            if i > 0 and len(first_derivatives) > i:
                prev_d2y = first_derivatives[i-1] - first_derivatives[i-2] if i > 1 else 0
                if (d2y > 0 and prev_d2y < 0) or (d2y < 0 and prev_d2y > 0):
                    inflection_points.append(data_points[i].scale_value)

        return inflection_points

    def _detect_degradation(
        self,
        data_points: list[ScalingDataPoint],
    ) -> tuple[bool, Optional[int], float]:
        """Detect non-linear degradation in the scaling curve.

        Args:
            data_points: List of scaling data points

        Returns:
            Tuple of (degradation_detected, degradation_point, severity)
        """
        if len(data_points) < 3:
            return False, None, 0.0

        # Calculate slopes between consecutive points
        slopes = []
        for i in range(1, len(data_points)):
            dx = data_points[i].scale_value - data_points[i-1].scale_value
            dy = data_points[i].query_latency_p99_ms - data_points[i-1].query_latency_p99_ms
            if dx > 0:
                slopes.append((data_points[i].scale_value, dy / dx))

        if not slopes:
            return False, None, 0.0

        # Calculate average slope
        avg_slope = statistics.mean([s for _, s in slopes])

        # Find first point where slope exceeds threshold
        degradation_point = None
        max_slope_ratio = 0.0

        for scale_value, slope in slopes:
            if avg_slope > 0:
                slope_ratio = slope / avg_slope
                if slope_ratio > self.config.degradation_threshold:
                    if degradation_point is None:
                        degradation_point = scale_value
                    max_slope_ratio = max(max_slope_ratio, slope_ratio)

        degradation_detected = degradation_point is not None
        severity = min(1.0, (max_slope_ratio - 1) / 10) if max_slope_ratio > 1 else 0.0

        return degradation_detected, degradation_point, severity

    def _generate_recommendations(
        self,
        analysis: CurveAnalysis,
        dimension: ScalingDimension,
    ) -> list[str]:
        """Generate recommendations based on curve analysis.

        Args:
            analysis: Curve analysis results
            dimension: The scaling dimension

        Returns:
            List of recommendations
        """
        recommendations = []

        if analysis.degradation_point:
            recommendations.append(
                f"Performance degradation detected at {dimension.value} = "
                f"{analysis.degradation_point}. Consider scaling horizontally "
                "or optimizing configuration before reaching this threshold."
            )

        if not analysis.is_linear:
            recommendations.append(
                f"Non-linear scaling behavior detected for {dimension.value}. "
                "Monitor closely as load increases."
            )

        if analysis.degradation_severity > 0.5:
            recommendations.append(
                "Severe degradation detected. Immediate action recommended: "
                "review resource allocation, query optimization, or consider "
                "federation/sharding."
            )

        if analysis.inflection_points:
            recommendations.append(
                f"Inflection points detected at: {analysis.inflection_points}. "
                "These represent significant changes in scaling behavior."
            )

        if not recommendations:
            recommendations.append(
                f"Scaling behavior for {dimension.value} appears healthy. "
                "Continue monitoring as load increases."
            )

        return recommendations

    def analyze_curve(
        self,
        data_points: list[ScalingDataPoint],
    ) -> CurveAnalysis:
        """Analyze a scaling curve from data points.

        Args:
            data_points: List of scaling data points

        Returns:
            CurveAnalysis with analysis results
        """
        if not data_points:
            return CurveAnalysis()

        x_values = [float(dp.scale_value) for dp in data_points]
        y_values = [dp.query_latency_p99_ms for dp in data_points]

        slope, _, r_squared = self._calculate_linear_regression(x_values, y_values)
        is_linear = r_squared >= self.config.linear_threshold

        inflection_points = self._find_inflection_points(data_points)
        _, degradation_point, severity = self._detect_degradation(
            data_points
        )

        return CurveAnalysis(
            slope=slope,
            r_squared=r_squared,
            is_linear=is_linear,
            degradation_point=degradation_point,
            degradation_severity=severity,
            inflection_points=inflection_points,
        )

    async def generate_scaling_curve(
        self,
        dimension: ScalingDimension,
    ) -> ScalingCurveReport:
        """Generate a scaling curve for a specific dimension.

        Args:
            dimension: The scaling dimension to analyze

        Returns:
            ScalingCurveReport with analysis results
        """
        report = ScalingCurveReport(dimension=dimension)
        report.start_time = datetime.utcnow()

        # Create tester with appropriate config
        test_config = ScalingTestConfig(
            prometheus_url=self.config.prometheus_url,
            query_iterations=self.config.query_iterations,
            timeout_seconds=self.config.timeout_seconds,
        )

        # Set scale values based on dimension
        if dimension == ScalingDimension.TARGETS:
            test_config.target_scale_values = self.config.scale_values
        elif dimension == ScalingDimension.SERIES:
            test_config.series_scale_values = self.config.scale_values
        elif dimension == ScalingDimension.CARDINALITY:
            test_config.cardinality_scale_values = self.config.scale_values
        elif dimension == ScalingDimension.RETENTION:
            test_config.retention_scale_values = self.config.scale_values
        elif dimension == ScalingDimension.QUERY_CONCURRENCY:
            test_config.concurrency_scale_values = self.config.scale_values

        tester = ScalingDimensionTester(test_config)

        # Run the appropriate test
        if dimension == ScalingDimension.TARGETS:
            result = await tester.test_target_scaling()
        elif dimension == ScalingDimension.SERIES:
            result = await tester.test_series_scaling()
        elif dimension == ScalingDimension.CARDINALITY:
            result = await tester.test_cardinality_scaling()
        elif dimension == ScalingDimension.RETENTION:
            result = await tester.test_retention_scaling()
        elif dimension == ScalingDimension.QUERY_CONCURRENCY:
            result = await tester.test_query_concurrency_scaling()
        else:
            result = ScalingTestResult(dimension=dimension)

        report.data_points = result.data_points

        # Analyze the curve
        analysis = self.analyze_curve(report.data_points)
        report.curve_analysis = analysis.to_dict()
        report.degradation_detected = analysis.degradation_point is not None

        # Generate recommendations
        report.recommendations = self._generate_recommendations(analysis, dimension)

        report.end_time = datetime.utcnow()

        return report

    async def generate_all_curves(self) -> dict[str, ScalingCurveReport]:
        """Generate scaling curves for all dimensions.

        Returns:
            Dictionary mapping dimension name to report
        """
        reports = {}

        for dimension in ScalingDimension:
            reports[dimension.value] = await self.generate_scaling_curve(dimension)

        return reports

    def save_report(
        self,
        report: ScalingCurveReport,
        output_dir: Path,
        formats: Optional[list[str]] = None,
    ) -> list[Path]:
        """Save a scaling curve report to files.

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
        base_name = f"scaling_curve_{report.dimension.value}_{timestamp}"

        if "json" in formats:
            json_path = output_dir / f"{base_name}.json"
            with open(json_path, "w", encoding="utf-8") as f:
                f.write(report.to_json())
            saved_files.append(json_path)

        if "markdown" in formats:
            md_path = output_dir / f"{base_name}.md"
            with open(md_path, "w", encoding="utf-8") as f:
                f.write(report.to_markdown())
            saved_files.append(md_path)

        return saved_files
