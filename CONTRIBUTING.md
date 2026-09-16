# 如何参与贡献

感谢你愿意完善这本《Agent 测试转型手册》！下面是几条简单约定，照着做就能顺利合入。

## 你可以贡献什么

- 文档修正 / 补充案例 / 翻译
- `starter/` 里的评测脚手架改进（新增评分器、数据集、Agent 适配器）
- 新的练手项目或 Benchmark 索引

## 目录约定

```
docs/              文档（按 01~12 顺序编号，新增专章请顺延编号并更新 README 文档地图）
starter/           可运行评测脚手架（纯本地、零依赖优先）
  agent/           被测 Agent
  evals/          P1 最小评测（pytest）
  datasets/       回归集 / 能力集 / 回流候选集
  platform/       平台 M1–M5
  p2/              P2 开源 Agent 评测（harness / adapter / judge / quality_gate）
  tests/           starter 单元测试（pytest）
```

## 开发约定

1. **零依赖优先**：核心路径只用 Python 标准库即可跑。`starter/requirements.txt` 里标注的第三方包必须是「按需启用」（懒加载 + 缺失即降级）。
2. **不假绿**：改了脚手架，请先本地跑通再提 PR：
   ```bash
   cd starter
   pytest evals test_p1_basic.py -q          # P1 最小闭环
   pytest tests -q                            # starter 单元测试
   cd platform && python run_suite.py --report r.json && python quality_gate.py r.json
   cd ../p2 && python run_p2.py --dataset dataset_security.json --agent realistic
   ```
3. **故意留的 Bug 不要修掉**：`customer_service_agent.run_agent`（空结果陷阱）、`DummyBrowserAgent`（越权支付）是教学锚点，门禁依赖它们被拦下。新增「正确版」请走 `run_agent_fixed` / `RealisticAgent` 的模式。
4. **安全用例**：涉及越权/注入的评测，请用 `expect_refuse` / `must_not_fabricate` 标注，并回流进数据集（见 `starter/p2/dataset_security.json`）。

## PR 规范

- 一个 PR 只做一件事，标题用 `feat/fix/docs/refactor` 前缀。
- 如改动文档，请同步更新 [README.md](README.md) 与 [README.en.md](README.en.md) 的「文档地图」与篇数徽章。
- 如改动 `starter/`，请确认上面的「不假绿」命令全绿。

Issues / PR 都欢迎 ⭐
