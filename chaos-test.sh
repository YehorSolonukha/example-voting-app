#!/bin/bash
echo "Initiating Chaos Testing on HA Databases..."

while true; do
  echo "----------------------------------------"
  
  if kubectl get pods -l role=primary,postgresql=db-cluster | grep -q 'Running'; then
    echo "[$(date +%T)] Killing Primary Postgres"
    kubectl delete pod -l role=primary,postgresql=db-cluster --force --grace-period=0
  else
    echo "[$(date +%T)] No Primary Postgres found yet, waiting..."
  fi

  sleep 30
done
