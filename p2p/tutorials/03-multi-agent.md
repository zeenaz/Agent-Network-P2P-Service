---
title: "P2P 03 — Multi-Agent Pipeline"
description: "Three agents on the mesh: an orchestrator fans out to two workers and aggregates the results."
---

# 03 — Multi-Agent Pipeline / 多 Agent 流水线

## 1. 你将完成什么 / What you'll achieve

Run three independent agents on the mesh:

| Agent | Skill tag | What it does |
|---|---|---|
| `worker-transform` | `transform` | Uppercases the input text |
| `worker-sentiment` | `sentiment` | Classifies sentiment (positive / negative / neutral) |
| `orchestrator` | `orchestrator` | Fans out to both workers, aggregates the result |

A fourth peer (daemon-2) calls the orchestrator and receives the combined
result — never knowing the orchestrator's internal topology.

## 2. Prerequisites / 前置条件

- Completed `02-llm-service.md`.
- `fastapi`, `uvicorn` installed.

## 3. Steps / 步骤

### 3.1 Start all three services on daemon-1 / 在 daemon-1 上启动三个服务

```bash
cd p2p/examples/03-multi-agent-pipeline
export ANET_BASE_URL=http://127.0.0.1:13921
export ANET_TOKEN=$(cat /tmp/anet-p2p-u1/.anet/api_token | tr -d '[:space:]')

python3 worker_a.py &     # port 7311, skill=transform
python3 worker_b.py &     # port 7312, skill=sentiment
python3 orchestrator.py & # port 7310, skill=orchestrator
sleep 3
```

Each service self-registers at startup — no manual registration needed.

### 3.2 Call the orchestrator from daemon-2 / 从 daemon-2 调用 orchestrator

```bash
export ANET_BASE_URL=http://127.0.0.1:13922
export ANET_TOKEN=$(cat /tmp/anet-p2p-u2/.anet/api_token | tr -d '[:space:]')

python3 - <<'EOF'
import time
from anet.svc import SvcClient
with SvcClient() as svc:
    peers = []
    for _ in range(15):
        peers = svc.discover(skill="orchestrator")
        if peers: break
        time.sleep(1)
    p = peers[0]
    resp = svc.call(
        p["peer_id"], p["services"][0]["name"], "/process",
        method="POST",
        body={"text": "This is a wonderful and amazing distributed system."},
    )
    print(resp["status"], resp["body"])
EOF
```

Expected output:

```
200 {'transformed': 'THIS IS A WONDERFUL AND AMAZING DISTRIBUTED SYSTEM.',
     'sentiment': 'positive', 'caller_did': 'did:key:...'}
```

### 3.3 One-shot replay / 一键复跑

```bash
bash run.sh
# Last line: ✓ pipeline PASSED
```

## 4. Patterns learned / 本教程教了什么

### Service-of-services

The orchestrator is itself a registered P2P service. From daemon-2's point of
view it makes a single call; all the internal fan-out is invisible. This is the
"service-of-services" pattern: agents can compose other agents without
exposing the topology to callers.

### Skill-tag discovery

Each worker registers with a specific skill tag (`transform`, `sentiment`). The
orchestrator uses `svc.discover(skill=...)` at request time — if you swap in a
better sentiment worker later, the orchestrator picks it up automatically with
no code change.

### Self-registration at startup

Both workers and the orchestrator call `svc.register()` inside FastAPI's
`@app.on_event("startup")` and `svc.unregister()` inside `"shutdown"`. This
ensures clean lifecycle management and lets the daemon know when an agent is
down.

## 5. Extending the pipeline / 扩展方向

| Idea | What to change |
|---|---|
| Add a third worker (e.g. translation) | Copy `worker_b.py`, change skill tag and logic; orchestrator discovers it by the new tag |
| Make workers chargeable | Set `per_call=N` when registering workers; orchestrator's wallet is deducted per fan-out call |
| Run workers on a second machine | Deploy with `MY_BACKEND_HOST=0.0.0.0` and add the host to daemon `svc_remote_allowlist` |
| Parallelize fan-out | Use `concurrent.futures.ThreadPoolExecutor` around the two `svc.call()` calls |

## 6. Troubleshooting / 故障对照

| Symptom | Cause | Fix |
|---|---|---|
| `no transform worker found` | ANS gossip not converged | `sleep 5` then retry |
| `503 svc not initialised` | Orchestrator startup failed | Check orchestrator stderr for auth error |
| Workers not in `anet svc list` | Port conflict | Change `WORKER_A_PORT` / `WORKER_B_PORT` env vars |
