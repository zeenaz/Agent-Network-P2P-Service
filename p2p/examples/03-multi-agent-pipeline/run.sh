#!/usr/bin/env bash
# 03-multi-agent-pipeline end-to-end driver.
# Prereqs: two-node.sh start, SDK importable, uvicorn+fastapi installed.
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
HOME1="${HOME1:-/tmp/anet-p2p-u1}"
HOME2="${HOME2:-/tmp/anet-p2p-u2}"
ORCH_PORT=7310; WA_PORT=7311; WB_PORT=7312

if [ ! -f "$HOME1/.anet/api_token" ]; then
  echo "✗ daemon-1 not running; run two-node.sh start first" >&2
  exit 1
fi

TOK1="$(tr -d '[:space:]' < "$HOME1/.anet/api_token")"
TOK2="$(tr -d '[:space:]' < "$HOME2/.anet/api_token")"

PIDS_TO_KILL=()
cleanup() {
  for pid in "${PIDS_TO_KILL[@]:-}"; do kill "$pid" 2>/dev/null || true; done
  for p in "$ORCH_PORT" "$WA_PORT" "$WB_PORT"; do
    lsof -ti tcp:"$p" 2>/dev/null | xargs -r kill -9 2>/dev/null || true
  done
}
trap cleanup EXIT

# All three services run on daemon-1.
export ANET_BASE_URL="http://127.0.0.1:13921"
export ANET_TOKEN="$TOK1"

echo "▶ Starting worker-a (transform) …"
WORKER_A_PORT="$WA_PORT" python3 "$HERE/worker_a.py" > /tmp/wa.log 2>&1 &
PIDS_TO_KILL+=($!)

echo "▶ Starting worker-b (sentiment) …"
WORKER_B_PORT="$WB_PORT" python3 "$HERE/worker_b.py" > /tmp/wb.log 2>&1 &
PIDS_TO_KILL+=($!)

echo "▶ Starting orchestrator …"
ORCH_PORT="$ORCH_PORT" python3 "$HERE/orchestrator.py" > /tmp/orch.log 2>&1 &
PIDS_TO_KILL+=($!)

sleep 3

# Sanity probes
for port in "$WA_PORT" "$WB_PORT" "$ORCH_PORT"; do
  curl -sf -m 3 "http://127.0.0.1:$port/health" >/dev/null \
    || { echo "✗ service on :$port failed"; exit 1; }
done
echo "✓ all three services healthy"

echo ""
echo "▶ Calling orchestrator from daemon-2 …"
ANET_BASE_URL="http://127.0.0.1:13922" \
  ANET_TOKEN="$TOK2" \
  python3 - <<'EOF'
import os, sys, time
from anet.svc import SvcClient
with SvcClient(base_url=os.environ["ANET_BASE_URL"]) as svc:
    peers = []
    for _ in range(15):
        peers = svc.discover(skill="orchestrator")
        if peers: break
        time.sleep(1)
    if not peers:
        print("✗ orchestrator not found", file=sys.stderr); sys.exit(1)
    p = peers[0]
    resp = svc.call(p["peer_id"], p["services"][0]["name"], "/process",
                    method="POST",
                    body={"text": "This is a wonderful and amazing distributed system."})
    print(f"HTTP {resp.get('status')}  body={resp.get('body')}")
    body = resp.get("body") or {}
    assert body.get("transformed"), "transformed is empty"
    assert body.get("sentiment") == "positive", f"expected positive, got {body.get('sentiment')}"
    print("✓ pipeline PASSED")
EOF
