"""Performance benchmark tests for Prometheus.

This module provides performance benchmarking capabilities for:
- Query latency (simple, complex, range queries)
- Remote write throughput and latency
- TSDB operations (compaction, WAL replay)

Requirements: 15.1, 15.2, 15.3, 15.4, 15.5, 15.6, 15.7
"""

from .benchmarks import (
    BenchmarkResult,
    BenchmarkSample,
    QueryBenchmarkConfig,
    QueryComplexity,
    QueryLatencyBenchmark,
)
from .test_query_latency import (
    QueryLatencyBenchmarkRunner,
    QueryLatencyReport,
    run_query_latency_benchmarks_sync,
)
from .test_remote_write import (
    RemoteWriteBenchmark,
    RemoteWriteBenchmarkRunner,
    RemoteWriteConfig,
    RemoteWriteMetrics,
    RemoteWriteReport,
    run_remote_write_benchmarks_sync,
)
from .test_tsdb import (
    CompactionMetrics,
    TSDBBenchmark,
    TSDBBenchmarkReport,
    TSDBBenchmarkRunner,
    TSDBConfig,
    TSDBMetrics,
    WALMetrics,
    run_tsdb_benchmarks_sync,
)
from .runner import (
    PerformanceTestReport,
    PerformanceTestRunner,
    run_performance_tests_sync,
)

__all__ = [
    # Core benchmarks
    "BenchmarkResult",
    "BenchmarkSample",
    "QueryBenchmarkConfig",
    "QueryComplexity",
    "QueryLatencyBenchmark",
    # Query latency
    "QueryLatencyBenchmarkRunner",
    "QueryLatencyReport",
    "run_query_latency_benchmarks_sync",
    # Remote write
    "RemoteWriteBenchmark",
    "RemoteWriteBenchmarkRunner",
    "RemoteWriteConfig",
    "RemoteWriteMetrics",
    "RemoteWriteReport",
    "run_remote_write_benchmarks_sync",
    # TSDB
    "CompactionMetrics",
    "TSDBBenchmark",
    "TSDBBenchmarkReport",
    "TSDBBenchmarkRunner",
    "TSDBConfig",
    "TSDBMetrics",
    "WALMetrics",
    "run_tsdb_benchmarks_sync",
    # Unified runner
    "PerformanceTestReport",
    "PerformanceTestRunner",
    "run_performance_tests_sync",
]
