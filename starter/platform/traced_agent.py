"""
给客服 Agent 套一层 Trace 埋点（M4 演示用）。

不改动原 customer_service_agent.py —— 那样会破坏 P1 测试。
这里只是复用它的底层函数（decide_tool / query_order / _build_answer），
在每个步骤外面包一层 span，产出一条可回放的 Trace。

运行：python demo_trace.py
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "agent"))
from customer_service_agent import decide_tool, query_order, _build_answer

from trace import get_tracer

STATUS_KEYWORDS = ["配送中", "已发货", "已签收", "未发货", "运输中", "派送中"]


def run_agent_traced(user_input: str, fabricate: bool = True, tracer=None) -> dict:
    """跑一轮被测 Agent 并产出 Trace。fabricate=True 复现「空结果陷阱」。"""
    tracer = tracer or get_tracer()

    with tracer.root("agent.run", input=user_input) as root:
        tool, ids = decide_tool(user_input)

        # ---- 规划 ----
        with root.span("plan", kind="plan", input=user_input) as sp:
            sp.set_attribute("decided_tool", tool)
            sp.set_attribute("order_ids", ids)
            sp.output = {"tool": tool, "ids": ids}

        # ---- 无订单号：应追问，不调工具 ----
        if tool == "query_order" and not ids:
            answer = "您好，请提供订单号，我帮您查询物流。"
            root.output = {"answer": answer, "tools_called": [], "tool_results": [],
                           "faithful": True}
            return root.output

        # ---- 调工具 ----
        if tool == "query_order":
            tool_results = []
            for oid in ids:
                with root.span(f"tool:query_order({oid})", kind="tool",
                               input={"order_id": oid}) as tsp:
                    res = query_order(oid)
                    tsp.output = res
                    tsp.set_attribute("tool_name", "query_order")
                    tsp.set_attribute("found", bool(res))
                    tool_results.append(res)

            answer = _build_answer(ids, tool_results, fabricate)

            # ---- 忠实度：工具全空却出现具体状态词 => 不忠实 ----
            faithful = not (
                all(r == {} for r in tool_results)
                and any(k in answer for k in STATUS_KEYWORDS)
            )
            root.set_attribute("faithful", faithful)
            root.output = {
                "answer": answer,
                "tools_called": [{"name": "query_order", "args": {"order_id": o}} for o in ids],
                "tool_results": tool_results,
                "faithful": faithful,
            }
        else:
            answer = "您好，请问有什么可以帮您？查询订单请告诉我订单号。"
            root.output = {"answer": answer, "tools_called": [], "tool_results": [],
                           "faithful": True}

    return root.output


if __name__ == "__main__":
    out = run_agent_traced("订单 99999 到哪了", fabricate=True)
    print("answer:", out["answer"])
    print("faithful:", out.get("faithful"))
