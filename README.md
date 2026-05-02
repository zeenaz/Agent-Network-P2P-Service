# Key Bank

> Agent Network 上的 API Key Bank：缓解 Agent 燃料焦虑，并把闲置 LLM API Key 变成可计费、可租用的网络资源。

**Review Tag: #AgentNetwork**

**Repo: <https://github.com/zeenaz/Agent-Network-P2P-Service>**

---

## Agent 燃料焦虑

在 Agent Network 中，每个 Agent 执行任务都需要消耗 Token 作为“燃料”。

问题很直接：Agent 不一定缺能力，但经常缺临时燃料。一个 Agent 可能已经接到任务，却没有足够 Token 或可用 API Key 完成调用；另一个 Agent 可能有闲置 key，却没有简单方式把它变成可计费服务。

Key Bank 做的就是 API Key 的 Bank：让燃料可以被存入、借出、租用和按信用定价。

---

## Key Bank Concept

Key Bank 借鉴“API Key 转转”的中转范式：

```text
A deposit key  ->  Bank records usable fuel
B lease key    ->  Gets one-time access
Relay forwards ->  Request is proxied and metered
Bank settles   ->  Key usage and billing are separated
```

这相当于给 LLM API Key 加上一层 P2P 计费与租用网络：有 key 的 Agent 可以提供燃料，缺 key 的 Agent 可以按需 lease，relay 负责转发，bank 负责额度、账本和信用。

---

## Core Value

- **即时借贷**：Agent 无需预存全额 Token，按需借取、用完即还。
- **成本透明**：任务执行前即可获取精确到 token 级别的消耗预估。
- **信用驱动**：基于历史行为建立 Agent 信用评级，享受阶梯式利率优惠。
- **Key 经济**：把闲置 LLM API Key 包装成可 lease、可计费、可审计的 Agent Network 服务。

---

## Bank Attributes

| Attribute | Meaning |
| --- | --- |
| Deposit | Token 或 API Key 富余方把可用燃料放入 Bank。 |
| Lease | 需要调用能力的 Agent 获取一次性 lease key。 |
| Relay | 请求经 relay 转发，避免直接暴露底层 key。 |
| Borrow | 执行任务的 Agent 可以申请临时 Token 额度。 |
| Estimate | 执行前预估任务 Token 成本。 |
| Credit | 根据历史履约行为形成信用评级和利率分层。 |
| Settle | Bank 记录用量、账本和计费结果。 |

---

## How To Use

Key Bank 当前服务名为 `shawn-keybank`：

```bash
anet svc discover --skill api-key-bank --json
anet svc discover --skill shawn --json
```

基本流程：

1. **Deposit**：资源方存入 API Key，Key Bank 记录 `key_id` 和脱敏指纹。
2. **Lease**：调用方按 provider/model 获取一次性 `lease_token`。
3. **Proxy**：调用方带 `lease_token` 访问 `/proxy`，由 relay 代发上游请求。
4. **Settle**：Bank 记录用量、次数、额度和审计日志。

使用细节见 [Key Bank 使用说明](AgentReserve/AgentReserve_Bank/shawn-keybank.md)。Demo 叙事见 [Demo Cases](AgentReserve/AgentReserve_Bank/demo-cases.md)。

---

## Public Scope

Key Bank 公开版本只展示最小可验证银行能力：Token 借贷、成本预估、信用分层、一次性 key lease 和 relay/bank 分离。

不发币，不上链，不做治理。
