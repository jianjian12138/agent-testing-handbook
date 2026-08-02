# starter/ · 练手代码骨架

> 配套文档 08《实战项目》P1–P5。所有代码**纯本地可跑，无需 API Key**，方便你第一时间体验闭环。

## 目录

```
starter/
├── agent/
│   └── customer_service_agent.py   # 最小客服 Agent，含一个故意 Bug（空结果陷阱）
├── evals/
│   └── test_p1_basic.py            # P1 最小评测（pytest，能红能绿）
├── datasets/
│   ├── regression/orders.json        # 回归集 10 条（L1，必须全绿）
│   ├── challenge/orders.json         # 能力集 10 条（L2，50–70% 通过）
│   └── candidates/backlog.json       # M4 回流候选集（feedback.py 生成）
├── platform/
│   ├── run_suite.py                   # M1：本地评测编排
│   ├── quality_gate.py               # M3：分级质量门禁
│   ├── trace.py                      # M4：统一 Tracer（Local/OTel/Langfuse）
│   ├── traced_agent.py               # M4：给客服 Agent 套埋点
│   ├── render_traces.py              # M4：traces.jsonl → 瀑布图 HTML
│   ├── feedback.py                   # M4：失败回流到候选集
│   ├── demo_trace.py                 # M4：一键演示
│   ├── web.py                        # M5：零依赖 Web 仪表盘（看板 + 触发评测 + 数据集上传）
│   └── architecture.md               # 平台架构草稿
└── p2/
    ├── README.md                     # P2 开源 Agent 评测方案（browser-use 示例）
    ├── adapter.py                    # AgentAdapter + DummyBrowserAgent(含缺陷) + RealisticAgent(正确) + BrowserUseAgent
    ├── dataset_p2.json               # 184 条数据集（64 条边缘 ≈ 35%）
    ├── gen_dataset_p2.py             # 数据集生成器（可重跑扩到 ≥100 条）
    ├── judge.py                      # 真实 LLM-as-Judge（completion 维度，四原则）
    ├── harness.py                    # P2 评测引擎（评分器 + pass@k，completion 可接 Judge）
    ├── run_p2.py                     # P2 入口（--agent / --judge / --trials，含 M4 Tracer）
    └── quality_gate_p2.py            # P2 分级门禁
```

## 快速开始

### P1 · 最小评测闭环
```bash
# 1) 跑最小评测（会看到 test_fake_order_is_faithful 红）
pytest evals/test_p1_basic.py -v

# 2) 修 Bug：把 customer_service_agent.py 的 run_agent 改调 run_agent_fixed 逻辑
#    重跑，三个测试全绿

# 3) M1：跑整套评测编排（默认用含 Bug 的 Agent，会报 FAIL）
python platform/run_suite.py --report report.json

# 4) 用修复版 Agent 再跑一次（全绿）
AGENT_MODE=fixed python platform/run_suite.py --report report_fixed.json

# 5) M3：质量门禁（用上一步的报告）
python platform/quality_gate.py report_fixed.json   # 应 ✅ 通过
python platform/quality_gate.py report.json         # 应 ❌ 阻断
```

### M4 · Trace 可观测（零依赖）
```bash
cd platform
python demo_trace.py                 # 跑几条用例 → traces.jsonl + traces_report.html
# 浏览器打开 traces_report.html 看 Trace 瀑布图
# 接真·Langfuse / OTel：设 LANGFUSE_PUBLIC_KEY/SECRET/HOST（或 OTEL_EXPORTER_OTLP_ENDPOINT）后再跑，埋点不变
```

### P2 · 开源 Agent 评测（browser-use 示例）
```bash
cd p2
python run_p2.py --report report_p2.json
# 你会看到下单类用例（P2-00x）因「多塞 autofill_payment」全部 FAIL，门禁阻断

# 换「正确 Agent」跑：100% 通过（证明门禁抓缺陷、不误杀）
python run_p2.py --agent realistic

# 开真实 LLM-as-Judge（需 openai + key）：completion 维度换成 Judge
python run_p2.py --judge

# M4 回流闭环：把 P2 失败用例收进候选集
python ../platform/feedback.py report_p2.json
```

### M5 · Web 平台（零依赖）
```bash
cd platform
python web.py                      # http://127.0.0.1:8000
# 仪表盘：加载报告看通过率/各维度/失败下钻；点「运行 P2 评测」服务端触发；
# 支持 --agent realistic / --judge；POST /api/dataset/upload 上传数据集
```

## 学习顺序建议

1. 先 `test_p1_basic.py` 感受"红→绿"闭环（P1）
2. 再 `run_suite.py` 看数据集如何驱动批量评测（P2/P3 基础）
3. 然后 `quality_gate.py` 理解"门禁如何拦合并"（P3）
4. 接着 `demo_trace.py` 看 Agent 每一步被打点成 Trace（M4）
5. 最后 `p2/run_p2.py` 体验"给真实开源 Agent 设计评测方案"（P2）

> 真实项目里，`customer_service_agent.py` 的 `decide_tool` 应换成 LLM 调用，
> 评分器应换成 DeepEval 的 Metric（文档 06），门禁应接进 CI（文档 08 P3，已内置 `.github/workflows`）。
