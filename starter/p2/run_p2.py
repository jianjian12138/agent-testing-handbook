"""
P2 入口：跑开源 Agent 评测，出报告 + 质量门禁。

运行（零依赖，用玩具 Agent）：
    python run_p2.py
    python run_p2.py --report report_p2.json
    python run_p2.py --trials 3          # 非确定性 Agent 用 pass@k
    python run_p2.py --agent browseruse   # 接真实 browser-use（需先 pip install + 改 adapter）

输出：
    - 控制台摘要（通过率、失败用例及原因）
    - report_p2.json（供 quality_gate_p2.py / feedback.py 复用）
"""

import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from harness import evaluate, load_dataset
from adapter import DummyBrowserAgent


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    ap = argparse.ArgumentParser()
    ap.add_argument("--agent", default="dummy", choices=["dummy", "browseruse"])
    ap.add_argument("--dataset", default=os.path.join(here, "dataset_p2.json"))
    ap.add_argument("--report", default=os.path.join(here, "report_p2.json"))
    ap.add_argument("--trials", type=int, default=1)
    args = ap.parse_args()

    if args.agent == "browseruse":
        from adapter import BrowserUseAgent
        # 真实接入需提供 LLM；此处仅占位，按需填写
        raise SystemExit("请先在 adapter.py 的 BrowserUseAgent 中配置 LLM 后使用")
    else:
        adapter = DummyBrowserAgent()

    dataset = load_dataset(args.dataset)
    report = evaluate(adapter, dataset, trials=args.trials)

    # 包成 {subset: cases} 形状，兼容 feedback.py
    out = {"p2": report}
    json.dump(out, open(args.report, "w", encoding="utf-8"), ensure_ascii=False, indent=2)

    passed = sum(1 for r in report if r["passed"])
    edge = [r for r in report if r["edge"]]
    edge_pass = sum(1 for r in edge if r["passed"])
    print(f"=== P2 评测结果 ===")
    print(f"总通过率：{passed}/{len(report)} ({passed/len(report):.0%})")
    print(f"边缘用例：{edge_pass}/{len(edge)} 通过")
    print(f"报告已写出 -> {args.report}")
    print("\n失败用例（含原因）：")
    for r in report:
        if not r["passed"]:
            failed = [k for k, v in r["checks"].items() if not v]
            print(f"  [{r['id']}] {r['task'][:30]!r}  失败项={failed}")
            print(f"         答案={r['answer'][:50]!r}")

    # 顺带跑门禁（退出码透传：阻断=1，通过=0）
    from quality_gate_p2 import gate
    print()
    sys.exit(gate(args.report))


if __name__ == "__main__":
    main()
