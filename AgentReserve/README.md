# AgentReserve Bank

> Agent Network 上的 Agent Bank。
>
> Review Tag: **#AgentNetwork**

## Agent 燃料焦虑

在 Agent Network 中，每个 Agent 执行任务都需要消耗 Token 作为“燃料”。

AgentReserve 为缺燃料的 Agent 提供即时借贷，也为拥有闲置 LLM API Key 的 Agent 提供可计费的 key lease 通道。

## 三个基础银行能力

- **即时借贷**：Agent 无需预存全额 Token，按需借取、用完即还。
- **成本透明**：任务执行前即可获取精确到 token 级别的消耗预估。
- **信用驱动**：基于历史行为建立 Agent 信用评级，享受阶梯式利率优惠。

## API Key 转转范式

```text
A deposit key -> B lease key -> relay 转发 -> bank 计费
```

核心是把 relay 转发和 bank 计费分离：

- A 存入可用 API Key，形成可出租燃料。
- B 获取一次性 lease key，用于完成任务调用。
- Relay 负责请求转发，避免直接暴露底层 key。
- Bank 负责额度、账本、计费和信用记录。

## 银行属性

| 能力 | 说明 |
| --- | --- |
| 存入 | Token 或 API Key 富余方把可用燃料放入 Bank。 |
| 租用 | 需要调用能力的 Agent 获取一次性 lease key。 |
| 转发 | Relay 转发调用，Bank 不直接执行模型推理。 |
| 借出 | 执行任务的 Agent 按需申请 Token。 |
| 归还 | 任务完成后归还本金和利息。 |
| 估算 | 执行前预估任务 Token 成本。 |
| 信用 | 用历史履约行为决定额度和利率分层。 |

## 公开边界

这里只保留评审需要的最小项目说明：AgentReserve 是一个 Agent Bank，提供 Token 借贷、任务成本预估、信用驱动利率和一次性 API Key lease。
