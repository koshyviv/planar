#!/bin/sh
# Usage: wait_for_it.sh <host> <port> [timeout_seconds]
HOST="$1"
PORT="$2"
TIMEOUT="${3:-30}"

echo "Waiting for $HOST:$PORT (timeout: ${TIMEOUT}s)..."
i=0
while ! nc -z "$HOST" "$PORT" 2>/dev/null; do
    i=$((i + 1))
    if [ "$i" -ge "$TIMEOUT" ]; then
        echo "Timeout waiting for $HOST:$PORT"
        exit 1
    fi
    sleep 1
done
echo "$HOST:$PORT is ready"
