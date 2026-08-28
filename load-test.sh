#!/bin/bash
echo "Starting continuous voting load test against Gateway (Port 9090)..."
echo "Press Ctrl+C to stop."

while true; do
  # Randomly vote for a or b
  if [ $((RANDOM % 2)) -eq 0 ]; then
    VOTE="a"
  else
    VOTE="b"
  fi

  # Send POST request quietly in the background
  curl -s -X POST -d "vote=$VOTE" http://localhost:9090 > /dev/null
  
  echo "Voted for $VOTE"
  sleep 0.1
done
