#!/bin/bash

echo "=== WAF Verification Test ==="
echo "Note: Make sure your containers are running! (Run 'docker compose up --build -d' first)"
echo "Waiting a few seconds for services to boot..."
sleep 5
echo ""

# 1. Test Legitimate Traffic
echo "1. Testing Legitimate Traffic..."
# We try to load the voting page. The HTML should contain the word "Cats" or "Dogs"
curl -s -H "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64)" http://localhost:9090/ | grep -q -E "Cats|Dogs|body"
if [ $? -eq 0 ]; then
    echo "✅ SUCCESS: Legitimate traffic passed through to the Vote app."
else
    echo "❌ FAILED: Could not reach the voting app (or the Time-based rule blocked us!)."
fi
echo ""

# 2. Test User-Agent Block
echo "2. Testing User-Agent Block (using fake 'sqlmap' bot)..."
RESPONSE=$(curl -s -A "sqlmap" http://localhost:9090/)
if [[ "$RESPONSE" == *"WAF BLOCK"* ]]; then
    echo "✅ SUCCESS: Blocked malicious User-Agent. Response: $RESPONSE"
else
    echo "❌ FAILED: User-Agent was not blocked."
fi
echo ""

# 3. Test SQL Injection Block
echo "3. Testing SQL Injection Block..."
# We pass a fake safe User-Agent so it doesn't get blocked by the UserAgent rule first!
RESPONSE=$(curl -s -A "Mozilla" -X POST -d "drop table users" http://localhost:9090/)
if [[ "$RESPONSE" == *"SQL Injection Detected"* ]]; then
    echo "✅ SUCCESS: Blocked SQL Injection. Response: $RESPONSE"
else
    echo "❌ FAILED: SQL Injection was not blocked. Response was: $RESPONSE"
fi
echo ""

# 4. Test Rate Limiting
echo "4. Testing Rate Limiting (Sending 55 requests instantly)..."
for i in {1..55}; do
    # Send request and throw away the output
    curl -s http://localhost:9090/ > /dev/null
done

# The 56th request should definitely be blocked
RESPONSE=$(curl -s http://localhost:9090/)
if [[ "$RESPONSE" == *"Rate Limit Exceeded"* ]]; then
    echo "✅ SUCCESS: Rate Limiter triggered! Response: $RESPONSE"
else
    echo "❌ FAILED: Rate Limiter did not trigger."
fi
echo ""

echo "=== Database Audit Log Verification ==="
echo "Checking the PostgreSQL 'waf-db' for recorded attacks..."
# We use docker compose exec to run a SQL query directly inside the database container
docker compose exec waf-db psql -U postgres -d waf_logs -c "SELECT client_ip, method, blocked_path, rule_name, reason FROM security_audit_logs LIMIT 10;"
