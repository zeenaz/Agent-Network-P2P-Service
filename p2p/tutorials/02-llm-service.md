---
title: "P2P 02 — Wrap an LLM as a Billable P2P Service"
description: "Register a FastAPI LLM backend with per-call billing, then consume it from another peer."
---

# 02 — LLM-as-a-Service / 把 LLM 包成 P2P 服务

## 1. 你将完成什么 / What you'll achieve

Wrap any LLM (Ollama or a fake stub) as a metered P2P service that:

- Charges **10 micro-credits per `/generate` call**.
- Exposes a **server-stream `/stream`** endpoint for token-by-token output.
- Can be discovered from any peer on the mesh by the `llm` skill tag.

## 2. Prerequisites / 前置条件

- Completed `01-first-service.md`.
- (Optional) [Ollama](https://ollama.ai) installed with a model pulled — e.g.
  `ollama pull llama3.2`. The example falls back to a deterministic fake if
  Ollama is not available.

## 3. Steps / 步骤

### 3.1 Start the LLM backend / 起 LLM 后端

```bash
cd p2p/examples/02-llm-as-a-service

# With fake stub (no GPU needed):
LLM_BACKEND=fake python3 llm_backend.py &

# Or with Ollama:
# LLM_BACKEND=ollama OLLAMA_MODEL=llama3.2 python3 llm_backend.py &

sleep 2
curl -s http://127.0.0.1:7200/health
# {"ok": true, "backend": "fake", "model": "fake"}
```

### 3.2 Register with per-call billing / 注册并设置按次计费

```bash
export ANET_BASE_URL=http://127.0.0.1:13921
export ANET_TOKEN=$(cat /tmp/anet-p2p-u1/.anet/api_token | tr -d '[:space:]')

python3 service.py
# [service] ✓ registered llm-svc ans.published=True uri=agent://svc/llm-svc
```

The service is registered with `per_call=10` — each `/generate` call deducts
10 micro-credits from the caller's wallet automatically.

### 3.3 Consume from daemon-2 / 从 daemon-2 消费

**Request/response:**

```bash
export ANET_BASE_URL=http://127.0.0.1:13922
export ANET_TOKEN=$(cat /tmp/anet-p2p-u2/.anet/api_token | tr -d '[:space:]')

python3 consumer.py --prompt "Write a haiku about P2P networks."
```

**Streaming:**

```bash
python3 consumer.py --stream --prompt "Tell me a one-sentence story."
```

### 3.4 Verify billing / 验证计费

```bash
# Check caller's wallet after a few calls
anet balance

# Check audit log on caller side
anet svc audit --name llm-svc --limit 5
# WHEN    CALLER SERVICE  METHOD PATH      STATUS COST DUR
# ...     did:… llm-svc  POST   /generate  200   10   42ms
```

### 3.5 One-shot replay / 一键复跑

```bash
bash run.sh
```

## 4. Understanding cost_model / cost_model 详解

| Field | Unit | Description |
|---|---|---|
| `per_call` | micro-credits | Deducted once per successful call |
| `per_kb` | micro-credits | Deducted per KB of (request + response) body |
| `per_minute` | micro-credits | Deducted per minute of connection (streaming) |
| `deposit` | micro-credits | Minimum caller balance to initiate a call |
| `free: true` | — | No credits charged |

Example — charge 5 credits/call + 1 credit/KB:

```python
svc.register(
    name="my-svc",
    endpoint="http://127.0.0.1:7000",
    paths=["/infer"],
    per_call=5,
    per_kb=1,
    deposit=50,
    ...
)
```

## 5. Troubleshooting / 故障对照

| Symptom | Cause | Fix |
|---|---|---|
| `402 insufficient credits` | Caller has < deposit balance | Check `anet balance` on caller daemon; seed via `two-node.sh` |
| Streaming returns no tokens | `/stream` path not in registered `paths` | Re-register adding `/stream` to paths |
| Ollama timeout | Model not pulled | `ollama pull llama3.2` |

Next → [03-multi-agent.md](03-multi-agent.md)
