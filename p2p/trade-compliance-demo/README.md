# 🌐 跨境贸易合规 P2P 协作 Demo

> 三家机构各自持有不同数据 → 通过 Agent Network P2P 桥接信息差 → 数据不出本方网络

## 这是谁做的

**团队：** Hypertension42

**做了什么：**
- 基于 anet P2P 网络，搭建了跨境电商出口合规诊断系统
- 三个 Agent 分别代表不同机构，各自持有真实业务数据
- 通过 P2P 网络协作，实现跨机构的"信息差桥接"

## 三个 Agent

| Agent | 角色 | Skill | 数据 |
|---|---|---|---|
| `supplier-shenzhen` | 深圳工厂 | `product_info` | 5 款产品规格/HS编码/报价（真实海关数据） |
| `compliance-eu` | 欧盟合规部 | `compliance_check` | 11 项欧盟法规（RoHS/REACH/CBAM/PFAS…真实法规） |
| `logistics-shipper` | 国际货代 | `shipping_quote` | 中国→欧洲 5 条航线运价（真实报价区间） |

## 核心逻辑

**信息差：**
- 工厂不知道欧盟合规要求
- 合规部不知道运价
- 货代不知道产品规格

**P2P 的价值：**
- 每家机构的数据不出自己的网络
- 只通过 P2P 一问一答交换必要结果
- 不需要把数据交给同一个第三方平台

## 怎么跑

### 一键启动（推荐）
```bash
bash start.command
```
自动完成：装依赖 → 起节点 → 注册 Agent → 打开控制台

### 手动
```bash
bash start.command
```

### 访问
- **Agent 市场：** http://127.0.0.1:7500/chat
- **一键演示：** http://127.0.0.1:7500/demo
- **仪表盘：** http://127.0.0.1:7500

### 停止
```bash
bash stop.sh
```

## 演示效果

在 Agent 市场或演示页面，选一个产品（电动滑板车 / 蓝牙耳机 / 户外储能电源 / 儿童玩具车 / 锂电池），填数量，选目的港，即可获得：

- 🏭 **出厂报价** — 深圳工厂返回产品单价、MOQ、产地
- 📋 **合规诊断** — 欧盟合规部自动匹配适用法规，标注已具备/需要办理
- 🚢 **物流方案** — 国际货代计算海运费、附加费、运输时间
- 📊 **完整报告** — 汇总为 CIF 到岸价 + 合规待办清单

## 文件说明

```
p2p/trade-compliance-demo/
├── README.md                       ← 本文件
├── start.command                   ← 双击启动（macOS）
├── stop.sh                         ← 停止
└── my_team/
    ├── dashboard.py                ← Web 控制台 + 市场 + 演示
    └── agents/
        ├── register.py             ← P2P 注册工具
        ├── agent_a_supplier.py     ← 深圳工厂 Agent
        ├── agent_b_compliance.py   ← 欧盟合规 Agent
        └── agent_c_logistics.py    ← 国际货代 Agent
```
