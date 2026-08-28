#!/bin/bash
echo "Initiating Chaos Testing on HA Databases..."

while true; do
  echo "----------------------------------------"
  
  # Find the primary postgres pod (CNPG automatically labels it with role=primary)
  PRIMARY_POD=$(kubectl get pods -l role=primary,postgresql=db-cluster -o jsonpath='{.items[0].metadata.name}' 2>/dev/null)
  
  if [ -n "$PRIMARY_POD" ]; then
    echo "[$(date +%T)] Killing Primary Postgres: $PRIMARY_POD"
    kubectl delete pod $PRIMARY_POD --force --grace-period=0
    echo "Wait and watch the app! A replica will instantly promote itself to Primary."
  else
    echo "[$(date +%T)] No Primary Postgres found yet, waiting..."
  fi

  # Sleep for a bit to let the cluster recover before striking again
  sleep 30
done
