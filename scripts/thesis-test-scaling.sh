#!/bin/bash

# THESIS CHECKLIST:
# [ ] Watch 'kubectl get hpa -w'
# [ ] Monitor Grafana CPU metrics and Pod count

TARGET_URL=${1:-"http://20.215.182.22:9090/"}
if [[ ! "$TARGET_URL" =~ ^https?:// ]]; then
    TARGET_URL="http://$TARGET_URL"
fi
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

echo "Starting autoscaling load test using k6..."

if command -v k6 &> /dev/null; then
    echo "Running native k6..."
    TARGET_URL=$TARGET_URL k6 run "/c/Users/YehorSolonukha/voting_app/scripts/k6-load-test.js"
else
    echo "k6 not found locally. Running via Docker..."
    # Note: Use host.docker.internal if targeting localhost from within Docker on Windows/Mac
    DOCKER_URL=${TARGET_URL/localhost/host.docker.internal}
    docker run --rm -i -e TARGET_URL="$DOCKER_URL" grafana/k6 run - < "$DIR/k6-load-test.js"
fi
