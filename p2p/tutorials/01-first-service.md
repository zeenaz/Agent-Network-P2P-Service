---
title: "P2P 01 — Your First P2P Service in 30 Minutes"
description: "From a 30-line stdlib HTTP server to a service another peer can discover and call across the libp2p mesh."
---

# 01 — Your First P2P Service / 第一个 P2P 服务

## 1. 你将完成什么 / What you'll achieve

Put a 30-line Python HTTP server onto the P2P network as an `echo` service, let
a **second daemon** discover it by skill tag and make a call.

After this tutorial you can explain:

- What a `ServiceEntry` looks like (`name / endpoint / paths / modes / cost_model / tags`).
- How `anet svc discover --skill=…` uses ANS to find the other side.
- Why the call appears in `anet svc audit` with a real `status` (200).

## 2. Prerequisites / 前置条件

- Completed `00-setup.md` — two daemons alive, SDK installed.
- `examples/01-echo-svc/` accessible.

## 3. Steps / 步骤

### 3.1 Start the minimal echo backend / 起最小 echo 后端

```bash
cd p2p/examples/01-echo-svc
python3 echo_backend.py &      # listens on 127.0.0.1:7100
sleep 1
curl -s -X POST :7100/echo -d '{"hi":1}'
# {"echo": {"hi": 1}, "caller_did": "<missing>"}
```

`<missing>` appears because we're calling directly without the daemon injecting
`X-Agent-DID`. The daemon takes over next.

### 3.2 Register (CLI) / 注册（CLI 一行）

```bash
export ANET_BASE_URL=http://127.0.0.1:13921
export ANET_TOKEN=$(cat /tmp/anet-p2p-u1/.anet/api_token | tr -d '[:space:]')

anet svc register \
  --name echo-l1 \
  --endpoint http://127.0.0.1:7100 \
  --paths /echo,/health,/meta \
  --modes rr \
  --free \
  --tags echo,demo \
  --description "L1 p2p echo" \
  --health-check /health
```

Expected last line:

```
✓ service "echo-l1" registered
  ans:  published=true  uri=agent://svc/echo-l1-…
```

### 3.2' Register (Python) / 等价 Python 写法

```python
from anet.svc import SvcClient

with SvcClient(base_url="http://127.0.0.1:13921") as svc:
    svc.register(
        name="echo-l1",
        endpoint="http://127.0.0.1:7100",
        paths=["/echo", "/health", "/meta"],
        modes=["rr"],
        free=True,
        tags=["echo", "demo"],
        description="L1 p2p echo",
        health_check="/health",
        meta_path="/meta",
    )
```

### 3.3 Discover + call from daemon-2 / 从第二个 daemon 发现 + 调用

```bash
export ANET_BASE_URL=http://127.0.0.1:13922
export ANET_TOKEN=$(cat /tmp/anet-p2p-u2/.anet/api_token | tr -d '[:space:]')

sleep 3   # wait for ANS gossip to converge
anet svc discover --skill echo
```

Expected:

```
✓ skill="echo" found 1 peer(s)

  peer:  12D3KooW…
  owner: did:key:z6Mk…
  ans:   agent://svc/echo-l1-…
    - echo-l1  [http/rr]  L1 p2p echo
```

Call it:

```bash
PEER=$(anet svc discover --skill echo --json \
       | python3 -c "import sys,json;print(json.load(sys.stdin)['results'][0]['peer_id'])")
anet svc call "$PEER" echo-l1 /echo --method POST --body '{"msg":"hi"}'
# HTTP 200
#   echo: {"msg":"hi"}
#   caller_did: did:key:...
```

### 3.4 One-shot replay / 一键复跑

```bash
cd p2p/examples/01-echo-svc
bash run.sh
# Last line: ✓ L1 demo PASSED
```

## 4. Sanity checklist / 自检命令

```bash
# A. echo-l1 is in the local registry
anet svc list

# B. health-check reports healthy
anet svc health

# C. Real status written to audit log
anet svc audit --name echo-l1 --limit 1

# D. Backend log shows X-Agent-DID (look at echo_backend.py stderr)
```

## 5. Troubleshooting / 故障对照

| Symptom | Cause | Fix |
|---|---|---|
| `register failed: name is required` | Missing required fields | Add missing fields per the `errors` list |
| `endpoint host must be localhost` | Non-localhost endpoint without allowlist | Use `127.0.0.1` or configure `svc_remote_allowlist` |
| `discover --skill echo` returns 0 | ANS gossip not converged | `sleep 5` then retry; check daemon-1 log for `[ans] published` |
| `peer not found in routing table` | Wrong peer_id source | Re-read peer_id from the same `discover` output |
| `audit status` is always 0 | Old daemon version | Upgrade to `anet v1.1.10+` |

Next → [02-llm-service.md](02-llm-service.md)
