/**
 * K6 Load Test - Baseline Performance Test
 *
 * Scenario: 10 concurrent users for 5 minutes
 * Purpose: Measure baseline performance metrics
 *
 * To run:
 * $ k6 run tests/k6_load_test_baseline.js
 */

import http from 'k6/http';
import { check, sleep } from 'k6';
import { Rate, Trend, Counter } from 'k6/metrics';

// Custom metrics
const apiDuration = new Trend('api_duration_ms');
const loginDuration = new Trend('login_duration_ms');
const parseDuration = new Trend('parse_duration_ms');
const errorRate = new Rate('errors');
const successfulRequests = new Counter('successful_requests');

// Test configuration
const BASE_URL = __ENV.BASE_URL || 'http://localhost:8000';
const TEST_USER = {
  email: 'testuser@example.com',
  password: 'TestPassword123!',
  full_name: 'Test User'
};

const SAMPLE_JOB = `Senior Software Engineer - Python

We are looking for a Senior Software Engineer with expertise in Python,
FastAPI, and cloud technologies. The ideal candidate should have:

Requirements:
- 5+ years of Python development experience
- Expertise in FastAPI and REST APIs
- Experience with PostgreSQL and Redis
- AWS experience (EC2, RDS, S3)
- Strong understanding of microservices architecture
- Experience with Docker and Kubernetes
- Git and CI/CD expertise
- Excellent communication skills`;

// Test options
export const options = {
  stages: [
    { duration: '1m', target: 10 },   // Ramp up to 10 users
    { duration: '3m', target: 10 },   // Stay at 10 users
    { duration: '1m', target: 0 },    // Ramp down to 0 users
  ],
  thresholds: {
    'http_req_duration': ['p(95)<500', 'p(99)<1000'],
    'http_req_failed': ['rate<0.1'],
    'api_duration_ms': ['p(95)<500', 'p(99)<1000'],
  },
};

// Setup: Register and login test user
export function setup() {
  // Register user
  let registerResponse = http.post(`${BASE_URL}/api/auth/register`, JSON.stringify({
    email: TEST_USER.email,
    password: TEST_USER.password,
    full_name: TEST_USER.full_name,
    role: 'recruiter',
  }), {
    headers: { 'Content-Type': 'application/json' },
  });

  // Login
  const loginResponse = http.post(`${BASE_URL}/api/auth/login`, JSON.stringify({
    email: TEST_USER.email,
    password: TEST_USER.password,
  }), {
    headers: { 'Content-Type': 'application/json' },
  });

  const token = loginResponse.json('access_token');
  return { token, email: TEST_USER.email };
}

// Main test function
export default function (data) {
  const token = data.token;
  const headers = {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json',
  };

  // Test 1: Health check
  let healthResponse = http.get(`${BASE_URL}/api/health`);
  check(healthResponse, {
    'health status is 200': (r) => r.status === 200,
  });

  // Test 2: Parse job description
  const parseResponse = http.post(`${BASE_URL}/api/jobs/parse`, JSON.stringify({
    job_description: SAMPLE_JOB,
  }), { headers });

  parseDuration.add(parseResponse.timings.duration);
  check(parseResponse, {
    'parse status is 200': (r) => r.status === 200,
    'parse response has data': (r) => r.json('data') !== undefined,
  });

  if (parseResponse.status !== 200) {
    errorRate.add(1);
  } else {
    successfulRequests.add(1);
  }

  sleep(1);

  // Test 3: Get candidates
  const candidatesResponse = http.get(`${BASE_URL}/api/candidates`, { headers });
  check(candidatesResponse, {
    'candidates status is 200': (r) => r.status === 200,
  });

  apiDuration.add(candidatesResponse.timings.duration);

  sleep(1);

  // Test 4: Get matches
  const matchesResponse = http.get(`${BASE_URL}/api/matches`, { headers });
  check(matchesResponse, {
    'matches status is 200': (r) => r.status === 200,
  });

  apiDuration.add(matchesResponse.timings.duration);

  sleep(1);
}

// Teardown: Cleanup (optional)
export function teardown(data) {
  console.log('Test completed');
}
