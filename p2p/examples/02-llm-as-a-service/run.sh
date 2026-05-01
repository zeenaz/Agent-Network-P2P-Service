#!/usr/bin/env bash
# 02-llm-as-a-service end-to-end driver.
# Prereqs: two-node.sh start, SDK importable, uvicorn installed.
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
HOME1="${HOME1:-/tmp/anet-p2p-u1}"
HOME2="${HOME2:-/tmp/anet-p2p-u2}"
LLM_PORT=7200

if [ ! -f "$HOME1/.anet/api_token" ] || [ ! -f "$HOME2/.anet/api_token" ]; then
  echo "✗ daemons not running; run starter-template/scripts/two-node.sh start first" >&2
  exit 1
fi

PIDS_TO_KILL=()
cleanup() {
  for pid in "${PIDS_TO_KILL[@]:-}"; do kill "$pid" 2>/dev/null || true; done
  # Clean up any stray process still binding the port (SIGTERM, then SIGKILL).
  lsof -ti tcp:"$LLM_PORT" 2>/dev/null | xargs -r kill    2>/dev/null || true
  sleep 1
  lsof -ti tcp:"$LLM_PORT" 2>/dev/null | xargs -r kill -9 2>/dev/null || true
}
trap cleanup EXIT

echo "▶ Starting LLM backend (fake) …"
LLM_PORT="$LLM_PORT" LLM_BACKEND=fake python3 "$HERE/llm_backend.py" \
  > /tmp/llm-backend.log 2>&1 &
PIDS_TO_KILL+=($!)
sleep 2

curl -sf -m 3 "http://127.0.0.1:$LLM_PORT/health" >/dev/null \
  || { echo "✗ LLM backend failed"; tail /tmp/llm-backend.log; exit 1; }
echo "✓ LLM backend healthy"

echo "▶ Registering LLM service on daemon-1 …"
ANET_BASE_URL="http://127.0.0.1:13921" \
  ANET_TOKEN="$(tr -d '[:space:]' < "$HOME1/.anet/api_token")" \
  LLM_PORT="$LLM_PORT" \
  python3 "$HERE/service.py"

echo "▶ Consuming from daemon-2 …"
ANET_BASE_URL="http://127.0.0.1:13922" \
  ANET_TOKEN="$(tr -d '[:space:]' < "$HOME2/.anet/api_token")" \
  python3 "$HERE/consumer.py" \
    --prompt "Write a haiku about P2P networks."

echo ""
echo "▶ Streaming from daemon-2 …"
ANET_BASE_URL="http://127.0.0.1:13922" \
  ANET_TOKEN="$(tr -d '[:space:]' < "$HOME2/.anet/api_token")" \
  python3 "$HERE/consumer.py" \
    --stream --prompt "Tell me a one-sentence story."
