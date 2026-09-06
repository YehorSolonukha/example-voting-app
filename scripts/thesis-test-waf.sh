#!/bin/bash

# THESIS CHECKLIST:
# [ ] Open WAF Admin Dashboard or Logs
# [ ] Verify blocking for malicious User-Agent and Rate Limiting

TARGET_URL=${1:-"http://20.215.182.22:9090/"}
SUCCESS_COUNT=0

echo "Running WAF defensive capability tests..."
echo "----------------------------------------"

# 1. Scanner Evasion / Bad User-Agent
echo -n "Testing malicious user-agent (nikto) ... "
HTTP_STATUS=$(curl.exe -s -o /dev/null -w "%{http_code}" -A "nikto/2.1.6" "$TARGET_URL")

if [ "$HTTP_STATUS" -eq 403 ]; then
    echo "SUCCESS (Blocked by WAF)"
    ((SUCCESS_COUNT++))
else
    echo "FAILED (Status: $HTTP_STATUS)"
fi

# 2. Rate Limiting (DDoS mitigation)
echo "Testing rate limit threshold (Bursting 200 requests) ... "
for i in {1..200}; do
    curl.exe -s -X POST -d "vote=b" "$TARGET_URL" > /dev/null &
done
wait

# Send one more to capture the block
HTTP_STATUS=$(curl.exe -s -o /dev/null -w "%{http_code}" "$TARGET_URL")

if [ "$HTTP_STATUS" -eq 403 ] || [ "$HTTP_STATUS" -eq 429 ]; then
    echo "SUCCESS (Blocked by Rate Limit)"
    ((SUCCESS_COUNT++))
else
    echo "FAILED (Status: $HTTP_STATUS)"
fi

echo "----------------------------------------"

# 3. SQL Injection Attempt
echo -n "Testing SQL Injection payload ... "
# Sending a classic SQL injection payload that matches the WAF rule regex
HTTP_STATUS=$(curl.exe -s -o /dev/null -w "%{http_code}" -X POST -d "vote=a' or 1=1 --" "$TARGET_URL")

if [ "$HTTP_STATUS" -eq 403 ]; then
    echo "SUCCESS (Blocked by WAF)"
    ((SUCCESS_COUNT++))
else
    echo "FAILED (Status: $HTTP_STATUS)"
fi

echo "----------------------------------------"
echo "Tests completed. Passed: $SUCCESS_COUNT/3"
