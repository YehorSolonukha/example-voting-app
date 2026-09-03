#!/bin/bash
echo "Starting continuous voting load test against Gateway (Port 9090)..."

while true; do
  if [ $((RANDOM % 2)) -eq 0 ]; then
    VOTE="a"
  else
    VOTE="b"
  fi

  curl -s -X POST -d "vote=$VOTE" http://localhost:9090 > /dev/null
  sleep 0.1
done
