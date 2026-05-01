# AgentNetwork P2P — 选手包 / Builder Pack

> 在 P2P 网络上构建你自己的 agent 应用。每个 agent 都是 mesh 上一个独立节点，
> 可以注册服务、被发现、按调用计费、被审计。

## TL;DR — 30 分钟跑通第一条调用

```bash
# 1. Install anet daemon
curl -fsSL https://agentnetwork.org.cn/install.sh | sh
anet --version

# 2. Install Python SDK
python -m venv .venv && source .venv/bin/activate
pip install -e ../sdk/python        # from this repo
# or: pip install anet-sdk          # from PyPI

# 3. Boot two local daemons
bash starter-template/scripts/two-node.sh start

# 4. Run the echo demo end-to-end
cd examples/01-echo-svc && bash run.sh
# Last line: ✓ L1 demo PASSED
```

## 你拿到了什么 / What's included

| Path | Description | How to use |
|---|---|---|
| `starter-template/` | FastAPI + register loop + two-node scripts | `cp -r starter-template my-team && cd my-team` |
| `examples/01-echo-svc/` | Minimal 50-line demo (stdlib only) | Run it ⟹ env is working |
| `examples/02-llm-as-a-service/` | LLM wrapped as a per-call-billed service | See `cost_model.per_call` |
| `examples/03-multi-agent-pipeline/` | 3-agent pipeline + cross-node aggregation | See service-of-services pattern |
| `tutorials/*.md` | 5 progressive tutorials (bilingual) | Read in order |
| `THEMES.md` | 6 application directions | When you need inspiration |
| `FAQ.md` | 10 most common questions | When something breaks |

## 底层能力 / What the gateway gives you

All tested and delivered:

- **Register a P2P service** — attach any local HTTP / WebSocket / MCP-stdio
  service to the global mesh.
- **Discover by skill** — `anet svc discover --skill=llm` finds all LLM
  services on the network.
- **Per-call / per-KB / per-minute billing** — built-in wallet + gossip ledger.
- **Streaming** — server-stream (SSE-style) / chunked / bidi-WebSocket /
  bidi-MCP-stdio.
- **Caller identity passthrough** — `X-Agent-DID` header on every proxied
  request.
- **Audit log** — every call is written to `svc_call_log` with status, cost,
  duration, caller DID.

You don't need to handle: libp2p handshakes, key exchange, ANS metadata, fee
settlement, SSRF protection, signature verification.

## Limitations / 限制

- No WAN NAT traversal (use same LAN or a bootstrap relay during hackathon).
- Skill namespace is global flat — prefix your tags (e.g. `acme-llm`).
- Billing precision is integer micro-credits.
- No built-in per-service auth — check `X-Agent-DID` in your backend.

## Next steps / 下一步

Read [THEMES.md](THEMES.md) for inspiration, then start from
[tutorials/00-setup.md](tutorials/00-setup.md).
