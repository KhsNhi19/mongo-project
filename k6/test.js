import http from 'k6/http';
import { check, sleep } from "k6";

export const options = {
  vus: 50,
  duration: "30s",
  thresholds: {
    http_req_failed: ["rate<0.01"],
    http_req_duration: ["p(95)<500"],
  },
};

export default function () {
  const res = http.get('http://backend:5000/api/businesses?category=Restaurants');
  check(res, { "status was 200": (r) => r.status == 200 });
  sleep(1);
}
