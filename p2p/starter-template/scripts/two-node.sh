#!/usr/bin/env bash
# scripts/two-node.sh — bring up two isolated anet daemons on this laptop so
# you can test register/discover/call locally without needing a teammate.
#
# Layout:
#   /tmp/anet-p2p-u1    HOME for daemon-1  (REST :13921, P2P :14021)
#   /tmp/anet-p2p-u2    HOME for daemon-2  (REST :13922, P2P :14022)
#
# Daemon-2 is wired to dial daemon-1 via explicit bootstrap_peers so this
# works even on campus networks where mDNS is blocked.
#
# Usage:
#   bash scripts/two-node.sh start   (default)
#   bash scripts/two-node.sh stop
#   bash scripts/two-node.sh status

set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
ANET="${ANET:-anet}"
HOME1="${HOME1:-/tmp/anet-p2p-u1}"
HOME2="${HOME2:-/tmp/anet-p2p-u2}"
API1=13921; P2P1=14021
API2=13922; P2P2=14022

green()  { printf "\033[32m✓\033[0m %s\n" "$*"; }
red()    { printf "\033[31m✗\033[0m %s\n" "$*"; }
header() { printf "\n\033[1;36m═══ %s ═══\033[0m\n" "$*"; }

write_config() {
  local dir="$1" api="$2" p2p="$3" boot_csv="$4"
  mkdir -p "$dir/.anet"
  cat > "$dir/.anet/config.json" <<EOF
{
  "listen_addrs": ["/ip4/127.0.0.1/tcp/$p2p"],
  "bootstrap_peers": [$boot_csv],
  "api_port": $api,
  "relay_enabled": false,
  "topics_auto_join": ["/anet/ans", "/anet/credits"],
  "bt_dht": {"enabled": false},
  "overlay": {"enabled": false}
}
EOF
}

api_alive() {
  local port="$1"
  curl -sf --noproxy '*' -m 2 "http://127.0.0.1:${port}/api/status" >/dev/null 2>&1
}

wait_for_api() {
  local port="$1" name="$2"
  printf "  waiting for %s on :%s …" "$name" "$port"
  for _ in $(seq 1 60); do
    if api_alive "$port"; then echo " ready"; return 0; fi
    sleep 1
  done
  echo " TIMEOUT"; return 1
}

cmd_start() {
  command -v "$ANET" >/dev/null \
    || { red "anet not in PATH (set ANET=/path/to/anet or install via install.sh)"; exit 1; }

  header "Reset homes"
  rm -rf "$HOME1" "$HOME2"
  mkdir -p "$HOME1" "$HOME2"

  for port in $API1 $API2 $P2P1 $P2P2; do
    lsof -ti tcp:"$port" 2>/dev/null | xargs -r kill -9 2>/dev/null || true
  done

  header "Start daemon-1"
  write_config "$HOME1" "$API1" "$P2P1" ""
  HOME="$HOME1" "$ANET" daemon > "$HOME1/daemon.log" 2>&1 &
  echo "  pid=$!  HOME=$HOME1"
  wait_for_api "$API1" daemon-1 \
    || { red "daemon-1 failed"; tail "$HOME1/daemon.log"; exit 1; }
  PEER1=$(curl -sf --noproxy '*' "http://127.0.0.1:${API1}/api/status" \
            | python3 -c "import sys,json;print(json.load(sys.stdin)['peer_id'])")
  green "daemon-1  PEER=$PEER1"

  header "Start daemon-2 (bootstrapped to daemon-1)"
  write_config "$HOME2" "$API2" "$P2P2" \
    "\"/ip4/127.0.0.1/tcp/$P2P1/p2p/$PEER1\""
  HOME="$HOME2" "$ANET" daemon > "$HOME2/daemon.log" 2>&1 &
  echo "  pid=$!  HOME=$HOME2"
  wait_for_api "$API2" daemon-2 \
    || { red "daemon-2 failed"; tail "$HOME2/daemon.log"; exit 1; }
  green "daemon-2 ready"

  header "Seed cross-node credit ledgers"
  TOK1=$(tr -d '[:space:]' < "$HOME1/.anet/api_token")
  TOK2=$(tr -d '[:space:]' < "$HOME2/.anet/api_token")
  DID1=$(curl -sf --noproxy '*' "http://127.0.0.1:${API1}/api/status" \
           | python3 -c "import sys,json;print(json.load(sys.stdin)['did'])" 2>/dev/null)
  DID2=$(curl -sf --noproxy '*' "http://127.0.0.1:${API2}/api/status" \
           | python3 -c "import sys,json;print(json.load(sys.stdin)['did'])" 2>/dev/null)

  if [ -n "$DID1" ] && [ -n "$DID2" ]; then
    for _ in $(seq 1 15); do
      peers=$(curl -sf --noproxy '*' "http://127.0.0.1:${API1}/api/status" \
                | python3 -c \
                    "import sys,json;print(json.load(sys.stdin).get('peers',0))" \
                    2>/dev/null || echo 0)
      [ "${peers:-0}" -ge 1 ] && break
      sleep 1
    done
    R1=$(curl -sf --noproxy '*' \
              -H "Authorization: Bearer $TOK1" \
              -H "Content-Type: application/json" \
              -X POST "http://127.0.0.1:${API1}/api/credits/transfer" \
              -d "{\"from\":\"$DID1\",\"to\":\"$DID2\",\"amount\":1000,\"reason\":\"p2p-seed\"}" \
              2>/dev/null || echo "")
    R2=$(curl -sf --noproxy '*' \
              -H "Authorization: Bearer $TOK2" \
              -H "Content-Type: application/json" \
              -X POST "http://127.0.0.1:${API2}/api/credits/transfer" \
              -d "{\"from\":\"$DID2\",\"to\":\"$DID1\",\"amount\":1000,\"reason\":\"p2p-seed\"}" \
              2>/dev/null || echo "")
    if echo "$R1" | grep -q sender_event && echo "$R2" | grep -q sender_event; then
      green "seed transfers ok (1000⇄1000 shells)"
    else
      red "seed transfer failed; cross-node priced calls may hit 402"
    fi
  fi

  header "Summary"
  green "daemon-1   API=http://127.0.0.1:${API1}   HOME=${HOME1}"
  green "daemon-2   API=http://127.0.0.1:${API2}   HOME=${HOME2}"
  echo ""
  echo "Next:"
  echo "  Terminal 2: bash scripts/run.sh u1    # start my-agent on daemon-1"
  echo "  Terminal 3: ANET_BASE_URL=http://127.0.0.1:${API2} \\"
  echo "              ANET_TOKEN=\$(tr -d '[:space:]' < ${HOME2}/.anet/api_token) \\"
  echo "              python -m my_agent.client --skill p2p"
}

cmd_stop() {
  for port in $API1 $API2 $P2P1 $P2P2; do
    lsof -ti tcp:"$port" 2>/dev/null | xargs -r kill 2>/dev/null || true
  done
  green "daemons stopped"
}

cmd_status() {
  for name in "daemon-1:${API1}" "daemon-2:${API2}"; do
    n="${name%%:*}"; p="${name##*:}"
    if api_alive "$p"; then
      green "$n  (:$p alive)"
    else
      red "$n  (:$p not responding)"
    fi
  done
}

case "${1:-start}" in
  start)  cmd_start ;;
  stop)   cmd_stop  ;;
  status) cmd_status ;;
  *) echo "usage: $0 {start|stop|status}" >&2; exit 1 ;;
esac
