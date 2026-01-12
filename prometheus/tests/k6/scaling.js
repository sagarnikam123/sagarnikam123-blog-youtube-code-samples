/**
 * k6 Scalability Test Script for Prometheus
 *
 * This script tests Prometheus scalability by generating concurrent query load
 * with configurable VU ramp-up to identify non-linear degradation points.
 *
 * Requirements: 16.8, 16.9
 *
 * Usage:
 *   k6 run --env PROMETHEUS_URL=http://localhost:9090 scaling.js
 *   k6 run --env PROMETHEUS_URL=http://localhost:9090 --env MAX_VUS=500 scaling.js
 *   k6 run --env PROMETHEUS_URL=http://localhost:9090 --env RAMP_STAGES=10,50,100,200,500 scaling.js
 *
 * Environment Variables:
 *   PROMETHEUS_URL: Base URL of Prometheus (default: http://localhost:9090)
 *   MAX_VUS: Maximum number of virtual users (default: 100)
 *   RAMP_STAGES: Comma-separated VU targets for ramp stages (default: 10,25,50,75,100)
 *   STAGE_DURATION: Duration for each stage (default: 2m)
 *   RAMP_DURATION: Duration for ramping between stages (default: 30s)
 *   QUERY_TIMEOUT: Query timeout in seconds (default: 30)
 */

import http from 'k6/http';
import { check, sleep, group } from 'k6';
import { Counter, Rate, Trend, Gauge } from 'k6/metrics';
import { randomIntBetween, randomItem } from 'https://jslib.k6.io/k6-utils/1.2.0/index.js';

// Configuration from environment variables
const PROMETHEUS_URL = __ENV.PROMETHEUS_URL || 'http://localhost:9090';
const MAX_VUS = parseInt(__ENV.MAX_VUS) || 100;
const STAGE_DURATION = __ENV.STAGE_DURATION || '2m';
const RAMP_DURATION = __ENV.RAMP_DURATION || '30s';
const QUERY_TIMEOUT = parseInt(__ENV.QUERY_TIMEOUT) || 30;

// Parse ramp stages from environment or use defaults
const DEFAULT_STAGES = [10, 25, 50, 75, 100];
const RAMP_STAGES = __ENV.RAMP_STAGES
    ? __ENV.RAMP_STAGES.split(',').map(s => parseInt(s.trim()))
    : DEFAULT_STAGES;

// Custom metrics for scalability testing
const queryLatency = new Trend('prometheus_query_latency_ms', true);
const rangeQueryLatency = new Trend('prometheus_range_query_latency_ms', true);
const labelQueryLatency = new Trend('prometheus_label_query_latency_ms', true);
const seriesQueryLatency = new Trend('prometheus_series_query_latency_ms', true);
const querySuccessRate = new Rate('prometheus_query_success_rate');
const totalQueries = new Counter('prometheus_total_queries');
const failedQueries = new Counter('prometheus_failed_queries');
const concurrentVUs = new Gauge('prometheus_concurrent_vus');
const throughput = new Counter('prometheus_queries_per_second');

// Metrics for degradation detection
const latencyByVULevel = new Trend('prometheus_latency_by_vu_level', true);
const successRateByVULevel = new Rate('prometheus_success_rate_by_vu_level');


// Test queries - mix of simple and complex queries for realistic load
const INSTANT_QUERIES = [
    // Simple queries
    'up',
    'prometheus_tsdb_head_series',
    'prometheus_tsdb_head_chunks',
    'process_resident_memory_bytes',
    'go_goroutines',
    'prometheus_http_requests_total',

    // Rate queries
    'rate(prometheus_http_requests_total[5m])',
    'rate(prometheus_tsdb_head_samples_appended_total[5m])',
    'rate(process_cpu_seconds_total[5m])',

    // Aggregation queries
    'sum(rate(prometheus_http_requests_total[5m])) by (handler)',
    'avg(scrape_duration_seconds) by (job)',
    'count(up) by (job)',

    // Histogram queries
    'histogram_quantile(0.99, rate(prometheus_http_request_duration_seconds_bucket[5m]))',
    'histogram_quantile(0.95, rate(prometheus_http_request_duration_seconds_bucket[5m]))',

    // Complex queries
    'topk(10, sum(rate(prometheus_http_requests_total[5m])) by (handler))',
    'bottomk(5, avg(scrape_duration_seconds) by (job))',
];

// Range query time windows
const RANGE_WINDOWS = ['15m', '1h', '6h', '24h'];

// Build dynamic stages based on RAMP_STAGES
function buildStages() {
    const stages = [];

    for (let i = 0; i < RAMP_STAGES.length; i++) {
        const target = Math.min(RAMP_STAGES[i], MAX_VUS);

        // Ramp up to target
        stages.push({ duration: RAMP_DURATION, target: target });
        // Hold at target
        stages.push({ duration: STAGE_DURATION, target: target });
    }

    // Ramp down
    stages.push({ duration: RAMP_DURATION, target: 0 });

    return stages;
}

// k6 options with dynamic stages for scalability testing
export const options = {
    stages: buildStages(),
    thresholds: {
        'prometheus_query_success_rate': ['rate>0.90'],
        'prometheus_query_latency_ms': ['p(95)<2000'],
        'prometheus_range_query_latency_ms': ['p(95)<5000'],
        'prometheus_label_query_latency_ms': ['p(95)<1000'],
        'prometheus_series_query_latency_ms': ['p(95)<3000'],
    },
    noConnectionReuse: false,
    userAgent: 'k6-scaling-test/1.0',
};

/**
 * Execute an instant query against Prometheus
 */
function executeInstantQuery(query) {
    const url = `${PROMETHEUS_URL}/api/v1/query`;
    const params = {
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        timeout: `${QUERY_TIMEOUT}s`,
    };

    const startTime = Date.now();
    const response = http.post(url, { query: query }, params);
    const latency = Date.now() - startTime;

    totalQueries.add(1);
    throughput.add(1);
    queryLatency.add(latency);
    latencyByVULevel.add(latency, { vus: __VU });

    const success = check(response, {
        'instant query status is 200': (r) => r.status === 200,
        'instant query has success status': (r) => {
            try {
                const body = JSON.parse(r.body);
                return body.status === 'success';
            } catch (e) {
                return false;
            }
        },
    });

    querySuccessRate.add(success);
    successRateByVULevel.add(success, { vus: __VU });

    if (!success) {
        failedQueries.add(1);
    }

    return { success, latency, response };
}

/**
 * Execute a range query against Prometheus
 */
function executeRangeQuery(query, window) {
    const url = `${PROMETHEUS_URL}/api/v1/query_range`;
    const now = Math.floor(Date.now() / 1000);

    const windowSeconds = parseWindow(window);
    const start = now - windowSeconds;
    const step = Math.max(15, Math.floor(windowSeconds / 500));

    const params = {
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        timeout: `${QUERY_TIMEOUT * 2}s`,
    };

    const startTime = Date.now();
    const response = http.post(url, {
        query: query,
        start: start.toString(),
        end: now.toString(),
        step: step.toString(),
    }, params);
    const latency = Date.now() - startTime;

    totalQueries.add(1);
    throughput.add(1);
    rangeQueryLatency.add(latency);
    latencyByVULevel.add(latency, { vus: __VU });

    const success = check(response, {
        'range query status is 200': (r) => r.status === 200,
        'range query has success status': (r) => {
            try {
                const body = JSON.parse(r.body);
                return body.status === 'success';
            } catch (e) {
                return false;
            }
        },
    });

    querySuccessRate.add(success);
    successRateByVULevel.add(success, { vus: __VU });

    if (!success) {
        failedQueries.add(1);
    }

    return { success, latency, response };
}


/**
 * Execute a labels query against Prometheus
 */
function executeLabelsQuery() {
    const url = `${PROMETHEUS_URL}/api/v1/labels`;
    const params = {
        timeout: `${QUERY_TIMEOUT}s`,
    };

    const startTime = Date.now();
    const response = http.get(url, params);
    const latency = Date.now() - startTime;

    totalQueries.add(1);
    throughput.add(1);
    labelQueryLatency.add(latency);
    latencyByVULevel.add(latency, { vus: __VU });

    const success = check(response, {
        'labels query status is 200': (r) => r.status === 200,
        'labels query has success status': (r) => {
            try {
                const body = JSON.parse(r.body);
                return body.status === 'success';
            } catch (e) {
                return false;
            }
        },
    });

    querySuccessRate.add(success);
    successRateByVULevel.add(success, { vus: __VU });

    if (!success) {
        failedQueries.add(1);
    }

    return { success, latency, response };
}

/**
 * Execute a series query against Prometheus
 */
function executeSeriesQuery(match) {
    const url = `${PROMETHEUS_URL}/api/v1/series`;
    const now = Math.floor(Date.now() / 1000);
    const start = now - 3600; // Last hour

    const params = {
        timeout: `${QUERY_TIMEOUT}s`,
    };

    const startTime = Date.now();
    const response = http.get(
        `${url}?match[]=${encodeURIComponent(match)}&start=${start}&end=${now}`,
        params
    );
    const latency = Date.now() - startTime;

    totalQueries.add(1);
    throughput.add(1);
    seriesQueryLatency.add(latency);
    latencyByVULevel.add(latency, { vus: __VU });

    const success = check(response, {
        'series query status is 200': (r) => r.status === 200,
