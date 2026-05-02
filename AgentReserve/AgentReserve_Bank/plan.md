# Flux 南客松 S2 · Key Bank 项目执行计划

## 项目定位

基于 Agent Network P2P Service Gateway 构建 **Key Bank**：Agent Network 上的 P2P inference-capacity bank。

Key Bank 的差异化不在“存 key”，而在 **P2P capacity market**：

- 有闲置 provider capacity 的 Agent 可以 deposit。
- 缺临时燃料的 Agent 可以 lease 短期调用权。
- Bank 通过 relay 代发请求，真实 key 不离开 Bank。
- Settlement 基于 request log，而不是基于 lease 发放。
- 信用体系从简单规则开始，记录成功还款、超额、超时、失败调用和争议率。

一句话：

> Resource owners escrow provider capacity; borrowers lease short-lived virtual access; the Bank relays requests, meters usage, settles value, and records credit.

---

## 黑客松约束

- **当前时间**：2026-05-03
- **赛道**：Agent Network
- **仓库标签**：`#flux-nankesong-s2`
- **提交要求**：
  - GitHub 项目公开。
  - README 清楚撰写项目技术栈、技术选型和框架。
  - 软件应用提供可直接访问 URL 或安装包/运行链接。
  - 商业项目可开源核心验证代码，并附带已部署实例。

黑客松版本重点验证概念和最短链路，不追求一次性完成完整金融系统。未来关键能力必须留在 roadmap 中讲清楚。

---

## 当前可验证范围

当前服务已经能验证最小 Key Bank 雏形：


| 能力                  | 状态  | 说明                                 |
| ------------------- | --- | ---------------------------------- |
| Agent Network 服务注册  | 已具备 | 通过 `anet svc discover` 发现服务        |
| Deposit             | 已具备 | 资源方提交 provider key/capacity        |
| Lease               | 已具备 | DID 会员可 lease 其他成员 deposit         |
| Membership          | 已具备 | 先 deposit 才能 lease                 |
| 防自借                 | 已具备 | borrower 不会 lease 自己 deposit 的 key |
| Audit               | 已具备 | 记录 members、deposits、leases         |
| Relay-only proxy    | 待实现 | MVP v1 核心                          |
| Virtual fuel budget | 待实现 | MVP v2 核心                          |
| Credit settlement   | 待实现 | MVP v3 核心                          |


重要边界：

- 当前实现更像“一次性 key 保管箱”。
- 下一步必须升级成 relay-only：borrower 不应接触真实 key。
- 裸 key lease 会削弱安全叙事，也难以与主流厂商 API key policy 对齐。

---

## MVP v1: Key Relay

目标：把当前“一次性 key 保管箱”升级成 **Key Relay**。

### 要实现的能力

1. `lease_token`
  - `/lease` 返回短期 token，而不是真实 `api_key`。
  - token 绑定 borrower DID、provider、model、deposit id。
2. TTL
  - 每个 lease 有 `expires_at`。
  - 过期后 `/proxy` 拒绝调用。
3. `max_uses`
  - 每个 lease 有最大调用次数。
  - 每次 `/proxy` 成功或尝试调用都写入 usage 计数。
4. `/proxy`
  - borrower 提交 `lease_token + path + method + payload`。
  - Bank 内部取出真实 provider key。
  - Relay 代发上游请求。
  - 真实 key 不返回给 borrower。
5. Provider/model 过滤
  - `/lease` 支持按 provider/model 选择 capacity。
  - `/proxy` 校验 payload model 是否符合 lease 约束。
6. Per-call audit
  - 记录 request id、borrower DID、provider DID、lease token hash、model、status、latency、estimated tokens、error。

### MVP v1 接口草案

```text
POST /deposit
POST /lease
POST /proxy
GET  /audit
GET  /deposits
GET  /health
```

### 验收标准

- borrower 通过 `/lease` 拿不到真实 key。
- 使用 `lease_token` 可以完成一次 `/proxy` 调用。
- TTL 过期后调用失败。
- 超过 `max_uses` 后调用失败。
- audit 能看到每次 proxy request。

---

## MVP v2: Virtual Fuel Account

目标：从一次 lease 升级为面向 borrower 的虚拟燃料账户。

Key Bank 直接采用 AI Gateway 成熟接口语义：

- `virtual_key`
- `budget`
- `rate_limit`
- `model_allowlist`
- `spend_log`

这些概念已经被 LiteLLM、Portkey、agentgateway 等产品验证。

### 账户模型草案

```json
{
  "lease_token": "lease_xxx",
  "borrower_did": "did:key:...",
  "expires_at": "2026-05-03T12:00:00Z",
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

### 要实现的能力

- 每个 borrower 有可查询的 fuel account。
- `/proxy` 写入 spend log。
- 超过 `max_tokens`、`max_cost`、RPM、TPM 后拒绝调用。
- 账户可以按 provider/model 精确限制。
- 支持将多个 deposit capacity 聚合成一个 borrower 可用额度。

### 验收标准

- 同一个 borrower 可持有一个或多个 virtual fuel account。
- spend log 能按 borrower DID 聚合。
- budget 和 rate limit 能被强制执行。
- model allowlist 能阻止越权模型调用。

---

## MVP v3: Agent Credit Settlement

目标：接入 Agent Network Shell 或外部 payment rail，把调用消耗转换成可结算的经济记录。

### 核心原则

- Lease 只是授权，不是最终计费点。
- Settlement 基于 `/proxy` request log。
- Request log 是计量、争议处理、信用评分的共同事实来源。

### 结算模型

每次 proxy request 产生一条 spend record：

```json
{
  "request_id": "req_xxx",
  "borrower_did": "did:key:borrower",
  "provider_did": "did:key:provider",
  "lease_id": "lease_xxx",
  "model": "gpt-5",
  "estimated_tokens": 1200,
  "actual_tokens": 1188,
  "provider_cost": 0.02,
  "bank_fee": 0.003,
  "total_charge": 0.023,
  "status": "settled"
}
```

拆账：

- borrower 消耗：`total_charge`
- deposit 方收益：`provider_cost`
- Bank 手续费：`bank_fee`

### 信用规则 v0

初版不做复杂风控模型，只做可解释规则：


| 事件     | 信用影响 |
| ------ | ---- |
| 成功结算   | 小幅提升 |
| 按时还款   | 提升   |
| 超额使用   | 降低   |
| 超时未结算  | 降低   |
| 失败调用率高 | 降低   |
| 争议率高   | 降低   |


### 验收标准

- settlement 能从 request log 生成，而不是从 lease 生成。
- 每个 DID 能查询 credit summary。
- 同样任务下，低风险 borrower 获得更低 risk premium。
- credit score 变化可解释。

---

## 技术选型


| 模块     | 技术                                | 理由                                      |
| ------ | --------------------------------- | --------------------------------------- |
| 后端     | Python FastAPI                    | 开发快，自带 OpenAPI / Swagger UI             |
| 类型校验   | Pydantic                          | 请求/响应 schema 清晰                         |
| 服务运行   | Uvicorn                           | FastAPI 标准运行时                           |
| P2P 网络 | Agent Network `anet` / `anet-sdk` | 服务发现、P2P 调用、DID 注入                      |
| 存储     | JSON file store                   | 黑客松阶段最小可验证；后续迁移 SQLite/Postgres         |
| Relay  | HTTPX / provider adapters         | MVP v1 用于上游转发                           |
| 部署     | Render / Railway / self-hosted    | 满足公开 URL 要求                             |
| 设计参考   | LiteLLM / Portkey / agentgateway  | virtual key、budget、rate limit、spend log |


---

## 黑客松提交计划

### 1. GitHub 与 README

- 仓库公开。
- 设置 `flux-nankesong-s2` topic/tag。
- README 写清楚项目定位、技术栈、运行方式。
- README 明确当前验证范围与后续 roadmap。
- README 提供部署 URL 或本地/Agent Network 调用方式。

### 2. Demo

- 演示 `anet svc discover --skill api-key-bank --json`。
- 演示 `/deposit`。
- 演示 `/lease`。
- 演示 `/audit` 或 `/deposits`。
- 如 MVP v1 完成，演示 `/proxy` 中 borrower 不接触真实 key。

### 3. 部署

- 准备 Render/Railway 部署配置。
- 提供公开 URL。
- 健康检查 `/health` 返回 200。
- Swagger UI 可访问。

### 4. 材料

- 竞品调研报告：`key-bank-competitor-research.md`。
- Demo case 文档。
- PPT / 路演故事线。
- 最终提交信息：GitHub 链接、部署 URL、项目简介、标签。

---

## 风险与边界


| 风险                | 影响  | 处理                                    |
| ----------------- | --- | ------------------------------------- |
| 裸 key lease 安全叙事弱 | 高   | MVP v1 优先实现 relay-only                |
| 厂商不鼓励 key 共享      | 高   | 对外讲 provider capacity lease，不讲 key 转租 |
| JSON 存储不可扩展       | 中   | 黑客松可接受；后续迁移 SQLite/Postgres           |
| token 计量不准        | 中   | 初版先估算，后续接 provider usage 字段           |
| 结算系统过重            | 中   | v3 再接 Shell/payment rail，黑客松只展示设计     |


---

## 最终叙事

> Agent Network 已经让 Agent 可以互相发现和调用服务，但还缺少一层“临时燃料市场”。Key Bank 让拥有闲置 provider capacity 的 Agent 可以 deposit，让缺燃料的 Agent 可以 lease 短期 virtual access。Bank 不把真实 key 交出去，而是通过 relay 代发请求、记录 request log、按实际调用结算，并把履约结果写入 Agent 信用记录。

黑客松版本验证最小链路；后续版本沿 Key Relay、Virtual Fuel Account、Agent Credit Settlement 三阶段演进。