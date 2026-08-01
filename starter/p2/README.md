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

- **规模目标**：≥100 条，**其中 ≥30% 为边缘用例**（本脚手架先给 22 条种子，10 条边缘 ≈ 45%，你按相同格式扩到 100+）
- **八类映射**（文档 05）：查询 / 下单 / 空输入 / 歧义 / 注入 / 不支持意图 / 长任务 / 多商品 —— 见 `dataset_p2.json`
- **Golden 标注字段**：`expected_tools` / `expected_route` / `must_not_fabricate` / `expect_refuse` / `edge`
- **质量 > 数量**：边缘用例（注入、无商品下单、约束冲突）才是能抓出缺陷的「贵」用例

---

## 4. 评分器（对齐文档 04）

- **代码评分器（优先）**：`tool_correct` / `route_correct` / `faithful` 用确定性比对，便宜、可复现、进 CI
- **LLM-as-Judge（占位）**：`completion` 目前用启发式占位；真实场景换成文档 04 的四原则 Judge Prompt（单一职责 / 先推理后判断 / 负例引导 / 结构化输出）
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

# 1) 跑评测（玩具 Agent，零依赖）
python run_p2.py --report report_p2.json
# 你会看到 P2-07~P2-12（下单类）全部 FAIL：被测 Agent 多塞了 autofill_payment —— 这就是要抓的缺陷

# 2) 接真实 browser-use（取消 adapter.py 注释并 pip install browser-use 后）
python run_p2.py --agent browseruse --trials 3

# 3) 失败回流（M4 闭环）：把失败用例收进候选集，人工标注后回流入回归集
python ../platform/feedback.py report_p2.json
```

---

## 8. 交付物清单

```
starter/p2/
├── README.md            # 本方案
├── adapter.py           # AgentAdapter 接口 + DummyBrowserAgent（含缺陷）+ BrowserUseAgent 接入示例
├── dataset_p2.json      # 22 条种子数据集（10 条边缘）
├── harness.py           # 评测引擎（评分器 + pass@k）
├── run_p2.py            # 入口
└── quality_gate_p2.py   # 分级门禁
```

---

## 9. 动手任务（验收标准）

- [ ] 把 `dataset_p2.json` 扩到 ≥100 条，边缘占比 ≥30%
- [ ] 把 `completion` 的占位换成真实 LLM-as-Judge Prompt（文档 04 四原则）
- [ ] 取消注释 `BrowserUseAgent`，接一个真实开源 Agent 跑一遍
- [ ] 故意改坏 `DummyBrowserAgent` 某条路径，确认门禁能拦下
