#!/bin/bash
set -e
cd "$(dirname "$0")/.."

echo "=== Running API tests ==="
PYTHONPATH=services/api python3 -m pytest tests/api/ -v

echo ""
echo "=== Running Worker tests ==="
PYTHONPATH=services/worker python3 -m pytest tests/worker/ -v

echo ""
echo "All tests passed!"
