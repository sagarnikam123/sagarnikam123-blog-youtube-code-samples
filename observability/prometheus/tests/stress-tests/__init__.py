"""
Stress tests for finding Prometheus breaking points.

This package provides comprehensive stress testing capabilities for Prometheus,
including progressive load, high cardinality, high ingestion rate, concurrent
queries, and memory pressure tests.

Requirements: 17.1, 17.2, 17.3, 17.4, 17.5, 17.6, 17.7
"""

from .config import (
    ConcurrentQueryConfig,
    HighCardinalityConfig,
    HighIngestionConfig,
    MemoryPressureConfig,
    ProgressiveLoadConfig,
    StressTestConfig,
)
from .models import (
    BreakingPoint,
    FailureMode,
    StressTestDataPoint,
    StressTestType,
)
from .test_cardinality import (
    CardinalityTestResult,
    HighCardinalityTester,
    run_high_cardinality_test_sync,
)
from .test_ingestion import (
    HighIngestionTester,
    IngestionTestResult,
    run_high_ingestion_test_sync,
)
from .test_memory import (
    MemoryPressureResult,
    MemoryPressureTester,
    run_memory_pressure_test_sync,
)
from .test_progressive_load import (
    ProgressiveLoadResult,
    ProgressiveLoadTester,
    run_progressive_load_test_sync,
)
from .test_queries import (
    ConcurrentQueryResult,
    ConcurrentQueryTester,
    run_concurrent_query_test_sync,
)

__all__ = [
    # Config classes
    "StressTestConfig",
    "ProgressiveLoadConfig",
    "HighCardinalityConfig",
    "HighIngestionConfig",
    "ConcurrentQueryConfig",
    "MemoryPressureConfig",
    # Model classes
    "BreakingPoint",
    "FailureMode",
    "StressTestDataPoint",
    "StressTestType",
    # Progressive load test
    "ProgressiveLoadTester",
    "ProgressiveLoadResult",
    "run_progressive_load_test_sync",
    # High cardinality test
    "HighCardinalityTester",
    "CardinalityTestResult",
    "run_high_cardinality_test_sync",
    # High ingestion test
    "HighIngestionTester",
    "IngestionTestResult",
    "run_high_ingestion_test_sync",
    # Concurrent query test
    "ConcurrentQueryTester",
    "ConcurrentQueryResult",
    "run_concurrent_query_test_sync",
    # Memory pressure test
    "MemoryPressureTester",
    "MemoryPressureResult",
    "run_memory_pressure_test_sync",
]
