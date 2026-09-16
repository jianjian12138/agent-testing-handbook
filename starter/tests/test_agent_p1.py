"""P1 被测 Agent 测试：真实订单、空结果陷阱(Bug)、修复版行为。"""
from customer_service_agent import run_agent, run_agent_fixed


def test_real_order_mentions_status():
    out = run_agent("我的订单 12345 到哪了？")
    assert any(t["name"] == "query_order" for t in out["tools_called"])
    assert "配送中" in out["answer"]


def test_fake_order_fabricates():
    # Bug 版：查不到订单却编造状态（空结果陷阱）
    out = run_agent("我的订单 99999 到哪了？")
    assert "已发货" in out["answer"]


def test_fixed_does_not_fabricate():
    out = run_agent_fixed("我的订单 99999 到哪了？")
    assert "未查到" in out["answer"]
    assert "已发货" not in out["answer"]
