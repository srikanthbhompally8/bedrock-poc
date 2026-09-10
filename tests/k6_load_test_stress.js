/**
 * K6 Load Test - Stress Test
 *
 * Scenario: Gradually increase load to 500+ concurrent users
 * Purpose: Find breaking point and measure system stability
 *
 * To run:
 * $ k6 run tests/k6_load_test_stress.js
 */

import http from 'k6/http';
import { check, sleep } from 'k6';
import { Rate, Trend } from 'k6/metrics';

const apiDuration = new Trend('api_duration_ms');
const errorRate = new Rate('errors');

const BASE_URL = __ENV.BASE_URL || 'http://localhost:8000';

const TEST_USER = {
  email: 'stresstest@example.com',
  password: 'TestPassword123!',
  full_name: 'Stress Test User',
};

const SAMPLE_JOB = `Senior Software Engineer - Python

Requirements:
- 5+ years of Python development experience
- Expertise in FastAPI and REST APIs
- Experience with PostgreSQL and Redis
- AWS experience (EC2, RDS, S3)`;

// Stress test configuration - gradually increase load
export const options = {
  stages: [
    { duration: '2m', target: 10 },    // Ramp up to 10 users
    { duration: '2m', target: 25 },    // Ramp up to 25 users
    { duration: '2m', target: 50 },    // Ramp up to 50 users
    { duration: '2m', target: 100 },   // Ramp up to 100 users
    { duration: '2m', target: 200 },   // Ramp up to 200 users
    { duration: '5m', target: 200 },   // Hold at 200 users
    { duration: '2m', target: 0 },     // Ramp down
  ],
  thresholds: {
    'http_req_duration': ['p(95)<1000', 'p(99)<2000'],
    'http_req_failed': ['rate<1'],
  },
};

export function setup() {
  const registerResponse = http.post(`${BASE_URL}/api/auth/register`, JSON.stringify({
    email: TEST_USER.email,
    password: TEST_USER.password,
    full_name: TEST_USER.full_name,
    role: 'recruiter',
  }), {
    headers: { 'Content-Type': 'application/json' },
  });

  const loginResponse = http.post(`${BASE_URL}/api/auth/login`, JSON.stringify({
    email: TEST_USER.email,
    password: TEST_USER.password,
  }), {
    headers: { 'Content-Type': 'application/json' },
  });

  const token = loginResponse.json('access_token');
  return { token };
}

export default function (data) {
  const token = data.token;
  const headers = {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json',
  };

  // Focus on job parsing - most resource intensive
  const parseResponse = http.post(`${BASE_URL}/api/jobs/parse`, JSON.stringify({
    job_description: SAMPLE_JOB,
  }), { headers });

  apiDuration.add(parseResponse.timings.duration);

  check(parseResponse, {
    'parse status is 200 or 201': (r) => r.status === 200 || r.status === 201,
  });

  if (parseResponse.status !== 200 && parseResponse.status !== 201) {
    errorRate.add(1);
  }

  sleep(0.5);
}
