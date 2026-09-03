#!/bin/bash
for i in {1..500}; do
  curl -s -X POST -d "vote=a" http://localhost:9090 > /dev/null
done
for i in {1..300}; do
  curl -s -X POST -d "vote=b" http://localhost:9090 > /dev/null
done
