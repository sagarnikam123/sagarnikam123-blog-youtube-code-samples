/**
 * Loki Push (Write Path) Load Test
 *
 * Tests Loki's ingestion performance by pushing logs with configurable:
 * - Number of streams per request
 * - Log batch size
 * - Label cardinality
 *
 * Usage:
 *   ./k6 run push-test.js
 *   ./k6 run --vus 10 --duration 5m push-test.js
 *
 * Reference: https://grafana.com/blog/a-quick-guide-to-load-testing-grafana-loki-with-grafana-k6/
 */

import loki from 'k6/x/loki';

// Configuration
const BASE_URL = __ENV.LOKI_URL || 'http://localhost:3100';
const VUS = __ENV.VUS || 10;
const DURATION = __ENV.DURATION || '5m';

// Label cardinality configuration
// Max unique streams = 3 (os) × 5 (format) × namespace × app × pod × VUs
const labelCardinality = {
  namespace: 5,    // 5 different namespaces
  app: 10,         // 10 different apps
  pod: 20,         // 20 different pods
};

// Initialize Loki client
// Parameters: url, timeout_ms, ratio, labels
const conf = new loki.Config(BASE_URL, 10000, 1.0, labelCardinality);
const client = new loki.Client(conf);

// k6 options
export const options = {
  vus: parseInt(VUS),
  duration: DURATION,
  thresholds: {
    // Push request duration thresholds
    'http_req_duration{name:push}': ['p(95)<500', 'p(99)<1000'],
    // Error rate threshold
    'http_req_failed{name:push}': ['rate<0.01'],
  },
};

/**
 * Default function - executed by each VU
 */
export default function () {
  // Basic push: 5 streams, 800KB-1MB total size
  // client.push();

  // Parameterized push: 2-8 streams, 500KB-1MB total size
  const streams = Math.floor(Math.random() * 7) + 2;  // 2-8 streams
  const minSize = 500 * 1024;  // 500KB
  const maxSize = 1024 * 1024; // 1MB

  const res = client.pushParameterized(streams, minSize, maxSize);

  // Check response
  if (res.status !== 204) {
    console.error(`Push failed: ${res.status} - ${res.body}`);
  }
}

/**
 * Setup function - runs once before test
 */
export function setup() {
  console.log(`Starting push test against ${BASE_URL}`);
  console.log(`VUs: ${VUS}, Duration: ${DURATION}`);
  console.log(`Label cardinality: ${JSON.stringify(labelCardinality)}`);
}

/**
 * Teardown function - runs once after test
 */
export function teardown(data) {
  console.log('Push test completed');
}
