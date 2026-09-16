"""质量门禁测试：平台门禁 + P2 分级门禁的阻断/放行逻辑。"""
import json


def _write(tmp_path, data):
    p = tmp_path / "report.json"
    p.write_text(json.dumps(data), encoding="utf-8")
    return str(p)


def test_platform_gate_blocks_incomplete(tmp_path):
    from quality_gate import gate
    p = _write(tmp_path, {
        "regression": [{"passed": True}, {"passed": False}],
        "challenge": [{"passed": True}],
    })
    assert gate(p) == 1


def test_platform_gate_passes_all_green(tmp_path):
    from quality_gate import gate
    p = _write(tmp_path, {
        "regression": [{"passed": True}],
        "challenge": [{"passed": True}],
    })
    assert gate(p) == 0


def test_p2_gate_blocks_faithful(tmp_path):
    from quality_gate_p2 import gate as gate2
    p = _write(tmp_path, {"p2": [
        {"checks": {"tool_correct": True, "faithful": False}, "passed": False},
        {"checks": {"tool_correct": True, "faithful": True}, "passed": True},
    ]})
    assert gate2(p) == 1


def test_p2_gate_passes_full(tmp_path):
    from quality_gate_p2 import gate as gate2
    p = _write(tmp_path, {"p2": [
        {"checks": {"tool_correct": True, "faithful": True}, "passed": True},
    ]})
    assert gate2(p) == 0
