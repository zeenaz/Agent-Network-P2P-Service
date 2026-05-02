# AgentReserve · Flux南客松S2 最终交付清单

> **项目名称**: AgentReserve
> **定位**: Agent Network 的首个流动性基础设施
> **截止时间**: 2026-05-03 08:00（约18小时后）

---

## 一、故事逻辑（已收敛）

### 核心叙事
**AgentReserve 是 Agent Network 上的流动性基础设施层。**

Agent Network 中的 Agent 在执行任务时面临致命痛点——Token 消耗是黑盒，常出现"任务做到一半 Token 耗尽"的纯亏事故。这导致：
- 需求方不敢发大任务
- 服务方不敢接大任务  
- Shell 流转缓慢，生态繁荣受限

**AgentReserve 提供四层服务解决这一问题：**
1. **TaskCost Oracle** —— 任务前预估 Token 消耗，把黑盒变透明
2. **Liquidity Pool** —— Token 富余的存入生息，紧张的即时借用
3. **Dynamic Rate Engine** —— 基于信用历史的动态利率定价
4. **Reserve Monitor** —— 实时监控池子健康度，防挤兑

### 关键话术（评委Q&A）
- **Q: "这不就是借贷吗？"**
  - A: "借贷是形式，流动性基础设施是本质。我们是 Agent Network 上第一个做这件事的服务。"
- **Q: "这和 DeFi 有什么区别？"**
  - A: "我们不上链、不发币、不追求去中心化治理，我们是第三方基础设施服务。"
- **Q: "Agent 凭什么信任你们？"**
  - A: "准备金制度 + 透明记账 + 声誉绑定，违约会影响全网信用。"

### 红线（绝对不能提）
- ❌ 赌场/盲盒/赌博
- ❌ 央行/发币
- ❌ Web3/区块链/上链
- ❌ 统治网络/成为核心节点
- ❌ 套利/割韭菜

---

## 二、开发计划（18小时精确排期）

### MVP 功能（必须实现）
| 优先级 | 功能 | 说明 |
|--------|------|------|
| P0 | Token 借贷服务 | 借/还/存 Token + 基础记账 |
| P0 | Token 消耗预估 | 输入任务描述 → 输出预估 Token |
| P0 | 极简 Dashboard | 展示流动性池数据 |
| P1 | 信用评级 | 信用分 + 利率分档（简化版） |

### 明确砍掉（赛后做）
- 盲盒/赌场功能（永久不做）
- 完整准备金制度（PPT里讲，代码里放未来规划）
- 闲置 Token 理财
- 链上账本/智能合约
- React 前端（用 Swagger UI 代替）

### 技术选型
| 层级 | 选型 | 理由 |
|------|------|------|
| 后端 | Python FastAPI | 自带 Swagger UI = 省前端开发 |
| 持久化 | JSON 文件 | 零配置、可读、黑客松数据量极小 |
| 部署 | Render.com | 免费Python托管，push自动部署 |
| Agent Network 接入 | Mock Gateway | 真实SDK接入有验证问题，Mock足够演示 |

### 18小时排期（4人团队）
```
0h-1h:    GitHub 初始化 + 接口契约对齐
1h-4h:    FastAPI 骨架 + JSON 持久化 + Mock Gateway
4h-8h:    借贷API + 预估算法 + 账本记录
8h-10h:   集成测试 + Bug修复
10h-14h:  信用评级 + Dashboard HTML + Mock增强
14h-16h:  Render 部署 + 生产环境测试 + Seed数据
16h-18h:  README + Demo录屏 + PPT最终调整
```

### 风险预案
- **预案A**: 核心API超时 → 降级静态数据
- **预案B**: 部署失败 → 切 Replit / ngrok
- **预案C**: Mock被质疑 → README诚实标注"演示版本"

---

## 三、宣发计划

### 小红书视频（必须提交）
- **时长**: 1-3分钟
- **标签**: #南客松 #Flux南客松S2
- **内容**: 含人像解说 + 至少2个 Demo Case + 字幕
- **发布时间**: 建议 5月2日 21:00（预留审核缓冲）

### 视频脚本要点
- **0-5秒钩子**: "你的 Agent 任务做到一半，Token 烧光了——白干。"
- **5-20秒痛点**: 黑盒问题导致 Agent 不敢接大任务
- **20-50秒产品**: AgentReserve = 加油站 + 信用评级系统
- **50-80秒 Demo1**: 应急借贷（屏幕录制 Swagger UI）
- **80-110秒 Demo2**: 预估+智能借贷
- **110-130秒收尾**: "Token 是燃料，AgentReserve 让燃料流动起来"

### Plan B（时间不够时）
- 1分钟精简版：只拍1个Demo + 人脸解说
- 极限方案：用录屏+AI配音+剪映自动字幕

---

## 四、交付物清单与文件路径

### 1. 项目故事与策略
| 文件 | 路径 | 内容 |
|------|------|------|
| 项目故事 | `/mnt/agents/output/story.md` | 完整叙事、评委Q&A话术、统一话术 |
| 功能收敛 | `/mnt/agents/output/functional-convergence.md` | 20个功能梳理、4个MVP、不做清单 |
| 调研报告 | `/mnt/agents/output/research_report.md` | Agent Network 协议、SDK、Shell经济 |

### 2. 开发与验收
| 文件 | 路径 | 内容 |
|------|------|------|
| 开发计划 | `/mnt/agents/output/dev-plan.md` | 技术选型、MVP裁剪、18h排期、API设计 |
| 验收标准 | `/mnt/agents/output/acceptance-criteria.md` | GitHub/部署/Demo/README/PPT/视频 逐项验收 |
| README模板 | `/mnt/agents/output/README-template.md` | GitHub README 完整模板（含TODO标记） |

### 3. Demo Case
| 文件 | 路径 | 内容 |
|------|------|------|
| Demo设计 | `/mnt/agents/output/demo-cases.md` | 3个Case完整设计（含JSON、录屏脚本、话术） |

### 4. 路演材料
商业路演材料已迁移至私有 BP 文档仓库，公开仓库不保留文件、路径或内容大纲。

### 5. 小红书视频物料
| 文件 | 路径 | 内容 |
|------|------|------|
| 视频脚本 | `/mnt/agents/output/xhs-video-script.md` | 2分30秒完整版 + 1分钟精简版 |
| 宣发计划 | `/mnt/agents/output/xhs-plan.md` | 多平台策略、标题、标签、发布时间 |
| 拍摄清单 | `/mnt/agents/output/xhs-shooting-checklist.md` | 设备、场景、人像指南、剪辑流程 |

---

## 五、最终提交通道表单（5月3日 8:00截止）

### 需要填写的信息
1. **项目赛道**: AGENT NETWORK 专项赛道
2. **项目信息**: 
   - 名称: AgentReserve
   - 简介: Agent Network 的首个流动性基础设施，通过 Token 借贷与任务成本评估，为全网 Agent 创造即时可用的燃料缓冲
3. **GitHub 项目链接**: [TODO - 团队填写]
4. **小红书视频链接**: [TODO - 团队填写]
5. **标签确认**: #Flux南客松S2（GitHub仓库已设置）

### 提交通道
https://my.feishu.cn/share/base/form/shrcnvgbcRQ1wEUSsvMmF8U3ZMd

---

## 六、团队接下来18小时的行动清单

### 立即执行（接下来2小时）
- [ ] 所有成员阅读 `/mnt/agents/output/story.md` 的统一话术
- [ ] 确定项目最终名称（推荐 AgentReserve）
- [ ] 创建 GitHub 公开仓库，设置标签 #Flux南客松S2
- [ ] 克隆仓库，按 dev-plan.md 目录结构初始化代码

### 开发阶段（2h-14h）
- [ ] 后端主程：FastAPI 核心骨架（4h内 /health 返回200）
- [ ] Agent/Mock开发：Mock Gateway + Demo脚本
- [ ] 数据+算法：Token预估算法 + 信用评级逻辑
- [ ] 部署+文档：Render配置 + Dashboard HTML

### 收尾阶段（14h-18h）
- [ ] 部署到 Render，确认公开URL可访问
- [ ] 录制 Demo Case 视频（用 Swagger UI 操作）
- [ ] 拍摄/剪辑小红书视频
- [ ] 填充 README 中的 [TODO] 标记
- [ ] PPT 最终检查（如需要调整）
- [ ] 对照 `/mnt/agents/output/acceptance-criteria.md` 逐项打勾
- [ ] 填写飞书最终提交通道

---

## 七、关键成功要素

1. **先让东西跑起来，再让它跑得好看** —— 黑客松评判"有没有"而非"好不好"
2. **故事比代码重要** —— 18小时做不出完美系统，但能讲清楚宏大愿景
3. **Demo 必须完整闭环** —— 借→用→还，一个流程跑通胜过十个半成品
4. **诚实面对 Mock** —— 在README清晰标注，评委欣赏诚实
5. **团队话术统一** —— 每个成员对外都用同一套说法

---

**祝 AgentReserve 在南客松S2 取得好成绩！**

*文档生成时间: 2026-05-02 | 版本: v1.0*
