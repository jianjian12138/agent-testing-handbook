"""
平台 M4：失败回流（对应文档 09 M4「失败回流到候选集」）

把一次评测报告里**没通过**的用例收集进「回流候选集」datasets/candidates/backlog.json，
供人工标注/复核后，再正式回流入回归集（回归集是 L1，必须全绿）。

这就是文档 07 讲的「在线评测 → 失败用例回流 → 数据集持续生长」闭环的最小落地。

运行：
    python feedback.py report.json
    python feedback.py report.json --out datasets/candidates/backlog.json
"""

import json
import os
import sys

DEFAULT_OUT = os.path.join(
    os.path.dirname(__file__), "..", "datasets", "candidates", "backlog.json"
)


def collect_failures(report_path, out_path=DEFAULT_OUT):
    report = json.load(open(report_path, encoding="utf-8"))
    fails = []
    for subset, cases in report.items():
        for c in cases:
            if not c.get("passed"):
                fails.append({
                    "from": subset,
                    "id": c.get("id"),
                    "checks": c.get("checks"),
                    "answer": c.get("answer"),
                })

    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    existing = json.load(open(out_path, encoding="utf-8")) if os.path.exists(out_path) else []
    seen = {f.get("id") for f in existing}
    new = [f for f in fails if f.get("id") not in seen]
    existing.extend(new)
    json.dump(existing, open(out_path, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print(f"回流候选新增 {len(new)} 条（去重后），累计 {len(existing)} 条 -> {out_path}")
    return existing


if __name__ == "__main__":
    rp = sys.argv[1] if len(sys.argv) > 1 else "report.json"
    out = sys.argv[2] if len(sys.argv) > 2 else DEFAULT_OUT
    collect_failures(rp, out)
