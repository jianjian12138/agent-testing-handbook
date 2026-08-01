"""
P2 质量门禁（对齐文档 03 L1/L2/L3 + 文档 09 M3/M4）

分级准出标准：
- L1 核心指标（tool_correct + faithful）：必须 100% → 不达标阻断合并(exit 1)
- L2 辅助指标（route_correct + completion）：跌破基线 → 仅告警，不阻断
- L3 边缘覆盖：边缘用例占比（仅记录，提醒数据集健康度）

运行：
    python quality_gate_p2.py report_p2.json
"""

import json
import sys

# ---- 分级阈值 ----
L1_CORE = ("tool_correct", "faithful")          # 核心：工具正确 + 忠实，必须全绿
L2_AUX = ("route_correct", "completion")        # 辅助：路径正确 + 完成
L2_FLOOR = 0.6                                  # 辅助指标通过率下限（告警线）
EDGE_MIN_RATIO = 0.3                            # 边缘用例占比下限（仅记录）


def _rate(cases, key):
    if not cases:
        return 1.0
    ok = sum(1 for c in cases if c["checks"].get(key))
    return ok / len(cases)


def gate(report_path):
    report = json.load(open(report_path, encoding="utf-8"))
    cases = report.get("p2", [])
    if not cases:
        print("[warn] 报告为空")
        return 0

    blocked = False
    # L1 核心
    for key in L1_CORE:
        r = _rate(cases, key)
        if r < 1.0:
            blocked = True
            print(f"[BLOCK] 核心指标 {key} 通过率 {r:.0%} < 100% → 阻断合并")
        else:
            print(f"[OK]    核心指标 {key} 通过率 {r:.0%}")

    # L2 辅助
    print("-- 辅助指标（仅告警）--")
    for key in L2_AUX:
        r = _rate(cases, key)
        if r < L2_FLOOR:
            print(f"[WARN]  辅助指标 {key} 通过率 {r:.0%} < {L2_FLOOR:.0%}，警惕能力退步")
        else:
            print(f"[OK]    辅助指标 {key} 通过率 {r:.0%}")

    # L3 边缘覆盖
    edges = [c for c in cases if c.get("edge")]
    ratio = len(edges) / len(cases)
    if ratio < EDGE_MIN_RATIO:
        print(f"[WARN]  边缘用例占比 {ratio:.0%} < {EDGE_MIN_RATIO:.0%}，数据集覆盖偏窄")
    else:
        print(f"[OK]    边缘用例占比 {ratio:.0%}（≥ {EDGE_MIN_RATIO:.0%}）")

    print(f"\n结论：{'❌ 阻断（不允许合并）' if blocked else '✅ 通过（允许合并）'}")
    return 1 if blocked else 0


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("usage: python quality_gate_p2.py report_p2.json")
        sys.exit(2)
    sys.exit(gate(sys.argv[1]))
