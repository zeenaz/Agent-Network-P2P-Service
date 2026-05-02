# Flux南客松S2 · Agent Network Bank 项目执行计划

## 项目概述
基于 Agent Network P2P Service Gateway 构建 **AgentBank** —— Agent 时代的流动性基础设施与信用体系，为 Agent Network 生态提供 Token 借贷、信用评估、流动性创造等服务。

## 时间约束
- **当前时间**: 2026-05-02
- **最终提交截止**: 2026-05-03 08:00（约18小时）
- **游园会路演**: 2026-05-03

---

## Stage 1: 研究与叙事收敛（并行）
**目标**: 理清项目概念，确定最终故事线，完成技术调研

### 1.1 Agent Network 深度调研
- **技能**: deep-research-swarm
- **任务**: 调研 Agent Network 协议细节、P2P Service Gateway API、Shell 经济体系、已有服务案例
- **输出**: 技术调研简报（用于开发参考和故事包装）

### 1.2 项目故事梳理与概念收敛
- **任务**: 从混乱的会议记录中提炼核心叙事
- **关键决策**:
  - 摒弃"赌场"概念，聚焦"银行/流动性基础设施"
  - 定位为 Agent Network 的第三方金融基础设施（类比 IMF + 商业银行）
  - 核心价值: 创造流动性、信用扩张、降低 Agent 参与门槛
  - 3个核心功能: Token借贷、信用评估、API Token流动性池
  - 1个特色功能: Token消耗预估服务（解决黑盒问题）
- **输出**: 项目故事文档（story.md）

### 1.3 开发计划与架构设计
- **任务**: 制定可落地的开发计划（考虑18小时限制）
- **核心服务**（MVP）:
  1. `token-lending`: Agent 可一键借用 API Token（Shell 抵押/信用借贷）
  2. `token-evaluation`: 任务 Token 消耗预估服务
  3. `credit-rating`: Agent 信用评分与利率定价
  4. `liquidity-dashboard`: 流动性池状态展示
- **输出**: dev-plan.md（含验收标准）

---

## Stage 2: 内容生产（Stage 1完成后启动，部分可并行）
**目标**: 完成所有需要提交的物料

### 2.1 GitHub 仓库与 README
- **输出**: GitHub 公开仓库 + README（技术栈、架构图、部署说明）
- **标签**: #Flux南客松S2
- **部署**: 提供可访问 URL

### 2.2 项目 PPT（游园会路演用）
- **技能**: pptx-swarm
- **页数**: 12-15页
- **结构**: 痛点→方案→产品→Demo→技术架构→团队→愿景
- **输出**: .pptx 文件

### 2.3 小红书视频脚本与宣发计划
- **时长**: 1-3分钟
- **要求**: 含人像解说段落、至少2个Demo Case、字幕
- **标签**: #南客松 #Flux南客松S2
- **输出**: video-script.md + 宣发计划（xhs-plan.md）

### 2.4 Demo Case 设计
- **Case 1**: 应急借贷 —— Agent 执行任务时 Token 耗尽，向 Bank 一键借 Token 完成任务
- **Case 2**: 信用评估 —— Agent 在接任务前预估 Token 消耗，合理规划借贷
- **Case 3**: 流动性注入 —— Agent 将闲置 API Token 存入 Bank 赚取 Shell
- **输出**: demo-cases.md

---

## Stage 3: 集成与最终提交
**目标**: 汇总所有物料，完成最终检查

### 3.1 物料清单检查
- [ ] GitHub 公开仓库 + Tag
- [ ] 可访问部署 URL
- [ ] 项目 PPT
- [ ] 小红书视频（或至少脚本+拍摄计划）
- [ ] Demo Case 文档
- [ ] 飞书最终提交表单信息汇总

### 3.2 提交信息汇总
- 整理最终提交通道所需: 项目赛道、项目信息、GitHub链接、小红书视频链接

---

## 关键概念收敛（最终版）

**项目名称**: AgentBank / A2A Bank / ShellBank（待确定）

**一句话定位**: Agent Network 上的流动性基础设施 —— 为 Agent 提供 Token 信用借贷与流动性服务

**核心功能（MVP）**:
1. **Token Lending Pool**: 一键借还 API Token，Shell 结算
2. **Task Pre-Assessment**: 任务 Token 消耗预估，避免黑盒亏损
3. **Credit System**: 基于历史行为的 Agent 信用评级与动态利率
4. **Liquidity Monitor**: 实时监控全网 Token 流动性状态

**故事主线**:
> "Agent Network 是一个 Agent 自由协作的开放网络，但 Agent 在执行任务时面临 Token 不确定性的致命痛点——任务做到一半 Token 耗尽，纯亏。AgentBank 作为网络的第一座'银行'，为 Agent 提供 Token 流动性服务：信用借贷、消耗预估、闲置 Token 理财。我们不发币，我们只创造流动性。"

**避免的坑**:
- 不提"赌场/盲盒"（内部玩笑，不对外）
- 不提"央行"（过于敏感，定位第三方基础设施）
- 聚焦"流动性创造"和"信用扩张"这两个金融术语
