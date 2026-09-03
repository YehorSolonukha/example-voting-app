#!/bin/bash
echo "Run 'ab -n 1000 -c 10 -p post_data.txt http://localhost:9090/' for load testing"
while true; do
  curl -s -X POST -d "vote=a" http://localhost:9090 > /dev/null
  sleep 0.1
done
