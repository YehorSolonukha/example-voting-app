#!/bin/bash

echo "=== WAF Verification Test ==="
sleep 5

echo "1. Testing Legitimate Traffic..."
curl -s -H "User-Agent: Mozilla/5.0" http://localhost:9090/ | grep -q -E "Cats|Dogs|body"
if [ $? -eq 0 ]; then
    echo "SUCCESS: Legitimate traffic passed."
else
    echo "FAILED: Could not reach the voting app."
fi

echo "2. Testing User-Agent Block..."
RESPONSE=$(curl -s -A "sqlmap" http://localhost:9090/)
if [[ "$RESPONSE" == *"WAF BLOCK"* ]]; then
    echo "SUCCESS: Blocked malicious User-Agent."
else
    echo "FAILED: User-Agent was not blocked."
fi

echo "3. Testing SQL Injection Block..."
RESPONSE=$(curl -s -A "Mozilla" -X POST -d "drop table users" http://localhost:9090/)
if [[ "$RESPONSE" == *"SQL Injection Detected"* ]]; then
    echo "SUCCESS: Blocked SQL Injection."
else
    echo "FAILED: SQL Injection was not blocked."
fi

echo "4. Testing Rate Limiting..."
for i in {1..55}; do
    curl -s http://localhost:9090/ > /dev/null
done

RESPONSE=$(curl -s http://localhost:9090/)
if [[ "$RESPONSE" == *"Rate Limit Exceeded"* ]]; then
    echo "SUCCESS: Rate Limiter triggered."
else
    echo "FAILED: Rate Limiter did not trigger."
fi

echo "=== Database Audit Log Verification ==="
docker compose exec waf-db psql -U postgres -d waf_logs -c "SELECT client_ip, method, blocked_path, rule_name, reason FROM security_audit_logs LIMIT 10;"
