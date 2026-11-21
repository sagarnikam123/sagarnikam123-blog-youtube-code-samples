/**
 * Loki Query (Read Path) Load Test
 *
 * Tests Loki's query performance with various LogQL queries:
 * - instantQuery: Point-in-time queries
 * - rangeQuery: Time range queries
 * - labelsQuery: Label discovery
 * - labelValuesQuery: Label value discovery
 * - seriesQuery: Series discovery
 *
 * Usage:
 *   ./k6 run query-test.js
 *   ./k6 run --vus 5 --duration 5m query-test.js
 *
 * Note: Run push-test.js first to populate data, or use existing data.
 *
 * Reference: https://grafana.com/blog/a-quick-guide-to-load-testing-grafana-loki-with-grafana-k6/
 */

import loki from 'k6/x/loki';
import { check, sleep } from 'k6';

// Configuration
const BASE_URL = __ENV.LOKI_URL || 'http://localhost:3100';
const VUS = __ENV.VUS || 5;
const DURATION = __ENV.DURATION || '5m';

// Label cardinality - should match push test for consistent queries
const labelCardinality = {
  namespace: 5,
  app: 10,
  pod: 20,
};

// Initialize Loki client
const conf = new loki.Config(BASE_URL, 30000, 1.0, labelCardinality);
const client = new loki.Client(conf);

// k6 options
export const options = {
  vus: parseInt(VUS),
  duration: DURATION,
  thresholds: {
    // Query duration thresholds
    'http_req_duration{name:query}': ['p(95)<3000', 'p(99)<5000'],
    // Error rate threshold
    'http_req_failed{name:query}': ['rate<0.01'],
  },
};

/**
 * Default function - executed by each VU
 */
export default function () {
  // Randomly select query type
  const queryType = Math.floor(Math.random() * 5);

  let res;

  switch (queryType) {
    case 0:
      // Instant query - point in time
      res = client.instantQuery(
        `count_over_time({namespace=~".+"}[5m])`,
        Math.floor(Date.now() / 1000)  // current timestamp
      );
      break;

    case 1:
      // Range query - time range
      const now = Math.floor(Date.now() / 1000);
      const oneHourAgo = now - 3600;
      res = client.rangeQuery(
        `{namespace=~".+"} |= ""`,
        oneHourAgo,
        now,
        100  // limit
      );
      break;

    case 2:
      // Labels query - discover labels
      res = client.labelsQuery();
      break;

    case 3:
      // Label values query - discover values for a label
      res = client.labelValuesQuery('namespace');
      break;

    case 4:
      // Series query - discover series
      const nowMs = Date.now();
      const oneHourAgoMs = nowMs - 3600000;
      res = client.seriesQuery(
        [`{namespace=~".+"}`],
        oneHourAgoMs,
        nowMs
      );
      break;
  }

  // Check response
  const success = check(res, {
    'query successful': (r) => r.status === 200,
  });

  if (!success) {
    console.error(`Query failed: ${res.status} - ${res.body}`);
  }

  // Small sleep to avoid overwhelming the system
  sleep(0.1);
}

/**
 * Setup function - runs once before test
 */
export function setup() {
  console.log(`Starting query test against ${BASE_URL}`);
  console.log(`VUs: ${VUS}, Duration: ${DURATION}`);

  // Verify Loki is accessible
  const res = client.labelsQuery();
  if (res.status !== 200) {
    throw new Error(`Loki not accessible: ${res.status}`);
  }
  console.log('Loki connection verified');
}

/**
 * Teardown function - runs once after test
 */
export function teardown(data) {
  console.log('Query test completed');
}
