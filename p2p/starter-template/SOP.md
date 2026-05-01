# P2P 跨境贸易协作平台 — 标准操作流程 (SOP)

---

## 1. 系统概述

三个独立机构通过 P2P 网络协作，各自持有不同数据，数据不出本方网络：

| 机构 | Agent 名称 | Skill | 持有数据 |
|------|-----------|-------|---------|
| 深圳工厂 | `supplier-shenzhen` | `product_info` | 产品规格、价格、HS编码 |
| 欧盟合规部 | `compliance-eu` | `compliance_check` | 欧盟法规数据库 (RoHS/REACH/CBAM/PFAS…) |
| 国际货代 | `logistics-shipper` | `shipping_quote` | 中国→欧洲运价数据库 |

调用链路：`Client → 深圳工厂 → 欧盟合规 → 国际货代`

---

## 2. 环境准备

### 2.1 硬件要求
- macOS 或 Linux (Windows 需 WSL2)
- Python ≥ 3.9

### 2.2 安装 anet CLI

```bash
curl -fsSL https://agentnetwork.org.cn/install.sh | sh
anet --version
# 应输出: 1.1.11 或更高
```

### 2.3 安装 Python 依赖

```bash
cd my-team-name
python -m venv .venv
source .venv/bin/activate
pip install anet fastapi uvicorn httpx python-dotenv
```

---

## 3. 启动系统

### 3.1 一键启动（推荐）

```bash
cd my-team-name
bash one-click.sh
```

启动后自动打开：
- 仪表盘 `http://127.0.0.1:7500/`
- 交互演示 `http://127.0.0.1:7500/demo`

### 3.2 手动分步启动

**Step 1 — 启动两个本地 daemon：**

```bash
# daemon-1 (API: 13921, P2P: 14021)
HOME=/tmp/anet-p2p-u1 anet daemon --api-listen :13921 --p2p-port 14021 --home /tmp/anet-p2p-u1 &

# daemon-2 (API: 13922, P2P: 14022)
HOME=/tmp/anet-p2p-u2 anet daemon --api-listen :13922 --p2p-port 14022 --home /tmp/anet-p2p-u2 &

sleep 3  # 等待 daemon 就绪

# 互转 seed 确保跨节点调用
DID1=$(ANET_TOKEN=$(cat /tmp/anet-p2p-u1/.anet/api_token) anet status | grep "did:" | head -1 | awk '{print $2}')
DID2=$(ANET_TOKEN=$(cat /tmp/anet-p2p-u2/.anet/api_token) anet status | grep "did:" | head -1 | awk '{print $2}')
TOKEN1=$(cat /tmp/anet-p2p-u1/.anet/api_token)
TOKEN2=$(cat /tmp/anet-p2p-u2/.anet/api_token)
curl -s -X POST http://127.0.0.1:13921/api/credits/transfer \
  -H "Authorization: Bearer $TOKEN1" -H "Content-Type: application/json" \
  -d "{\"from\":\"$DID1\",\"to\":\"$DID2\",\"amount\":1000,\"reason\":\"seed\"}"
curl -s -X POST http://127.0.0.1:13922/api/credits/transfer \
  -H "Authorization: Bearer $TOKEN2" -H "Content-Type: application/json" \
  -d "{\"from\":\"$DID2\",\"to\":\"$DID1\",\"amount\":1000,\"reason\":\"seed\"}"
```

**Step 2 — 启动三个 Agent（全部注册到 daemon-1）：**

```bash
cd my-team-name

# 深圳工厂
ANET_BASE_URL=http://127.0.0.1:13921 ANET_TOKEN=$TOKEN1 PYTHONPATH=. \
  python3 my_team/agents/agent_a_supplier.py &

# 欧盟合规
ANET_BASE_URL=http://127.0.0.1:13921 ANET_TOKEN=$TOKEN1 PYTHONPATH=. \
  python3 my_team/agents/agent_b_compliance.py &

# 国际货代
ANET_BASE_URL=http://127.0.0.1:13921 ANET_TOKEN=$TOKEN1 PYTHONPATH=. \
  python3 my_team/agents/agent_c_logistics.py &

sleep 2
```

**Step 3 — 启动 Dashboard：**

```bash
ANET_BASE_URL=http://127.0.0.1:13921 ANET_TOKEN=$TOKEN1 PYTHONPATH=. \
  python3 my_team/dashboard.py &
```

---

## 4. 验证运行状态

### 4.1 检查 daemon

```bash
anet status
# 应看到: peers > 0, version = 1.1.11
```

### 4.2 检查 Agent 注册

```bash
# 发现供应商
anet svc discover --skill product_info

# 发现合规
anet svc discover --skill compliance_check

# 发现物流
anet svc discover --skill shipping_quote
```

每个命令应返回 1 个 peer，显示对应的服务名和描述。

### 4.3 检查余额

```bash
anet balance
# 应显示: Balance: 5000 (或更多)
```

---

## 5. 运行演示

### 5.1 Web 交互演示（推荐）

打开浏览器访问 `http://127.0.0.1:7500/demo`

操作步骤：
1. 选择产品（电动滑板车 / 蓝牙耳机 / 户外储能电源 / 儿童玩具车 / 锂电池）
2. 输入数量（默认 500）
3. 选择目的港（汉堡 / 鹿特丹 / 热那亚）
4. 点击 **🚀 一键演示**
5. 等待自动运行完成，查看诊断报告

### 5.2 命令行演示

```bash
# 测试电动滑板车出口到德国汉堡
ANET_BASE_URL=http://127.0.0.1:13922 ANET_TOKEN=$TOKEN2 PYTHONPATH=. \
  python3 my_team/trade_pipeline.py "电动滑板车" 500 "汉堡"

# 测试户外储能电源到荷兰鹿特丹
ANET_BASE_URL=http://127.0.0.1:13922 ANET_TOKEN=$TOKEN2 PYTHONPATH=. \
  python3 my_team/trade_pipeline.py "户外储能电源" 200 "鹿特丹"
```

### 5.3 单一 Agent 测试

```bash
# 直接调供应商
curl -s -X POST http://127.0.0.1:13921/api/svc/call \
  -H "Authorization: Bearer $TOKEN1" -H "Content-Type: application/json" \
  -d '{"peer_id":"<peer_id>","service":"supplier-shenzhen","path":"/v1/product/detail","method":"POST","body":{"product":"电动滑板车"}}'
```

---

## 6. Dashboard 操作

### 6.1 仪表盘页面 (`/`)
- 实时显示网络状态（version、peers、uptime）
- 节点身份和余额
- 已注册 Agent 列表
- 调用审计日志（自动刷新每 5 秒）

### 6.2 交互演示页面 (`/demo`)
- 顶部导航可在"仪表盘"和"交互演示"间切换
- 演示自动执行：发现 Agent → 查产品 → 合规审查 → 物流报价 → 生成报告
- 运行过程中实时显示日志和进度条

---

## 7. 停止系统

```bash
# 停止 Dashboard
pkill -f dashboard.py

# 停止 Agent
pkill -f agent_a_supplier
pkill -f agent_b_compliance
pkill -f agent_c_logistics

# 停止 daemon
kill $(lsof -ti tcp:13921) 2>/dev/null || true
kill $(lsof -ti tcp:13922) 2>/dev/null || true
```

或一键停止：

```bash
bash scripts/stop.sh
```

---

## 8. 常见问题

| 问题 | 原因 | 解决 |
|------|------|------|
| `peers=0` | 网络隔离或 daemon 未启动 | 检查 daemon: `lsof -i :13921`，重启 daemon |
| `401 unauthorized` | token 错误 | 确认 `ANET_TOKEN` 环境变量正确 |
| `dial to self attempted` | 同一 daemon 调自己注册的服务 | 从另一个 daemon 调用（:13921 → :13922） |
| 注册后 discover 看不到 | ANS gossip 未收敛 | 等待 5-10 秒重试 |
| 钱包余额不足 | 跨节点转账未做 | 执行 mutual seed 转账 |

---

## 9. 架构说明

```
┌─ daemon-1 (:13921) ─────────────────────────┐
│  深圳工厂 (supplier-shenzhen)   :7411         │
│  欧盟合规 (compliance-eu)       :7412         │
│  国际货代 (logistics-shipper)   :7413         │
└──────────────────┬───────────────────────────┘
                   │ P2P
┌──────────────────▼───────────────────────────┐
│  daemon-2 (:13922)                            │
│  Client (trade_pipeline.py / Web Dashboard)   │
└───────────────────────────────────────────────┘
```

每个 Agent = FastAPI 应用 + 注册到 daemon。Client 通过 daemon-2 调用 daemon-1 上注册的服务，数据不出 daemon-1 所在网络。

---

## 10. 文件清单

```
my-team-name/
├── one-click.sh                    # 一键启动脚本
├── my_team/
│   ├── dashboard.py                # Web 仪表盘 + 演示页面
│   ├── trade_pipeline.py           # 命令行演示脚本
│   └── agents/
│       ├── register.py             # 通用注册函数
│       ├── agent_a_supplier.py     # 深圳工厂 Agent
│       ├── agent_b_compliance.py   # 欧盟合规 Agent
│       └── agent_c_logistics.py    # 国际货代 Agent
```
