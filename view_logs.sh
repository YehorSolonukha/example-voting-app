#!/bin/bash

echo "============================================="
echo "       WAF Security Audit Logs               "
echo "============================================="

docker compose exec waf-db psql -U postgres -d waf_logs -c "SELECT id, timestamp, client_ip, reason FROM security_audit_logs ORDER BY id DESC LIMIT 20;"
