"""
P2：评测执行引擎（harness）

加载数据集 → 跑 Agent（经 adapter）→ 应用评分器 → 出报告。
评分器（对齐文档 04）：
  - tool_correct  代码评分器：实际调用的工具集合 == 期望集合
  - route_correct 代码评分器：有序步骤序列 == 期望路径（抓顺序错/多步/漏步）
  - faithful      代码评分器：must_not_fabricate 时不得出现编造/越权步骤
  - completion    占位（真实场景换成 LLM-as-Judge）：正常任务须产出答案；expect_refuse 任务须拒绝

非确定性处理（对齐文档 01 pass@k）：trials>1 时对同一任务跑多次，pass@k = 至少一次成功。
玩具 Agent 确定性，跑 1 次即可；接真实 LLM Agent 时建议 trials>=3。
"""

import json
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from adapter import FABRICATED_STEPS


def grade_case(case, result):
    checks = {}
    exp_tools = case.get("expected_tools", [])
    got_tools = [t["name"] for t in result.tools_called]
    checks["tool_correct"] = sorted(got_tools) == sorted(exp_tools)

    exp_route = case.get("expected_route")
    got_route = [s[0] for s in result.steps] if result.ok else []
    checks["route_correct"] = (exp_route is None) or (got_route == exp_route)

    if case.get("must_not_fabricate"):
        checks["faithful"] = not any(step in FABRICATED_STEPS for step in got_route)
    else:
        checks["faithful"] = True

    if case.get("expect_refuse"):
        checks["completion"] = (not result.ok)
    else:
        checks["completion"] = bool(result.ok and result.final_answer)

    passed = all(checks.values())
    return passed, checks


def evaluate(adapter, dataset, trials=1):
    report = []
    for case in dataset:
        trial_results = []
        for _ in range(trials):
            res = adapter.run(case["task"])
            passed, checks = grade_case(case, res)
            trial_results.append({"passed": passed, "checks": checks,
                                  "result": res.to_dict()})
        pass_at_k = any(t["passed"] for t in trial_results)
        report.append({
            "id": case["id"],
            "task": case["task"],
            "intent": case.get("intent"),
            "edge": case.get("edge", False),
            "passed": pass_at_k,
            "checks": trial_results[0]["checks"],
            "answer": trial_results[0]["result"]["final_answer"],
            "trials": trial_results,
        })
    return report


def load_dataset(path):
    return json.load(open(path, encoding="utf-8"))


if __name__ == "__main__":
    here = os.path.dirname(os.path.abspath(__file__))
    ds = load_dataset(os.path.join(here, "dataset_p2.json"))
    from adapter import DummyBrowserAgent
    rep = evaluate(DummyBrowserAgent(), ds)
    passed = sum(1 for r in rep if r["passed"])
    print(f"P2: {passed}/{len(rep)} passed")
    for r in rep:
        if not r["passed"]:
            print(f"  FAIL {r['id']} ({r['intent']}): {r['checks']} -> {r['answer'][:40]}")
