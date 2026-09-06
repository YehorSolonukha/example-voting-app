import http from 'k6/http';
import { check, sleep } from 'k6';

// Read target URL from environment or default to localhost
const targetUrl = __ENV.TARGET_URL || 'http://20.215.182.22:9090/';

export const options = {
  stages: [
    { duration: '1m', target: 100 }, // Ramp up to 100 concurrent users
    { duration: '3m', target: 100 }, // Maintain massive load for 3 minutes
    { duration: '1m', target: 0 },   // Ramp down
  ],
};

export default function () {
  const res = http.post(targetUrl, 'vote=a', {
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
  });
  
  check(res, {
    'status was 200': (r) => r.status == 200,
  });
  
  sleep(0.1);
}
