#!/bin/bash
set -e
echo "=== Checking static files ==="
ls /app/backend/static/ || echo "ERROR: static/ folder MISSING"
ls /app/backend/static/assets/ || echo "ERROR: assets/ folder MISSING"
cat /app/backend/static/index.html || echo "ERROR: index.html MISSING"
echo "=== Starting server ==="
cd /app/backend
python3 -m uvicorn "fastapi_app:create_app" --factory --host 0.0.0.0 --port 8000