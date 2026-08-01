"""
最小可运行客服 Agent（含一个故意 Bug，用于 P1 练手）

这是文档 02《被测对象解剖》里提到的最小 Agent 裸实现（约 60 行）。
它刻意保留一个 Bug：当 `query_order` 查不到订单时返回空 dict，
而 Agent 没有真实数据却"编"了一个配送状态——这正好对应文档 03 最关键的
**忠实度(Faithfulness)** 指标。

运行（交互模式）：
    python customer_service_agent.py

评测（见 ../evals/test_p1_basic.py）：
    pytest ../evals/test_p1_basic.py -v

无需任何 API Key，纯本地可跑——方便你第一时间体验"Agent 测试闭环"。
真实项目里，decide_tool 这一步应换成真正的 LLM 调用。
"""

import re

# ---------------------------------------------------------------------------
# 模拟工具层（真实场景里是查数据库 / 调用下游 API）
# ---------------------------------------------------------------------------
ORDERS = {
    "12345": {"status": "配送中", "eta": "今天 18:00", "item": "机械键盘"},
    "67890": {"status": "已签收", "eta": "昨天", "item": "显示器"},
    "11111": {"status": "未发货", "eta": "明天", "item": "USB 集线器"},
}


def query_order(order_id: str) -> dict:
    """查询订单。找不到时返回空 dict——这是陷阱的源头。

    ⚠️ 真实实现应当区分「查到但为空」与「订单不存在」，
    并返回明确的错误信号，而不是让上层自己猜。
    """
    return ORDERS.get(order_id, {})  # Bug 源头：找不到返回 {}


# ---------------------------------------------------------------------------
# 极简"模型决策"：基于关键词选工具（无需 API Key 即可跑）
# 真实 Agent 里这里换成 LLM 调用，返回「下一步调哪个工具 + 参数」
# ---------------------------------------------------------------------------
def decide_tool(user_input: str):
    """模拟 LLM 的规划/决策。返回 (tool_name, [order_ids])。

    真实 Agent 里这里换成 LLM 调用，返回「下一步调哪个工具 + 参数」。
    这里用关键词 + 正则抽取订单号，支持多订单、支持「无订单号」情况。
    """
    ids = re.findall(r"(\d{4,})", user_input)
    if any(k in user_input for k in ("订单", "到哪", "物流", "快递")):
        return "query_order", ids
    return None, []


# ---------------------------------------------------------------------------
# Agent 主循环（真实 Agent 这里是 while 循环，这里简化为单轮）
# ---------------------------------------------------------------------------
def _build_answer(ids, results, fabricate: bool) -> str:
    """根据工具结果拼答案。fabricate=True 时复现「空结果陷阱」Bug。"""
    parts = []
    for oid, res in zip(ids, results):
        if res:
            parts.append(
                f"订单 {oid}：状态「{res['status']}」，"
                f"预计 {res['eta']} 送达，商品 {res['item']}。"
            )
        else:
            if fabricate:
                # ❌ Bug：没有真实数据，却编了一个「已发货 / 配送中」状态
                parts.append(f"订单 {oid} 已发货，正在配送中，请耐心等待。")
            else:
                # ✅ 修复：查不到就老实说查不到，绝不编造
                parts.append(f"订单 {oid}：未查到，请确认订单号是否正确。")
    return " ".join(parts)


def run_agent_impl(user_input: str, fabricate: bool) -> dict:
    """Agent 主循环（真实 Agent 这里是 while 循环，这里简化为单轮）。"""
    tools_called = []
    tool_results = []
    tool, ids = decide_tool(user_input)
    if tool == "query_order":
        if not ids:
            # 没有订单号，无法查询——应追问，而不是瞎编
            return {
                "answer": "您好，请提供订单号，我帮您查询物流。",
                "tools_called": [],
                "tool_results": [],
            }
        for oid in ids:
            tools_called.append({"name": "query_order", "args": {"order_id": oid}})
            tool_results.append(query_order(oid))
        answer = _build_answer(ids, tool_results, fabricate)
    else:
        answer = "您好，请问有什么可以帮您？查询订单请告诉我订单号。"
    return {"answer": answer, "tools_called": tools_called, "tool_results": tool_results}


def run_agent(user_input: str) -> dict:
    """含 Bug 版本：查不到订单时编造状态（用于演示 P1 的「空结果陷阱」）。"""
    return run_agent_impl(user_input, fabricate=True)


def run_agent_fixed(user_input: str) -> dict:
    """修复版本：查不到就诚实说明，绝不编造。"""
    return run_agent_impl(user_input, fabricate=False)


if __name__ == "__main__":
    print("客服 Agent（输入 exit 退出）")
    while True:
        try:
            q = input("你：")
        except (EOFError, KeyboardInterrupt):
            break
        if q.strip().lower() in ("exit", "quit"):
            break
        out = run_agent(q)
        print("Agent：", out["answer"])
