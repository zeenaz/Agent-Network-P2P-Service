---
title: "Troubleshooting — Common Errors and Fixes"
description: "15 most common errors encountered when building on the AgentNetwork P2P gateway."
---

# 99 — Troubleshooting / 常见问题排查

## Q1 — `anet: command not found`

**Cause:** The install script placed the binary in `~/.anet/bin` which is not
on your `$PATH`.

**Fix:**

```bash
export PATH="$HOME/.anet/bin:$PATH"
# To make permanent:
echo 'export PATH="$HOME/.anet/bin:$PATH"' >> ~/.bashrc && source ~/.bashrc
```

---

## Q2 — `AuthMissingError: no API token`

**Cause:** The SDK cannot find a bearer token.

**Fix (in priority order):**

1. `export ANET_TOKEN=$(cat ~/.anet/api_token | tr -d '[:space:]')` — or set `ANET_BASE_URL` to point at a running daemon.
2. Pass `token=...` directly to `SvcClient(token="...")`.
3. Make sure `anet daemon` is running and wrote `~/.anet/api_token`.

---

## Q3 — `daemon HTTP 400: register failed: endpoint host must be localhost`

**Cause:** You passed a non-`127.0.0.1` endpoint to `svc.register()` without
opting both the daemon and the service into the SSRF allowlist.

**Fix:**

1. Edit `~/.anet/config.json` → add the host to `svc_remote_allowlist`.
2. Pass `remote_hosts=[<host>]` to `svc.register()`.

---

## Q4 — `discover --skill=<tag>` returns 0 results

**Cause (most likely):** ANS gossip has not converged yet.

**Fix:** Wait 3-5 seconds after registration and retry. Also verify:

- `anet svc list` shows the service on daemon-1.
- `anet status` on daemon-2 shows `peers >= 1`.
- The mesh actually connected: `bash scripts/two-node.sh status`.

---

## Q5 — `402 insufficient credits` on the first priced cross-node call

**Cause:** Bootstrap grants are local-only and do not gossip. The provider's
ledger does not know the caller's DID, so even though both `anet balance` show
5000, the provider sees 0 for the caller.

**Fix:** Run a mutual seed transfer before the first priced call:

```bash
# The two-node.sh start script does this automatically.
# To do it manually:
curl -s -H "Authorization: Bearer $TOK1" \
     -X POST http://127.0.0.1:13921/api/credits/transfer \
     -H "Content-Type: application/json" \
     -d '{"from":"<DID1>","to":"<DID2>","amount":1000,"reason":"seed"}'
```

---

## Q6 — `peer not found in routing table`

**Cause:** You stored the `peer_id` from daemon-1's discover and tried to call
from daemon-2 (or vice versa). The peer_id is correct but you connected to the
wrong daemon.

**Fix:** Always call from the same daemon that ran `svc.discover()`. The
routing table is per-daemon.

---

## Q7 — `audit` rows show `status: 0`

**Cause:** Old daemon version (< v1.1.10) that did not write the real upstream
HTTP status into `svc_call_log`.

**Fix:** `curl -fsSL https://agentnetwork.org.cn/install.sh | sh` to upgrade.

---

## Q8 — `svc.stream()` hangs forever

**Cause:** The upstream backend returned a chunked or SSE response but the
daemon timeout is shorter than the stream duration.

**Fix:** Pass `timeout=None` to `SvcClient(timeout=None)` for long streams.

---

## Q9 — `meta` returns 404

**Cause:** `register()` was called with `meta_path="/meta"` but the backend
does not implement `GET /meta`.

**Fix:** Add a `/meta` handler to your backend, or omit `meta_path=` from the
`register()` call.

---

## Q10 — Two nodes on the same laptop can see each other but a third
machine can't join

**Cause:** The `two-node.sh` script uses `127.0.0.1` for P2P listen addresses,
which are not reachable from another machine.

**Fix:** For multi-machine testing, change `listen_addrs` in
`~/.anet/config.json` to the machine's LAN IP and ensure the P2P port is
reachable (e.g., no firewall blocking it).

---

## Q11 — `FastAPI startup error: address already in use`

**Cause:** Another process is already using the port.

**Fix:**

```bash
lsof -ti tcp:8000 | xargs kill    # replace 8000 with the port in use
```

---

## Q12 — `ImportError: No module named 'fastapi'`

**Cause:** FastAPI is not installed in the active virtualenv.

**Fix:**

```bash
pip install fastapi uvicorn
```

---

## Q13 — `two-node.sh: anet not in PATH`

**Cause:** `anet` binary is not found. `ANET` env var can override the path.

**Fix:**

```bash
ANET=/path/to/anet bash scripts/two-node.sh start
```

---

## Q14 — Register succeeds but `anet svc health` shows `unhealthy`

**Cause:** The daemon's health probe to `health_check` path failed — the
backend is not running or returned non-200.

**Fix:** Ensure your backend is running and `GET /health` returns HTTP 200
before registering.

---

## Q15 — `SvcAPIError: daemon HTTP 409: service name already registered`

**Cause:** A previous run left the service registered. The daemon does not
persist registrations across restarts, but if the daemon is still running the
old entry is there.

**Fix:** Call `svc.unregister(name)` before re-registering, or ignore the 409
on first registration (as the example scripts do).
