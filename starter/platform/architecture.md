# 平台架构草稿（M1–M6 演进）

> 这是你「搭建自己的 Agent 测试自动化平台」的起点。对应文档 09。
> 先有 M1 脚本，再逐步长成 M6 平台。不要一上来做 Web。

## 当前已有（M1 + M3 + M4 骨架）

```
starter/
├── agent/customer_service_agent.py   # 被测 Agent（含 Bug 可演示）
├── evals/test_p1_basic.py            # P1 最小评测（pytest）
├── datasets/
│   ├── regression/orders.json        # 回归集（L1，必须全绿）
│   ├── challenge/orders.json         # 能力集（L2，50–70% 通过）
│   └── candidates/backlog.json       # M4 回流候选集（由 feedback.py 生成）
├── platform/
│   ├── run_suite.py                   # M1：读数据集→跑Agent→评分→报告
│   ├── quality_gate.py               # M3：分级门禁（核心阻断/辅助告警）
│   ├── trace.py                      # M4：统一 Tracer（Local/OTel/Langfuse 三后端）
│   ├── traced_agent.py               # M4：给客服 Agent 套埋点
│   ├── render_traces.py              # M4：traces.jsonl → 瀑布图 HTML
│   ├── feedback.py                   # M4：失败回流到候选集
│   └── demo_trace.py                 # M4：一键演示
└── p2/                               # P2：开源 Agent 评测方案（browser-use 示例）
    ├── README.md                     # 评测方案
    ├── adapter.py                    # AgentAdapter + DummyBrowserAgent + 真实接入示例
    ├── dataset_p2.json               # 22 条种子数据集（10 条边缘）
    ├── harness.py                    # 评测引擎（评分器 + pass@k）
    ├── run_p2.py                     # 入口
    └── quality_gate_p2.py            # 分级门禁
```

## 演进路线（详见文档 09.3）

- **M1** `run_suite.py` —— 本地一键评测 ✅ 已落地
- **M2** 数据集可视化管理（schema 校验 + 版本 + 标注）
- **M3** `quality_gate.py` —— CI 质量门禁 ✅ 已落地
- **M4** 可观测 + 回流 ✅ 已落地（本地零依赖骨架；接 Langfuse/OTel 设环境变量即切换）
- **M5** Web 平台化（FastAPI + Streamlit/Gradio）
- **M6** 多 Agent 评测 + 动态基线门禁

## 平台五层（文档 09.2）

```
用户入口层 → 数据集管理层 → 评测编排层 → 评分器层(Grader) → 质量门禁 → 存储&可观测层
```

## 建议的 API 草稿（M5 用）

| 端点 | 方法 | 作用 |
| --- | --- | --- |
| `/datasets` | POST | 上传数据集（带 schema 校验） |
| `/datasets/{id}` | GET | 查看数据集 + 版本 |
| `/eval/run` | POST | 触发一次评测（指定数据集 + Agent） |
| `/eval/{run_id}/report` | GET | 取评测报告 |
| `/gate/{run_id}` | GET | 取门禁结论（阻断/通过） |
| `/candidates` | GET | 查看回流候选集 |

> 现在把 M1/M3/M4 跑顺，M2/M5/M6 在自然推进，P2 已补进开源 Agent 评测方案。
