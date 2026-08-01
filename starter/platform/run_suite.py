"""
平台 M1：本地评测编排（文档 09 的 M1 里程碑）

读数据集 → 跑 Agent → 应用评分器 → 出报告。
这是你平台最底层的一块：把"评测"从一次性脚本变成可复用的服务入口。

运行：
    python starter/platform/run_suite.py
    AGENT_MODE=fixed python starter/platform/run_suite.py   # 用修复版 Agent

退出码：全部通过返回 0，有失败返回 1（方便 CI 直接当作门禁）。
也可加 --report path.json 把结果写成 JSON，供 quality_gate.py 复用。
"""

import glob
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "agent"))
from customer_service_agent import run_agent, run_agent_fixed

STATUS_KEYWORDS = ["配送中", "已发货", "已签收", "未发货", "运输中", "派送中"]


def _faithful(out):
    """忠实度朴素版：工具结果全空时，答案不得出现任何具体状态词。"""
    if all(r == {} for r in out["tool_results"]):
        return not any(k in out["answer"] for k in STATUS_KEYWORDS)
    return True


def _tool_called_ok(out, expected_tools):
    called = [(t["name"], tuple(t["args"].items())) for t in out["tools_called"]]
    for exp in expected_tools:
        if (exp["name"], tuple(exp["args"].items())) not in called:
            return False
    return True


def grade_case(case, agent_fn):
    out = agent_fn(case["input"])
    checks = {
        "tool_called": _tool_called_ok(out, case.get("expected_tools", [])),
        "faithful": _faithful(out),
    }
    for kw in case.get("expected_output_contains", []):
        checks.setdefault("contains", True)
        if kw not in out["answer"]:
            checks["contains"] = False
    passed = all(checks.values())
    return {"id": case["id"], "passed": passed, "checks": checks, "answer": out["answer"]}


def run_suite(data_dir, agent_fn):
    results = []
    for f in sorted(glob.glob(os.path.join(data_dir, "*.json"))):
        for case in json.load(open(f, encoding="utf-8")):
            results.append(grade_case(case, agent_fn))
    return results


def main():
    base = os.path.join(os.path.dirname(__file__), "..", "datasets")
    agent_fn = run_agent_fixed if os.environ.get("AGENT_MODE") == "fixed" else run_agent
    report = {}
    for subset in ("regression", "challenge"):
        res = run_suite(os.path.join(base, subset), agent_fn)
        report[subset] = res
        passed = sum(1 for r in res if r["passed"])
        print(f"[{subset}] {passed}/{len(res)} passed")

    all_results = report["regression"] + report["challenge"]
    total_p = sum(1 for r in all_results if r["passed"])
    print(f"\nTOTAL {total_p}/{len(all_results)} passed")
    for r in all_results:
        if not r["passed"]:
            print(f"  FAIL {r['id']}: checks={r['checks']} answer={r['answer']!r}")

    if "--report" in sys.argv:
        path = sys.argv[sys.argv.index("--report") + 1]
        json.dump(report, open(path, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
        print(f"\nreport written -> {path}")

    return 0 if total_p == len(all_results) else 1


if __name__ == "__main__":
    sys.exit(main())
