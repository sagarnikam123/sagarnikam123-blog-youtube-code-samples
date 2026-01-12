/**
 * k6 Soak Test Script for Prometheus Endurance Testing
 *
 * This script generates sustained query load against Prometheus for extended
 * periods (24h+) to detect memory leaks, performance degradation, and stability issues.
 *
 * Requirements: 18.8, 18.9
 *
 * Usage:
 *   k6 run --env PROMETHEUS_URL=http://localhost:9090 --duration 24h soak.js
 *   k6 run --env PROMETHEUS_URL=http://localhost:9090 --vus 50 --duration 24h soak.js
 *
 * Environment Variables:
 *   PROMETHEUS_URL: Base URL of Prometheus (default: http://localhost:9090)
 *   VUS: Number of virtual users (default: 50)
 *   DURATION: Test duration (default: 24h)
 *   RAMP_UP_TIME: Time to ramp up to target VUs (default: 5m)
 *   RAMP_DOWN_TIME: Time to ramp down at end (default: 5m)
 *   HEALTHCHECK_INTERVAL: Interval for health checks in seconds (default: 300)
 */

import http from 'k6/http';
import { check, sleep, group } from 'k6';
import { Counter, Rate, Trend, Gauge } from 'k6/metrics';
import { randomIntBetween, randomItem } from 'https://jslib.k6.io/k6-utils/1.2.0/index.js';

// Configuration from environment variables
const PROMETHEUS_URL = __ENV.PROMETHEUS_URL || 'http://localhost:9090';
const TARGET_VUS = parseInt(__ENV.VUS) || 50;
const DURATION = __ENV.DURATION || '24h';
const RAMP_UP_TIME = __ENV.RAMP_UP_TIME || '5m';
const RAMP_DOWN_TIME = __ENV.RAMP_DOWN_TIME || '5m';
const HEALTHCHECK_INTERVAL = parseInt(__ENV.HEALTHCHECK_INTERVAL) || 300;

// Custom metrics for soak testing
const queryLatency = new Trend('prometheus_query_latency_ms', true);
const rangeQueryLatency = new Trend('prometheus_range_query_latency_ms', true);
const healthcheckLatency = new Trend('prometheus_healthcheck_latency_ms', true);
const querySuccessRate = new Rate('prometheus_query_success_rate');
const healthcheckSuccessRate = new Rate('prometheus_healthcheck_success_rate');
const totalQueries = new Counter('prometheus_total_queries');
const failedQueries = new Counter('prometheus_failed_queries');
const memoryUsage = new Gauge('prometheus_memory_bytes');
const activeSeries = new Gauge('prometheus_active_series');
const goroutines = new Gauge('prometheus_goroutines');

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
    'histogram_quantile(0.50, rate(prometheus_http_request_duration_seconds_bucket[5m]))',

    // Complex queries
    'topk(10, sum(rate(prometheus_http_requests_total[5m])) by (handler))',
    'bottomk(5, avg(scrape_duration_seconds) by (job))',
];

// Range query time windows
const RANGE_WINDOWS = ['1h', '6h', '12h', '24h'];

// k6 options for soak testing with gradual ramp-up/down
export const options = {
    stages: [
        { duration: RAMP_UP_TIME, target: TARGET_VUS },    // Ramp up
        { duration: DURATION, target: TARGET_VUS },         // Sustained load
        { duration: RAMP_DOWN_TIME, target: 0 },           // Ramp down
    ],
    thresholds: {
        'prometheus_query_success_rate': ['rate>0.95'],     // 95% success rate
        'prometheus_healthcheck_success_rate': ['rate>0.99'], // 99% health checks pass
        'prometheus_query_latency_ms': ['p(95)<1000'],      // 95th percentile under 1s
        'prometheus_range_query_latency_ms': ['p(95)<5000'], // Range queries under 5s
    },
    // Soak test specific settings
    noConnectionReuse: false,
    userAgent: 'k6-soak-test/1.0',
};

/**
 * Execute an instant query against Prometheus
 */
function executeInstantQuery(query) {
    const url = `${PROMETHEUS_URL}/api/v1/query`;
    const params = {
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        timeout: '30s',
    };

    const startTime = Date.now();
    const response = http.post(url, { query: query }, params);
    const latency = Date.now() - startTime;

    totalQueries.add(1);
    queryLatency.add(latency);

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

    // Parse window to seconds
    const windowSeconds = parseWindow(window);
    const start = now - windowSeconds;
    const step = Math.max(15, Math.floor(windowSeconds / 1000)); // At least 15s step

    const params = {
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        timeout: '60s',
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
    rangeQueryLatency.add(latency);

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
    if (!success) {
        failedQueries.add(1);
    }

    return { success, latency, response };
}

/**
 * Parse time window string to seconds
 */
function parseWindow(window) {
    const match = window.match(/^(\d+)([smhd])$/);
    if (!match) return 3600; // Default 1h

    const value = parseInt(match[1]);
    const unit = match[2];

    switch (unit) {
        case 's': return value;
        case 'm': return value * 60;
        case 'h': return value * 3600;
        case 'd': return value * 86400;
        default: return 3600;
    }
}

/**
 * Check Prometheus health endpoints
 */
function checkHealth() {
    const healthyUrl = `${PROMETHEUS_URL}/-/healthy`;
    const readyUrl = `${PROMETHEUS_URL}/-/ready`;

    const startTime = Date.now();
    const healthyResponse = http.get(healthyUrl, { timeout: '10s' });
    const healthyLatency = Date.now() - startTime;

    const readyResponse = http.get(readyUrl, { timeout: '10s' });
    const totalLatency = Date.now() - startTime;

    healthcheckLatency.add(totalLatency);

    const success = check(healthyResponse, {
        'healthy endpoint returns 200': (r) => r.status === 200,
    }) && check(readyResponse, {
        'ready endpoint returns 200': (r) => r.status === 200,
    });

    healthcheckSuccessRate.add(success);

    return success;
}

/**
 * Collect Prometheus internal metrics for monitoring
 */
function collectPrometheusMetrics() {
    // Memory usage
    const memResult = executeInstantQuery('process_resident_memory_bytes');
    if (memResult.success) {
        try {
            const body = JSON.parse(memResult.response.body);
            if (body.data && body.data.result && body.data.result.length > 0) {
                const value = parseFloat(body.data.result[0].value[1]);
                memoryUsage.add(value);
            }
        } catch (e) { /* ignore */ }
    }

    // Active series
    const seriesResult = executeInstantQuery('prometheus_tsdb_head_series');
    if (seriesResult.success) {
        try {
            const body = JSON.parse(seriesResult.response.body);
            if (body.data && body.data.result && body.data.result.length > 0) {
                const value = parseFloat(body.data.result[0].value[1]);
                activeSeries.add(value);
            }
        } catch (e) { /* ignore */ }
    }

    // Goroutines
    const goroutinesResult = executeInstantQuery('go_goroutines');
    if (goroutinesResult.success) {
        try {
            const body = JSON.parse(goroutinesResult.response.body);
            if (body.data && body.data.result && body.data.result.length > 0) {
                const value = parseFloat(body.data.result[0].value[1]);
                goroutines.add(value);
            }
        } catch (e) { /* ignore */ }
    }
}

/**
 * Setup function - runs once before the test
 */
export function setup() {
    console.log(`Starting soak test against ${PROMETHEUS_URL}`);
    console.log(`Target VUs: ${TARGET_VUS}, Duration: ${DURATION}`);

    // Verify Prometheus is accessible
    const healthy = checkHealth();
    if (!healthy) {
        console.error('Prometheus is not healthy at test start!');
    }

    return {
        startTime: Date.now(),
        prometheusUrl: PROMETHEUS_URL,
    };
}

/**
 * Main test function - runs for each VU iteration
 */
export default function(data) {
    // Determine which type of operation to perform
    const operationType = randomIntBetween(1, 100);

    if (operationType <= 60) {
        // 60% instant queries
        group('instant_queries', function() {
            const query = randomItem(INSTANT_QUERIES);
            executeInstantQuery(query);
        });
    } else if (operationType <= 85) {
        // 25% range queries
        group('range_queries', function() {
            const query = randomItem(INSTANT_QUERIES.slice(0, 10)); // Use simpler queries for range
            const window = randomItem(RANGE_WINDOWS);
            executeRangeQuery(query, window);
        });
    } else if (operationType <= 95) {
        // 10% health checks
        group('health_checks', function() {
            checkHealth();
        });
    } else {
        // 5% metrics collection
        group('metrics_collection', function() {
            collectPrometheusMetrics();
        });
    }

    // Small sleep to prevent overwhelming the server
    sleep(randomIntBetween(1, 3) / 10); // 0.1-0.3 seconds
}

/**
 * Teardown function - runs once after the test
 */
export function teardown(data) {
    const duration = (Date.now() - data.startTime) / 1000 / 3600;
    console.log(`Soak test completed after ${duration.toFixed(2)} hours`);

    // Final health check
    const healthy = checkHealth();
    console.log(`Final health check: ${healthy ? 'PASSED' : 'FAILED'}`);
}

/**
 * Handle summary - custom summary output
 */
export function handleSummary(data) {
    const summary = {
        test_type: 'soak',
        prometheus_url: PROMETHEUS_URL,
        target_vus: TARGET_VUS,
        duration: DURATION,
        metrics: {
            total_queries: data.metrics.prometheus_total_queries ?
                data.metrics.prometheus_total_queries.values.count : 0,
            failed_queries: data.metrics.prometheus_failed_queries ?
                data.metrics.prometheus_failed_queries.values.count : 0,
            query_success_rate: data.metrics.prometheus_query_success_rate ?
                data.metrics.prometheus_query_success_rate.values.rate : 0,
            query_latency_p50: data.metrics.prometheus_query_latency_ms ?
                data.metrics.prometheus_query_latency_ms.values['p(50)'] : 0,
            query_latency_p95: data.metrics.prometheus_query_latency_ms ?
                data.metrics.prometheus_query_latency_ms.values['p(95)'] : 0,
            query_latency_p99: data.metrics.prometheus_query_latency_ms ?
                data.metrics.prometheus_query_latency_ms.values['p(99)'] : 0,
            range_query_latency_p95: data.metrics.prometheus_range_query_latency_ms ?
                data.metrics.prometheus_range_query_latency_ms.values['p(95)'] : 0,
            healthcheck_success_rate: data.metrics.prometheus_healthcheck_success_rate ?
                data.metrics.prometheus_healthcheck_success_rate.values.rate : 0,
        },
        thresholds_passed: !data.root_group || Object.values(data.root_group.checks || {})
            .every(c => c.passes / (c.passes + c.fails) >= 0.95),
    };

    return {
        'stdout': JSON.stringify(summary, null, 2) + '\n',
        'soak-test-results.json': JSON.stringify(summary, null, 2),
    };
}
