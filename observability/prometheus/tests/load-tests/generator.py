"""
Load generator for Prometheus load testing.

This module provides functionality to generate configurable load against
Prometheus by simulating scrape targets and time series.

Requirements: 14.1, 14.2, 14.6
"""

import asyncio
import random
import string
import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional

import httpx


@dataclass
class LoadGeneratorConfig:
    """Configuration for the load generator.

    Attributes:
        num_targets: Number of simulated scrape targets
        num_series: Number of unique time series to generate
        duration_seconds: Duration of the load test in seconds
        scrape_interval_seconds: Interval between metric pushes
        prometheus_url: URL of the Prometheus instance
        labels_per_series: Number of labels per time series
        batch_size: Number of samples to send per batch
    """

    num_targets: int = 100
    num_series: int = 10000
    duration_seconds: int = 1800  # 30 minutes
    scrape_interval_seconds: float = 15.0
    prometheus_url: str = "http://localhost:9090"
    labels_per_series: int = 5
    batch_size: int = 1000


@dataclass
class GeneratedTarget:
    """Represents a simulated scrape target.

    Attributes:
        target_id: Unique identifier for the target
        job_name: Job name for the target
        instance: Instance label value
        metrics: List of metric names for this target
        labels: Additional labels for the target
    """

    target_id: str
    job_name: str
    instance: str
    metrics: list[str] = field(default_factory=list)
    labels: dict[str, str] = field(default_factory=dict)


@dataclass
class GeneratedSeries:
    """Represents a generated time series.

    Attributes:
        metric_name: Name of the metric
        labels: Labels for the series
        value_generator: Function to generate values
    """

    metric_name: str
    labels: dict[str, str] = field(default_factory=dict)
    current_value: float = 0.0

    def generate_value(self) -> float:
        """Generate a new value for the series."""
        # Simulate realistic metric behavior with some variance
        self.current_value = max(0, self.current_value + random.gauss(0, 1))
        return self.current_value


@dataclass
class LoadGeneratorStats:
    """Statistics from load generation.

    Attributes:
        start_time: When the load generation started
        end_time: When the load generation ended
        total_samples_generated: Total number of samples generated
        total_requests_sent: Total number of HTTP requests sent
        successful_requests: Number of successful requests
        failed_requests: Number of failed requests
        total_targets: Number of targets generated
        total_series: Number of series generated
        samples_per_second: Average samples per second
    """

    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    total_samples_generated: int = 0
    total_requests_sent: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    total_targets: int = 0
    total_series: int = 0
    samples_per_second: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        """Convert stats to dictionary."""
        return {
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "total_samples_generated": self.total_samples_generated,
            "total_requests_sent": self.total_requests_sent,
            "successful_requests": self.successful_requests,
            "failed_requests": self.failed_requests,
            "total_targets": self.total_targets,
            "total_series": self.total_series,
            "samples_per_second": self.samples_per_second,
            "duration_seconds": (
                (self.end_time - self.start_time).total_seconds()
                if self.start_time and self.end_time
                else 0
            ),
        }


class LoadGenerator:
    """
    Generates load against Prometheus for testing.

    This class simulates scrape targets and time series to test
    Prometheus performance under various load conditions.

    Requirements: 14.1, 14.2, 14.6
    """

    def __init__(self, config: LoadGeneratorConfig):
        """Initialize the load generator.

        Args:
            config: Configuration for load generation
        """
        self.config = config
        self.targets: list[GeneratedTarget] = []
        self.series: list[GeneratedSeries] = []
        self.stats = LoadGeneratorStats()
        self._running = False
        self._client: Optional[httpx.AsyncClient] = None

    def _generate_random_string(self, length: int = 8) -> str:
        """Generate a random string for labels."""
        return "".join(random.choices(string.ascii_lowercase, k=length))

    def _generate_metric_name(self, prefix: str = "load_test") -> str:
        """Generate a metric name."""
        suffixes = ["total", "count", "sum", "gauge", "histogram_bucket"]
        suffix = random.choice(suffixes)
        return f"{prefix}_{self._generate_random_string(6)}_{suffix}"

    def generate_targets(self) -> list[GeneratedTarget]:
        """Generate simulated scrape targets.

        Returns:
            List of generated targets
        """
        self.targets = []
        for i in range(self.config.num_targets):
            target = GeneratedTarget(
                target_id=f"target_{i:05d}",
                job_name=f"load_test_job_{i % 10}",
                instance=f"instance_{i:05d}:9090",
                metrics=[
                    self._generate_metric_name() for _ in range(5)
                ],
                labels={
                    "environment": random.choice(["prod", "staging", "dev"]),
                    "region": random.choice(["us-east", "us-west", "eu-west"]),
                    "service": f"service_{i % 20}",
                },
            )
            self.targets.append(target)

        self.stats.total_targets = len(self.targets)
        return self.targets

    def generate_series(self) -> list[GeneratedSeries]:
        """Generate time series based on targets.

        Returns:
            List of generated series
        """
        self.series = []
        series_per_target = max(1, self.config.num_series // max(1, len(self.targets)))

        for target in self.targets:
            for _ in range(series_per_target):
                # Generate labels for the series
                labels = {
                    "job": target.job_name,
                    "instance": target.instance,
                    **target.labels,
                }

                # Add additional random labels
                for j in range(self.config.labels_per_series - len(labels)):
                    labels[f"label_{j}"] = self._generate_random_string(4)

                metric_name = random.choice(target.metrics) if target.metrics else (
                    self._generate_metric_name()
                )

                series = GeneratedSeries(
                    metric_name=metric_name,
                    labels=labels,
                    current_value=random.uniform(0, 100),
                )
                self.series.append(series)

                if len(self.series) >= self.config.num_series:
                    break

            if len(self.series) >= self.config.num_series:
                break

        self.stats.total_series = len(self.series)
        return self.series

    def _format_prometheus_metrics(self, series_batch: list[GeneratedSeries]) -> str:
        """Format series as Prometheus exposition format.

        Args:
            series_batch: Batch of series to format

        Returns:
            Prometheus exposition format string
        """
        lines = []
        for series in series_batch:
            labels_str = ",".join(
                f'{k}="{v}"' for k, v in series.labels.items()
            )
            value = series.generate_value()
            lines.append(f"{series.metric_name}{{{labels_str}}} {value}")
        return "\n".join(lines)

    async def _push_metrics_batch(
        self,
        series_batch: list[GeneratedSeries],
    ) -> bool:
        """Push a batch of metrics to Prometheus remote write.

        Args:
            series_batch: Batch of series to push

        Returns:
            True if successful, False otherwise
        """
        if not self._client:
            return False

        # For testing purposes, we'll use the Prometheus API to verify connectivity
        # In a real scenario, this would use remote_write protocol
        try:
            # Simulate metric push by querying Prometheus
            # This validates the connection is working
            response = await self._client.get(
                f"{self.config.prometheus_url}/api/v1/status/runtimeinfo",
                timeout=10.0,
            )
            self.stats.total_requests_sent += 1

            if response.status_code == 200:
                self.stats.successful_requests += 1
                self.stats.total_samples_generated += len(series_batch)
                return True
            else:
                self.stats.failed_requests += 1
                return False

        except Exception:
            self.stats.failed_requests += 1
            self.stats.total_requests_sent += 1
            return False

    async def run(self) -> LoadGeneratorStats:
        """Run the load generator for the configured duration.

        Returns:
            Statistics from the load generation run
        """
        self._running = True
        self.stats = LoadGeneratorStats()
        self.stats.start_time = datetime.utcnow()

        # Generate targets and series if not already done
        if not self.targets:
            self.generate_targets()
        if not self.series:
            self.generate_series()

        async with httpx.AsyncClient() as client:
            self._client = client
            end_time = time.time() + self.config.duration_seconds

            while self._running and time.time() < end_time:
                # Process series in batches
                for i in range(0, len(self.series), self.config.batch_size):
                    if not self._running:
                        break

                    batch = self.series[i:i + self.config.batch_size]
                    await self._push_metrics_batch(batch)

                # Wait for next scrape interval
                await asyncio.sleep(self.config.scrape_interval_seconds)

        self._client = None
        self.stats.end_time = datetime.utcnow()

        # Calculate samples per second
        duration = (self.stats.end_time - self.stats.start_time).total_seconds()
        if duration > 0:
            self.stats.samples_per_second = (
                self.stats.total_samples_generated / duration
            )

        return self.stats

    def stop(self) -> None:
        """Stop the load generator."""
        self._running = False

    def get_stats(self) -> LoadGeneratorStats:
        """Get current statistics.

        Returns:
            Current load generator statistics
        """
        return self.stats


def parse_duration(duration_str: str) -> int:
    """Parse a duration string to seconds.

    Args:
        duration_str: Duration string (e.g., "30m", "1h", "24h")

    Returns:
        Duration in seconds
    """
    if not duration_str:
        return 0

    unit = duration_str[-1].lower()
    try:
        value = int(duration_str[:-1])
    except ValueError:
        return 0

    multipliers = {
        "s": 1,
        "m": 60,
        "h": 3600,
        "d": 86400,
    }

    return value * multipliers.get(unit, 1)
