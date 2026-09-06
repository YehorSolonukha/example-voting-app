#!/bin/bash

# THESIS CHECKLIST:
# [ ] Monitor DB connection metrics in Grafana
# [ ] Check app logs for "Connection Refused" and "Successfully reconnected"

echo "Simulating Database Primary Pod Failure..."

# Using kubectl.exe since you run K8s on Windows! 
# tr -d '\r' removes the hidden Windows carriage returns that break bash variables.
PRIMARY_POD=$(kubectl.exe get pods -l role=primary -o jsonpath='{.items[0].metadata.name}' 2>/dev/null | tr -d '\r')

if [ -z "$PRIMARY_POD" ]; then
    echo "Could not find a pod with label 'role=primary'."
    read -p "Enter the exact name of your primary database pod: " PRIMARY_POD
    PRIMARY_POD=$(echo "$PRIMARY_POD" | tr -d '\r')
fi

if [ -z "$PRIMARY_POD" ]; then
    echo "Aborted."
    exit 1
fi

echo "Deleting primary DB pod: $PRIMARY_POD"
kubectl.exe delete pod "$PRIMARY_POD" --grace-period=0 --force

echo "Pod deleted. Failover initiated."
echo "Action: Watch 'kubectl.exe get pods -w' and your database operator logs."
