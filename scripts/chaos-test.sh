#!/bin/bash
while true; do
  kubectl delete pod -l role=primary,postgresql=db-cluster --force --grace-period=0
  sleep 30
done
