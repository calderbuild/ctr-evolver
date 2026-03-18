# cohort0

1. research proposals（the deeper parts of what it means to build grounded reasoning agents,；if you are interesting）

2. i ask that you present your solution demo or at least a solution proposal.

3. codex，claude code or other

4. openhands 等等是他们的好朋友

ideas：

挑战：

1. office qa benchmark

2. ![](/Users/calder/Library/Application%20Support/marktext/images/2026-03-15-11-16-36-image.png)

![](/Users/calder/Library/Application%20Support/marktext/images/2026-03-15-11-17-20-image.png)

![](/Users/calder/Library/Application%20Support/marktext/images/2026-03-15-11-17-57-image.png)

![](/Users/calder/Library/Application%20Support/marktext/images/2026-03-15-11-20-10-image.png)

![](/Users/calder/Library/Application%20Support/marktext/images/2026-03-15-11-21-53-image.png)

![](/Users/calder/Library/Application%20Support/marktext/images/2026-03-15-11-22-29-image.png)

![](/Users/calder/Library/Application%20Support/marktext/images/2026-03-15-11-22-42-image.png)

![](/Users/calder/Library/Application%20Support/marktext/images/2026-03-15-11-22-57-image.png)

![](/Users/calder/Library/Application%20Support/marktext/images/2026-03-15-11-26-54-image.png)

![](/Users/calder/Library/Application%20Support/marktext/images/2026-03-15-12-22-05-image.png)

![](/Users/calder/Library/Application%20Support/marktext/images/2026-03-15-12-23-13-image.png)

以下是关于 Sentient Arena Cohort 0 启动仪式视频的全面细节拆解。内容涵盖了赛事背景、核心技术挑战、五场技术基础设施演讲的深度细节，以及具体的评审与研究方向要求。

### 赛事背景与核心挑战

Sentient Labs 举办此次 Hackathon 的核心目标是通过自动化 AI 研发流程，推动 AI 的 Grounded Reasoning（基石推理）能力。Cohort 0 从超过 1000 名申请者中筛选了 126 人参与。

**核心考题：Databricks Office QA Benchmark**

- **任务本质：** 针对经过解析的 SEC filings（美国证券交易委员会文件）进行复杂的问答与数据聚合。这在金融和企业合规领域具有极高的经济价值。

- **当前痛点：** 现有的前沿模型（包括 Claude Code 开箱即用状态）在该基准测试中最困难子集的通过率不到 25%。

- **解题思路：** 官方要求参赛者不要仅仅构建静态的工作流，而是要将 OpenHands、CodeX、Aider 等开源 Coding Harnesses 作为 Skills 整合进自定义的 Agent 架构中进行解题。

---

### 关键技术演讲与基础设施剖析

#### 1. OpenHands：构建处理大规模语料的 Agent

Shia 介绍了 OpenHands（前身为 OpenDevin）的核心架构与实践。

- **核心组件：** 包含 SaaS 应用、CLI 工具以及在本次比赛中最关键的 SDK。SDK 允许开发者剥离其内置的编码设定，并注入自定义的推理逻辑。

- **架构流：** 开发者可以配置 Terminal、FileEditor、TaskTracker 等工具给 Agent。Agent 负责调用后端大模型、执行任务、获取结果并整合。

- **性能演示：** 现场展示了一个耗时 45 分钟构建的 Agent。该 Agent 能够克隆包含约 1.2 万行代码的代码库，自主遍历并阅读所有文件，生成完整的说明文档，并最终通过 Mintlify 在本地启动文档服务器。该过程耗时约 12 分钟，API 成本为 3.50 美元。

#### 2. Sentient 内部框架：EVO Skills

Meet 介绍了用于 Agent 自我进化的闭环系统，旨在解决 Skills 或 Prompt 随时间推移而失效（Stale）的问题。

- **系统机制：** 这是一个自动化的自我改进闭环，包含五个核心模块：
  
  1. **Base Agent：** 执行核心任务的底层 Agent。
  
  2. **Proposer：** 分析基准测试的运行结果，提出改进意见。
  
  3. **Generator：** 根据提案生成新的 Skills 或 System Prompt。
  
  4. **Evaluator：** 在 Git branches 或 worktrees 的隔离环境中测试生成的代码。
  
  5. **Frontier：** 并行运行测试，选拔出性能最优的方案合并至主分支。

- **模型偏好：** 官方实测发现，该进化框架与 Claude 3.5 Sonnet 配合效果最佳。Opus 成本过高，投入产出比不佳。

#### 3. Daytona：AI 代码执行的弹性基础设施

Steipe 讲解了如何安全地运行 Agent 生成的不可靠代码。

- **核心特性：** 提供底层全栈控制，沙箱启动时间不到 90 毫秒。支持大规模并行化（Massive Parallelization），可在一秒内拉起上千个 Agents。

- **Stateful 设计：** 与通常生命周期只有几十分钟的云环境不同，Daytona 的沙箱具有持久性，可以持续运行数月，非常适合长时间的强化学习训练或长期运行的 Agent。

- **SDK 与扩展能力：** 提供 File system toolbox、Git toolbox 和 Sandbox volumes（用于在不同沙箱间共享大规模数据集）。同时支持 Computer Use，允许 Agent 在沙箱内操控 Windows、Linux 或 Android 系统的图形界面。

#### 4. Datalus Labs：Multi-Agent 架构与商业化协议

CEO Kathy 提出了关于 Agent 架构的系统性思考，并发布了相关基础设施。

- **非线性与非确定性：** 她强调真正的 Agent 不是固定的工作流（Workflow），也不是简单的模型封装。Agent 必须由大脑（Models）和身体（Tools）组成，能够应对复杂的现实世界。

- **Multi-Agent 协作范式：** 理想的架构由一个具备全局上下文的 Parent Agent 负责目标拆解，并调用多个具备独立运行环境、特定模型和动态权限范围（Dynamic Access）的 Sub-agents 执行具体任务。

- **基础设施建设：** * 实现了 MCP (Model Context Protocol) 以及 A2A (Agent-to-Agent) 通信层。
  
  - 发布了 **dAuth**：一个多租户的 MCP OAuth 解决方案，用于解决 Agent 调用外部工具或互相调用时的动态权限管理，防止密钥泄露。
  
  - 预告即将推出基于 Stripe 的 Agent Extensions Marketplace，以及 "Agent as a Service" 托管功能。

#### 5. Alphacive：重塑学术研究的 Artifacts

Rahan 探讨了 AI 将如何彻底改变 ML 领域的科研模式。

- **现状痛点：** arXiv 上呈指数级增长的论文导致研究人员无法紧跟前沿。

- **技术演进：** Alphacive 最初作为论文社区，随后引入了 Gemini 2.0 Flash 处理长文本，最终演进出 Deep Research 功能。

- **未来的科研 Artifacts：** 随着 Auto-research 能力的逼近，未来的研究成果不再是一篇 PDF 论文，而是动态的 **Experiment Trees**。Agent 会自主提出假设、选择 RLM（强化学习模型）架构、生成评估数据、并记录“哪些尝试成功了，哪些失败了”。

---

### 交付物要求与高价值研究方向

Oleg 在总结中明确了本次 Hackathon 的具体要求。参赛团队在周末结束时不仅需要提交针对 Office QA 的代码解决方案，还必须提交一份具有深度的研究提案。

官方指定了三个高优先级研究方向：

1. **AI Self-improvement 评估：** 比较近期涌现的自动化工具（如 GAPA、Evolver、Hermes Agent 及 EVO Skills），分析它们在端到端任务中的最佳设计模式。

2. **Transfer Learning 与泛化能力：** 考察针对 Office QA 构建的定制化 Agent 架构，是否能够无缝迁移并解决另一个完全不同的垂直领域基准测试。

3. **Automatic Evaluation：** 静态 Benchmark 无法反映真实业务环境。研究如何让 Agent 基于用户需求和特定数据集，在运行（On the fly）中自动生成评估标准和测试用例。

### 竞赛策略与规则约束

- **成本控制警告：** 官方强烈建议不要在初期直接在完整数据集上运行代码。应切分极小规模的子集进行迭代测试。推荐使用 GLM 4.5 或 Qwen 2.5 等高性能开源模型，或充分利用 Harness 内置的免费额度。

- **评判标准：** 奖金池为 45,000 美元。最终评判是综合性的（Holistic evaluation）。排行榜分数仅是指标之一，一个排名第四但拥有开创性研究提案的团队，可能会击败排名第一的团队获得冠军。
