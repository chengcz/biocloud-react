#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo "=== VEP Service Dev Mode ==="
echo "Project root: $PROJECT_ROOT"
echo ""

cd "$PROJECT_ROOT"

# Step 1: Start PostgreSQL via Docker and wait for it to be ready
echo "[1/4] Starting PostgreSQL (Docker)..."
docker compose up -d postgres

echo "Waiting for PostgreSQL to be ready..."
for i in $(seq 1 30); do
    if docker exec vep_postgres pg_isready -U vep_user -d vep_cache >/dev/null 2>&1; then
        echo "PostgreSQL is ready."
        break
    fi
    if [ "$i" -eq 30 ]; then
        echo "ERROR: PostgreSQL did not become ready within 30s" >&2
        exit 1
    fi
    sleep 1
done

# Step 2: Activate or create venv
echo "[2/4] Setting up virtual environment..."
if [ -d "venv" ]; then
    source venv/bin/activate
else
    python3 -m venv venv
    source venv/bin/activate
fi

# Step 3: Install dependencies and initialize database
echo "[3/4] Installing dependencies and initializing database..."
pip install -q -r requirements.txt
python init_db.py

# Step 4: Start backend
echo "[4/4] Starting backend with hot-reload..."
echo ""
echo "=== VEP Service Dev Mode Ready ==="
echo "  API:   http://127.0.0.1:8001"
echo "  Docs:  http://127.0.0.1:8001/docs"
echo "  Health: http://127.0.0.1:8001/health"
echo "  PostgreSQL: localhost:5433 (Docker)"
echo "  Press Ctrl+C to stop"
echo ""

python -m uvicorn main:app --host 127.0.0.1 --port 8001 --reload
