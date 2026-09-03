#!/bin/bash
curl -s -H "User-Agent: sqlmap" http://localhost:9090/
curl -s -X POST -d "vote=a' OR 1=1 --" http://localhost:9090/
for i in {1..60}; do
  curl -s http://localhost:9090/
done
