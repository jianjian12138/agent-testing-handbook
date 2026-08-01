"""
P1 最小评测：朴素断言 + 忠实度检查

这是文档 08《实战项目》P1 的配套评测。目标：
1. 跑通"写 Agent → 写评测 → 看它失败 → 修 Agent"的最小闭环。
2. 亲手踩中"空结果陷阱"——Agent 查不到订单却编造状态（文档 03 的 Faithfulness）。

运行（无需 API Key，纯本地）：
    pytest starter/evals/test_p1_basic.py -v

说明：
- 前两个测试在「有 Bug 的 Agent」上应该 PASS（查得到订单时行为正常）。
- 第三个测试 test_fake_order_is_faithful 在当前 Bug 版本上应该 FAIL ——
  这就是你要观察的"红"。把 customer_service_agent.py 里 run_agent 的 fabricate
  改为 False（或直接改用 run_agent_fixed）后，它变绿。
- 真实项目里你会用 DeepEval 的 ToolCorrectnessMetric / AgentGoalCompletionMetric
  替换这里的朴素断言（见文档 06），但 P1 先用最朴素的写法建立直觉。
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "agent"))
from customer_service_agent import run_agent

# 订单状态关键词：答案里出现这些，意味着 Agent "声称"了一个具体状态
STATUS_KEYWORDS = ["配送中", "已发货", "已签收", "未发货", "运输中", "派送中"]


def _mentioned_status(answer: str):
    return [k for k in STATUS_KEYWORDS if k in answer]


def test_real_order_calls_tool():
    """真实存在的订单：Agent 应当调用 query_order，且答案与工具返回一致。"""
    out = run_agent("我的订单 12345 到哪了？")
    assert any(t["name"] == "query_order" for t in out["tools_called"])
    assert out["tool_results"][0]["status"] == "配送中"
    assert "配送中" in out["answer"]


def test_greeting_no_tool():
    """普通问候：不应触发任何工具调用。"""
    out = run_agent("你好")
    assert out["tools_called"] == []
    assert out["answer"]


def test_fake_order_is_faithful():
    """关键测试：不存在的订单，Agent 不应编造状态。

    当前（含 Bug 版本）应当 FAIL，演示「空结果陷阱」。
    把 run_agent 的 fabricate 改为 False（或改用 run_agent_fixed）后变绿。
    """
    out = run_agent("我的订单 99999 到哪了？")
    # 工具确实没查到
    assert out["tool_results"][0] == {}, "工具层确实返回空"
    # 忠实度：没有真实数据，答案不能出现任何具体状态词（不能编造）
    mentioned = _mentioned_status(out["answer"])
    assert mentioned == [], f"Agent 编造了订单状态：{mentioned} | 答案={out['answer']}"
