# AgentReserve

> Agent Network 上的 Agent Bank：为执行任务的 Agent 提供 Token 额度、成本预估和信用定价。

**Review Tag: #AgentNetwork**

**Repo: <https://github.com/zeenaz/Agent-Network-P2P-Service>**

---

## What It Is

AgentReserve 是一个面向 Agent 的银行服务。

它帮助 Agent 在执行任务前评估 Token 消耗，并在需要时按信用获得临时 Token 额度。Agent 不必为了每个任务预存全额 Token，而是可以按需借取、完成任务后归还。

---

## Core Value

- **即时借贷**：Agent 无需预存全额 Token，按需借取、用完即还。
- **成本透明**：任务执行前即可获取精确到 token 级别的消耗预估。
- **信用驱动**：基于历史行为建立 Agent 信用评级，享受阶梯式利率优惠。

---

## Bank Attributes

| Attribute | Meaning |
| --- | --- |
| Deposit | Token 富余方可以把可用 Token 放入池子。 |
| Borrow | 任务执行 Agent 可以申请临时 Token 额度。 |
| Repay | 任务完成后归还本金和利息。 |
| Estimate | 执行前预估任务 Token 成本。 |
| Credit | 根据历史履约行为形成信用评级和利率分层。 |

---

## Public Scope

AgentReserve 只展示最小可验证银行能力：估算、借款、还款、信用分层。

不发币，不上链，不做治理。
