#!/bin/bash
kubectl exec $(kubectl get pod -l role=primary,postgresql=waf-db-cluster -o jsonpath='{.items[0].metadata.name}') -- psql -U postgres -d waf_logs -c "SELECT * FROM security_audit_logs ORDER BY timestamp DESC LIMIT 20;"
