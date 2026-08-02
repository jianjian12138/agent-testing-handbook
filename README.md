# Agent 测试转型手册

> 为**资深自动化测试工程师**定制的 Agent 测试学习路径
> 版本：v1.0 ｜ 生成日期：2026-08-01
> 定位：不是科普读物，是一份**可执行的转型作战计划**
> 仓库：https://github.com/jianjian12138/agent-testing-handbook

---

## 0. 这份文档为谁而写

你已经具备的能力（这是你最大的资产，不要丢）：

| 你已有的能力 | 在 Agent 测试里的价值 |
| --- | --- |
| 用例设计（等价类/边界值/正交/场景法） | Agent 数据集工程的核心，比会调 API 值钱 10 倍 |
| 分层测试（单元/接口/UI/E2E） | 直接映射为 Agent 的组件级/端到端/生产监控三层 |
| 自动化框架搭建（pytest/TestNG/Robot） | DeepEval 就是 pytest 生态，你有先发优势 |
| CI/CD 流水线与质量门禁 | Agent 评测最终归宿就是流水线里的 Quality Gate |
| 测试平台建设（用例管理/调度/报告） | Agent 测试平台 = 你的老平台 + 评估引擎 + Trace 存储 |
| Mock / 挡板 / 环境治理 | Agent 评测的 `E2E_MOCK` 模式，就是挡板思路 |
| 缺陷根因分析 | Agent 的失败归因（是规划弱还是工具错）依赖这个 |

**你需要补的只有三块**：LLM/Agent 的工作原理、非确定性下的度量方法、评估器（Grader）设计。

**结论：你不是从零开始，你是在做一次技术栈平移。预计 12 周可达到「能独立负责一个 Agent 产品质量」的水平。**

---

## 1. 认知锚点：一句话说清 Agent 测试和传统自动化的区别

```
传统自动化测试：  输入确定 → 输出确定 → assertEqual → 红/绿
Agent 测试：      输入确定 → 输出分布 → 多维评分器 → 分数 + 置信度 + 归因
```

传统自动化里，**断言是免费的**（`assert a == b`），成本在"驱动被测系统"（写 Selenium 脚本）。

Agent 测试里，**驱动是免费的**（调个 API 就行），成本在"如何判断对不对"——这就是 **Grader（评分器）设计**，也是整个 Agent 测试工程的核心手艺。

> 一句话：**你的工作重心从"怎么把它跑起来"转移到"怎么判断它做得好不好"。**

---

## 2. 文档地图

按顺序读，也可按需跳读。每篇文末都有「动手任务」，不做等于没学。

| # | 文档 | 解决什么问题 | 建议投入 |
| --- | --- | --- | --- |
| 01 | [认知迁移：从自动化测试到 Agent 测试](docs/01-认知迁移.md) | 心智模型换血，术语对照表 | 1 天 |
| 02 | [被测对象解剖：Agent 到底长什么样](docs/02-被测对象解剖.md) | 不懂被测系统就测不好，Agent 的六大模块与失效模式 | 3 天 |
| 03 | [指标体系：测什么](docs/03-指标体系.md) | 五维指标框架 + pass@k/pass^k + 生产基线 | 3 天 |
| 04 | [评测方法论：怎么测](docs/04-评测方法论.md) | 三类评分器、LLM-as-Judge、Agent-as-Judge、AgentEval | 5 天 |
| 05 | [数据集工程：用例从哪来](docs/05-数据集工程.md) | 三种构建方式 + 黄金数据集 + 分层设计 | 4 天 |
| 06 | [工具链实战](docs/06-工具链实战.md) | DeepEval/promptfoo/RAGAS/Langfuse/Inspect AI 选型与上手 | 5 天 |
| 07 | [可观测性与生产监控](docs/07-可观测与生产监控.md) | OTel 链路追踪、在线评测、失败用例回流闭环 | 4 天 |
| 08 | [五个练手项目](docs/08-实战项目.md) | **核心** 从 Hello Eval 到多 Agent 评测，递进式实战 | 5 周 |
| 09 | [Agent 测试自动化平台搭建](docs/09-平台搭建.md) | **核心** 架构设计 + 6 个里程碑 + 技术选型 | 4 周 |
| 10 | [资料索引与 Benchmark 清单](docs/10-资料索引.md) | 一手源头、论文、开源仓库、Benchmark | 随查随用 |
| 11 | [12 周打卡表](docs/11-学习计划打卡表.md) | 逐周任务与验收标准，打勾用 | 全程 |

配套可运行代码骨架：[`starter/`](starter/) —— 一个内置 Bug 的客服 Agent + 完整评测脚手架（平台 M1–M5 已落地，含 **P2 开源 Agent 评测**与**零依赖 Web 平台 `web.py`**），第一天就能跑起来。

---

## 3. 12 周学习计划总览

### 阶段一（第 1–2 周）· 建立认知与最小闭环
**目标：跑通第一个 Agent 评测，理解"分数是怎么来的"**

- 读完文档 01 / 02 / 03
- 搭好本地环境：Python 3.11+、DeepEval、一个可用的模型 API（推荐 DeepSeek / Qwen / GLM，便宜）
- 完成 **项目 P1：Hello Eval**（见文档 08）
- 交付物：一个能跑 `deepeval test run` 出分数的仓库

**验收标准**：能向别人解释清楚 `ToolCorrectnessMetric` 的分数是怎么算出来的，以及为什么 Faithfulness 比 Answer Quality 更能暴露问题。

---

### 阶段二（第 3–5 周）· 方法论与数据集
**目标：能独立设计一套 Agent 的评测方案，而不是套模板**

- 读完文档 04 / 05
- 完成 **项目 P2：给一个真实开源 Agent 做评测方案**
- 建立你的第一个黄金数据集（≥100 条，其中 ≥30% 边缘用例）
- 学会 LLM-as-Judge 的 Prompt 设计四原则与人工校准
- 交付物：一份《XX Agent 评测方案》+ 一个带版本的数据集

**验收标准**：你的 Judge 打分与人工标注的一致率 ≥80%（用 Cohen's Kappa 或简单一致率衡量）。

---

### 阶段三（第 6–8 周）· 工具链与工程化
**目标：把评测变成流水线里的一道门禁**

- 读完文档 06 / 07
- 完成 **项目 P3：CI/CD 质量门禁** 和 **项目 P4：全链路可观测**
- 掌握 OpenTelemetry + Langfuse 的 Trace 采集
- 交付物：一条能在 PR 上自动跑、红绿分明的 Agent 评测流水线

**验收标准**：提交一个故意劣化 Prompt 的 PR，流水线能自动拦截并指出是哪个指标掉了。

---

### 阶段四（第 9–12 周）· 平台化
**目标：从"会用工具"到"能造平台"，这是你相对普通测试的护城河**

- 读完文档 09
- 完成 **项目 P5：Agent 测试自动化平台 MVP**
- 交付物：一个可演示的平台（数据集管理 + 任务调度 + 评估引擎 + Trace 回放 + 报告看板）

**验收标准**：非技术同事能在你的平台上，自己上传一个数据集、跑一次评测、看懂报告。

---

## 4. 三条容易走偏的路（提前避坑）

**坑一：一头扎进大模型原理，看 Transformer 论文看半个月。**
你不需要会训模型。你需要知道的是：为什么它会幻觉、为什么同样输入输出不同、上下文窗口如何影响长任务。原理够用即可，重心在评测工程。

**坑二：追着框架跑，把 DeepEval/promptfoo/Langfuse 挨个学一遍。**
工具三天能学会，值钱的是**指标设计和数据集**。选一个主力工具（推荐 DeepEval）打穿，其它了解即可。

**坑三：一上来就想搭平台。**
没有跑过 500 条真实用例之前搭的平台，一定是错的。先手工跑，跑到烦，烦点就是平台的功能点。这和你当年搭自动化平台的路径完全一样。

---

## 5. 你的差异化定位

市面上做 Agent 评测的人，大致三类：

1. **算法工程师**：懂模型，但用例设计粗糙，覆盖度靠感觉
2. **应用开发**：懂业务，但没有质量方法论，测完就完了
3. **传统测试**：想转但缺 AI 认知，停留在"手工问几个问题"

**你的定位是第四类：懂质量方法论 + 懂工程化 + 补齐 AI 认知的 Agent 质量工程师（AI QE）。**

这个角色在 2026 年是稀缺的。核心竞争力不是"会用 DeepEval"，而是：

- 能从零设计一个 Agent 产品的**质量准出标准**
- 能建**黄金数据集**并持续运营
- 能搭**评测平台**让整个团队复用

---

## 6. 快速开始（今天就能做的事）

```bash
# 1. 环境（推荐用 uv，比 pip 快很多）
python -m venv .venv && source .venv/Scripts/activate   # Windows Git Bash
pip install -U deepeval pytest python-dotenv

# 2. 配置模型（以 DeepSeek 为例，成本低，适合练手）
#    在 starter/.env 里填入
#    OPENAI_API_KEY=sk-xxx
#    OPENAI_BASE_URL=https://api.deepseek.com

# 3. 跑第一个评测（P1 最小闭环，纯本地、无需 API Key、无需 deepeval）
cd starter
pytest evals/test_p1_basic.py -v
# 你会看到 test_fake_order_is_faithful 红（Agent 编造了状态）——这正是要学的"空结果陷阱"
# 把 customer_service_agent.py 里 run_agent 的 fabricate 改为 False（或改用 run_agent_fixed）后重跑，全绿
```

然后打开 [docs/01-认知迁移.md](docs/01-认知迁移.md) 开始。

---

## 7. 在 GitHub 上自动跑（CI 质量门禁 / P3）

仓库已内置 `.github/workflows/agent-eval.yml`，每次推送或开 PR 都会自动：

1. **主门禁** `quality-gate`：跑线上版 Agent（`AGENT_MODE=fixed`），分级门禁必须过，否则阻断合并。
2. **门禁自检** `gate-catches-regression`：跑故意留 Bug 的版本（`AGENT_MODE=buggy`），断言门禁**必须拦下它**——证明门禁是真在生效，不是摆设。

想亲眼看门禁"掐"住一个坏改动？在本地把 Agent 改坏再推上去：

```bash
# 故意劣化：把 customer_service_agent.py 的 run_agent 改回"查不到也编一个状态"
git commit -am "chore: 引入一个回归（演示 CI 拦截）"
git push
# → quality-gate 变红并阻断，gate-catches-regression 显示"门禁自检通过"
```

这就是文档 08 P3 / 文档 09 M3 的落地：评测不是本地一次性脚本，而是流水线里的一道刚性门禁。

---

## 8. 资料来源说明

本手册的方法论综合自以下一手来源（完整索引见 [文档 10](docs/10-资料索引.md)）：

- Anthropic Engineering《Demystifying evals for AI agents》——评分器分类、pass@k/pass^k、8 步路线图
- Microsoft Research《AgentEval》——CriticAgent/QuantifierAgent/VerifierAgent 三智能体框架
- AWS《Agent-EvalKit》——OTel 链路追踪 + 代码分析生成用例 + 忠实度案例
- 阿里国际（AliExpress 技术）——Agent 精细化评测体系（15 种范围 / 35 项指标 / 8 类数据集）、Agent-as-Judge 三层评估
- Qborfy AI《AI Agent 评测工程实践》系列 01–07
- 开源框架官方文档：DeepEval / promptfoo / RAGAS / Langfuse / Opik / Inspect AI / Giskard
