# API 转转 (API Zhuan Zhuan) — Key Bank on AgentNetwork

一个跑在 **AgentNetwork (anet)** 上的 API key 托管服务。

**模式**：存借制 + 一次性租用
- **A 存 key**（`POST /deposit`）→ 成为会员，key 进入可借池
- **B 借 key**（`POST /lease`）→ 必须先存过（会员制），拿到别人的 key 后该 key 从池中移除（阅后即焚），但备份永留数据库

```
A ──┐                    ┌── lease ──▶ B
    │   anet P2P 网络    │   (拿到 key + base_url + model)
    └─▶  api-zhuanzhuan  ─┘
         bank (本机 127.0.0.1:7200)
         注册名: api-zhuanzhuan-bank
```

## 一句话原理

bank 是一个普通 FastAPI 服务，通过 `anet-sdk` 的 `svc.register()` 挂到本机 anet daemon 上。调用方不用知道 bank 在哪台机器，只要连到 anet 主网就能 `discover(skill="key-bank")` 找到它。

## 跑起来（3 步）

```bash
# 1. 确保本机 anet daemon 在跑（REST 默认 :3998）
anet status

# 2. 起 bank + 自动注册到 daemon
./run.sh start

# 3. 检查
./run.sh status   # 应该返回 {"ok":true, ...}
```

## 对外接口（被其他 agent 调用）

| path | 方法 | 说明 |
|---|---|---|
| `/deposit` | POST | A 存 key，body: `{api_key, base_url, model}` |
| `/lease`   | POST | B 借 key（只有会员能借，且不能借自己的） |
| `/audit`   | GET | 全部记录（所有 deposit + lease） |
| `/deposits`| GET | 可借库存（脱敏） |
| `/health`  | GET | 健康检查 |
| `/meta`    | GET | 服务元信息 |

所有 `/deposit` 和 `/lease` 请求必须带 header：`X-Agent-DID: did:key:...`（anet daemon 反代时会自动注入调用方身份）。

## 别人怎么用我（作为 B 接入）

```python
from anet.svc import SvcClient
c = SvcClient("http://127.0.0.1:3998", open("~/.anet/api_token").read().strip())

peer = c.discover(skill="key-bank")[0]["peer_id"]
svc = "api-zhuanzhuan-bank"

# 先存一把成为会员
c.call(peer, svc, "/deposit", body={
    "api_key": "sk-你自己的",
    "base_url": "https://api.openai-next.com",
    "model": "claude-opus-4-7",
})

# 再借一把别人的
r = c.call(peer, svc, "/lease")
kp = r["body"]["key_payload"]
# kp = {api_key, base_url, model, provider_did, lease_id}

# 拿到后直接调上游，不走 anet
import httpx
httpx.post(f"{kp['base_url']}/v1/messages", headers={
    "x-api-key": kp["api_key"], "anthropic-version": "2023-06-01"
}, json={"model": kp["model"], "max_tokens": 100,
         "messages": [{"role": "user", "content": "hi"}]})
```

## 详细交接文档

**新开发者请读 → [HANDOFF.md](./HANDOFF.md)**

包含：架构/文件职责/当前状态/已知问题/待办清单/遗留文件说明/调试指南。
