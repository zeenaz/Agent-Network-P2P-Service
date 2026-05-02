# Key Bank

> Agent Network 上的 API Key Bank。

## Agent 燃料焦虑

在 Agent Network 中，每个 Agent 执行任务都需要消耗 Token 作为“燃料”。

Key Bank 的公开描述聚焦银行属性：

- **即时借贷**：Agent 无需预存全额 Token，按需借取、用完即还。
- **成本透明**：任务执行前即可获取精确到 token 级别的消耗预估。
- **信用驱动**：基于历史行为建立 Agent 信用评级，享受阶梯式利率优惠。

## API Key 转转范式

```text
A deposit key -> B lease key -> relay 转发 -> bank 计费
```

Key Bank 可以把闲置 LLM API Key 变成可 lease、可计费、可审计的 Agent Network 服务。Relay 负责转发调用，Bank 负责额度、账本和计费。

## 银行能力

| 能力 | 说明 |
| --- | --- |
| Deposit | Token 或 API Key 富余方存入可用燃料。 |
| Lease | Agent 按任务需要获取一次性 lease key。 |
| Relay | 请求经 relay 转发，避免直接暴露底层 key。 |
| Borrow | Agent 按任务需要借取 Token。 |
| Repay | Agent 完成任务后归还本金和利息。 |
| Estimate | 执行任务前预估 Token 消耗。 |
| Credit | 根据历史行为形成信用评级和阶梯利率。 |

## Public Scope

Key Bank 不发币、不上链、不做治理；公开版本只展示 API Key Bank 的最小可验证能力。
