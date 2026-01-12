"""
Prometheus API Client for the Testing Framework.

This module provides a comprehensive client for interacting with the Prometheus HTTP API,
including healthchecks, queries, and management endpoints.

Requirements: 12.7, 12.8, 12.9, 13.9
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Optional, Union
from urllib.parse import urlencode

import httpx


class PrometheusAPIError(Exception):
    """Base exception for Prometheus API errors."""

    def __init__(self, message: str, status_code: Optional[int] = None,
                 response_body: Optional[str] = None):
        super().__init__(message)
        self.status_code = status_code
        self.response_body = response_body


class PrometheusConnectionError(PrometheusAPIError):
    """Raised when connection to Prometheus fails."""
    pass


class PrometheusTimeoutError(PrometheusAPIError):
    """Raised when request to Prometheus times out."""
    pass


class PrometheusQueryError(PrometheusAPIError):
    """Raised when a PromQL query fails."""
    pass


class HealthStatus(Enum):
    """Health status of Prometheus."""
    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


class ReadinessStatus(Enum):
    """Readiness status of Prometheus."""
    READY = "ready"
    NOT_READY = "not_ready"
    UNKNOWN = "unknown"


@dataclass
class QueryResult:
    """
    Result of a Prometheus query.

    Attributes:
        status: Query status ('success' or 'error')
        data: Query result data
        result_type: Type of result ('vector', 'matrix', 'scalar', 'string')
        warnings: Any warnings from the query
        error: Error message if query failed
        error_type: Type of error if query failed
    """
    status: str
    data: Optional[list[dict[str, Any]]] = None
    result_type: Optional[str] = None
    warnings: list[str] = field(default_factory=list)
    error: Optional[str] = None
    error_type: Optional[str] = None

    @property
    def is_success(self) -> bool:
        """Check if query was successful."""
        return self.status == "success"

    @property
    def is_empty(self) -> bool:
        """Check if query returned no results."""
        return self.data is None or len(self.data) == 0


@dataclass
class RuntimeInfo:
    """
    Prometheus runtime information.

    Attributes:
        start_time: When Prometheus started
        cwd: Current working directory
        reload_config_success: Whether last config reload was successful
        last_config_time: Time of last config reload
        corrupt_chunks: Number of corrupt chunks
        goroutines: Number of goroutines
        tsdb_storage_retention: Storage retention period
        tsdb_storage_retention_bytes: Storage retention in bytes
    """
    start_time: Optional[str] = None
    cwd: Optional[str] = None
    reload_config_success: Optional[bool] = None
    last_config_time: Optional[str] = None
    corrupt_chunks: Optional[int] = None
    goroutines: Optional[int] = None
    tsdb_storage_retention: Optional[str] = None
    tsdb_storage_retention_bytes: Optional[str] = None
    raw_data: dict[str, Any] = field(default_factory=dict)


@dataclass
class HealthCheckResult:
    """
    Result of a health check operation.

    Attributes:
        status: Health/readiness status
        response_time_ms: Response time in milliseconds
        status_code: HTTP status code
        message: Optional message from the endpoint
        timestamp: When the check was performed
    """
    status: Union[HealthStatus, ReadinessStatus]
    response_time_ms: float
    status_code: Optional[int] = None
    message: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.utcnow)

    @property
    def is_healthy(self) -> bool:
        """Check if the status indicates healthy/ready."""
        return self.status in (HealthStatus.HEALTHY, ReadinessStatus.READY)


class PrometheusAPIClient:
    """
    Client for interacting with the Prometheus HTTP API.

    This client provides methods for:
    - Health and readiness checks (/-/healthy, /-/ready)
    - Instant and range queries (/api/v1/query, /api/v1/query_range)
    - Label and series discovery (/api/v1/labels, /api/v1/series)
    - Runtime and configuration info (/api/v1/status/*)
    - Federation endpoint (/federate)

    Requirements: 12.7, 12.8, 12.9, 13.9

    Example:
        >>> client = PrometheusAPIClient("http://localhost:9090")
        >>> if client.healthcheck():
        ...     result = client.query("up")
        ...     print(result.data)
    """

    def __init__(
        self,
        base_url: str,
        timeout: float = 30.0,
        auth: Optional[tuple[str, str]] = None,
        headers: Optional[dict[str, str]] = None,
    ):
        """
        Initialize the Prometheus API client.

        Args:
            base_url: Base URL of the Prometheus instance (e.g., http://localhost:9090)
            timeout: Request timeout in seconds (default: 30.0)
            auth: Optional tuple of (username, password) for basic auth
            headers: Optional additional headers to include in requests
        """
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.auth = auth
        self.headers = headers or {}
        self._client: Optional[httpx.Client] = None
        self._async_client: Optional[httpx.AsyncClient] = None

    @property
    def client(self) -> httpx.Client:
        """Get or create the synchronous HTTP client."""
        if self._client is None:
            self._client = httpx.Client(
                timeout=self.timeout,
                auth=self.auth,
                headers=self.headers,
            )
        return self._client

    @property
    def async_client(self) -> httpx.AsyncClient:
        """Get or create the asynchronous HTTP client."""
        if self._async_client is None:
            self._async_client = httpx.AsyncClient(
                timeout=self.timeout,
                auth=self.auth,
                headers=self.headers,
            )
        return self._async_client

    def close(self) -> None:
        """Close the HTTP clients."""
        if self._client is not None:
            self._client.close()
            self._client = None
        if self._async_client is not None:
            # Note: async client should be closed with await in async context
            pass

    async def aclose(self) -> None:
        """Close the async HTTP client."""
        if self._async_client is not None:
            await self._async_client.aclose()
            self._async_client = None

    def __enter__(self) -> "PrometheusAPIClient":
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager exit."""
        self.close()

    async def __aenter__(self) -> "PrometheusAPIClient":
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Async context manager exit."""
        await self.aclose()

    def _handle_request_error(self, e: Exception, endpoint: str) -> None:
        """Handle request exceptions and raise appropriate errors."""
        if isinstance(e, httpx.TimeoutException):
            raise PrometheusTimeoutError(
                f"Request to {endpoint} timed out after {self.timeout}s"
            )
        elif isinstance(e, httpx.ConnectError):
            raise PrometheusConnectionError(
                f"Failed to connect to Prometheus at {self.base_url}: {str(e)}"
            )
        elif isinstance(e, httpx.HTTPStatusError):
            raise PrometheusAPIError(
                f"HTTP error from {endpoint}: {e.response.status_code}",
                status_code=e.response.status_code,
                response_body=e.response.text[:500] if e.response.text else None,
            )
        else:
            raise PrometheusAPIError(f"Unexpected error accessing {endpoint}: {str(e)}")

    # =========================================================================
    # Health and Readiness Endpoints
    # =========================================================================

    def healthcheck(self) -> bool:
        """
        Check if Prometheus is healthy via the /-/healthy endpoint.

        Requirements: 12.7

        Returns:
            True if Prometheus returns HTTP 200, False otherwise

        Raises:
            PrometheusConnectionError: If connection fails
            PrometheusTimeoutError: If request times out
        """
        return self.healthcheck_detailed().is_healthy

    def healthcheck_detailed(self) -> HealthCheckResult:
        """
        Perform a detailed health check via the /-/healthy endpoint.

        Requirements: 12.7

        Returns:
            HealthCheckResult with status, response time, and details

        Raises:
            PrometheusConnectionError: If connection fails
            PrometheusTimeoutError: If request times out
        """
        url = f"{self.base_url}/-/healthy"
        start_time = datetime.utcnow()

        try:
            import time
            start = time.perf_counter()
            response = self.client.get(url)
            response_time_ms = (time.perf_counter() - start) * 1000

            if response.status_code == 200:
                return HealthCheckResult(
                    status=HealthStatus.HEALTHY,
                    response_time_ms=response_time_ms,
                    status_code=response.status_code,
                    message=response.text.strip() if response.text else None,
                    timestamp=start_time,
                )
            else:
                return HealthCheckResult(
                    status=HealthStatus.UNHEALTHY,
                    response_time_ms=response_time_ms,
                    status_code=response.status_code,
                    message=response.text.strip() if response.text else None,
                    timestamp=start_time,
                )
        except Exception as e:
            self._handle_request_error(e, "/-/healthy")
            # This line won't be reached but satisfies type checker
            return HealthCheckResult(
                status=HealthStatus.UNKNOWN,
                response_time_ms=0,
                timestamp=start_time,
            )

    def readiness(self) -> bool:
        """
        Check if Prometheus is ready via the /-/ready endpoint.

        Requirements: 12.8

        Returns:
            True if Prometheus returns HTTP 200, False otherwise

        Raises:
            PrometheusConnectionError: If connection fails
            PrometheusTimeoutError: If request times out
        """
        return self.readiness_detailed().is_healthy

    def readiness_detailed(self) -> HealthCheckResult:
        """
        Perform a detailed readiness check via the /-/ready endpoint.

        Requirements: 12.8

        Returns:
            HealthCheckResult with status, response time, and details

        Raises:
            PrometheusConnectionError: If connection fails
            PrometheusTimeoutError: If request times out
        """
        url = f"{self.base_url}/-/ready"
        start_time = datetime.utcnow()

        try:
            import time
            start = time.perf_counter()
            response = self.client.get(url)
            response_time_ms = (time.perf_counter() - start) * 1000

            if response.status_code == 200:
                return HealthCheckResult(
                    status=ReadinessStatus.READY,
                    response_time_ms=response_time_ms,
                    status_code=response.status_code,
                    message=response.text.strip() if response.text else None,
                    timestamp=start_time,
                )
            else:
                return HealthCheckResult(
                    status=ReadinessStatus.NOT_READY,
                    response_time_ms=response_time_ms,
                    status_code=response.status_code,
                    message=response.text.strip() if response.text else None,
                    timestamp=start_time,
                )
        except Exception as e:
            self._handle_request_error(e, "/-/ready")
            return HealthCheckResult(
                status=ReadinessStatus.UNKNOWN,
                response_time_ms=0,
                timestamp=start_time,
            )

    # =========================================================================
    # Query Endpoints
    # =========================================================================

    def query(
        self,
        promql: str,
        time: Optional[str] = None,
        timeout: Optional[str] = None,
    ) -> QueryResult:
        """
        Execute an instant query via /api/v1/query.

        Requirements: 12.9

        Args:
            promql: PromQL query expression
            time: Evaluation timestamp (RFC3339 or Unix timestamp), defaults to current time
            timeout: Evaluation timeout (e.g., "30s")

        Returns:
            QueryResult with query results

        Raises:
            PrometheusQueryError: If query fails
            PrometheusConnectionError: If connection fails
            PrometheusTimeoutError: If request times out

        Example:
            >>> result = client.query("up{job='prometheus'}")
            >>> for item in result.data:
            ...     print(item['metric'], item['value'])
        """
        url = f"{self.base_url}/api/v1/query"
        params: dict[str, str] = {"query": promql}

        if time is not None:
            params["time"] = time
        if timeout is not None:
            params["timeout"] = timeout

        try:
            response = self.client.get(url, params=params)
            data = response.json()

            if data.get("status") == "success":
                result_data = data.get("data", {})
                return QueryResult(
                    status="success",
                    data=result_data.get("result", []),
                    result_type=result_data.get("resultType"),
                    warnings=data.get("warnings", []),
                )
            else:
                return QueryResult(
                    status="error",
                    error=data.get("error"),
                    error_type=data.get("errorType"),
                    warnings=data.get("warnings", []),
                )
        except httpx.HTTPStatusError as e:
            raise PrometheusQueryError(
                f"Query failed with HTTP {e.response.status_code}",
                status_code=e.response.status_code,
                response_body=e.response.text[:500] if e.response.text else None,
            )
        except Exception as e:
            self._handle_request_error(e, "/api/v1/query")
            # Unreachable but satisfies type checker
            return QueryResult(status="error", error=str(e))

    def query_range(
        self,
        promql: str,
        start: str,
        end: str,
        step: str,
        timeout: Optional[str] = None,
    ) -> QueryResult:
        """
        Execute a range query via /api/v1/query_range.

        Requirements: 12.9

        Args:
            promql: PromQL query expression
            start: Start timestamp (RFC3339 or Unix timestamp)
            end: End timestamp (RFC3339 or Unix timestamp)
            step: Query resolution step width (e.g., "15s", "1m")
            timeout: Evaluation timeout (e.g., "30s")

        Returns:
            QueryResult with query results (matrix type)

        Raises:
            PrometheusQueryError: If query fails
            PrometheusConnectionError: If connection fails
            PrometheusTimeoutError: If request times out

        Example:
            >>> result = client.query_range(
            ...     "rate(http_requests_total[5m])",
            ...     start="2024-01-01T00:00:00Z",
            ...     end="2024-01-01T01:00:00Z",
            ...     step="1m"
            ... )
        """
        url = f"{self.base_url}/api/v1/query_range"
        params: dict[str, str] = {
            "query": promql,
            "start": start,
            "end": end,
            "step": step,
        }

        if timeout is not None:
            params["timeout"] = timeout

        try:
            response = self.client.get(url, params=params)
            data = response.json()

            if data.get("status") == "success":
                result_data = data.get("data", {})
                return QueryResult(
                    status="success",
                    data=result_data.get("result", []),
                    result_type=result_data.get("resultType"),
                    warnings=data.get("warnings", []),
                )
            else:
                return QueryResult(
                    status="error",
                    error=data.get("error"),
                    error_type=data.get("errorType"),
                    warnings=data.get("warnings", []),
                )
        except httpx.HTTPStatusError as e:
            raise PrometheusQueryError(
                f"Range query failed with HTTP {e.response.status_code}",
                status_code=e.response.status_code,
                response_body=e.response.text[:500] if e.response.text else None,
            )
        except Exception as e:
            self._handle_request_error(e, "/api/v1/query_range")
            return QueryResult(status="error", error=str(e))

    # =========================================================================
    # Label and Series Discovery Endpoints
    # =========================================================================

    def get_labels(
        self,
        match: Optional[list[str]] = None,
        start: Optional[str] = None,
        end: Optional[str] = None,
    ) -> list[str]:
        """
        Get all label names via /api/v1/labels.

        Requirements: 12.9

        Args:
            match: Optional list of series selectors to filter labels
            start: Optional start timestamp for the time range
            end: Optional end timestamp for the time range

        Returns:
            List of label names

        Raises:
            PrometheusAPIError: If request fails
            PrometheusConnectionError: If connection fails
            PrometheusTimeoutError: If request times out

        Example:
            >>> labels = client.get_labels()
            >>> print(labels)  # ['__name__', 'instance', 'job', ...]
        """
        url = f"{self.base_url}/api/v1/labels"
        params: dict[str, Any] = {}

        if match:
            params["match[]"] = match
        if start:
            params["start"] = start
        if end:
            params["end"] = end

        try:
            response = self.client.get(url, params=params)
            response.raise_for_status()
            data = response.json()

            if data.get("status") == "success":
                return data.get("data", [])
            else:
                raise PrometheusAPIError(
                    f"Failed to get labels: {data.get('error', 'Unknown error')}"
                )
        except httpx.HTTPStatusError as e:
            raise PrometheusAPIError(
                f"Failed to get labels: HTTP {e.response.status_code}",
                status_code=e.response.status_code,
            )
        except Exception as e:
            if isinstance(e, PrometheusAPIError):
                raise
            self._handle_request_error(e, "/api/v1/labels")
            return []

    def get_label_values(
        self,
        label: str,
        match: Optional[list[str]] = None,
        start: Optional[str] = None,
        end: Optional[str] = None,
    ) -> list[str]:
        """
        Get values for a specific label via /api/v1/label/{label}/values.

        Requirements: 12.9

        Args:
            label: Label name to get values for
            match: Optional list of series selectors to filter values
            start: Optional start timestamp for the time range
            end: Optional end timestamp for the time range

        Returns:
            List of label values

        Raises:
            PrometheusAPIError: If request fails
            PrometheusConnectionError: If connection fails
            PrometheusTimeoutError: If request times out

        Example:
            >>> jobs = client.get_label_values("job")
            >>> print(jobs)  # ['prometheus', 'node-exporter', ...]
        """
        url = f"{self.base_url}/api/v1/label/{label}/values"
        params: dict[str, Any] = {}

        if match:
            params["match[]"] = match
        if start:
            params["start"] = start
        if end:
            params["end"] = end

        try:
            response = self.client.get(url, params=params)
            response.raise_for_status()
            data = response.json()

            if data.get("status") == "success":
                return data.get("data", [])
            else:
                raise PrometheusAPIError(
                    f"Failed to get label values: {data.get('error', 'Unknown error')}"
                )
        except httpx.HTTPStatusError as e:
            raise PrometheusAPIError(
                f"Failed to get label values for '{label}': HTTP {e.response.status_code}",
                status_code=e.response.status_code,
            )
        except Exception as e:
            if isinstance(e, PrometheusAPIError):
                raise
            self._handle_request_error(e, f"/api/v1/label/{label}/values")
            return []

    def get_series(
        self,
        match: list[str],
        start: Optional[str] = None,
        end: Optional[str] = None,
    ) -> list[dict[str, str]]:
        """
        Get series matching selectors via /api/v1/series.

        Requirements: 12.9

        Args:
            match: List of series selectors (at least one required)
            start: Optional start timestamp for the time range
            end: Optional end timestamp for the time range

        Returns:
            List of series (each series is a dict of label name to value)

        Raises:
            PrometheusAPIError: If request fails
            PrometheusConnectionError: If connection fails
            PrometheusTimeoutError: If request times out
            ValueError: If match list is empty

        Example:
            >>> series = client.get_series(["up{job='prometheus'}"])
            >>> for s in series:
            ...     print(s)  # {'__name__': 'up', 'job': 'prometheus', ...}
        """
        if not match:
            raise ValueError("At least one series selector is required")

        url = f"{self.base_url}/api/v1/series"
        params: dict[str, Any] = {"match[]": match}

        if start:
            params["start"] = start
        if end:
            params["end"] = end

        try:
            response = self.client.get(url, params=params)
            response.raise_for_status()
            data = response.json()

            if data.get("status") == "success":
                return data.get("data", [])
            else:
                raise PrometheusAPIError(
                    f"Failed to get series: {data.get('error', 'Unknown error')}"
                )
        except httpx.HTTPStatusError as e:
            raise PrometheusAPIError(
                f"Failed to get series: HTTP {e.response.status_code}",
                status_code=e.response.status_code,
            )
        except Exception as e:
            if isinstance(e, (PrometheusAPIError, ValueError)):
                raise
            self._handle_request_error(e, "/api/v1/series")
            return []

    # =========================================================================
    # Status and Management Endpoints
    # =========================================================================

    def get_runtime_info(self) -> RuntimeInfo:
        """
        Get Prometheus runtime information via /api/v1/status/runtimeinfo.

        Requirements: 12.9

        Returns:
            RuntimeInfo with Prometheus runtime details

        Raises:
            PrometheusAPIError: If request fails
            PrometheusConnectionError: If connection fails
            PrometheusTimeoutError: If request times out

        Example:
            >>> info = client.get_runtime_info()
            >>> print(info.goroutines)
            >>> print(info.tsdb_storage_retention)
        """
        url = f"{self.base_url}/api/v1/status/runtimeinfo"

        try:
            response = self.client.get(url)
            response.raise_for_status()
            data = response.json()

            if data.get("status") == "success":
                info_data = data.get("data", {})
                return RuntimeInfo(
                    start_time=info_data.get("startTime"),
                    cwd=info_data.get("CWD"),
                    reload_config_success=info_data.get("reloadConfigSuccess"),
                    last_config_time=info_data.get("lastConfigTime"),
                    corrupt_chunks=info_data.get("corruptionCount"),
                    goroutines=info_data.get("goroutineCount"),
                    tsdb_storage_retention=info_data.get("storageRetention"),
                    tsdb_storage_retention_bytes=info_data.get("storageRetentionBytes"),
                    raw_data=info_data,
                )
            else:
                raise PrometheusAPIError(
                    f"Failed to get runtime info: {data.get('error', 'Unknown error')}"
                )
        except httpx.HTTPStatusError as e:
            raise PrometheusAPIError(
                f"Failed to get runtime info: HTTP {e.response.status_code}",
                status_code=e.response.status_code,
            )
        except Exception as e:
            if isinstance(e, PrometheusAPIError):
                raise
            self._handle_request_error(e, "/api/v1/status/runtimeinfo")
            return RuntimeInfo()

    def get_config(self) -> dict[str, Any]:
        """
        Get Prometheus configuration via /api/v1/status/config.

        Requirements: 12.9

        Returns:
            Dictionary containing the YAML configuration

        Raises:
            PrometheusAPIError: If request fails
            PrometheusConnectionError: If connection fails
            PrometheusTimeoutError: If request times out

        Example:
            >>> config = client.get_config()
            >>> print(config['yaml'])  # Raw YAML configuration
        """
        url = f"{self.base_url}/api/v1/status/config"

        try:
            response = self.client.get(url)
            response.raise_for_status()
            data = response.json()

            if data.get("status") == "success":
                return data.get("data", {})
            else:
                raise PrometheusAPIError(
                    f"Failed to get config: {data.get('error', 'Unknown error')}"
                )
        except httpx.HTTPStatusError as e:
            raise PrometheusAPIError(
                f"Failed to get config: HTTP {e.response.status_code}",
                status_code=e.response.status_code,
            )
        except Exception as e:
            if isinstance(e, PrometheusAPIError):
                raise
            self._handle_request_error(e, "/api/v1/status/config")
            return {}

    # =========================================================================
    # Federation Endpoint
    # =========================================================================

    def federate(
        self,
        match: list[str],
        timeout: Optional[float] = None,
    ) -> str:
        """
        Get federated metrics via the /federate endpoint.

        The federation endpoint returns metrics in Prometheus text exposition format,
        which can be used to scrape metrics from one Prometheus server to another.

        Requirements: 13.9

        Args:
            match: List of series selectors to federate (at least one required)
            timeout: Optional request timeout override

        Returns:
            Metrics in Prometheus text exposition format

        Raises:
            PrometheusAPIError: If request fails
            PrometheusConnectionError: If connection fails
            PrometheusTimeoutError: If request times out
            ValueError: If match list is empty

        Example:
            >>> metrics = client.federate(["{job='prometheus'}"])
            >>> print(metrics)
            # HELP up The up metric
            # TYPE up gauge
            up{instance="localhost:9090",job="prometheus"} 1
        """
        if not match:
            raise ValueError("At least one series selector is required for federation")

        url = f"{self.base_url}/federate"
        params: dict[str, Any] = {"match[]": match}

        try:
            # Use custom timeout if provided
            client_timeout = timeout if timeout else self.timeout
            response = self.client.get(url, params=params, timeout=client_timeout)
            response.raise_for_status()

            return response.text
        except httpx.HTTPStatusError as e:
            raise PrometheusAPIError(
                f"Federation request failed: HTTP {e.response.status_code}",
                status_code=e.response.status_code,
                response_body=e.response.text[:500] if e.response.text else None,
            )
        except Exception as e:
            if isinstance(e, (PrometheusAPIError, ValueError)):
                raise
            self._handle_request_error(e, "/federate")
            return ""

    # =========================================================================
    # Async Methods
    # =========================================================================

    async def healthcheck_async(self) -> bool:
        """
        Async version of healthcheck().

        Requirements: 12.7

        Returns:
            True if Prometheus returns HTTP 200, False otherwise
        """
        result = await self.healthcheck_detailed_async()
        return result.is_healthy

    async def healthcheck_detailed_async(self) -> HealthCheckResult:
        """
        Async version of healthcheck_detailed().

        Requirements: 12.7

        Returns:
            HealthCheckResult with status, response time, and details
        """
        url = f"{self.base_url}/-/healthy"
        start_time = datetime.utcnow()

        try:
            import time
            start = time.perf_counter()
            response = await self.async_client.get(url)
            response_time_ms = (time.perf_counter() - start) * 1000

            if response.status_code == 200:
                return HealthCheckResult(
                    status=HealthStatus.HEALTHY,
                    response_time_ms=response_time_ms,
                    status_code=response.status_code,
                    message=response.text.strip() if response.text else None,
                    timestamp=start_time,
                )
            else:
                return HealthCheckResult(
                    status=HealthStatus.UNHEALTHY,
                    response_time_ms=response_time_ms,
                    status_code=response.status_code,
                    message=response.text.strip() if response.text else None,
                    timestamp=start_time,
                )
        except Exception as e:
            self._handle_request_error(e, "/-/healthy")
            return HealthCheckResult(
                status=HealthStatus.UNKNOWN,
                response_time_ms=0,
                timestamp=start_time,
            )

    async def readiness_async(self) -> bool:
        """
        Async version of readiness().

        Requirements: 12.8

        Returns:
            True if Prometheus returns HTTP 200, False otherwise
        """
        result = await self.readiness_detailed_async()
        return result.is_healthy

    async def readiness_detailed_async(self) -> HealthCheckResult:
        """
        Async version of readiness_detailed().

        Requirements: 12.8

        Returns:
            HealthCheckResult with status, response time, and details
        """
        url = f"{self.base_url}/-/ready"
        start_time = datetime.utcnow()

        try:
            import time
            start = time.perf_counter()
            response = await self.async_client.get(url)
            response_time_ms = (time.perf_counter() - start) * 1000

            if response.status_code == 200:
                return HealthCheckResult(
                    status=ReadinessStatus.READY,
                    response_time_ms=response_time_ms,
                    status_code=response.status_code,
                    message=response.text.strip() if response.text else None,
                    timestamp=start_time,
                )
            else:
                return HealthCheckResult(
                    status=ReadinessStatus.NOT_READY,
                    response_time_ms=response_time_ms,
                    status_code=response.status_code,
                    message=response.text.strip() if response.text else None,
                    timestamp=start_time,
                )
        except Exception as e:
            self._handle_request_error(e, "/-/ready")
            return HealthCheckResult(
                status=ReadinessStatus.UNKNOWN,
                response_time_ms=0,
                timestamp=start_time,
            )

    async def query_async(
        self,
        promql: str,
        time: Optional[str] = None,
        timeout: Optional[str] = None,
    ) -> QueryResult:
        """
        Async version of query().

        Requirements: 12.9

        Args:
            promql: PromQL query expression
            time: Evaluation timestamp
            timeout: Evaluation timeout

        Returns:
            QueryResult with query results
        """
        url = f"{self.base_url}/api/v1/query"
        params: dict[str, str] = {"query": promql}

        if time is not None:
            params["time"] = time
        if timeout is not None:
            params["timeout"] = timeout

        try:
            response = await self.async_client.get(url, params=params)
            data = response.json()

            if data.get("status") == "success":
                result_data = data.get("data", {})
                return QueryResult(
                    status="success",
                    data=result_data.get("result", []),
                    result_type=result_data.get("resultType"),
                    warnings=data.get("warnings", []),
                )
            else:
                return QueryResult(
                    status="error",
                    error=data.get("error"),
                    error_type=data.get("errorType"),
                    warnings=data.get("warnings", []),
                )
        except Exception as e:
            self._handle_request_error(e, "/api/v1/query")
            return QueryResult(status="error", error=str(e))

    async def query_range_async(
        self,
        promql: str,
        start: str,
        end: str,
        step: str,
        timeout: Optional[str] = None,
    ) -> QueryResult:
        """
        Async version of query_range().

        Requirements: 12.9

        Args:
            promql: PromQL query expression
            start: Start timestamp
            end: End timestamp
            step: Query resolution step width
            timeout: Evaluation timeout

        Returns:
            QueryResult with query results
        """
        url = f"{self.base_url}/api/v1/query_range"
        params: dict[str, str] = {
            "query": promql,
            "start": start,
            "end": end,
            "step": step,
        }

        if timeout is not None:
            params["timeout"] = timeout

        try:
            response = await self.async_client.get(url, params=params)
            data = response.json()

            if data.get("status") == "success":
                result_data = data.get("data", {})
                return QueryResult(
                    status="success",
                    data=result_data.get("result", []),
                    result_type=result_data.get("resultType"),
                    warnings=data.get("warnings", []),
                )
            else:
                return QueryResult(
                    status="error",
                    error=data.get("error"),
                    error_type=data.get("errorType"),
                    warnings=data.get("warnings", []),
                )
        except Exception as e:
            self._handle_request_error(e, "/api/v1/query_range")
            return QueryResult(status="error", error=str(e))
