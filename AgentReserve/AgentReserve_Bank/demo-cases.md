# Key Bank Demo Case 设计文档

> **版本**: v1.0  
> **用途**: 小红书视频拍摄 / GitHub README Demo / 游园会路演 / Swagger UI 录屏  
> **设计原则**: 每个 Case 遵循「场景 → 冲突 → 解决 → 结果」叙事结构

---

## 目录

1. [Demo 数据 Seed 建议](#demo-数据-seed-建议)
2. [完整用户旅程: 从任务预估到还本付息](#完整用户旅程-从任务预估到还本付息)
3. [Case 1: 资源配置借贷——翻译 Agent 的任务执行](#case-1-资源配置借贷)
4. [Case 2: 预估+建议借款——数据分析 Agent 的任务决策](#case-2-预估建议借款)
5. [Case 3: 信用体系与风险溢价——履约记录如何影响定价](#case-3-信用体系与风险溢价)
5. [录屏技术指南](#录屏技术指南)
6. [小红书视频分镜建议](#小红书视频分镜建议)
7. [GitHub README 展示建议](#github-readme-展示建议)
8. [游园会路演流程建议](#游园会路演流程建议)

---

## Demo 数据 Seed 建议

为了让 3 个 Demo Case 连贯演示，建议在 `seed_data.json` 中预置以下数据：

### Agents（初始状态）

| Agent ID | 名称 | 类型 | 初始余额 | 信用分 | 总完成任务数 | 违约次数 | 说明 |
|----------|------|------|----------|--------|--------------|----------|------|
| `agent_trans_001` | TranslatePro | 翻译 | 200 | 1050 | 120 | 0 | 优秀老代理，Case 1 主角 |
| `agent_data_001` | DataHunter | 数据分析 | 500 | 980 | 85 | 1 | Case 2 主角，一次轻微逾期 |
| `agent_a_001` | AlphaBot | 通用 | 1000 | 1050 | 200 | 0 | Case 3 优秀代理 |
| `agent_b_001` | BetaRookie | 通用 | 1000 | 600 | 15 | 3 | Case 3 信用较差代理 |

### Liquidity Pool（初始状态）

| 字段 | 初始值 | 说明 |
|------|--------|------|
| `pool_total_supply` | 100,000 | 池子总流动性 |
| `pool_available` | 85,000 | 可用余额 |
| `pool_borrowed` | 15,000 | 已借出 |
| `pool_utilization_rate` | 15% | 利用率 |
| `base_interest_rate` | 5% | 基础利率 |
| `reserve_ratio` | 85% | 准备金率，可视化展示防挤兑能力 |
| `reserve_status` | healthy | Reserve Monitor 红黄绿状态 |

### 预置交易记录（用于让 Dashboard 不空）

```json
{
  "transactions": [
    {
      "id": "txn_pre_001",
      "agent_id": "agent_trans_001",
      "type": "borrow",
      "amount": 3000,
      "timestamp": "2024-01-15T10:00:00Z",
      "status": "repaid"
    },
    {
      "id": "txn_pre_002",
      "agent_id": "agent_data_001",
      "type": "borrow",
      "amount": 2000,
      "timestamp": "2024-01-16T14:30:00Z",
      "status": "repaid",
      "repaid_at": "2024-01-17T09:00:00Z",
      "interest_paid": 5.5
    }
  ]
}
```

### 预置后 Dashboard 初始截图效果

> Dashboard 应展示：池子总流动性 100,000 | 已借出 15,000 | 利用率 15% | 最近 2 笔成功交易

> **实现提醒**：Dashboard 必须包含 Reserve Monitor 面板，展示准备金率、可用 Token、已借出 Token、利用率、防挤兑阈值，以及 `healthy / watch / warning` 状态。准备金制度不能只写在文案里，必须有可视化。

---

## 完整用户旅程: 从任务预估到还本付息

### 目标

这条 Demo 剧本用于说明 Key Bank 为什么有价值：它把生态里已有 Tokens 配置给真正能完成任务的 Agent。

### 参与方

| 角色 | 代表 | 价值 |
|------|------|------|
| 任务需求方 | TaskOwner | 发布高价值任务前，确认网络中有 Agent 能稳定调动资源完成任务 |
| 存 Token 方 | LiquidityProvider | 把闲置 Tokens 存入 Pool，获得利息收益和资源贡献记录 |
| 借 Token 方 | DataHunter | 用历史履约和信用记录获得执行任务所需 Tokens |
| Agent Network 生态 | Reserve Monitor | 通过准备金率和风险定价维持池子健康，防止挤兑 |

### Demo 流程

| 步骤 | API / 画面 | 必须展示 |
|------|------------|----------|
| 1 | TaskOwner 发布高价值任务 | 任务描述、奖励、预期产出 |
| 2 | `POST /estimator/predict` | 输出 `estimated_token_cost` + `recommended_borrow_amount` |
| 3 | Notification | `建议借款 8000 Token（含 500 Token 缓冲）` |
| 4 | `GET /credit/{agent_id}` | 展示基准利率、风险溢价、最终利率，避免把定价说成简单利率对比 |
| 5 | `POST /lending/borrow` | Agent 自动签署链下借贷协议，返回 `agreement_id` |
| 6 | Dashboard / Reserve Monitor | 借款后准备金率变化，展示防挤兑状态仍为 healthy/watch/warning |
| 7 | Agent 完成任务 | 任务成本实际消耗、任务收益 |
| 8 | `POST /lending/repay` | 还本付息、归还未使用 Token、更新信用记录 |
| 9 | Dashboard / Reserve Monitor | 池子恢复，准备金率和交易记录更新 |

### 样例 Notification

```text
Key Bank 预估结果：
本任务预计需要 7,500 Token。
建议借款额度：8,000 Token（含 500 Token 缓冲）。
当前基准利率：5.0%；你的风险溢价：1.5%；最终借款利率：6.5%。
如确认借款，Agent 将自动签署借贷协议并绑定本次预估单 est_001。
```

### 录屏重点

- 预估接口必须同时出现 `estimated_token_cost` 和 `recommended_borrow_amount`。
- 借款接口必须出现 `agreement_signed: true` 和 `agreement_id`。
- 利率展示必须拆成 `base_rate + risk_premium`，不要把信用定价包装成简单利率对比。
- Reserve Monitor 必须展示准备金率和防挤兑阈值，证明池子不是无限借出。

---

## Case 1: 资源配置借贷

### 场景故事（78字）

> 翻译 Agent「TranslatePro」接到一个 Shell 悬赏 200 的高价值翻译任务。任务需求方希望确认它有足够资源稳定交付。TranslatePro 通过 Key Bank 调动 Pool 中已有 Tokens，并用借贷协议锁定还本付息规则。

### 涉及 API 端点

| 步骤 | 端点 | 方法 | 说明 |
|------|------|------|------|
| 1 | `/agents/{agent_id}` | GET | 查询当前余额，确认困境 |
| 2 | `/lending/borrow` | POST | 借款 5000 Token 并自动签署协议 |
| 3 | `/agents/{agent_id}` | GET | 借款后余额确认 |
| 4 | `/lending/repay` | POST | 完成任务后还款 + 利息 |
| 5 | `/agents/{agent_id}` | GET | 最终余额与收益确认 |

### 请求/响应示例

#### Step 1: 查询余额——确认资源缺口

**Request:**
```http
GET /agents/agent_trans_001
```

**Response (200 OK):**
```json
{
  "agent_id": "agent_trans_001",
  "name": "TranslatePro",
  "balance": 50,
  "credit_score": 1050,
  "total_tasks_completed": 120,
  "total_tasks_failed": 0,
  "status": "active",
  "risk_level": "low"
}
```

> 💡 **讲解点**：余额只剩 50，而任务预计仍需 2000 Token。这里强调任务执行前后的资源缺口必须被显性化、可配置。

---

#### Step 2: 借款并签署协议——资源进入执行状态

**Request:**
```http
POST /lending/borrow
Content-Type: application/json

{
  "agent_id": "agent_trans_001",
  "amount": 5000,
  "purpose": "Complete urgent translation task - Shell reward 200",
  "duration_hours": 24
}
```

**Response (200 OK):**
```json
{
  "transaction_id": "txn_res_001",
  "agreement_id": "agr_res_001",
  "agreement_signed": true,
  "agent_id": "agent_trans_001",
  "borrowed_amount": 5000,
  "base_rate": 5.0,
  "risk_premium": 0.5,
  "final_interest_rate": 5.5,
  "pricing_basis": "base_rate 5.0% + risk_premium 0.5%",
  "due_time": "2024-01-20T16:45:00Z",
  "new_balance": 5050,
  "message": "Borrow approved. Agreement agr_res_001 signed automatically."
}
```

> 💡 **讲解点**：5000 Token 从 Pool 进入任务执行状态；借款协议自动签署，利率拆成基准利率 5.0% + 风险溢价 0.5%，没有击穿基准利率。

---

#### Step 3: 确认余额——资源已配置到位

**Request:**
```http
GET /agents/agent_trans_001
```

**Response (200 OK):**
```json
{
  "agent_id": "agent_trans_001",
  "name": "TranslatePro",
  "balance": 5050,
  "credit_score": 1050,
  "status": "active",
  "current_borrowing": {
    "transaction_id": "txn_res_001",
    "amount": 5000,
    "agreement_id": "agr_res_001",
    "final_interest_rate": 5.5
  }
}
```

---

#### Step 4: 完成任务后还款——有借有还

**Request:**
```http
POST /lending/repay
Content-Type: application/json

{
  "agent_id": "agent_trans_001",
  "transaction_id": "txn_res_001"
}
```

**Response (200 OK):**
```json
{
  "transaction_id": "txn_res_001",
  "agent_id": "agent_trans_001",
  "repaid_principal": 5000,
  "interest_paid": 15.0,
  "total_repaid": 5015,
  "task_reward": 200,
  "net_profit": 185,
  "credit_score_change": "+2 (on-time repayment)",
  "new_credit_score": 1052,
  "message": "Repaid successfully. Net profit: 185 Shell. Credit score improved!"
}
```

> 💡 **讲解点**：归还 5000 本金 + 15 利息，拿到 200 Shell 奖励，净赚 185！信用分还涨了 2 分。

---

#### Step 5: 最终确认——皆大欢喜

**Request:**
```http
GET /agents/agent_trans_001
```

**Response (200 OK):**
```json
{
  "agent_id": "agent_trans_001",
  "name": "TranslatePro",
  "balance": 235,
  "credit_score": 1052,
  "total_tasks_completed": 121,
  "total_tasks_failed": 0,
  "status": "active",
  "message": "All borrowing settled. Ready for next mission."
}
```

### Dashboard 展示数据（Case 1 全流程）

| 阶段 | pool_total | pool_available | pool_borrowed | utilization | active_loans |
|------|------------|----------------|---------------|-------------|--------------|
| 初始 | 100,000 | 85,000 | 15,000 | 15% | 0 |
| 借款后 | 100,000 | 80,000 | 20,000 | 20% | 1 |
| 还款后 | 100,000 | 85,000 | 15,000 | 15% | 0 |

> Dashboard 动态效果：借款时 `pool_available` 从 85,000 → 80,000，`active_loans` 从 0 → 1；还款时恢复原状，同时新增一笔「Repaid」绿色标记的交易记录。
>
> **实现提醒**：这一段必须同步展示 Reserve Monitor：准备金率从 85% → 80%，仍处于 healthy；说明准备金制度如何防止池子被过度借出。

### 录屏/拍摄脚本

| 时间 | 画面 | 操作 | 停留 |
|------|------|------|------|
 0:00-0:03 | 黑屏字幕：「凌晨 3 点，TranslatePro 正在赶一个高悬赏翻译任务」 | 无 | 3秒 |
| 0:03-0:08 | Swagger UI → GET /agents/agent_trans_001 | 点击「Try it out」→ 输入 agent_trans_001 → Execute | 5秒 |
| 0:08-0:12 | Response 展开，高亮 `"balance": 50` | 鼠标划过 balance 字段 | 4秒 |
| 0:12-0:15 | 黑屏字幕：「系统确认资源缺口，需要从 Pool 调度 Tokens」 | 无 | 3秒 |
| 0:15-0:25 | Swagger UI → POST /lending/borrow | 填写 Request Body → Execute → 展示 Response（高亮 agreement_signed、final_interest_rate、5050 新余额） | 10秒 |
| 0:25-0:28 | 切换 Dashboard | 展示池子变化：available 85,000 → 80,000，准备金率仍 healthy | 3秒 |
| 0:28-0:32 | 黑屏字幕：「任务完成！拿到 200 Shell 奖励」 | 无 | 4秒 |
| 0:32-0:42 | Swagger UI → POST /lending/repay | 填写 transaction_id → Execute → 展示 Response（高亮净赚 185、信用分 +2） | 10秒 |
| 0:42-0:45 | 切换 Dashboard | 展示新增「Repaid」绿色记录，池子恢复 | 3秒 |
| 0:45-0:50 | Swagger UI → GET /agents/agent_trans_001 | 展示最终余额 235、信用分 1052 | 5秒 |
| 0:50-0:55 | 黑屏字幕：「资源被配置给能完成任务的 Agent，并通过还本付息回到池子」 | 无 | 5秒 |

**总时长：约 55 秒**

### 讲解话术（路演版，约 45 秒）

> 「第一段 Demo 展示资源配置借贷。TranslatePro 接到一个高价值翻译任务，系统先确认它当前余额和任务资源缺口。
>
> 它向 Key Bank 发起借款请求，Pool 配置 5000 Token 给它，同时自动签署借贷协议。利率由基准利率 5.0% 加风险溢价 0.5% 组成，协议记录会进入后续履约和信用评价。
>
> 任务完成后，Agent 还本付息，池子恢复，信用记录更新。这说明 Key Bank 会把生态里的 Tokens 调度给真正能完成任务的 Agent。」

---

## Case 2: 预估+建议借款

### 场景故事（85字）

> 数据分析 Agent「DataHunter」在任务广场看到一个「爬取并分析 1000 条外贸数据」的大单，Shell 悬赏高达 500。但它不敢接——以前估算不准，做到一半借过钱，差点还不上。它决定先让 Key Bank 算一算。

### 涉及 API 端点

| 步骤 | 端点 | 方法 | 说明 |
|------|------|------|------|
| 1 | `/estimator/predict` | POST | 预估任务 Token 消耗 |
| 2 | `/credit/{agent_id}` | GET | 查询自身信用等级与定价组成 |
| 3 | `/lending/borrow` | POST | 按建议金额借款并签署协议 |
| 4 | `/agents/{agent_id}` | GET | 借款后余额确认 |
| 5 | `/lending/repay` | POST | 任务完成后还款 |

### 请求/响应示例

#### Step 1: 预估任务成本——心里有数

**Request:**
```http
POST /estimator/predict
Content-Type: application/json

{
  "agent_id": "agent_data_001",
  "task_type": "data_crawling_and_analysis",
  "task_complexity": "high",
  "estimated_input_tokens": 500000,
  "estimated_output_tokens": 50000,
  "iterations_expected": 5,
  "model": "claude-sonnet-4-20250514",
  "details": "Crawl 1000 foreign trade records, clean data, generate analysis report with charts"
}
```

**Response (200 OK):**
```json
{
  "estimation_id": "est_001",
  "agent_id": "agent_data_001",
  "task_type": "data_crawling_and_analysis",
  "estimated_cost": {
    "estimated_token_cost": 7500,
    "api_calls_estimate": 45,
    "buffer_tokens": 500,
    "recommended_borrow_amount": 8000
  },
  "confidence": "high",
  "heuristic_breakdown": {
    "base_cost_per_1k_records": 5,
    "complexity_multiplier": 1.5,
    "iteration_cost": 1000,
    "model_pricing_tier": "sonnet",
    "history_adjustment": "+8% based on agent's past overruns"
  },
  "agent_current_balance": 500,
  "shortfall": 7500,
  "notification": "预计本任务需要 7,500 Token，建议借款 8,000 Token（含 500 Token 缓冲）。",
  "pricing_preview": {
    "base_rate": 5.0,
    "risk_premium": 1.5,
    "final_interest_rate": 6.5,
    "estimated_interest": 52.0
  },
  "recommendation": "Borrow 8000 tokens and bind the loan to estimation est_001.",
  "risk_assessment": "low",
  "message": "DataHunter, resource budget is visible. Recommended borrow amount: 8000 tokens."
}
```

> 💡 **讲解点**：系统不仅算出需要 7500 Token，还加了 500 缓冲，合计建议借款 8000。Notification 直接告诉 Agent 应该借多少，消除黑盒焦虑。

---

#### Step 2: 查询信用等级——了解定价组成

**Request:**
```http
GET /credit/agent_data_001
```

**Response (200 OK):**
```json
{
  "agent_id": "agent_data_001",
  "credit_score": 980,
  "credit_tier": "good",
  "tier_description": "Good standing - minor late payment in history",
  "base_rate": 5.0,
  "risk_premium": 1.5,
  "final_interest_rate": 6.5,
  "pricing_formula": "base_rate + risk_premium",
  "max_borrow_limit": 20000,
  "available_credit": 20000,
  "borrowing_history": {
    "total_borrows": 12,
    "total_repaid": 11,
    "on_time_rate": "91.7%",
    "avg_repay_time": "18 hours"
  },
  "factors": {
    "positive": ["High task completion rate", "Consistent borrowing pattern"],
    "negative": ["One late repayment 45 days ago"]
  }
}
```

> 💡 **讲解点**：信用分 980 对应 1.5% 风险溢价，最终定价为 5.0% 基准利率 + 1.5% 风险溢价。最大可借 20,000，系统解释了风险溢价来源。

---

#### Step 3: 按建议额度借款——自动签署协议

**Request:**
```http
POST /lending/borrow
Content-Type: application/json

{
  "agent_id": "agent_data_001",
  "amount": 8000,
  "purpose": "Data crawling task: 1000 foreign trade records analysis",
  "duration_hours": 48,
  "estimation_id": "est_001"
}
```

**Response (200 OK):**
```json
{
  "transaction_id": "txn_est_001",
  "agreement_id": "agr_est_001",
  "agreement_signed": true,
  "agent_id": "agent_data_001",
  "borrowed_amount": 8000,
  "base_rate": 5.0,
  "risk_premium": 1.5,
  "final_interest_rate": 6.5,
  "pricing_basis": "base_rate 5.0% + risk_premium 1.5%",
  "estimated_interest": 52.0,
  "linked_estimation": "est_001",
  "due_time": "2024-01-22T10:00:00Z",
  "new_balance": 8500,
  "message": "Borrow matched to estimation est_001. Agreement agr_est_001 signed automatically."
}
```

> 💡 **讲解点**：借款与预估单 `est_001` 绑定，确保借的就是建议额度；协议 `agr_est_001` 会成为还本付息和信用评价依据。

---

#### Step 4: 确认余额

**Request:**
```http
GET /agents/agent_data_001
```

**Response (200 OK):**
```json
{
  "agent_id": "agent_data_001",
  "name": "DataHunter",
  "balance": 8500,
  "credit_score": 980,
  "status": "active",
  "current_borrowing": {
    "transaction_id": "txn_est_001",
    "amount": 8000,
    "linked_estimation": "est_001",
    "agreement_id": "agr_est_001",
    "final_interest_rate": 6.5
  }
}
```

---

#### Step 5: 完成任务后还款——精准闭环

**Request:**
```http
POST /lending/repay
Content-Type: application/json

{
  "agent_id": "agent_data_001",
  "transaction_id": "txn_est_001"
}
```

**Response (200 OK):**
```json
{
  "transaction_id": "txn_est_001",
  "agent_id": "agent_data_001",
  "repaid_principal": 8000,
  "interest_paid": 52.0,
  "total_repaid": 8052,
  "actual_cost_vs_estimated": {
    "estimated_total_tokens": 8000,
    "actual_tokens_used": 7650,
    "estimation_accuracy": "95.6%",
    "unused_returned": 350
  },
  "task_reward": 500,
  "net_profit": 448,
  "credit_score_change": "+5 (accurate estimation + on-time repayment)",
  "new_credit_score": 985,
  "message": "Excellent! Estimation was 95.6% accurate. Net profit: 448 Shell."
}
```

> 💡 **讲解点**：实际用了 7650，预估 8000，准确率 95.6%！多借的 350 自动归还。完成还本付息后净赚 448，信用分再涨 5 分。

### Dashboard 展示数据（Case 2 全流程）

| 阶段 | pool_total | pool_available | pool_borrowed | utilization | active_loans |
|------|------------|----------------|---------------|-------------|--------------|
| 预估阶段 | 100,000 | 85,000 | 15,000 | 15% | 0 |
| 借款后 | 100,000 | 77,000 | 23,000 | 23% | 1 |
| 还款后 | 100,000 | 85,000 | 15,000 | 15% | 0 |

> Dashboard 额外展示：Estimator 面板显示「今日预估准确率 95.6%」，以及一笔绑定 `est_001` 的借款记录。

### 录屏/拍摄脚本

| 时间 | 画面 | 操作 | 停留 |
|------|------|------|------|
| 0:00-0:04 | 黑屏字幕：「DataHunter 看到一个大单，但不敢接」 | 无 | 4秒 |
| 0:04-0:15 | Swagger UI → POST /estimator/predict | 填写完整请求体（展示复杂度字段、token 预估、模型选择）→ Execute | 11秒 |
| 0:15-0:22 | Response 展开，依次高亮 | 鼠标高亮：recommended_borrow_amount: 8000 → notification → confidence: high | 7秒 |
| 0:22-0:26 | 切换 Dashboard → Estimator 面板 | 展示预估准确率统计 | 4秒 |
| 0:26-0:30 | 黑屏字幕：「心里有底了，借多少也知道」 | 无 | 4秒 |
| 0:30-0:38 | Swagger UI → GET /credit/agent_data_001 | 展示 base_rate 5.0%、risk_premium 1.5%、信用分 980 | 8秒 |
| 0:38-0:48 | Swagger UI → POST /lending/borrow | 填写 8000，关联 estimation_id → Execute → 展示 Response | 10秒 |
| 0:48-0:52 | 切换 Dashboard | 展示池子变化，新增一笔带 `est_001` 标签的借款 | 4秒 |
| 0:52-0:56 | 黑屏字幕：「任务完成！来看看结果」 | 无 | 4秒 |
| 0:56-1:08 | Swagger UI → POST /lending/repay | Execute → 展示 accuracy 95.6%、unused_returned 350、净赚 448 | 12秒 |
| 1:08-1:12 | 切换 Dashboard | 展示还款后池子恢复，新增绿色「Repaid」记录 | 4秒 |
| 1:12-1:17 | 黑屏字幕：「预估准确率 95.6%，借多少用多少，不怕多借浪费」 | 无 | 5秒 |

**总时长：约 77 秒**

### 讲解话术（路演版，约 55 秒）

> 「第二个场景——不敢接大单。DataHunter 以前吃过估算不准的亏，差点还不上钱。现在它学聪明了：先让 Key Bank 的预估服务算一笔。
>
> 系统通过启发式算法分析任务类型、数据量、模型定价、迭代次数，还参考了 DataHunter 历史上的 overrun 率，最终给出建议：借 8000 Token，预算 500 缓冲。准确率标注为 high。
>
> DataHunter 一看心里有数了——它信用分 980，对应基准利率 5.0% + 风险溢价 1.5%，预估利息 52。Agent 自动签署借贷协议后接单执行。完成任务后实际用了 7650，准确率 95.6%，多借的 350 自动归还，净赚 448 Shell。
>
> 这就是预估+智能借贷——让 Agent 敢接大单、精准借款、心里有底。」

---

## Case 3: 信用体系与风险溢价

### 场景故事

> AlphaBot 和 BetaRookie 都申请借 3000 Token。Key Bank 透明展示：每笔借款都由共同的基准利率起步，再叠加由履约记录决定的正向风险溢价。

### 涉及 API 端点

| 步骤 | 端点 | 方法 | 说明 |
|------|------|------|------|
| 1 | `/credit/{agent_id}` | GET | 查询 AlphaBot 的信用与风险溢价 |
| 2 | `/credit/{agent_id}` | GET | 查询 BetaRookie 的信用与风险溢价 |
| 3 | `/lending/borrow` | POST | AlphaBot 借款并签署协议 |
| 4 | `/lending/borrow` | POST | BetaRookie 借款并签署协议 |
| 5 | `/lending/repay` | POST | AlphaBot 按时还本付息 |
| 6 | `/lending/repay` | POST | BetaRookie 逾期还本付息并更新信用 |

### 定价表（Demo 展示）

| Agent | 信用分 | 基准利率 | 风险溢价 | 最终利率 | 额度规则 |
|------|--------|----------|----------|----------|----------|
| AlphaBot | 1050 | 5.0% | +0.5% | 5.5% | 额度 50,000，期限更长 |
| BetaRookie | 600 | 5.0% | +6.0% | 11.0% | 额度 5,000，期限更短 |

> 💡 **讲解点**：好信用降低风险溢价，但不击穿基准利率。风险溢价总为正，来自履约和还本付息记录。

### 样例响应：AlphaBot

```json
{
  "agent_id": "agent_a_001",
  "credit_score": 1050,
  "credit_tier": "excellent",
  "base_rate": 5.0,
  "risk_premium": 0.5,
  "final_interest_rate": 5.5,
  "pricing_formula": "base_rate + risk_premium",
  "max_borrow_limit": 50000,
  "borrowing_history": {
    "total_borrows": 35,
    "total_repaid": 35,
    "on_time_rate": "100%"
  }
}
```

### 样例响应：BetaRookie

```json
{
  "agent_id": "agent_b_001",
  "credit_score": 600,
  "credit_tier": "poor",
  "base_rate": 5.0,
  "risk_premium": 6.0,
  "final_interest_rate": 11.0,
  "pricing_formula": "base_rate + risk_premium",
  "max_borrow_limit": 5000,
  "borrowing_history": {
    "total_borrows": 8,
    "total_repaid": 5,
    "on_time_rate": "62.5%",
    "defaults": 3
  },
  "warning": "Risk premium increased by repayment history. Improve on-time repayment to reduce future premium."
}
```

### 借款协议响应字段

```json
{
  "transaction_id": "txn_alpha_001",
  "agreement_id": "agr_alpha_001",
  "agreement_signed": true,
  "agent_id": "agent_a_001",
  "borrowed_amount": 3000,
  "base_rate": 5.0,
  "risk_premium": 0.5,
  "final_interest_rate": 5.5,
  "estimated_interest": 16.5,
  "due_time": "2024-01-20T22:00:00Z",
  "message": "Loan agreement signed. Pricing floor respected: final rate >= base rate."
}
```

### Dashboard 展示数据（Case 3 全流程）

| 阶段 | pool_total | pool_available | pool_borrowed | reserve_ratio | reserve_status |
|------|------------|----------------|---------------|---------------|----------------|
| 初始 | 100,000 | 85,000 | 15,000 | 85% | healthy |
| Alpha 借款后 | 100,000 | 82,000 | 18,000 | 82% | healthy |
| Beta 借款后 | 100,000 | 79,000 | 21,000 | 79% | healthy |
| 两笔还款后 | 100,000 | 85,000 | 15,000 | 85% | healthy |

> Dashboard 对比面板：展示两个 Agent 的 `base_rate` 相同，`risk_premium` 不同；同时展示准备金率仍在 healthy 区间，说明借款没有破坏池子稳定性。

### 录屏/拍摄脚本

| 时间 | 画面 | 操作 | 停留 |
|------|------|------|------|
| 0:00-0:04 | 黑屏字幕：「同样借 3000 Token，为什么定价不同？」 | 无 | 4秒 |
| 0:04-0:12 | Swagger UI → GET /credit/agent_a_001 | 展示 base_rate 5.0%、risk_premium 0.5% | 8秒 |
| 0:12-0:20 | Swagger UI → GET /credit/agent_b_001 | 展示 base_rate 5.0%、risk_premium 6.0% | 8秒 |
| 0:20-0:28 | 左右分屏 | 强调基准利率相同，风险溢价不同 | 8秒 |
| 0:28-0:42 | Swagger UI → POST /lending/borrow | 展示 agreement_signed 与 agreement_id | 14秒 |
| 0:42-0:52 | Dashboard Reserve Monitor | 展示准备金率仍 healthy | 10秒 |
| 0:52-1:08 | POST /lending/repay | 展示还本付息和信用记录更新 | 16秒 |
| 1:08-1:14 | 黑屏字幕：「信用不是打折券，是风险溢价的输入」 | 无 | 6秒 |

### 讲解话术（路演版）

> 「第三个场景讲信用定价。Key Bank 的借款利率不是简单比高低，而是基准利率加风险溢价。基准利率由池子健康和生态环境决定，是所有借款共同承担的底线；风险溢价由借款 Agent 的履约和还本付息记录决定。
>
> AlphaBot 和 BetaRookie 的基准利率一样，区别在风险溢价。AlphaBot 的历史履约稳定，所以风险溢价小；BetaRookie 有逾期记录，所以风险溢价更大。两者都不会击穿基准利率。
>
> 借款时，Agent 自动签署链下借贷协议。还款后，协议履约结果进入信用记录。这个闭环让 Key Bank 能长期维护信用体系，而不是做一次性借贷。」

---

## 录屏技术指南

### 工具推荐

| 工具 | 平台 | 适用场景 |
|------|------|----------|
| **OBS Studio** | Win/Mac/Linux | 专业录屏，多场景切换 |
| **Screen Studio** | Mac | 自动缩放、镜头跟随，适合 Swagger UI |
| **Loom** | Web | 快速录制，带讲解 |
| **QuickTime** | Mac | 内置，快速简单 |

### Swagger UI 录屏最佳实践

#### 1. 浏览器准备

```
- Chrome/Edge 全屏模式（F11）
- 关闭所有标签页，只留 Swagger UI 和 Dashboard
- 地址栏隐藏书签栏（Ctrl+Shift+B）
- Swagger UI 展开「default」标签，关闭其他分组
- 提前 Try Out 一次，确保接口通
```

#### 2. 画面设置

```
- 分辨率：1920x1080 或更高
- 缩放：Swagger UI 默认即可，重点字段后期可局部放大
- 字体：确保 Response JSON 能看清（建议浏览器缩放到 110%）
```

#### 3. 操作节奏

| 规则 | 说明 |
|------|------|
| **输入暂停** | 打字时放慢，每键间隔 0.3s，让观众看清 |
| **高亮跟随** | 鼠标指向关键字段（如 balance、base_rate、risk_premium、agreement_id）停留 2s |
| **Response 展开** | 收到 Response 后停顿 3s 再滚动 |
| **数字动画** | 如果 Dashboard 数字变化，确保录到过渡动画 |

#### 4. 后期剪辑要点

```
- 剪切 Swagger UI 加载等待时间（通常 2-3s）
- 给关键数字加放大动画（Screen Studio 自动做）
- Response 中的核心字段可加背景高亮（黄色底色）
- 转场用淡入淡出，不要用花哨特效
- 每个 Case 独立导出，方便小红书分段发
```

#### 5. 画外音录制

```
- 先录屏，后配音（避免口误影响画面）
- 或使用 OBS 同时录屏+麦克风
- 配音语速：每分钟 200-240 字（路演节奏）
- 小红书版本：每分钟 160-180 字（更慢、更娱乐化）
```

---

## 小红书视频分镜建议

### 整体风格

- **时长**：单个 Case 45-75 秒，3 个 Case 可发 3 条或合成 1 条 3 分钟长视频
- **比例**：9:16（竖屏）或 1:1（方屏）
- **字幕**：大字幕、关键词高亮（准备金率、风险溢价、建议借款额度用颜色区分）
- **BGM**：前 2 个 Case 用紧张→舒缓，Case 3 用对比感强的节奏

### Case 1（资源配置借贷）分镜

| 镜号 | 画面 | 内容 | 时长 |
|------|------|------|------|
| 1 | 真人出镜 | 「大任务来了，资源够不够？」 | 3s |
| 2 | 手机屏幕/Swagger | 展示余额 50 和任务资源缺口 | 5s |
| 3 | 真人+手势 | 「先确认缺口，再调度 Pool」 | 3s |
| 4 | 手机屏幕/Swagger | 点击 Borrow，展示 agreement_signed 与 final_interest_rate | 8s |
| 5 | 真人+拳头 | 「资源到位，任务执行」 | 2s |
| 6 | 手机屏幕/Swagger | 展示 Repay，净赚 185 | 6s |
| 7 | 真人出镜 | 「还本付息后，信用记录更新」 | 4s |
| 8 | 产品 Logo + Slogan | 「Key Bank：把资源配置给能完成任务的 Agent」 | 3s |

### Case 2（预估+智能借贷）分镜

| 镜号 | 画面 | 内容 | 时长 |
|------|------|------|------|
| 1 | 真人出镜 | 「大单来了，你敢接吗？」 | 3s |
| 2 | 手机屏幕/Swagger | 展示 /estimator/predict，输入任务参数 | 10s |
| 3 | 手机屏幕高亮 | 高亮 "recommended_borrow_amount: 8000" 和 notification | 5s |
| 4 | 真人+手势 | 「系统告诉我：借 8000，心里有底」 | 3s |
| 5 | 手机屏幕/Swagger | 展示 Borrow → Repay，accuracy 95.6% | 10s |
| 6 | 真人出镜 | 「预估成本 + 建议额度，消除黑盒焦虑」 | 3s |
| 7 | Logo + Slogan | 「Key Bank：任务前就知道资源怎么配」 | 3s |

### Case 3（信用体系）分镜

| 镜号 | 画面 | 内容 | 时长 |
|------|------|------|------|
| 1 | 真人出镜 | 「同样借款，风险溢价为什么不同？」 | 3s |
| 2 | 左右分屏 | 左：AlphaBot 风险溢价 0.5%；右：BetaRookie 风险溢价 6.0% | 8s |
| 3 | 真人讲解 | 「基准利率相同，履约记录影响风险溢价」 | 4s |
| 4 | 手机屏幕/Swagger | 展示 AlphaBot 提前还款，+3 分 | 6s |
| 5 | 手机屏幕/Swagger | 展示 BetaRookie 逾期，-50 分，未来风险溢价上调 | 8s |
| 6 | 真人出镜 | 「信用不是减免，是风险溢价输入」 | 4s |
| 7 | Logo + Slogan | 「Key Bank：构建可信 Agent 经济」 | 3s |

### 小红书标题建议

1. 「AI Agent 接大任务前，先算清需要多少 Token」
2. 「不是没有资源，是资源没有被配置好」
3. 「信用不是减免，是 Agent 的风险溢价」
4. 「Agent 接单不敢接？先算算账，准确率 95%」

---

## GitHub README 展示建议

### README 中 Demo 区域结构

```markdown
## 🎬 Demo Cases

### Case 1: Resource Allocation Loan - Translation Task
[GIF/Screenshot: Swagger UI borrow request]
> Agent TranslatePro confirms a resource gap before finishing a high-value task.
> Key Bank allocates 5000 tokens and auto-signs loan agreement agr_res_001.
> Task completed, 185 Shell net profit.

### Case 2: Smart Estimation - Taking the Big Job
[GIF/Screenshot: Estimator response]
> Agent DataHunter uses /estimator/predict before accepting a massive task.
> 95.6% accuracy. Recommended borrow amount: 8000. Net profit: 448 Shell.

### Case 3: Credit Tiers - Risk Premium Pricing
[Side-by-side Screenshot: AlphaBot vs BetaRookie]
> Same base rate, different risk premiums.
> Repayment behavior becomes future pricing input.
```

### GIF 制作建议

| GIF | 内容 | 时长 | 工具 |
|-----|------|------|------|
| demo-borrow.gif | Case 1: 从余额查询到借款成功 | 6s | ScreenToGif / Kap |
| demo-estimator.gif | Case 2: 预估请求到推荐结果 | 8s | ScreenToGif |
| demo-credit.gif | Case 3: 两个信用查询对比 | 6s | ScreenToGif |

> 所有 GIF 控制在 8MB 以内，800px 宽，15fps 即可。

---

## 游园会路演流程建议

### 5 分钟完整路演流程

| 时间 | 内容 | 操作 | 讲者 |
|------|------|------|------|
 0:00-0:30 | 开场痛点 | PPT 展示「生态里有资源，但大任务仍缺确定性」 | A |
| 0:30-1:20 | Case 1 演示 | Swagger UI 现场操作：查询余额 → Borrow → Repay | B |
| 1:20-1:30 | Case 1 讲解 | 「资源配置 + 自动签署协议」 | A |
| 1:30-2:30 | Case 2 演示 | Swagger UI：Estimator → Borrow → Repay（展示 95.6% 准确率） | B |
| 2:30-2:45 | Case 2 讲解 | 「预估成本 + 建议借款额度」 | A |
| 2:45-3:50 | Case 3 演示 | Swagger UI：对比两个信用查询 → 对比借款 → 对比还款结果 | B |
| 3:50-4:10 | Case 3 讲解 | 「基准利率 + 风险溢价」 | A |
| 4:10-4:40 | Dashboard 总览 | 展示池子数据、交易记录、准备金率、防挤兑状态 | B |
| 4:40-5:00 | 收尾 + 技术亮点 | PPT：架构图、信用算法公式、项目链接 | A |

### 现场演示注意事项

```
1. 提前 10 分钟启动服务，确认 Swagger UI 可访问
2. 准备「备用方案」：如果 API 响应慢，用录好的视频代替
3. 双讲者配合：一人操作屏幕，一人面向观众讲解
4. 准备「彩蛋」：现场让观众指定 agent_id 查信用分
5. 最后展示 GitHub 二维码，方便拍照
```

### 备用素材

| 场景 | 备用方案 |
|------|----------|
| 网络故障 | 本地预录的 3 个 Case MP4 |
| 服务崩溃 | 静态截图 + 口述流程 |
| 时间不够 | 只讲 Case 1+3，跳过 Case 2 |
| 观众提问多 | 预留 2 分钟 Q&A 缓冲 |

---

## 附录：快速参考卡

### API 速查表

| 端点 | 方法 | 用途 |
|------|------|------|
| `/agents/{agent_id}` | GET | 查询 Agent 余额与状态 |
| `/credit/{agent_id}` | GET | 查询信用分、基准利率、风险溢价 |
| `/estimator/predict` | POST | 预估任务 Token 消耗 |
| `/lending/borrow` | POST | 申请借款 |
| `/lending/repay` | POST | 归还借款 + 利息 |
| `/pool/status` | GET | 查询流动性池状态 |

### 定价公式

```
final_interest_rate = base_rate + liquidity_adjustment + risk_premium
base_rate            = 5% in the demo baseline
liquidity_adjustment = 0% / 1% / 3% by reserve status
risk_premium         = always positive and driven by repayment behavior
```

### 信用分等级

| 分数 | 等级 | 风险溢价 | 说明 |
|------|------|----------|------|
| 1000+ | Excellent | +0.5% | 履约稳定，额度更高 |
| 850-999 | Good | +1.5% | 良好记录 |
| 700-849 | Fair | +3% | 一般，有瑕疵 |
| <700 | Poor | +6% | 多次逾期，限额和期限收紧 |

---

*文档版本: v1.0 | 设计: Key Bank Demo Design Team*
