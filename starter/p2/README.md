# P2 · 开源 Agent 评测方案（browser-use 示例）

> 对应文档 08 P2。目标：**给一个真实开源 Agent 设计一套完整评测方案**，并落地成可运行的脚手架。
> 本目录代码**零依赖可跑**（用 `DummyBrowserAgent` 模拟），真实接入只需换 `adapter.py` 里的 `BrowserUseAgent`。

---

## 1. 为什么选 browser-use 作示例

[`browser-use`](https://github.com/browser-use/browser-use) 是 2025–2026 最活跃的开源 Web 自动化 Agent 之一，特点非常适合做评测练习：

- **工具调用清晰**：navigate / search / click / type 等动作可观、可回放
- **结果可观测**：每步有 DOM 快照与抽取内容，便于做代码评分器
- **缺陷典型**：真实 Agent 常犯「多调一步」「跳步」「编造页面状态」等错，正是 Agent 测试的核心靶子

> 方法可平移：把 `adapter.py` 的 `BrowserUseAgent` 换成 **AutoGPT / MetaGPT / OpenHands / 任意 LangChain Agent**，harness 与评分器不用改。

---

## 2. 评测范围（对齐文档 02 六模块 + 文档 03 五维）

| 维度 | 评什么 | 本脚手架怎么度量 |
| --- | --- | --- |
| 任务完成度 | 最终是否给出答案/是否该拒绝时拒绝 | `completion` |
| 工具质量 | 调了哪些工具、顺序对不对 | `tool_correct` + `route_correct` |
| 规划推理 | 多步顺序是否符合预期路径 | `route_correct` |
| 忠实度 | 是否编造/越权步骤（如自动填支付） | `faithful`（must_not_fabricate） |
| 安全 | 是否拒绝提示注入/越权操作 | `expect_refuse` + `faithful` |

---

## 3. 数据集设计（对齐文档 05）

- **规模**：**184 条**（10 商品 × 3 站点 × 4 意图 = 120 正常 + 64 条边缘），**边缘占比 35%**（≥30% 达标）
- **生成脚本**：`gen_dataset_p2.py` 从 `adapter.expected_plan()` 这一「单一真相源」派生所有期望值，保证数据集与 Agent 参考行为一致；只有玩具 Agent 故意多塞的 `autofill_payment` 一处与期望不一致
- **八类映射**（文档 05）：查询 / 下单 / 空输入 / 歧义 / 注入 / 不支持意图 / 长任务 / 多商品 —— 见 `dataset_p2.json`
- **Golden 标注字段**：`expected_tools` / `expected_route` / `must_not_fabricate` / `expect_refuse` / `edge`
- **质量 > 数量**：边缘用例（提示注入/免费白嫖、无商品下单、约束冲突）才是能抓出缺陷的「贵」用例

---

## 4. 评分器（对齐文档 04）

- **代码评分器（优先）**：`tool_correct` / `route_correct` / `faithful` 用确定性比对，便宜、可复现、进 CI
- **LLM-as-Judge（已落地）**：`completion` 维度由 `judge.py` 的真实 Judge 评分，严格遵循文档 04 四原则——
  - 单一职责：只评「任务完成度/回答质量」，不抢代码评分器的活
  - 先推理后判断（CoT）：模型先给 `reason` 再给 `pass`/`score`
  - 负例引导：prompt 显式列出「空答 / 答非所问 / 未授权自动填充支付」等失败模式
  - 结构化输出：只输出 JSON `{reason, pass, score}`，便于解析留痕
  - 启用：`python run_p2.py --judge`（需 `pip install openai` + `OPENAI_API_KEY`；无 key 自动降级回启发式）
- **人工评分**：边缘用例与失败用例进「回流候选集」做人工复核（见 M4 `feedback.py`）

---

## 5. 非确定性处理（对齐文档 01 pass@k）

真实 LLM Agent 同输入不同输出，`run_p2.py --trials 3` 对同一任务跑 3 次，
`pass@k = 至少一次成功`。玩具 Agent 确定性，跑 1 次即可。

---

## 6. 质量门禁（对齐文档 03 / 09 M3）

`quality_gate_p2.py`：
- **L1 核心**（tool_correct + faithful）必须 100% → 不达标阻断合并
- **L2 辅助**（route_correct + completion）跌破 60% → 仅告警
- **L3 边缘覆盖**占比 < 30% → 仅记录，提醒数据集健康度

---

## 7. 跑起来

```bash
cd starter/p2

# 1) 跑评测（玩具 Agent，零依赖）—— 下单类用例因「多塞 autofill_payment」全 FAIL，门禁阻断
python run_p2.py --report report_p2.json

# 2) 换「正确 Agent」跑 —— 100% 通过（证明门禁抓的是缺陷、不是误杀）
python run_p2.py --agent realistic --report report_realistic.json

# 3) 真实 LLM-as-Judge（completion 维度，需 openai + key）
OPENAI_BASE_URL=https://api.deepseek.com OPENAI_MODEL=deepseek-chat python run_p2.py --judge

# 4) 接真实 browser-use（需 pip install browser-use langchain-openai && playwright install chromium）
python run_p2.py --agent browseruse --trials 3
#    LLM 默认读 OPENAI_API_KEY / OPENAI_BASE_URL / OPENAI_MODEL，或用 --llm-key/--llm-base-url/--llm-model 传入

# 5) M4 可观测：每次 run 自动把规划/工具步打点成 traces.jsonl（可用 ../platform/render_traces.py 看瀑布图）

# 6) 失败回流（M4 闭环）：把失败用例收进候选集
python ../platform/feedback.py report_p2.json
```

---

## 8. 交付物清单

```
starter/p2/
├── README.md            # 本方案
├── adapter.py           # AgentAdapter 接口 + DummyBrowserAgent（含缺陷）+ RealisticAgent（正确）+ BrowserUseAgent 接入
├── dataset_p2.json      # 184 条数据集（64 条边缘 ≈ 35%）
├── gen_dataset_p2.py    # 数据集生成器（从 expected_plan 派生期望值，可重跑扩数据）
├── judge.py             # 真实 LLM-as-Judge（completion 维度，四原则）
├── harness.py           # 评测引擎（评分器 + pass@k，completion 可接 Judge）
├── run_p2.py            # 入口（--agent / --judge / --trials，含 M4 Tracer 注入）
└── quality_gate_p2.py   # 分级门禁
```

---

## 9. 动手任务（验收标准）

- [x] 把 `dataset_p2.json` 扩到 ≥100 条（已 184），边缘占比 ≥30%（已 35%）
- [x] 把 `completion` 的占位换成真实 LLM-as-Judge（`judge.py`，四原则）
- [x] 接一个真实开源 Agent（`BrowserUseAgent` + `--agent browseruse` 已接好；环境装好后即可真跑；本地用 `RealisticAgent` 已真跑通端到端）
- [x] 故意改坏 `DummyBrowserAgent` 某条路径，确认门禁能拦下（M4 门禁自检同思路）
