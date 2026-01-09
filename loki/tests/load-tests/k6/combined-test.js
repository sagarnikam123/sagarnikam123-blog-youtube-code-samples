/**
 * Loki Combined Write + Read Load Test
 *
 * Simulates realistic workload with both:
 * - Push operations (write path)
 * - Query operations (read path)
 *
 * Configurable write/read ratio to match production patterns.
 *
 * Usage:
 *   ./k6 run combined-test.js
 *   ./k6 run --vus 10 --duration 10m combined-test.js
 *
 * Reference: https://grafana.com/blog/a-quick-guide-to-load-testing-grafana-loki-with-grafana-k6/
 */

import loki from 'k6/x/loki';
import { check, sleep } from 'k6';

// Configuration
const BASE_URL = __ENV.LOKI_URL || 'http://localhost:3100';
const VUS = __ENV.VUS || 10;
const DURATION = __ENV.DURATION || '10m';

// Write/Read ratio (0.8 = 80% writes, 20% reads)
const WRITE_RATIO = parseFloat(__ENV.WRITE_RATIO) || 0.8;

// Label cardinality
const labelCardinality = {
  namespace: 5,
  app: 10,
  pod: 20,
};

// Initialize Loki client
const conf = new loki.Config(BASE_URL, 30000, 1.0, labelCardinality);
const client = new loki.Client(conf);

// k6 options with scenarios
export const options = {
  scenarios: {
    // Write scenario - 80% of VUs
    writers: {
      executor: 'constant-vus',
      vus: Math.ceil(parseInt(VUS) * WRITE_RATIO),
      duration: DURATION,
      exec: 'pushLogs',
    },
    // Read scenario - 20% of VUs
    readers: {
      executor: 'constant-vus',
      vus: Math.floor(parseInt(VUS) * (1 - WRITE_RATIO)),
      duration: DURATION,
      exec: 'queryLogs',
      startTime: '30s',  // Start queries after 30s of data ingestion
    },
  },
  thresholds: {
    'http_req_duration{scenario:writers}': ['p(95)<500', 'p(99)<1000'],
    'http_req_duration{scenario:readers}': ['p(95)<3000', 'p(99)<5000'],
    'http_req_failed': ['rate<0.01'],
  },
};

/**
 * Push logs function - write path
 */
export function pushLogs() {
  const streams = Math.floor(Math.random() * 5) + 2;  // 2-6 streams
  const minSize = 500 * 1024;  // 500KB
  const maxSize = 1024 * 1024; // 1MB

  const res = client.pushParameterized(streams, minSize, maxSize);

  check(res, {
    'push successful': (r) => r.status === 204,
  });

  if (res.status !== 204) {
    console.error(`Push failed: ${res.status}`);
  }
}

/**
 * Query logs function - read path
 */
export function queryLogs() {
  const queryType = Math.floor(Math.random() * 3);

  let res;
  const now = Math.floor(Date.now() / 1000);
  const fiveMinAgo = now - 300;

  switch (queryType) {
    case 0:
      // Range query
      res = client.rangeQuery(
        `{namespace=~".+"} |= ""`,
        fiveMinAgo,
        now,
        100
      );
      break;

    case 1:
      // Instant query with aggregation
      res = client.instantQuery(
        `count_over_time({namespace=~".+"}[5m])`,
        now
      );
      break;

    case 2:
      // Label values query
      res = client.labelValuesQuery('app');
      break;
  }

  const success = check(res, {
    'query successful': (r) => r.status === 200,
  });

  if (!success) {
    console.error(`Query failed: ${res.status}`);
  }

  sleep(0.5);  // Queries are less frequent than pushes
}

/**
 * Setup function
 */
export function setup() {
  console.log(`Starting combined test against ${BASE_URL}`);
  console.log(`Total VUs: ${VUS}`);
  console.log(`Write VUs: ${Math.ceil(parseInt(VUS) * WRITE_RATIO)}`);
  console.log(`Read VUs: ${Math.floor(parseInt(VUS) * (1 - WRITE_RATIO))}`);
  console.log(`Duration: ${DURATION}`);
}

/**
 * Teardown function
 */
export function teardown(data) {
  console.log('Combined test completed');
}
