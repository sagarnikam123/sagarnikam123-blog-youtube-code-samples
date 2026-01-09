/**
 * Loki Multi-Tenant Load Test
 *
 * Tests Loki's multi-tenant capabilities:
 * - Each VU acts as a different tenant (xk6-tenant-$VU)
 * - Tests tenant isolation
 * - Validates per-tenant performance
 *
 * Usage:
 *   ./k6 run multi-tenant-test.js
 *   ./k6 run --vus 20 --duration 5m multi-tenant-test.js
 *
 * Note: Loki must be running with auth_enabled: true for multi-tenant mode.
 *
 * Reference: https://grafana.com/blog/a-quick-guide-to-load-testing-grafana-loki-with-grafana-k6/
 */

import loki from 'k6/x/loki';
import { check, sleep } from 'k6';

// Configuration
// For multi-tenant: URL without credentials = each VU gets unique tenant
// For single-tenant: URL with credentials = all VUs use same tenant
const BASE_URL = __ENV.LOKI_URL || 'http://localhost:3100';
const SINGLE_TENANT_URL = __ENV.SINGLE_TENANT_URL || 'http://fake:@localhost:3100';

const VUS = __ENV.VUS || 10;
const DURATION = __ENV.DURATION || '5m';
const MODE = __ENV.MODE || 'multi';  // 'multi' or 'single'

// Label cardinality
const labelCardinality = {
  namespace: 3,
  app: 5,
  pod: 10,
};

// Initialize client based on mode
const url = MODE === 'single' ? SINGLE_TENANT_URL : BASE_URL;
const conf = new loki.Config(url, 10000, 1.0, labelCardinality);
const client = new loki.Client(conf);

// k6 options
export const options = {
  vus: parseInt(VUS),
  duration: DURATION,
  thresholds: {
    'http_req_duration': ['p(95)<1000', 'p(99)<2000'],
    'http_req_failed': ['rate<0.01'],
  },
};

/**
 * Default function - executed by each VU
 */
export default function () {
  // Alternate between push and query
  if (Math.random() < 0.7) {
    // 70% push operations
    pushLogs();
  } else {
    // 30% query operations
    queryLogs();
  }
}

/**
 * Push logs for current tenant
 */
function pushLogs() {
  const streams = Math.floor(Math.random() * 3) + 2;  // 2-4 streams
  const minSize = 100 * 1024;  // 100KB
  const maxSize = 500 * 1024;  // 500KB

  const res = client.pushParameterized(streams, minSize, maxSize);

  check(res, {
    'push successful': (r) => r.status === 204,
  });
}

/**
 * Query logs for current tenant
 * In multi-tenant mode, each VU only sees its own data
 */
function queryLogs() {
  const now = Math.floor(Date.now() / 1000);
  const fiveMinAgo = now - 300;

  // Range query - will only return data for current tenant
  const res = client.rangeQuery(
    `{namespace=~".+"}`,
    fiveMinAgo,
    now,
    50
  );

  check(res, {
    'query successful': (r) => r.status === 200,
  });

  sleep(0.2);
}

/**
 * Setup function
 */
export function setup() {
  console.log(`Starting ${MODE}-tenant test against ${url}`);
  console.log(`VUs: ${VUS}, Duration: ${DURATION}`);

  if (MODE === 'multi') {
    console.log(`Each VU will use tenant: xk6-tenant-$VU`);
    console.log(`Total tenants: ${VUS}`);
  } else {
    console.log('All VUs using single tenant');
  }
}

/**
 * Teardown function
 */
export function teardown(data) {
  console.log(`${MODE}-tenant test completed`);
}
