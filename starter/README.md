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
│   ├── regression/orders.json      # 回归集 10 条（L1，必须全绿）
│   └── challenge/orders.json       # 能力集 10 条（L2，50–70% 通过）
└── platform/
    ├── run_suite.py                 # M1：本地评测编排
    ├── quality_gate.py             # M3：分级质量门禁
    └── architecture.md             # 平台架构草稿
```

## 快速开始

```bash
# 1) P1：跑最小评测（会看到 test_fake_order_is_faithful 红）
pytest starter/evals/test_p1_basic.py -v

# 2) 修 Bug：把 customer_service_agent.py 的 else 分支换成 run_agent_fixed 的逻辑
#    重跑，三个测试全绿

# 3) M1：跑整套评测编排（默认用含 Bug 的 Agent，会报 FAIL）
python starter/platform/run_suite.py --report report.json

# 4) 用修复版 Agent 再跑一次（全绿）
AGENT_MODE=fixed python starter/platform/run_suite.py --report report_fixed.json

# 5) M3：质量门禁（用上一步的报告）
python starter/platform/quality_gate.py report_fixed.json   # 应 ✅ 通过
python starter/platform/quality_gate.py report.json         # 应 ❌ 阻断
```

## 学习顺序建议

1. 先 `test_p1_basic.py` 感受"红→绿"闭环（P1）
2. 再 `run_suite.py` 看数据集如何驱动批量评测（P2/P3 基础）
3. 最后 `quality_gate.py` 理解"门禁如何拦合并"（P3）

> 真实项目里，`customer_service_agent.py` 的 `decide_tool` 应换成 LLM 调用，
> 评分器应换成 DeepEval 的 Metric（文档 06），门禁应接进 CI（文档 08 P3）。
