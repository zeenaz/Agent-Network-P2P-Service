# HANDOFF — API 转转 交接文档

> **交接对象**：下一位接手的开发者
> **最后更新**：2026-05-02
> **当前状态**：已上线 anet 主网，功能可用

---

## 1. 这个项目是干嘛的

一句话：**key 托管所**，在 AgentNetwork 上跑一个 FastAPI 服务，帮 agent 之间互相"存/借" API key。

### 业务规则（要熟记）

| 规则 | 说明 |
|---|---|
| **先存才能借** | DID 必须至少 deposit 过一次，才能调 `/lease`。非会员调 `/lease` → 403 |
| **一次性** | 每把 key 被 `/lease` 命中一次后 status 从 `available` 变 `leased`，从可借池消失 |
| **备份永留** | 被借走的 key 不会删除，`bank.json > leases` 里永久保留 snapshot 和调用链 |
| **不能自借** | 如果借用者是 key 的 provider，本笔 deposit 跳过（避免自己借自己） |
| **~~上游验证~~** | **已关**（见 §5）。deposit 不再调上游握手，任意 key 秒过 |

### 不是什么（避免误解）

- ❌ 不是 LLM 代理（不转发请求到上游）
- ❌ 不是账本（没有余额、没有计费、没有 credit）
- ❌ 不是网关（不解包、不改包、不鉴权上游）
- ✅ 就是个**带会员制的 key 保管箱**

---

## 2. 架构 & 文件职责

```
┌────────────────────────────────────────────────────────────┐
│  anet daemon (Go, 独立进程)                                  │
│   - REST   :3998    ← 本地业务进程用这个                        │
│   - libp2p :4001    ← peer 间 P2P                          │
│   - 作用：注册发现 / P2P 路由 / 身份注入                          │
└────────────┬───────────────────────────────────────────────┘
             │  反代（把 P2P 入站请求映射到本地 HTTP endpoint）
             ▼
┌────────────────────────────────────────────────────────────┐
│  bank (FastAPI, 本项目)                                      │
│   - :7200                                                    │
│   - llm_backend.py  ← 路由层（HTTP handlers）                  │
│   - bank.py         ← 业务层（deposit/lease/audit）            │
│   - data/bank.json  ← 持久化（JSON，atomic write）             │
└────────────────────────────────────────────────────────────┘
```

### 文件清单（新架构 — 实际在用）

| 文件 | 职责 | 关键代码 |
|---|---|---|
| `bank.py` | 业务核心 | `Bank.deposit()`, `Bank.lease()`, `Bank.audit()`, `Bank.list_deposits_safe()` |
| `llm_backend.py` | FastAPI 路由 | 只做参数校验 + 转发到 `Bank` 方法 |
| `register_llm.py` | 注册脚本 | 启动时调 `SvcClient.register()` 把 bank 挂到 daemon |
| `run.sh` | 生命周期 | `./run.sh {start\|stop\|status\|logs}` |
| `requirements.txt` | 依赖 | fastapi / uvicorn / pydantic / anet-sdk |
| `.env.example` | 环境变量模板 | 实际 `.env` 不入库 |
| `data/bank.json` | 数据库 | **不入库**（含明文 key） |

### 文件清单（遗留 — 旧架构残留，没人 import）

> 这些是上一版 "relay agent / 账本" 架构的文件，**新 bank 完全不用**。
> 交接保留是为了历史参考。可以安全删除，但先问清楚 owner。

| 文件 | 旧用途 |
|---|---|
| `main.py` | 老 FastAPI 入口（relay agent） |
| `router.py` | 老 `SvcClient` 封装 |
| `registrar.py` | 老注册逻辑 |
| `config.py` | 老环境变量加载 |
| `ledger.py` | 老账本（credit 计费） |
| `key_pool.py` | 老 key 池 |
| `Dockerfile` | 给老 main.py 用的 |
| `docker-compose.yml` | 同上 |
| `data/ledger.json` | 老账本数据（不入库） |
| `data/key_pool.json` | 老 key 池数据（不入库） |

---

## 3. 数据模型

`data/bank.json` 结构：

```json
{
  "deposits": {
    "dep_3c1ca33a12ce": {
      "deposit_id": "dep_3c1ca33a12ce",
      "provider_did": "did:key:z6Mk...",
      "api_key":      "sk-...",
      "base_url":     "https://api.openai-next.com",
      "model":        "claude-opus-4-7",
      "status":       "available" | "leased",
      "deposited_at": 1777694299.08
    }
  },
  "leases": [
    {
      "lease_id":     "lease_84eda8c31a6e",
      "deposit_id":   "dep_3c1ca33a12ce",
      "borrower_did": "did:key:z6Mk...",
      "provider_did": "did:key:z6Mk...",
      "leased_at":    1777695477.31,
      "snapshot":     { "api_key": "sk-...", "base_url": "...", "model": "..." }
    }
  ],
  "members": {
    "did:key:z6Mk...": { "first_deposit_at": 1777694299.08, "total_deposits": 3 }
  }
}
```

并发：`bank.py` 里用 `threading.Lock()` 保护 `_data`，写盘用 `tmp + replace` 原子操作。**单进程**，扩容到多进程要换存储（SQLite / Postgres）。

---

## 4. 部署与运维

### 当前部署位置

- **机器**：`edy` 的 Mac (Apple Silicon, Darwin 24.6.0)
- **bank 进程**：监听 `127.0.0.1:7200`，pid 在 `/tmp/api-zhuanzhuan-bank.pid`
- **bank 日志**：`/tmp/api-zhuanzhuan-bank.log`
- **数据文件**：`/Users/edy/Desktop/API转转/data/bank.json` ⚠️ **路径硬编码**（见 §6 坑位）
- **anet daemon**：系统主 daemon（pid 40665），REST `:3998`，libp2p `:4001`
- **daemon 身份**：
  - DID: `did:key:z6MkjQFXgSHprJXYwdHWBZjNVQe73fsEQpzhLy9cJDDXuU7T`
  - peer_id: `12D3KooWEmMeqKd6hfJaF1xE8bWsR7AwiRe22dppcYbhqvQQtC41`
- **ANS**: `agent://svc/api-zhuanzhuan-bank-6c7c3d36`

### 启停

```bash
./run.sh start    # 起 bank + 注册到 daemon
./run.sh stop     # kill 进程（不 unregister — 见 §6）
./run.sh status   # 看 pid + health
./run.sh logs     # tail -f 日志
```

### 重新注册到主 daemon（换机器或改了 description 后）

```bash
ANET_BASE_URL=http://127.0.0.1:3998 \
ANET_TOKEN=$(cat ~/.anet/api_token) \
BANK_PORT=7200 \
python3 register_llm.py
```

### 常用 curl

```bash
# 健康
curl http://127.0.0.1:7200/health

# 存
curl -X POST http://127.0.0.1:7200/deposit \
  -H "Content-Type: application/json" \
  -H "X-Agent-DID: did:key:tester" \
  -d '{"api_key":"sk-xxx","base_url":"https://api.openai-next.com","model":"claude-opus-4-7"}'

# 借
curl -X POST http://127.0.0.1:7200/lease \
  -H "X-Agent-DID: did:key:tester"

# 审计
curl http://127.0.0.1:7200/audit
```

---

## 5. 功能变更记录

| 日期 | 变更 | 原因 |
|---|---|---|
| 初版 | deposit 前调上游 `/v1/messages` 握手验证 | 想过滤无效 key |
| 2026-05-02 | **关闭上游验证** | 部分合法 key 因网络超时被误拒（"握手失败"），业务方决定"信任提交方" |

**代码上的痕迹**：`bank.py` 里 `httpx` import 已删，`verify_key()` 方法已删。如果以后要恢复验证，参考 git log。

---

## 6. 已知坑 / TODO（按优先级）

### 🔴 P0 — 必须修

1. **api_key 明文存盘**
   `data/bank.json` 里所有 `api_key` 是明文，`leases[].snapshot.api_key` 也是一份。磁盘/备份/日志任何一处漏掉就全裸奔。
   **建议**：用 `keyring` / `age` / 对称加密，至少别明文。

2. **`.env` 真 token 泄露风险**
   `.env` 里曾经有 `AGENT_NET_TOKEN=40426cfb...`（本机 daemon 真 token）。已 `.gitignore`，但本地副本还在。换人接手时要 rotate 一次。

3. **bank.py 路径硬编码**
   `BANK_PATH = /Users/edy/Desktop/API转转/data/bank.json`（bank.py:19），换机器直接挂。
   **建议**：改成 `Path(__file__).parent / "data/bank.json"` 或读 env。

### 🟡 P1 — 尽快修

4. **停止时不 unregister**
   `./run.sh stop` 只 kill bank 进程，不通知 daemon 摘掉注册。daemon 会显示服务"unhealthy"直到超时。
   **建议**：在 `llm_backend.py` 加 `@app.on_event("shutdown")` 或 signal handler，调 `svc.unregister()`。

5. **DID 身份不校验**
   bank 信任 header `X-Agent-DID`。走 anet daemon 反代时 daemon 会注入真实调用方 DID，没问题；但**如果有人直接打 7200 端口**（bind 是 `127.0.0.1`，要 SSH/其它本地进程），随便填 DID 就能当会员。
   **建议**：校验请求来源（只接受 daemon 反代的 UA/signature），或 daemon 签身份 JWT。

6. **重复注册**
   历史上在 u1/u2/u3 测试 daemon 上也注册过，`discover(skill="key-bank")` 会返回重复的 ans。
   **建议**：写个清理脚本 unregister 掉孤岛注册。

### 🟢 P2 — 可以不急

7. **单进程 + JSON 存储**
   不能水平扩容。并发量上来要换 SQLite / Postgres。

8. **没有限流**
   理论上一个会员能 `/lease` 到把池抽干。
   **建议**：每 DID 每天借 N 把、冷却时间等。

9. **verify_key 已删，要恢复怎么办**
   上游对不同家（Anthropic / OpenAI / Gemini）格式不一样，旧版固定用 Anthropic `/v1/messages` 格式恰好被 `openai-next.com` 这个中转站兼容了。要恢复验证得写 adapter。

---

## 7. anet 集成要点

### SDK 关键方法（`anet.svc.SvcClient`）

```python
# 初始化（不传 token 会从 ~/.anet/api_token 读）
c = SvcClient("http://127.0.0.1:3998", token)

# 注册（启动时）
c.register(name="api-zhuanzhuan-bank", endpoint="http://127.0.0.1:7200",
           paths=["/deposit", "/lease", "/audit", "/deposits", "/health", "/meta"],
           modes=["rr"], free=True,
           tags=["key-bank", "api-zhuanzhuan", "deposit-lease"],
           description="...", health_check="/health", meta_path="/meta")

# 发现
peers = c.discover(skill="key-bank")  # 返回 [{peer_id, owner_did, ans_name, services:[...]}]

# 调用（从 B 的角度）
r = c.call(peer_id, "api-zhuanzhuan-bank", "/deposit",
           body={"api_key":"...", ...})
# r = {"status":200, "headers":{...}, "body":{...}}

# 关服
c.unregister("api-zhuanzhuan-bank")
```

### 关键行为（踩坑经验）

- **`SvcClient.call(headers=...)`** 传的 headers **不会透传给上游** HTTP endpoint。daemon 只帮你注入 `X-Agent-DID`，其他 header（如自定义 Authorization）到不了 bank。**业务参数用 body 传，不要用 header。**
- **`dial to self attempted`**：同一个 daemon 上的 agent 想 call 它自己注册的服务，libp2p 会拒。只能跨 daemon 测。
- **P2P 发现依赖 bootstrap**：`config.json` 里 `bootstrap_peers: []` 是孤岛模式。系统主 daemon（`~/.anet/`）接了公共 bootstrap，自带 DHT；测试用的 `/tmp/anet-p2p-u1/` daemon 是孤岛，**只能同机 u1/u2/u3 互通**。

---

## 8. 怎么验证当前部署是活的

```bash
# 1. 主 daemon 里能看到 bank
python3 <<'EOF'
from anet.svc import SvcClient
t = open("/Users/edy/.anet/api_token").read().strip()
c = SvcClient("http://127.0.0.1:3998", t)
for s in c.list():
    print(s["name"], "→", s["endpoint"])
EOF

# 2. 全网 discover 能找到
python3 -c "
from anet.svc import SvcClient
t = open('/Users/edy/.anet/api_token').read().strip()
c = SvcClient('http://127.0.0.1:3998', t)
for p in c.discover(skill='key-bank'):
    print(p['ans_name'])
"

# 3. bank 直接 health
curl http://127.0.0.1:7200/health
```

预期输出都有 `api-zhuanzhuan-bank` 相关条目。

---

## 9. 联系/提问

- anet SDK 问题：看 `sdk/` 目录或 https://github.com/zeenaz/Agent-Network-P2P-Service
- anet daemon 问题：`anet help` / `anet status`
- 业务规则问题：看本文 §1 / bank.py 顶部 docstring

**交接 checklist**（下一位接手时过一遍）：

- [ ] 本文读完
- [ ] `./run.sh start` 能起来
- [ ] 能访问 `http://127.0.0.1:7200/health` 返回 `{"ok":true, ...}`
- [ ] `anet status` 有本机主 daemon 在跑
- [ ] `discover(skill="key-bank")` 能看到 `-6c7c3d36` 或新生成的 ans
- [ ] 跑一遍 `deposit → lease` 流程验证功能
- [ ] 理解 §6 P0 三个坑
