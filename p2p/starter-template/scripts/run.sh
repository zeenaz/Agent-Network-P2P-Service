#!/usr/bin/env bash
# scripts/run.sh — start uvicorn + register loop pinned to one daemon.
#
# Usage:
#   bash scripts/run.sh u1    # use daemon-1 (REST :13921)
#   bash scripts/run.sh u2    # use daemon-2 (REST :13922)
#   bash scripts/run.sh       # uses ANET_BASE_URL from env or .env

set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

USER_SLOT="${1:-}"

case "$USER_SLOT" in
  u1)
    export ANET_BASE_URL="http://127.0.0.1:13921"
    export ANET_TOKEN="$(tr -d '[:space:]' < /tmp/anet-p2p-u1/.anet/api_token)"
    export MY_BACKEND_PORT="${MY_BACKEND_PORT:-8001}"
    ;;
  u2)
    export ANET_BASE_URL="http://127.0.0.1:13922"
    export ANET_TOKEN="$(tr -d '[:space:]' < /tmp/anet-p2p-u2/.anet/api_token)"
    export MY_BACKEND_PORT="${MY_BACKEND_PORT:-8002}"
    ;;
  "")
    # Use whatever is in the environment / .env
    export MY_BACKEND_PORT="${MY_BACKEND_PORT:-8000}"
    ;;
  *)
    echo "usage: $0 {u1|u2}" >&2; exit 1 ;;
esac

# Activate venv if present
if [ -f .venv/bin/activate ]; then
  # shellcheck source=/dev/null
  source .venv/bin/activate
fi

echo "Starting backend on port ${MY_BACKEND_PORT} …"
uvicorn my_agent.backend:app --host 127.0.0.1 --port "${MY_BACKEND_PORT}" &
UVICORN_PID=$!

echo "Starting register loop …"
python -m my_agent.service &
SERVICE_PID=$!

cleanup() {
  kill "$UVICORN_PID" "$SERVICE_PID" 2>/dev/null || true
}
trap cleanup EXIT INT TERM

wait
