#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo "=== VEP Service Backend Dev Mode ==="
echo "Project root: $PROJECT_ROOT"
echo ""

cd "$PROJECT_ROOT"

# Step 1: Activate or create venv
if [ -d "venv" ]; then
    source venv/bin/activate
else
    echo "[1/2] Creating virtual environment..."
    python3 -m venv venv
    source venv/bin/activate
fi

# Step 2: Install dependencies and start server
echo "[2/2] Installing dependencies..."
pip install -q -r requirements.txt

echo ""
echo "Starting backend with hot-reload..."
echo ""
echo "  API:   http://127.0.0.1:8001"
echo "  Docs:  http://127.0.0.1:8001/docs"
echo "  Health: http://127.0.0.1:8001/health"
echo "  Press Ctrl+C to stop"
echo ""

python -m uvicorn main:app --host 127.0.0.1 --port 8001 --reload
