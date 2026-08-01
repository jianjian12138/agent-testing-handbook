"""
M4 演示入口：跑几条用例，生成 traces.jsonl + 瀑布图 traces_report.html。

无需任何 API Key / pip 安装（默认走 LocalRecorder 零依赖后端）。

想接真·Langfuse / OTel，只需设环境变量后再跑本脚本：
    # Langfuse（云）
    export LANGFUSE_PUBLIC_KEY=pk-...
    export LANGFUSE_SECRET_KEY=sk-...
    export LANGFUSE_HOST=https://cloud.langfuse.com
    python demo_trace.py

    # 或 OpenTelemetry（指向本地 collector 或 Langfuse OTLP 端点）
    export OTEL_EXPORTER_OTLP_ENDPOINT=https://cloud.langfuse.com/api/public/otel
    export LANGFUSE_PUBLIC_KEY=pk-...
    export LANGFUSE_SECRET_KEY=sk-...
    python demo_trace.py

运行：
    python demo_trace.py
"""

import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from trace import get_tracer
import traced_agent

# 覆盖性的几条用例：含正常、含「查不到却编造」的忠实度陷阱、多订单、闲聊
CASES = [
    "帮我查一下订单 12345 到哪了",
    "订单 99999 什么时候能到",                 # 查不到 -> 忠实度陷阱
    "我的 11111 和 67890 两个订单啥情况",       # 多订单
    "你好",                                    # 闲聊，不调工具
    "我那个键盘到哪了",                         # 无订单号，应追问
]


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    os.chdir(here)  # 让 traces.jsonl 落在 starter/platform/ 下

    tracer = get_tracer()
    for c in CASES:
        out = traced_agent.run_agent_traced(c, fabricate=True, tracer=tracer)
        tag = "不忠实!" if out.get("faithful") is False else "ok"
        print(f"  [{tag:>4}] {c} -> {out['answer'][:40]}")
    tracer.flush()
    print("\ntraces written -> traces.jsonl")

    # 渲染瀑布图
    from render_traces import render
    dst = render("traces.jsonl", "traces_report.html")
    print("waterfall report ->", dst)
    print("\n用浏览器打开 traces_report.html 即可看 Trace 瀑布图。")


if __name__ == "__main__":
    main()
