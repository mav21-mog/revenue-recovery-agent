#!/usr/bin/env bash
# ==============================================================================
# RecoverPay - Start Development Server
# ==============================================================================

set -euo pipefail

if [[ ! -d ".venv" ]]; then
    echo "Virtual environment not found. Running ./setup.sh first..."
    ./setup.sh
fi

PORT="${PORT:-8000}"
HOST="${HOST:-0.0.0.0}"

echo "Starting RecoverPay API server on http://${HOST}:${PORT}..."
echo "Swagger docs available at: http://127.0.0.1:${PORT}/docs"

exec ./.venv/bin/uvicorn backend.main:app --host "$HOST" --port "$PORT" --reload
