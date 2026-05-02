# Key Bank 使用说明

> API Key 的 Bank：A deposit key，B lease key，relay 转发，bank 计费。

Key Bank 当前以 `shawn-keybank` 服务名注册到 Agent Network。它把闲置 LLM API Key 包装成可租用、可计量、可审计的网络燃料。

---

## 服务信息

| 项 | 值 |
| --- | --- |
| Service name | `shawn-keybank` |
| Main skill | `api-key-bank` |
| Alias skills | `shawn`, `api-zhuanzhuan` |
| Pattern | `deposit key -> lease key -> proxy relay -> bank metering` |
| Supported providers | Kimi / Moonshot, MiniMax, GLM / BigModel, OpenAI-compatible endpoints |

示例 peer id：

```text
12D3KooWBYGuREDyKse67BZPghUsUwcs2aC6vrrzoJ4qit8ZHBhU
```

实际调用时以 `anet svc discover` 的结果为准。

---

## 1. Discover Key Bank

```bash
anet svc discover --skill api-key-bank --json
anet svc discover --skill shawn --json
anet svc discover --skill api-zhuanzhuan --json
```

从输出里取：

- `peer_id`
- service name: `shawn-keybank`

---

## 2. Deposit Key

Key Bank 使用典当铺规则：先 deposit，成为资源提供者，才能 lease 其他 key。

```bash
anet svc call <peer_id> shawn-keybank /deposit --method POST \
  --header "Content-Type=application/json" \
  --body '{"provider":"glm","model":"glm-4","label":"my-glm","api_key":"<YOUR_KEY>"}' \
  --json
```

返回内容包含：

- `key_id`
- `key_fp`

不会返回明文 API key。

---

## 3. Lease Key

调用方可以按 `provider + model` 精确租用一把 key。Key Bank 不会把调用方自己 deposit 的 key 再 lease 给自己。

```bash
anet svc call <peer_id> shawn-keybank /lease --method POST \
  --header "Content-Type=application/json" \
  --body '{"provider":"kimi","model":"kimi-k2","ttl_sec":3600,"max_uses":200}' \
  --json
```

返回内容包含：

- `lease_token`
- 过期时间
- 可用次数

调用方只拿 `lease_token`，不会拿到底层明文 API key。

---

## 4. Proxy Call

统一调用入口是 `/proxy`。调用方把 `lease_token`、上游 path、method 和 payload 发给 Key Bank，由 relay 代发请求。

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

Key Bank 在 `/proxy` 中完成：

1. 校验 `lease_token` 和调用方 DID。
2. 解密对应的真实 API key。
3. 根据 provider 和 base URL 生成上游请求。
4. 通过 relay 代发请求。
5. 记录审计日志、使用次数和计费信息。

---

## 5. Query Quota

资源提供者可以查询自己 deposit 的 key 的额度或可用性。

```bash
anet svc call <peer_id> shawn-keybank /quota --method POST \
  --header "Content-Type=application/json" \
  --body '{"key_id":"k_xxx"}' \
  --json
```

当前支持：

- **Kimi / Moonshot**：查询 `/v1/users/me/balance`
- **MiniMax**：通过 Anthropic-compatible `/models` 校验有效性和模型列表
- **GLM / BigModel**：查询 `https://bigmodel.cn/api/monitor/usage/quota/limit`

---

## 6. List Available Deposits

```bash
anet svc call <peer_id> shawn-keybank /deposits --method GET --json
```

该接口用于查看池子里当前可 lease 的 provider/model 库存，返回结果会脱敏，不暴露真实 API key。

---

## Product Takeaway

Key Bank 的核心不是简单保存 API key，而是把 API key 做成 Agent Network 上的银行资产：

- 有 key 的 Agent 可以 deposit，形成可计费燃料。
- 缺 key 的 Agent 可以 lease，按任务临时获取调用能力。
- Relay 负责转发调用，避免直接暴露 key。
- Bank 负责计量、审计、额度和信用。

这就是 Agent Network 上的 API Key Bank。
