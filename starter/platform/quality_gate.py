"""
平台 M3：质量门禁 Quality Gate（文档 09 的 M3 里程碑）

分级准出标准（对应文档 03 的 L1/L2/L3）：
- L1 核心指标（回归集通过率）：必须 100%，不达标 → 阻断合并(exit 1)
- L2 辅助指标（能力集通过率）：跌破基线 → 仅告警，不阻断
- L3 实验指标（新指标）：仅记录

CI 里这样用：
    python starter/platform/run_suite.py --report report.json
    python starter/platform/quality_gate.py report.json
"""

import json
import sys


# ---- 分级准出阈值（文档 03：核心阻断、辅助告警）----
L1_REGRESSION_PASS_RATE = 1.0   # 回归集必须全绿
L2_CHALLENGE_FLOOR = 0.5        # 能力集跌破此线告警（防能力退步）


def compute_rates(report: dict):
    rates = {}
    for subset, cases in report.items():
        if not cases:
            rates[subset] = 1.0
            continue
        passed = sum(1 for c in cases if c["passed"])
        rates[subset] = passed / len(cases)
    return rates


def gate(report_path: str):
    report = json.load(open(report_path, encoding="utf-8"))
    rates = compute_rates(report)
    blocked = False
    warnings = []

    reg = rates.get("regression", 1.0)
    if reg < L1_REGRESSION_PASS_RATE:
        blocked = True
        print(f"[BLOCK] 回归集通过率 {reg:.0%} < {L1_REGRESSION_PASS_RATE:.0%} → 阻断合并")
    else:
        print(f"[OK]    回归集通过率 {reg:.0%}")

    cha = rates.get("challenge", 1.0)
    if cha < L2_CHALLENGE_FLOOR:
        warnings.append(f"能力集通过率 {cha:.0%} < {L2_CHALLENGE_FLOOR:.0%}，警惕能力退步")
    else:
        print(f"[OK]    能力集通过率 {cha:.0%}")

    for w in warnings:
        print(f"[WARN]  {w}")

    print(f"\n结论：{'❌ 阻断（不允许合并）' if blocked else '✅ 通过（允许合并）'}")
    return 1 if blocked else 0


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("usage: python quality_gate.py report.json")
        sys.exit(2)
    sys.exit(gate(sys.argv[1]))
