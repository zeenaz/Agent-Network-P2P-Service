# Key Bank

> Agent Network 上的 P2P inference-capacity bank：资源方托管 provider capacity，调用方租用短期调用权，Bank 通过 relay 执行请求、计量消耗、完成结算和信用记录。

**Hackathon Tag:** `#flux-nankesong-s2`
**Track:** Agent Network
**Repo:** <https://github.com/zeenaz/Agent-Network-P2P-Service>
**Agent Network service:** `shawn-keybank` / `api-key-bank`
**Public demo URL:** 待部署实例填写；当前可通过 Agent Network P2P Service Gateway 发现与调用。

---

## Problem

在 Agent Network 中，每个 Agent 执行任务都需要消耗 Token 或 LLM API 调用能力作为“燃料”。

问题很直接：Agent 不一定缺能力，但经常缺临时燃料。一个 Agent 可能已经接到任务，却没有足够 Token 或可用 provider capacity 完成调用；另一个 Agent 可能有闲置 LLM API key 或额度，却没有简单方式把它变成可计费、可审计、可租用的网络资源。

Key Bank 的目标不是做一个普通“存 key 工具”，而是做 Agent Network 上的 **P2P capacity market**：让闲置推理容量可以被托管、租用、计量和信用定价。

---

## Core Insight

差异化不在“存 key”，而在 **P2P capacity market**。

存 key 和 proxy 只是基础设施，真正的新意是：

- **Agent DID**：用 Agent Network 身份区分资源方、调用方和履约记录。
- **P2P 服务发现**：通过 Agent Network Service Gateway 发现可用 Bank 服务。
- **临时燃料租用**：调用方获取短期 `lease_token` 或 virtual access，而不是长期持有真实 key。
- **信用定价**：根据成功还款、超额、超时、失败调用、争议率形成信用记录。
- **按请求结算**：settlement 基于 request log，不基于 lease 发放本身。

因此 Key Bank 不应被理解为“API key 二级市场”。更准确的表述是：

```text
Resource owner deposits provider capacity
Borrower leases short-lived virtual access
Relay executes upstream request
Bank meters usage and settles value
```

真实 provider API key 不应离开 Bank。borrower 只拿短期授权，不接触底层 key。

---

## Architecture

```text
Agent Network P2P
      |
      | discover / call by service name
      v
Key Bank Service
      |
      | deposit / lease / proxy / audit
      v
Bank Core
      |-- key custody
      |-- lease token
      |-- request log
      |-- spend log
      |-- credit record
      v
Provider Relay
      |
      | upstream LLM API call
      v
OpenAI-compatible / Kimi / MiniMax / GLM / other providers
```

目标调用路径：

1. **Deposit**：资源方存入 provider capacity，Bank 记录 `key_id`、provider、model、脱敏指纹和可用额度。
2. **Lease**：调用方按 provider/model 获取短期 `lease_token`。
3. **Proxy**：调用方带 `lease_token` 调 `/proxy`，Bank 内部解密真实 key 并代发上游请求。
4. **Audit**：Bank 记录 request log、usage、latency、status、borrower DID、provider DID。
5. **Settle**：基于 request log 拆分 borrower 消耗、deposit 方收益和 Bank 手续费。

---

## Hackathon Scope

本次黑客松目标是验证 Key Bank 的最小可行叙事与技术路径。

当前可验证能力：

- Agent Network P2P Service Gateway 注册与发现。
- `deposit -> lease -> audit -> deposits` 的最小 Key Bank 流程。
- DID 会员规则：先 deposit，才能 lease。
- 防自借规则：borrower 不能 lease 自己 deposit 的 key。
- 可审计记录：lease 记录 provider DID、borrower DID、deposit id、时间和快照。

后续路线会把当前“一次性 key 保管箱”升级为 relay-only 的 Key Bank。黑客松版本强调概念验证，生产级版本必须确保真实 key 不离开 Bank。

---

## Roadmap

### MVP v1: Key Relay

把当前“一次性 key 保管箱”升级成 Key Relay。

目标：

- 实现 `lease_token`。
- 支持 TTL、`max_uses`、provider/model 过滤。
- 实现 `/proxy`，所有上游请求由 Bank relay。
- 建立 per-call audit。
- 真实 key 不返回给 borrower。

核心接口：

```text
POST /deposit
POST /lease
POST /proxy
GET  /audit
GET  /deposits
```

### MVP v2: Virtual Fuel Account

给每个 borrower 发虚拟额度，采用成熟 AI Gateway 语义。

参考 LiteLLM / Portkey / agentgateway 的接口设计：

```json
{
  "lease_token": "lease_xxx",
  "borrower_did": "did:key:...",
  "expires_at": "...",
  "provider_allowlist": ["openai", "kimi", "glm"],
  "model_allowlist": ["gpt-5", "kimi-k2", "glm-4"],
  "max_tokens": 100000,
  "max_cost": 10.0,
  "rate_limit": {
    "rpm": 60,
    "tpm": 30000
  }
}
```

关键设计：

- `virtual_key`
- `budget`
- `rate_limit`
- `model_allowlist`
- `spend_log`

这些概念已经被 AI Gateway 市场验证，Key Bank 不需要重新发明。

### MVP v3: Agent Credit Settlement

接入 Agent Network Shell 或外部 payment rail，把 deposit 方收益、borrower 消耗、Bank 手续费拆账。

原则：

- lease 只是授权，不是最终计费点。
- settlement 基于 `/proxy` request log。
- 信用体系从简单规则开始。

初版信用规则：

- 成功还款：提升信用。
- 超额使用：降低信用或提高风险溢价。
- 超时未结算：降低信用。
- 失败调用率高：降低信用。
- 争议率高：降低信用。

---

## Technical Stack

| Layer | Choice | Why |
| --- | --- | --- |
| Language | Python 3 | 快速开发，适合黑客松验证 |
| Web framework | FastAPI | 自动生成 OpenAPI / Swagger UI，适合服务型 demo |
| Data model | Pydantic | 请求参数校验清晰 |
| Service runtime | Uvicorn | FastAPI 标准运行时 |
| P2P integration | Agent Network `anet` + `anet-sdk` | 服务注册、发现、P2P 调用、DID 注入 |
| Persistence | JSON file store | 黑客松阶段简单可审计；生产版本应迁移 SQLite/Postgres |
| Gateway pattern | AI Gateway / Virtual Key / Spend Log | 借鉴 LiteLLM、Portkey、agentgateway 成熟语义 |
| Deployment target | Render / Railway / self-hosted | 提供公开 URL 或可安装运行方式 |

---

## How To Use

### Discover Key Bank

```bash
anet svc discover --skill api-key-bank --json
anet svc discover --skill shawn --json
anet svc discover --skill api-zhuanzhuan --json
```

从输出里取：

- `peer_id`
- service name: `shawn-keybank`

### Deposit Provider Capacity

```bash
anet svc call <peer_id> shawn-keybank /deposit --method POST \
  --header "Content-Type=application/json" \
  --body '{"provider":"glm","model":"glm-4","label":"my-glm","api_key":"<YOUR_KEY>"}' \
  --json
```

目标返回：

- `key_id`
- `key_fp`

### Lease Short-lived Access

```bash
anet svc call <peer_id> shawn-keybank /lease --method POST \
  --header "Content-Type=application/json" \
  --body '{"provider":"kimi","model":"kimi-k2","ttl_sec":3600,"max_uses":200}' \
  --json
```

目标返回：

- `lease_token`
- `expires_at`
- `max_uses`

### Proxy Call

```bash
anet svc call <peer_id> shawn-keybank /proxy --method POST \
  --header "Content-Type=application/json" \
  --body '{
    "lease_token":"lease_xxx",
    "path":"/v1/responses",
    "method":"POST",
    "payload":{
      "model":"gpt-5",
      "input":"1+1=?"
    }
  }' \
  --json
```

MVP v1 之后，borrower 只通过 `/proxy` 使用租来的 capacity，不直接接触真实 provider API key。

---

## Local Development

```bash
cd AgentReserve
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python3 llm_backend.py
```

Health check:

```bash
curl http://127.0.0.1:7200/health
```

Register to local Agent Network daemon:

```bash
ANET_BASE_URL=http://127.0.0.1:3998 \
ANET_TOKEN=$(cat ~/.anet/api_token) \
BANK_PORT=7200 \
python3 register_llm.py
```

---

## Submission Checklist

- [ ] GitHub repository is public.
- [ ] Repository tag/topic includes `#flux-nankesong-s2` or `flux-nankesong-s2`.
- [ ] README lists technical stack and framework choices.
- [ ] README includes deployment URL or installation/run instructions.
- [ ] Public deployed instance is available, or Agent Network service discovery instructions are verified.
- [ ] Demo shows the path from deposit to lease to audit.
- [ ] Roadmap clearly separates hackathon validation from future production work.

---

## Research

竞品与相关技术调研报告已归档到非公开 BP 文档仓库。本公开仓库仅保留可开源的实现、README、使用说明和 demo 材料。

---

## Public Scope

Key Bank 公开版本展示最小可验证银行能力：provider capacity deposit、short-lived lease、Agent DID membership、audit trail，以及向 Key Relay / Virtual Fuel Account / Agent Credit Settlement 演进的路线。

不发币，不上链，不做治理。真实 provider key 在生产设计中不应离开 Bank。
