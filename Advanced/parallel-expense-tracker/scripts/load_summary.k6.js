// k6 load test for GET /api/summary (and a light write mix).
//
// Validates the A6 optimization under sustained concurrency, not just a
// single-threaded micro-benchmark. Thresholds fail the run if p95 latency or
// the error rate regress — wire into CI once k6 is available on the runner.
//
//   BASE_URL=http://localhost:8000 k6 run scripts/load_summary.k6.js
//
// See docs/LOAD_TESTING.md for how to seed data and interpret results.
import http from 'k6/http';
import { check, sleep } from 'k6';

const BASE_URL = __ENV.BASE_URL || 'http://localhost:8000';

export const options = {
  scenarios: {
    summary_read: {
      executor: 'ramping-vus',
      exec: 'readSummary',
      startVUs: 0,
      stages: [
        { duration: '15s', target: 20 }, // ramp up
        { duration: '30s', target: 20 }, // steady
        { duration: '10s', target: 0 },  // ramp down
      ],
    },
    occasional_write: {
      executor: 'constant-vus',
      exec: 'writeExpense',
      vus: 2,
      duration: '55s',
    },
  },
  thresholds: {
    // The A6 optimization keeps summary p95 well under 100ms even under load.
    'http_req_duration{endpoint:summary}': ['p(95)<100'],
    'http_req_failed': ['rate<0.01'], // < 1% errors (WAL should prevent lock errors)
  },
};

export function readSummary() {
  const res = http.get(`${BASE_URL}/api/summary`, {
    tags: { endpoint: 'summary' },
  });
  check(res, {
    'summary 200': (r) => r.status === 200,
    'summary has count': (r) => r.json('count') !== undefined,
  });
  sleep(0.5);
}

export function writeExpense() {
  const payload = JSON.stringify({
    amount: 12.34,
    category: 'load-test',
    note: 'k6',
  });
  const res = http.post(`${BASE_URL}/api/expenses`, payload, {
    headers: { 'Content-Type': 'application/json' },
    tags: { endpoint: 'create' },
  });
  check(res, { 'create 201': (r) => r.status === 201 });
  sleep(1);
}
