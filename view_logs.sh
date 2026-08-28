#!/bin/bash

echo "============================================="
echo "       WAF Security Audit Logs               "
echo "============================================="

# We use 'docker compose exec' to run a command inside the running 'waf-db' container
# We run 'psql' (the PostgreSQL command line tool)
# -U postgres (login as the postgres user)
# -d waf_logs (connect to the waf_logs database)
# -c (execute the following SQL command and exit)

docker compose exec waf-db psql -U postgres -d waf_logs -c "SELECT id, timestamp, client_ip, reason FROM security_audit_logs ORDER BY id DESC LIMIT 20;"
