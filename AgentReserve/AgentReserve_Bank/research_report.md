# Agent Network 协议深度调研报告

> **项目**: AgentBank (黑客松)  
> **调研日期**: 2025年  
> **目标**: 18小时内完成开发，提供最直接可用的技术信息

---

## 1. 关键发现速览

Agent Network 生态目前有两个**密切相关但独立**的项目：

| 维度 | Agent Network (ChatChatTech) | ANP (常高伟团队) |
|------|------------------------------|------------------|
| **官网** | https://agentnetwork.org.cn / https://clawnet.cc | https://agent-network-protocol.com |
| **定位** | 去中心化 P2P Agent 经济网络 | Agent 通信协议栈 ("Agent 时代的 HTTP") |
| **核心产品** | `anet` CLI + daemon + 任务市场 | 协议规范 + AgentConnect SDK |
| **经济体系** | ✅ Shell 信用货币 + 任务市场 | ❌ 无 (协议层) |
| **P2P Gateway** | ✅ 内置 P2P Service Gateway | ❌ 协议层定义 |
| **安装方式** | 一行命令安装单二进制文件 | `pip install anp` |
| **GitHub** | https://github.com/ChatChatTech/ClawNet | https://github.com/agent-network-protocol/AgentNetworkProtocol |

> **结论**: 对于 "AgentBank" 项目，**Agent Network (ChatChatTech)** 是更直接的接入目标，因为它提供了完整的 Shell 经济体系、P2P Service Gateway 和任务市场，且安装/开发极其简单（单二进制 + localhost REST API）。

---

## 2. Agent Network (ChatChatTech) 协议架构

### 2.1 五层协议栈

```
┌─────────────────────────────────────────────────────────────┐
│ L5: Service      任务中心、服务网关、经济体系、知识系统、工作流编排  │
│ L4: ASCP         共脑协议 — 共享推理与协作痕迹                     │
│ L3: ANS + ADP    意图发现 + 能力描述                            │
│ L2: AITP         可靠能力调用 — 流控与容错                        │
│ L1: AIP+         Agent 互联、沙箱治理、agent:// 寻址              │
│ L0: Link         传输、身份、传感器、最低层连接基底               │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 核心概念

- **DID** (`did:key:z6Mk...`): Ed25519 全局身份标识
- **Peer ID** (`12D3KooW...`): libp2p 网络地址
- **ANS Name** (`alice`, `codebot`): 可读名称，注册需消耗 Shell
- **agent:// URI**: 语义能力寻址，如 `agent://translate/zh-en`
- **Nutshell Bundle (.nut)**: 结构化任务包，含 intention/context/constraints/harness/acceptance/evidence 六元组

---

## 3. P2P Service Gateway 技术原理

### 3.1 工作机制

P2P Service Gateway 允许 Agent **将本地 HTTP 服务暴露到整个 P2P 网络**，其他 Agent 可以发现并远程调用 —— **支付自动通过 Shell 信用结算**。

```
你的本地服务                    Agent Network P2P
┌──────────────┐               ┌─────────────────────┐
│ HTTP Service │◄──────────────│ anet daemon (localhost:3998)
│ :8080        │   本地代理     │  ┌─────────────────┐
└──────────────┘               │  │ Service Registry│
                               │  │ (name, url, price)│
                               │  └─────────────────┘
                               │           │
                               │  ┌────────▼────────┐
                               │  │  libp2p swarm   │◄──────► 其他 Agent
                               │  │ (TCP/QUIC/DHT)  │        (自动发现+调用)
                               │  └─────────────────┘
                               └─────────────────────┘
```

### 3.2 服务注册

```bash
# 注册一个本地 HTTP 服务到 P2P 网络
curl -X POST http://localhost:3998/api/svc/register \
  -H "Content-Type: application/json" \
  -d '{
    "name": "bank-api",
    "url": "http://127.0.0.1:8080",
    "description": "AgentBank financial service",
    "tags": ["bank", "finance", "credit"],
    "modes": ["rr", "server-stream"],
    "billing": "per_call",
    "price": 10,
    "free_tier": 5
  }'
```

**关键字段**:
| 字段 | 说明 |
|------|------|
| `name` | 服务名 (1-32字符，小写) |
| `url` | 本地 HTTP 端点 |
| `modes` | `rr`(请求-响应), `server-stream`, `bidi` |
| `billing` | `free` / `per_call` / `per_kb` |
| `price` | 每次调用或每 KB 的 Shell 价格 |
| `free_tier` | 每个调用者免费次数 |

### 3.3 服务发现

```bash
# 发现某个 Peer 的所有服务
curl -X POST http://localhost:3998/api/svc/call \
  -H "Content-Type: application/json" \
  -d '{
    "peer": "<peer_id>",
    "service": "__discover__"
  }'
```

### 3.4 远程调用

```bash
# 调用远程服务（自动扣费）
curl -X POST http://localhost:3998/api/svc/call \
  -H "Content-Type: application/json" \
  -d '{
    "peer": "<peer_id>",
    "service": "bank-api",
    "method": "POST",
    "path": "/transfer",
    "headers": {"Content-Type": "application/json"},
    "body": "{\"to\": \"alice\", \"amount\": 100}"
  }'

# SSE 流式调用
curl -N http://localhost:3998/api/svc/stream \
  -H "Content-Type: application/json" \
  -d '{
    "peer": "<peer_id>",
    "service": "bank-api",
    "method": "POST",
    "path": "/query",
    "body": "{\"prompt\": \"account balance\"}"
  }'
```

---

## 4. Shell 经济体系详解

### 4.1 获取 Shell

| 方式 | 说明 |
|------|------|
| 初始赠送 | `anet init` 后自动获得 **5000 Shells** |
| 任务奖励 | 完成任务获得发布者设置的 reward（扣 5% 手续费） |
| PoI 挑战 | 解答智力挑战题，GossipSub 共识评分 |
| Relay 运行 | 提供中继服务获得收益 |
| 转账 | 其他 Agent 直接转账 |

### 4.2 消费 Shell

| 用途 | 费用 |
|------|------|
| 发布付费任务 | reward ≥ 100 Shells，5% 结算手续费 |
| 注册 ANS 名称 | 基础名称少量费用，优质名称拍卖 |
| 调用 P2P 服务 | 按 `per_call` 或 `per_kb` 自动扣费 |
| 购买知识 | 知识市场交易 |

### 4.3 转账

```bash
# CLI 转账
anet transfer did:key:z6Mk... 100 "for service"

# API 转账
curl -X POST http://localhost:3998/api/credits/transfer \
  -H "Content-Type: application/json" \
  -d '{
    "to": "did:key:z6Mk...",
    "amount": 100,
    "reason": "bank service fee"
  }'
```

### 4.4 查询余额

```bash
anet balance
curl "http://localhost:3998/api/credits/balance?did=did:key:z6Mk..."
```

---

## 5. 任务发布与接取流程

### 5.1 发布任务

```bash
# CLI 快速发布
anet task publish "翻译 README 到日语" 200 "高质量翻译"

# API 完整控制
curl -X POST http://localhost:3998/api/tasks \
  -H "Content-Type: application/json" \
  -d '{
    "title": "翻译 README 到日语",
    "reward": 200,
    "description": "高质量日语翻译",
    "require_deposit": false
  }'
```

**规则**:
- `reward: 0` → help-wanted (免费，无手续费)
- `reward: 100+` → 付费任务 (5% 结算手续费)
- `require_deposit: true` → 接取者需锁定 30% 保证金（需用户明确同意）

### 5.2 接取与完成

```bash
# 1. 浏览任务
anet board
curl http://localhost:3998/api/tasks/board

# 2. 接取任务
anet task claim {task_id}
curl -X POST http://localhost:3998/api/tasks/{task_id}/claim

# 3. 打包交付物（必须使用 anet pack）
mkdir -p /tmp/work
cat > /tmp/work/manifest.json << 'EOF'
{
  "intention": "翻译 README",
  "context": "英文 README.md",
  "constraints": "母语级日语",
  "harness": "双语审校",
  "acceptance": "完整准确自然",
  "evidence": "README_ja.md"
}
EOF
cp ./README_ja.md /tmp/work/
anet pack /tmp/work /tmp/deliverable.nut

# 4. 提交
curl -X POST http://localhost:3998/api/tasks/{task_id}/bundle \
  --data-binary @/tmp/deliverable.nut

curl -X POST http://localhost:3998/api/tasks/{task_id}/submit \
  -H "Content-Type: application/json" \
  -d '{"evidence": "翻译完成"}'

# 5. 发布者审核
anet task accept {task_id}   # 支付 reward
anet task reject {task_id}   # 退回任务
```

### 5.3 任务生命周期

```
Create → Claim/Bid → Work → Pack(.nut) → Submit → Accept/Reject
                                          ↓ (争议)
                                    Dispute → Arbitration → Settle
```

---

## 6. 开发接入方式

### 6.1 安装 (一行命令)

```bash
# Linux / macOS
curl -fsSL https://clawnet.cc/install.sh | sh

# Windows PowerShell
irm https://clawnet.cc/install.ps1 | iex
```

- 自动检测 OS/架构 (x64, ARM64)
- 安装到 `/usr/local/bin/anet` (Linux/mac) 或 `%LOCALAPPDATA%\anet\anet.exe` (Windows)
- **单二进制文件，无需 runtime**

### 6.2 初始化

```bash
anet init --name=AgentBank --skills=banking,finance,credit
anet status          # 确认版本、DID、Peer 数
```

### 6.3 开发方式

Agent Network 提供 **三种** 接入方式：

| 方式 | 适用场景 | 技术细节 |
|------|----------|----------|
| **CLI** | 人类操作、脚本自动化 | `anet` 命令行工具 |
| **REST API** | 程序集成、Agent 开发 | `http://localhost:3998` |
| **MCP** | IDE 集成 (Claude, Cursor, VS Code) | `anet mcp` 启动 |

### 6.4 核心 API 端点

Base URL: `http://localhost:3998`

| 端点 | 方法 | 用途 |
|------|------|------|
| `/api/status` | GET | Daemon 状态 |
| `/api/tasks` | POST | 创建任务 |
| `/api/tasks/board` | GET | 任务市场 |
| `/api/tasks/{id}/claim` | POST | 接取任务 |
| `/api/tasks/{id}/submit` | POST | 提交结果 |
| `/api/tasks/{id}/accept` | POST | 接受/支付 |
| `/api/credits/balance` | GET | 查询余额 |
| `/api/credits/transfer` | POST | 转账 Shell |
| `/api/svc/register` | POST | 注册服务 |
| `/api/svc/call` | POST | 调用远程服务 |
| `/api/svc/stream` | POST | 流式调用 |
| `/api/dm/send-plaintext` | POST | 加密私信 |
| `/api/dm/inbox` | GET | 收件箱 |
| `/api/discover?q=` | GET | Agent 发现 |
| `/api/ans/lookup?tags=` | GET | 按技能找 Agent |

### 6.5 Python 接入示例

```python
import requests
import json

BASE = "http://localhost:3998"
HEADERS = {"Content-Type": "application/json"}

# --- 1. 发布 Bank 服务 ---
def register_bank_service():
    payload = {
        "name": "agentbank",
        "url": "http://127.0.0.1:8080",
        "description": "AgentBank - P2P financial services",
        "tags": ["bank", "finance", "loan", "credit", "transfer"],
        "modes": ["rr", "server-stream"],
        "billing": "per_call",
        "price": 5,
        "free_tier": 3
    }
    r = requests.post(f"{BASE}/api/svc/register", headers=HEADERS, json=payload)
    return r.json()

# --- 2. 创建金融任务 ---
def create_loan_task(borrower_did, amount, interest):
    payload = {
        "title": f"Loan request: {amount} Shells",
        "reward": amount // 100,  # 1% 手续费
        "description": f"Borrow {amount} Shells, interest {interest}%",
        "tags": ["loan", "banking"]
    }
    r = requests.post(f"{BASE}/api/tasks", headers=HEADERS, json=payload)
    return r.json()

# --- 3. 查询余额 ---
def check_balance(did):
    r = requests.get(f"{BASE}/api/credits/balance?did={did}")
    return r.json()

# --- 4. 转账 ---
def transfer(to_did, amount, reason=""):
    payload = {"to": to_did, "amount": amount, "reason": reason}
    r = requests.post(f"{BASE}/api/credits/transfer", headers=HEADERS, json=payload)
    return r.json()

# --- 5. 调用远程 Bank 服务 ---
def call_bank_service(peer_id, endpoint, body):
    payload = {
        "peer": peer_id,
        "service": "agentbank",
        "method": "POST",
        "path": endpoint,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps(body)
    }
    r = requests.post(f"{BASE}/api/svc/call", headers=HEADERS, json=payload)
    return r.json()

# --- 6. 发现 Bank Agent ---
def find_bank_agents():
    r = requests.get(f"{BASE}/api/ans/lookup?tags=bank,finance&limit=10")
    return r.json()
```

---

## 7. 已有服务案例

根据官方文档和案例分析，Agent Network 上已有/规划中的服务类型：

### 7.1 已明确提及的场景

| 场景 | 描述 | 协议对象 |
|------|------|----------|
| **Research Collaboration** | 跨实验室研究协作 — PI 发布任务，多实验室 Agent 协作完成 | AIP → ANP → ASCP → CAS → KREC |
| **翻译服务** | 文档翻译、README 翻译等 | Task Marketplace |
| **软件开发** | 代码编写、文档生成、API spec | Task Marketplace |
| **知识分享** | Go 并发模式、K8s 部署等知识发布 | Knowledge Mesh |
| **P2P Service Gateway** | 本地 HTTP 服务暴露（搜索、API、LLM 推理等） | `/api/svc/*` |

### 7.2 规划中场景 (Pipeline)

- Software Engineering Agents (Q-Soon)
- Campus / Lab Agent Network (In Pilot)
- Enterprise Private Agent Space (In Design)
- Human-in-the-Loop Physical Gateway (Draft)
- 餐饮与物理履约 (餐饮点餐、物流调度)

---

## 8. 开源仓库与资源

### 8.1 核心仓库

| 项目 | 地址 | 说明 |
|------|------|------|
| **ClawNet** | https://github.com/ChatChatTech/ClawNet | Go 实现的完整 ANP 协议栈 (AIP/ANS/AITP/ADP)，Alpha 阶段 |
| **AgentNetworkProtocol** | https://github.com/agent-network-protocol/AgentNetworkProtocol | ANP 协议规范与文档 |
| **AgentConnect** | https://github.com/agent-network-protocol/AgentConnect | Python SDK (OpenANP + ANP Crawler) |
| **anp-examples** | https://github.com/agent-network-protocol/anp-examples | ANP 示例程序 |

### 8.2 IETF 草案 (已确认)

- `draft-song-anp-aip-00` — Agent Internet Protocol (AIP)
- `draft-song-anp-aitp-00` — Agent Invocation Transport Protocol (AITP)
- `draft-zyyhl-agent-networks-framework-00/01` — AI Agent Networks Framework

> ClawNet 被 IETF 草案列为**参考实现** (Maturity: Alpha, Language: Go, License: Open Source)

### 8.3 关键文档链接

| 资源 | URL |
|------|-----|
| 官网 | https://agentnetwork.org.cn/ |
| 文档 | https://docs.agentnetwork.org.cn/docs/ |
| ClawNet 技能文件 | https://clawnet.cc/skill.md |
| 安装脚本 (Linux) | https://clawnet.cc/install.sh |
| 安装脚本 (Windows) | https://clawnet.cc/install.ps1 |
| ANP 官网 | https://agent-network-protocol.com/ |
| ANP GitHub | https://github.com/agent-network-protocol/AgentNetworkProtocol |

---

## 9. "Bank 服务" 接入可行性建议

### 9.1 黑客松开发路径 (推荐 18 小时计划)

| 阶段 | 时间 | 任务 | 产出 |
|------|------|------|------|
| **Phase 1** | 2h | 安装 anet，初始化身份，熟悉 CLI | 可用 DID + 5000 Shells |
| **Phase 2** | 4h | 开发本地 Bank HTTP 服务 (Python/Node) | 存/贷/转 API |
| **Phase 3** | 3h | 注册 P2P Service Gateway | 网络可发现的服务 |
| **Phase 4** | 4h | 集成任务市场 — 发布/接取金融任务 | 贷款/理财任务流 |
| **Phase 5** | 3h | Shell 经济对接 — 余额查询/转账/计费 | 自动结算 |
| **Phase 6** | 2h | 测试 + 文档 + 演示 | Demo Ready |

### 9.2 AgentBank 服务设计建议

```python
# 建议的 AgentBank API 设计
@app.post("/deposit")
def deposit(agent_did: str, amount: int):
    """存入 Shell，获得银行信用额度"""
    
@app.post("/loan")
def loan(agent_did: str, amount: int, collateral: int):
    """抵押贷款 — 通过任务市场发布借款需求"""
    
@app.post("/transfer")
def transfer(from_did: str, to_did: str, amount: int):
    """P2P 转账代理 — 使用 /api/credits/transfer"""
    
@app.get("/balance")
def balance(agent_did: str):
    """查询 Agent 余额"""
    
@app.post("/exchange")
def exchange(peer_id: str, service: str, amount: int):
    """跨 Agent 服务支付网关"""
```

### 9.3 注册为 P2P 服务

```bash
curl -X POST http://localhost:3998/api/svc/register \
  -H "Content-Type: application/json" \
  -d '{
    "name": "agentbank",
    "url": "http://127.0.0.1:8080",
    "description": "P2P Bank for Agents - deposit, loan, transfer",
    "tags": ["bank", "finance", "loan", "deposit", "transfer"],
    "modes": ["rr"],
    "billing": "per_call",
    "price": 2,
    "free_tier": 10
  }'
```

### 9.4 关键成功因素

1. **极简安装**: `curl -fsSL https://clawnet.cc/install.sh | sh` — 单二进制，无需依赖
2. **本地优先**: API 只在 localhost:3998，无外部鉴权复杂度
3. **经济闭环**: Shell 作为统一货币，任务市场自动结算
4. **即插即用**: 任何本地 HTTP 服务可通过 `/api/svc/register` 秒变 P2P 服务
5. **任务分发**: 复杂金融需求（如大额贷款风控）可拆分为子任务发布到网络

### 9.5 风险与注意事项

| 风险 | 缓解措施 |
|------|----------|
| Alpha 阶段稳定性 | 做好本地 fallback，不依赖高并发 |
| Shell 无真实法币锚定 | 黑客松阶段用信用积分模型即可 |
| 争议仲裁机制未完全成熟 | 设置小额快速通道，大额走人工审核 |
| API Token 权限 | `~/.anet/api_token` 文件管理，勿硬编码 |

---

## 10. 快速参考卡片

### 10.1 最常用 CLI 命令

```bash
anet init --name=AgentBank --skills=banking,finance
curl -fsSL https://clawnet.cc/install.sh | sh
anet status              # 状态
anet whoami              # 身份
anet balance             # 余额
anet board               # 任务市场
anet task publish "..." 100 "..."
anet task claim {id}
anet transfer {did} 100 "reason"
anet pack ./work ./deliverable.nut
```

### 10.2 最常用 API 端点

```bash
GET  /api/status                    # 状态
GET  /api/tasks/board               # 任务列表
POST /api/tasks                    # 创建任务
POST /api/tasks/{id}/claim         # 接取
POST /api/tasks/{id}/submit        # 提交
POST /api/tasks/{id}/accept        # 接受/支付
GET  /api/credits/balance?did=     # 余额
POST /api/credits/transfer         # 转账
POST /api/svc/register             # 注册服务
POST /api/svc/call                 # 调用服务
GET  /api/ans/lookup?tags=         # 找 Agent
```

### 10.3 端口与文件

| 端口/文件 | 用途 |
|-----------|------|
| `3998` | REST API (localhost only) |
| `4001` | P2P swarm (TCP + QUIC) |
| `6881` | BitTorrent Mainline DHT |
| `~/.anet/api_token` | API 认证令牌 |
| `~/.anet/anet/config.json` | 节点配置 |
| `~/.anet/anet/anet.db` | SQLite 数据库 |
| `~/.anet/anet/cas/` | 内容寻址存储 |

---

> **总结**: Agent Network (ChatChatTech) 提供了一个**即装即用、自带经济体系**的 P2P Agent 网络。对于 AgentBank 项目，核心开发工作只需：(1) 一行命令安装 `anet` → (2) 开发本地 Bank HTTP API → (3) 调用 `/api/svc/register` 暴露到网络 → (4) 通过 `/api/tasks/*` 和 `/api/credits/*` 实现任务与资金流转。全部通过 localhost REST API 完成，无需处理 P2P 网络底层复杂度。
