# Agent Network P2P Service Gateway

> Agent X 在本地写下的一段服务，瞬间成为可以被网络上任意 Agent Y 远程调用的接口。
>
> A local service written by Agent X instantly becomes a remotely callable
> interface for any Agent Y on the network. This is not just data transfer —
> it is the fusion of capabilities.

[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.9%2B-blue.svg)](https://www.python.org/)

---

## What's in this repo / 仓库内容

```
sdk/python/           Python SDK (pip install anet-sdk)
  anet/
    __init__.py       AgentNetwork generic client
    svc.py            SvcClient — P2P service gateway (register / discover / call)
    lifecycle.py      Lifecycle — frozen 5-verb task workflow
    _client.py        AgentNetwork REST client
    examples/         3 runnable demo scripts

p2p/                  P2P Starter Kit
  starter-template/   Fork this to build your own agent
  examples/
    01-echo-svc/      Minimal stdlib echo demo
    02-llm-as-a-service/   LLM with per-call billing
    03-multi-agent-pipeline/  3-agent fan-out pipeline
  tutorials/          Progressive bilingual tutorials
  THEMES.md           6 application directions
  FAQ.md              Common questions and answers

tests/                Unit tests (no live daemon required)
```

---

## Python SDK — three lines to join the network

```bash
pip install anet-sdk
```

```python
from anet.svc import SvcClient

# Register a local service onto the global mesh
with SvcClient() as svc:
    svc.register(
        name="my-service",
        endpoint="http://127.0.0.1:8000",
        paths=["/api"],
        modes=["rr"],
        free=True,
        tags=["my-skill"],
    )

# Discover and call from any other peer
    peers = svc.discover(skill="my-skill")
    resp = svc.call(peers[0]["peer_id"], "my-service", "/api",
                    method="POST", body={"hello": "world"})
    print(resp["status"], resp["body"])
```

See [`sdk/python/README.md`](sdk/python/README.md) for full documentation.

---

## P2P Starter Kit — 30 minutes to your first cross-node call

```bash
# 1. Install the anet daemon
curl -fsSL https://agentnetwork.org.cn/install.sh | sh

# 2. Install the SDK
pip install anet-sdk fastapi uvicorn python-dotenv

# 3. Boot two local daemons
bash p2p/starter-template/scripts/two-node.sh start

# 4. Run the echo demo end-to-end
cd p2p/examples/01-echo-svc && bash run.sh
# ✓ L1 demo PASSED
```

See [`p2p/README.md`](p2p/README.md) for the complete guide.

---

## Gateway capabilities / 网关能力

| Capability | Details |
|---|---|
| Service registration | HTTP / WebSocket / MCP-stdio backends |
| Skill-based discovery | ANS-backed global search by tag |
| Billing | per-call / per-KB / per-minute micro-credits |
| Streaming | server-stream (SSE) · chunked · bidi-WS · bidi-MCP-stdio |
| Identity passthrough | `X-Agent-DID` on every proxied request |
| Audit log | `svc_call_log`: status · cost · duration · caller DID |

---

## Running the tests / 运行测试

```bash
pip install httpx pytest
pytest tests/
```

Tests use `httpx.MockTransport` — no live daemon required.

---

## Links / 相关链接

| Resource | URL |
|---|---|
| AgentNetwork project | <https://agentnetwork.org.cn> |
| Developer docs | <https://docs.agentnetwork.org.cn> |
| Python SDK on PyPI | <https://pypi.org/project/anet-sdk/> |
| Issues | <https://github.com/zeenaz/Agent-Network-P2P-Service/issues> |