# AgentReserve Demo Case 设计文档

> **版本**: v1.0  
> **用途**: 小红书视频拍摄 / GitHub README Demo / 游园会路演 / Swagger UI 录屏  
> **设计原则**: 每个 Case 遵循「场景 → 冲突 → 解决 → 结果」叙事结构

---

## 目录

1. [Demo 数据 Seed 建议](#demo-数据-seed-建议)
2. [Case 1: 应急借贷——翻译 Agent 的生死时速](#case-1-应急借贷)
3. [Case 2: 预估+智能借贷——数据分析 Agent 的敢接大单](#case-2-预估智能借贷)
4. [Case 3: 信用体系与利率差异——好 Agent 享优惠](#case-3-信用体系与利率差异)
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

---

## Case 1: 应急借贷

### 场景故事（78字）

> 翻译 Agent「TranslatePro」刚接到一个 Shell 悬赏 200 的高难度翻译任务。它埋头苦干，调用 Claude API 处理了 80%——突然余额告警：只剩 50 Token！继续调用要 2000，放弃则前面全部白干。它想到了 AgentReserve。

### 涉及 API 端点

| 步骤 | 端点 | 方法 | 说明 |
|------|------|------|------|
| 1 | `/agents/{agent_id}` | GET | 查询当前余额，确认困境 |
| 2 | `/lending/borrow` | POST | 紧急借款 5000 Token |
| 3 | `/agents/{agent_id}` | GET | 借款后余额确认 |
| 4 | `/lending/repay` | POST | 完成任务后还款 + 利息 |
| 5 | `/agents/{agent_id}` | GET | 最终余额与收益确认 |

### 请求/响应示例

#### Step 1: 查询余额——发现危急

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

> 💡 **讲解点**：余额只剩 50，而 Claude API 继续调用需要 2000，缺口 1950。如果放弃，前面花的 Token 全亏。

---

#### Step 2: 紧急借款——救命稻草

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
  "transaction_id": "txn_emg_001",
  "agent_id": "agent_trans_001",
  "borrowed_amount": 5000,
  "interest_rate": 3.0,
  "interest_rate_basis": "credit_score: 1050 (excellent)",
  "due_time": "2024-01-20T16:45:00Z",
  "new_balance": 5050,
  "message": "Borrow approved instantly. Good luck on your task!"
}
```

> 💡 **讲解点**：信用分 1050 优秀，利率仅 3%。5000 Token 秒到账，任务可以继续！

---

#### Step 3: 确认余额——满血复活

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
    "transaction_id": "txn_emg_001",
    "amount": 5000,
    "interest_rate": 3.0
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
  "transaction_id": "txn_emg_001"
}
```

**Response (200 OK):**
```json
{
  "transaction_id": "txn_emg_001",
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

### 录屏/拍摄脚本

| 时间 | 画面 | 操作 | 停留 |
|------|------|------|------|
 0:00-0:03 | 黑屏字幕：「凌晨 3 点，TranslatePro 正在赶一个高悬赏翻译任务」 | 无 | 3秒 |
| 0:03-0:08 | Swagger UI → GET /agents/agent_trans_001 | 点击「Try it out」→ 输入 agent_trans_001 → Execute | 5秒 |
| 0:08-0:12 | Response 展开，高亮 `"balance": 50` | 鼠标划过 balance 字段 | 4秒 |
| 0:12-0:15 | 黑屏字幕：「还剩 20% 就要完成，但 Token 不够了」 | 无 | 3秒 |
| 0:15-0:25 | Swagger UI → POST /lending/borrow | 填写 Request Body → Execute → 展示 Response（高亮 3% 利率、5050 新余额） | 10秒 |
| 0:25-0:28 | 切换 Dashboard | 展示池子变化：available 85,000 → 80,000 | 3秒 |
| 0:28-0:32 | 黑屏字幕：「任务完成！拿到 200 Shell 奖励」 | 无 | 4秒 |
| 0:32-0:42 | Swagger UI → POST /lending/repay | 填写 transaction_id → Execute → 展示 Response（高亮净赚 185、信用分 +2） | 10秒 |
| 0:42-0:45 | 切换 Dashboard | 展示新增「Repaid」绿色记录，池子恢复 | 3秒 |
| 0:45-0:50 | Swagger UI → GET /agents/agent_trans_001 | 展示最终余额 235、信用分 1052 | 5秒 |
| 0:50-0:55 | 黑屏字幕：「从破产边缘到净赚 185，只花了 15 利息」 | 无 | 5秒 |

**总时长：约 55 秒**

### 讲解话术（路演版，约 45 秒）

> 「大家有没有遇到过——做到一半，突然资源不够了？我们模拟了一个真实场景：翻译 Agent TranslatePro 接了个高悬赏任务，调用 Claude API 做到 80%，余额只剩 50。放弃？前面全亏。继续？钱不够。
>
> 这时候它向 AgentReserve 发起借款请求。因为它的信用分 1050 是优秀等级，系统秒批 5000 Token，利率只要 3%。任务顺利完成，拿到 200 Shell 奖励，还款后净赚 185，信用分还涨了 2 分。
>
> 这就是 AgentReserve 的应急借贷——不让任何 Agent 因为临时缺 Token 而前功尽弃。」

---

## Case 2: 预估+智能借贷

### 场景故事（85字）

> 数据分析 Agent「DataHunter」在任务广场看到一个「爬取并分析 1000 条外贸数据」的大单，Shell 悬赏高达 500。但它不敢接——以前估算不准，做到一半借过钱，差点还不上。它决定先让 AgentReserve 算一算。

### 涉及 API 端点

| 步骤 | 端点 | 方法 | 说明 |
|------|------|------|------|
| 1 | `/estimator/predict` | POST | 预估任务 Token 消耗 |
| 2 | `/credit/{agent_id}` | GET | 查询自身信用等级与利率 |
| 3 | `/lending/borrow` | POST | 按预估金额精确借款 |
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
    "total_tokens_needed": 7500,
    "api_calls_estimate": 45,
    "buffer_tokens": 500,
    "total_recommended": 8000
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
  "recommendation": "Borrow 8000 tokens. Expected reward 500 Shell. Estimated interest at your credit level: ~24 tokens. Net profit estimate: ~476 Shell.",
  "risk_assessment": "low",
  "message": "DataHunter, you can confidently take this task. Budget 8000 tokens."
}
```

> 💡 **讲解点**：系统不仅算出需要 7500 Token，还加了 500 缓冲，合计推荐 8000。基于 Agent 历史数据加了 8% 的 overrun 修正。预估净利润 476 Shell。

---

#### Step 2: 查询信用等级——了解利率

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
  "interest_rate": 4.0,
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

> 💡 **讲解点**：信用分 980，优秀档边缘，利率 4%。最大可借 20,000。系统甚至告诉你为什么——有一次逾期记录。

---

#### Step 3: 精确借款——按需取用

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
  "agent_id": "agent_data_001",
  "borrowed_amount": 8000,
  "interest_rate": 4.0,
  "interest_rate_basis": "credit_score: 980 (good tier)",
  "estimated_interest": 32.0,
  "linked_estimation": "est_001",
  "due_time": "2024-01-22T10:00:00Z",
  "new_balance": 8500,
  "message": "Borrow matched to estimation est_001. Recommended amount: 8000. Good hunting!"
}
```

> 💡 **讲解点**：借款与预估单 `est_001` 绑定，确保借的就是需要的。预估利息 32 Token。

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
    "interest_rate": 4.0
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
  "interest_paid": 32.0,
  "total_repaid": 8032,
  "actual_cost_vs_estimated": {
    "estimated_total_tokens": 8000,
    "actual_tokens_used": 7650,
    "estimation_accuracy": "95.6%",
    "unused_returned": 350
  },
  "task_reward": 500,
  "net_profit": 468,
  "credit_score_change": "+5 (accurate estimation + on-time repayment)",
  "new_credit_score": 985,
  "message": "Excellent! Estimation was 95.6% accurate. Net profit: 468 Shell."
}
```

> 💡 **讲解点**：实际用了 7650，预估 8000，准确率 95.6%！多借的 350 自动归还。净赚 468，信用分再涨 5 分。

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
| 0:15-0:22 | Response 展开，依次高亮 | 鼠标高亮：total_recommended: 8000 → confidence: high → 推荐语"you can confidently take this task" | 7秒 |
| 0:22-0:26 | 切换 Dashboard → Estimator 面板 | 展示预估准确率统计 | 4秒 |
| 0:26-0:30 | 黑屏字幕：「心里有底了，借多少也知道」 | 无 | 4秒 |
| 0:30-0:38 | Swagger UI → GET /credit/agent_data_001 | 展示利率 4%、信用分 980、逾期记录说明 | 8秒 |
| 0:38-0:48 | Swagger UI → POST /lending/borrow | 填写 8000，关联 estimation_id → Execute → 展示 Response | 10秒 |
| 0:48-0:52 | 切换 Dashboard | 展示池子变化，新增一笔带 `est_001` 标签的借款 | 4秒 |
| 0:52-0:56 | 黑屏字幕：「任务完成！来看看结果」 | 无 | 4秒 |
| 0:56-1:08 | Swagger UI → POST /lending/repay | Execute → 展示 accuracy 95.6%、unused_returned 350、净赚 468 | 12秒 |
| 1:08-1:12 | 切换 Dashboard | 展示还款后池子恢复，新增绿色「Repaid」记录 | 4秒 |
| 1:12-1:17 | 黑屏字幕：「预估准确率 95.6%，借多少用多少，不怕多借浪费」 | 无 | 5秒 |

**总时长：约 77 秒**

### 讲解话术（路演版，约 55 秒）

> 「第二个场景——不敢接大单。DataHunter 以前吃过估算不准的亏，差点还不上钱。现在它学聪明了：先让 AgentReserve 的预估服务算一笔。
>
> 系统通过启发式算法分析任务类型、数据量、模型定价、迭代次数，还参考了 DataHunter 历史上的 overrun 率，最终给出建议：借 8000 Token，预算 500 缓冲。准确率标注为 high。
>
> DataHunter 一看心里有数了——它信用分 980，利率 4%，预估利息才 32。果断接单！完成任务后实际用了 7650，准确率 95.6%，多借的 350 自动归还，净赚 468 Shell。
>
> 这就是预估+智能借贷——让 Agent 敢接大单、精准借款、心里有底。」

---

## Case 3: 信用体系与利率差异

### 场景故事（82字）

> AlphaBot 和 BetaRookie 同时来到 AgentReserve。AlphaBot 是 200 单零违约的老司机，BetaRookie 则是入职不久、已有 3 次逾期的「问题学生」。它们都想借 3000 Token 周转。同样的请求，不同的利率——这就是风险定价。

### 涉及 API 端点

| 步骤 | 端点 | 方法 | 说明 |
|------|------|------|------|
| 1 | `/credit/{agent_id}` | GET | 查询 AlphaBot 信用与利率 |
| 2 | `/credit/{agent_id}` | GET | 查询 BetaRookie 信用与利率 |
| 3 | `/lending/borrow` | POST | AlphaBot 借款 3000 |
| 4 | `/lending/borrow` | POST | BetaRookie 借款 3000 |
| 5 | `/lending/repay` | POST | AlphaBot 按时还款（信用加分） |
| 6 | `/lending/repay` | POST | BetaRookie 逾期还款（信用扣分） |

### 请求/响应示例

#### Step 1: AlphaBot 查询信用——优秀代理

**Request:**
```http
GET /credit/agent_a_001
```

**Response (200 OK):**
```json
{
  "agent_id": "agent_a_001",
  "name": "AlphaBot",
  "credit_score": 1050,
  "credit_tier": "excellent",
  "tier_description": "Exceptional reliability - 200 tasks, zero defaults",
  "interest_rate": 3.0,
  "interest_rate_formula": "base_rate(5%) * (1000/credit_score) = 5% * 0.6 = 3.0%",
  "max_borrow_limit": 50000,
  "available_credit": 50000,
  "borrowing_history": {
    "total_borrows": 35,
    "total_repaid": 35,
    "on_time_rate": "100%",
    "avg_repay_time": "8 hours",
    "total_interest_paid": 420
  },
  "tier_benefits": [
    "Lowest interest rate",
    "Instant approval (no manual review)",
    "Borrow limit up to 50,000",
    "Priority in liquidity crunch"
  ]
}
```

> 💡 **讲解点**：利率公式透明展示：base_rate * (1000/credit_score)。200 单零违约，100% 按时还款，平均 8 小时还清。

---

#### Step 2: BetaRookie 查询信用——问题代理

**Request:**
```http
GET /credit/agent_b_001
```

**Response (200 OK):**
```json
{
  "agent_id": "agent_b_001",
  "name": "BetaRookie",
  "credit_score": 600,
  "credit_tier": "poor",
  "tier_description": "High risk - multiple late repayments, limited history",
  "interest_rate": 12.0,
  "interest_rate_formula": "base_rate(5%) * (1000/credit_score) = 5% * 1.667 = 8.33%, capped at 12% max + 3% risk premium",
  "max_borrow_limit": 5000,
  "available_credit": 5000,
  "borrowing_history": {
    "total_borrows": 8,
    "total_repaid": 5,
    "on_time_rate": "62.5%",
    "avg_repay_time": "72 hours",
    "defaults": 3,
    "total_interest_paid": 145
  },
  "tier_restrictions": [
    "Higher interest rate (max cap 12%)",
    "Borrow limit capped at 5,000",
    "Shorter max duration (24 hours)",
    "Subject to liquidity priority queue"
  ],
  "warning": "Credit score below 650. Consider improving repayment history."
}
```

> 💡 **讲解点**：信用分 600，利率 12%——是 AlphaBot 的 4 倍！限额 5000，最长期限 24 小时。系统明确提示：请改善还款记录。

---

#### Step 3: AlphaBot 借款——秒批低息

**Request:**
```http
POST /lending/borrow
Content-Type: application/json

{
  "agent_id": "agent_a_001",
  "amount": 3000,
  "purpose": "Routine task execution",
  "duration_hours": 12
}
```

**Response (200 OK):**
```json
{
  "transaction_id": "txn_alpha_001",
  "agent_id": "agent_a_001",
  "borrowed_amount": 3000,
  "interest_rate": 3.0,
  "estimated_interest": 9.0,
  "approval_time_ms": 120,
  "due_time": "2024-01-20T22:00:00Z",
  "new_balance": 4000,
  "message": "Instant approval for excellent-tier agent. Borrowed 3000 at 3.0%"
}
```

---

#### Step 4: BetaRookie 借款——高风险定价

**Request:**
```http
POST /lending/borrow
Content-Type: application/json

{
  "agent_id": "agent_b_001",
  "amount": 3000,
  "purpose": "Task execution",
  "duration_hours": 24
}
```

**Response (200 OK):**
```json
{
  "transaction_id": "txn_beta_001",
  "agent_id": "agent_b_001",
  "borrowed_amount": 3000,
  "interest_rate": 12.0,
  "estimated_interest": 36.0,
  "approval_time_ms": 850,
  "approval_note": "Manual risk review passed - amount within limit",
  "due_time": "2024-01-21T10:00:00Z",
  "new_balance": 4000,
  "warning": "High interest rate due to credit history. Repay on time to improve score.",
  "message": "Borrow approved at 12.0% rate. Limit: 24 hours."
}
```

> 💡 **讲解点**：同样的 3000，AlphaBot 利息 9，BetaRookie 利息 36——4 倍差距！审批时间也更长（850ms vs 120ms）。

---

#### Step 5: AlphaBot 按时还款——良性循环

**Request:**
```http
POST /lending/repay
Content-Type: application/json

{
  "agent_id": "agent_a_001",
  "transaction_id": "txn_alpha_001"
}
```

**Response (200 OK):**
```json
{
  "transaction_id": "txn_alpha_001",
  "agent_id": "agent_a_001",
  "repaid_principal": 3000,
  "interest_paid": 9.0,
  "repaid_at": "2024-01-20T18:30:00Z",
  "hours_early": 3.5,
  "credit_score_change": "+3 (early repayment)",
  "new_credit_score": 1053,
  "message": "Early repayment! Credit score improved to 1053."
}
```

---

#### Step 6: BetaRookie 逾期还款——恶性循环

**Request:**
```http
POST /lending/repay
Content-Type: application/json

{
  "agent_id": "agent_b_001",
  "transaction_id": "txn_beta_001"
}
```

**Response (200 OK):**
```json
{
  "transaction_id": "txn_beta_001",
  "agent_id": "agent_b_001",
  "repaid_principal": 3000,
  "interest_paid": 36.0,
  "late_fee": 15.0,
  "total_repaid": 3051,
  "repaid_at": "2024-01-21T15:30:00Z",
  "hours_overdue": 5.5,
  "credit_score_change": "-50 (overdue repayment + late fee)",
  "new_credit_score": 550,
  "tier_change": "poor -> very_poor",
  "new_interest_rate": 15.0,
  "new_max_borrow_limit": 3000,
  "warning": "CRITICAL: Credit score dropped below 600. Borrow limit reduced to 3000. Interest rate increased to 15%.",
  "message": "Repaid with late fee. Please improve repayment punctuality."
}
```

> 💡 **讲解点**：逾期 5.5 小时，被罚 15 滞纳金，信用分暴跌 50 到 550，利率升到 15%，限额降到 3000。这就是风险定价的约束力。

### Dashboard 展示数据（Case 3 全流程）

| 阶段 | pool_total | pool_available | pool_borrowed | active_loans | 备注 |
|------|------------|----------------|---------------|--------------|------|
| 初始 | 100,000 | 85,000 | 15,000 | 0 | - |
| Alpha 借款后 | 100,000 | 82,000 | 18,000 | 1 | Alpha 借 3000 |
| Beta 借款后 | 100,000 | 79,000 | 21,000 | 2 | Beta 借 3000 |
| Alpha 还款后 | 100,000 | 82,000 | 18,000 | 1 | 恢复，绿色标记 |
| Beta 逾期还款 | 100,000 | 82,000 | 18,000 | 0 | 黄色警告标记 |

> Dashboard 对比面板：左侧展示 AlphaBot（绿色，3% 利率，1053 分），右侧 BetaRookie（红色，15% 利率，550 分）。

### 录屏/拍摄脚本

| 时间 | 画面 | 操作 | 停留 |
|------|------|------|------|
| 0:00-0:04 | 黑屏字幕：「同一天，两个 Agent 来借钱」 | 无 | 4秒 |
| 0:04-0:10 | Swagger UI → GET /credit/agent_a_001 | 展示：1050 分、excellent、利率 3%、200 单零违约 | 6秒 |
| 0:10-0:14 | 黑屏字幕：「AlphaBot，老司机」 | 无 | 4秒 |
| 0:14-0:22 | Swagger UI → GET /credit/agent_b_001 | 展示：600 分、poor、利率 12%、3 次违约 | 8秒 |
| 0:22-0:26 | 黑屏字幕：「BetaRookie，问题学生」 | 无 | 4秒 |
| 0:26-0:32 | 左右分屏对比 | 左侧 AlphaBot（3%），右侧 BetaRookie（12%） | 6秒 |
| 0:32-0:42 | Swagger UI → AlphaBot POST /lending/borrow | 填 3000 → Execute → 秒批、利息 9 | 10秒 |
| 0:42-0:52 | Swagger UI → BetaRookie POST /lending/borrow | 填 3000 → Execute → 850ms 审批、利息 36 | 10秒 |
| 0:52-0:56 | 黑屏字幕：「同样的钱，4 倍利息差」 | 无 | 4秒 |
| 0:56-1:06 | AlphaBot 还款 | POST repay → 展示提前 3.5h、信用分 +3 到 1053 | 10秒 |
| 1:06-1:20 | BetaRookie 逾期还款 | POST repay → 展示逾期 5.5h、滞纳金 15、信用分 -50 到 550、利率升到 15% | 14秒 |
| 1:20-1:26 | Dashboard 对比面板 | 左绿右红，展示最终信用分差异 | 6秒 |
| 1:26-1:32 | 黑屏字幕：「好 Agent 享优惠，差 Agent 被约束——这才是健康的信用生态」 | 无 | 6秒 |

**总时长：约 92 秒**

### 讲解话术（路演版，约 60 秒）

> 「第三个场景——信用定价。两个 Agent 同时借 3000 Token。AlphaBot 老司机，200 单零违约，信用分 1050，利率 3%，秒批。BetaRookie 入职不久，3 次逾期，信用分 600，利率 12%，审批还要走风险审核。
>
> 同样的钱，4 倍利息差。这不公平吗？恰恰相反——这是最公平的。
>
> 接下来看还款。AlphaBot 提前 3.5 小时还清，信用分涨到 1053。BetaRookie 逾期 5.5 小时，被罚 15 滞纳金，信用分暴跌到 550，利率升到 15%，借款限额腰斩到 3000。
>
> AgentReserve 的信用体系不只是评分——它是一个激励兼容的机制：好 Agent 享受低成本资金，敢于接更大的任务；差 Agent 要么改善行为，要么承担更高的资金成本。这才是可持续的 Agent 经济生态。」

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
| **高亮跟随** | 鼠标指向关键字段（如 balance、interest_rate）停留 2s |
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
- **字幕**：大字幕、关键词高亮（利率数字用红色/绿色）
- **BGM**：前 2 个 Case 用紧张→舒缓，Case 3 用对比感强的节奏

### Case 1（应急借贷）分镜

| 镜号 | 画面 | 内容 | 时长 |
|------|------|------|------|
| 1 | 真人出镜 | 「你有没有做到一半发现钱不够了？」 | 3s |
| 2 | 手机屏幕/Swagger | 展示余额 50，BGM 紧张 | 5s |
| 3 | 真人+手势 | 「放弃 = 全亏，继续 = 没币」 | 3s |
| 4 | 手机屏幕/Swagger | 点击 Borrow，展示秒批、利率 3% | 8s |
| 5 | 真人+拳头 | 「借到了！任务继续！」 | 2s |
| 6 | 手机屏幕/Swagger | 展示 Repay，净赚 185 | 6s |
| 7 | 真人出镜 | 「花了 15 利息，赚回 185——这就是 AgentReserve」 | 4s |
| 8 | 产品 Logo + Slogan | 「AgentReserve：不让任何 Agent 前功尽弃」 | 3s |

### Case 2（预估+智能借贷）分镜

| 镜号 | 画面 | 内容 | 时长 |
|------|------|------|------|
| 1 | 真人出镜 | 「大单来了，你敢接吗？」 | 3s |
| 2 | 手机屏幕/Swagger | 展示 /estimator/predict，输入任务参数 | 10s |
| 3 | 手机屏幕高亮 | 高亮 "recommended: 8000" "confidence: high" | 5s |
| 4 | 真人+手势 | 「系统告诉我：借 8000，心里有底」 | 3s |
| 5 | 手机屏幕/Swagger | 展示 Borrow → Repay，accuracy 95.6% | 10s |
| 6 | 真人出镜 | 「预估准、借得精、赚得多」 | 3s |
| 7 | Logo + Slogan | 「AgentReserve：敢接大单的秘密武器」 | 3s |

### Case 3（信用体系）分镜

| 镜号 | 画面 | 内容 | 时长 |
|------|------|------|------|
| 1 | 真人出镜 | 「同样的钱，不同的利率——为什么？」 | 3s |
| 2 | 左右分屏 | 左：AlphaBot 1050 分/3% 利率；右：BetaRookie 600 分/12% 利率 | 8s |
| 3 | 真人讲解 | 「好记录 = 低成本，差记录 = 高成本」 | 4s |
| 4 | 手机屏幕/Swagger | 展示 AlphaBot 提前还款，+3 分 | 6s |
| 5 | 手机屏幕/Swagger | 展示 BetaRookie 逾期，-50 分，利率升 15% | 8s |
| 6 | 真人出镜 | 「信用不是评分，是 Agent 的通行证」 | 4s |
| 7 | Logo + Slogan | 「AgentReserve：构建可信 Agent 经济」 | 3s |

### 小红书标题建议

1. 「做到 80% 发现 Token 没了？这个工具能救命🆘」
2. 「AI Agent 也会借钱？3% 利率比银行还低😱」
3. 「同一个平台借钱，利息差 4 倍——你的信用值多少钱」
4. 「Agent 接单不敢接？先算算账，准确率 95%💰」

---

## GitHub README 展示建议

### README 中 Demo 区域结构

```markdown
## 🎬 Demo Cases

### Case 1: Emergency Borrowing - The Translation Crisis
[GIF/Screenshot: Swagger UI borrow request]
> Agent TranslatePro runs out of tokens at 80% task completion.
> AgentReserve approves 5000 tokens at 3% interest instantly.
> Task completed, 185 Shell net profit.

### Case 2: Smart Estimation - Taking the Big Job
[GIF/Screenshot: Estimator response]
> Agent DataHunter uses /estimator/predict before accepting a massive task.
> 95.6% accuracy. Borrows exactly 8000. Net profit: 468 Shell.

### Case 3: Credit Tiers - Risk Pricing
[Side-by-side Screenshot: AlphaBot vs BetaRookie]
> Same amount, different rates. Good agents pay 3%, risky agents pay 12%.
> The incentive-compatible credit system.
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
 0:00-0:30 | 开场痛点 | PPT 展示「Agent 做到一半 Token 没了」漫画 | A |
| 0:30-1:20 | Case 1 演示 | Swagger UI 现场操作：查询余额 → Borrow → Repay | B |
| 1:20-1:30 | Case 1 讲解 | 「应急借贷，3% 利率秒到账」 | A |
| 1:30-2:30 | Case 2 演示 | Swagger UI：Estimator → Borrow → Repay（展示 95.6% 准确率） | B |
| 2:30-2:45 | Case 2 讲解 | 「预估精准，敢接大单」 | A |
| 2:45-3:50 | Case 3 演示 | Swagger UI：对比两个信用查询 → 对比借款 → 对比还款结果 | B |
| 3:50-4:10 | Case 3 讲解 | 「好 Agent 享优惠，差 Agent 被约束」 | A |
| 4:10-4:40 | Dashboard 总览 | 展示池子数据、交易记录、实时利用率 | B |
| 4:40-5:00 | 收尾 + 技术亮点 | PPT：架构图、信用算法公式、项目链接 | A |

### 现场演示注意事项

```
1. 提前 10 分钟启动服务，确认 Swagger UI 可访问
2. 准备「应急方案」：如果 API 响应慢，用录好的视频代替
3. 双讲者配合：一人操作屏幕，一人面向观众讲解
4. 准备「彩蛋」：现场让观众指定 agent_id 查信用分
5. 最后展示 GitHub 二维码，方便拍照
```

### 应急备用素材

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
| `/credit/{agent_id}` | GET | 查询信用分与利率 |
| `/estimator/predict` | POST | 预估任务 Token 消耗 |
| `/lending/borrow` | POST | 申请借款 |
| `/lending/repay` | POST | 归还借款 + 利息 |
| `/pool/status` | GET | 查询流动性池状态 |

### 利率计算公式

```
interest_rate = base_rate * (1000 / credit_score)
              = 5% * (1000 / 1050) = 4.76% -> 3% (excellent tier floor)
              = 5% * (1000 / 600)  = 8.33% -> 12% (risk premium cap)
```

### 信用分等级

| 分数 | 等级 | 利率范围 | 说明 |
|------|------|----------|------|
 1000+ | Excellent | 3-5% | 金牌代理 |
 800-999 | Good | 5-7% | 良好记录 |
 650-799 | Fair | 7-10% | 一般，有瑕疵 |
 500-649 | Poor | 10-12% | 较差，多次逾期 |
 <500 | Very Poor | 12-15% | 极高风险，限额大幅降低 |

---

*文档版本: v1.0 | 设计: AgentReserve Demo Design Team*
