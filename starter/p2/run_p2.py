"""
P2 入口：跑开源 Agent 评测，出报告 + 质量门禁。

运行（零依赖，用玩具 Agent）：
    python run_p2.py
    python run_p2.py --report report_p2.json
    python run_p2.py --trials 3          # 非确定性 Agent 用 pass@k

换不同 Agent（--agent）：
    python run_p2.py --agent realistic    # 仿真「正确」Agent：应通过整套评测
    python run_p2.py --agent browseruse   # 接真·browser-use（需 pip install + LLM）

开启真实 LLM-as-Judge（替换 completion 占位检查，需 pip install openai + OPENAI_API_KEY）：
    python run_p2.py --judge
    OPENAI_BASE_URL=https://api.deepseek.com OPENAI_MODEL=deepseek-chat python run_p2.py --judge

可观测（M4）：自动把每个用例的规划/工具步打点成 Trace -> traces.jsonl
    （可用 ../platform/render_traces.py 生成瀑布图）

输出：
    - 控制台摘要（通过率、失败用例及原因）
    - report_p2.json（供 quality_gate_p2.py / feedback.py 复用）
    - traces.jsonl（M4 Trace，可选）
"""

import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from harness import evaluate, load_dataset
from adapter import DummyBrowserAgent, RealisticAgent, BrowserUseAgent, get_tracer


def build_adapter(name, args):
    if name == "realistic":
        return RealisticAgent()
    if name == "browseruse":
        # 真实接入：需要 LLM 客户端（langchain_openai.ChatOpenAI 等）
        try:
            from langchain_openai import ChatOpenAI
        except ImportError:
            raise SystemExit(
                "BrowserUseAgent 需要 langchain_openai，请先：\n"
                "  pip install browser-use langchain-openai\n"
                "  playwright install chromium"
            )
        try:
            llm = ChatOpenAI(
                model=args.llm_model or os.environ.get("OPENAI_MODEL", "deepseek-chat"),
                base_url=args.llm_base_url or os.environ.get("OPENAI_BASE_URL", "https://api.deepseek.com"),
                api_key=args.llm_key or os.environ.get("OPENAI_API_KEY"),
                temperature=0.0,
            )
        except Exception as e:
            raise SystemExit(
                "BrowserUseAgent 构造 LLM 失败（缺少凭证或端点不可达）：\n"
                f"  {e}\n"
                "请设置 OPENAI_API_KEY（或 --llm-key），以及 OPENAI_BASE_URL / OPENAI_MODEL，\n"
                "并确保已 `pip install browser-use langchain-openai && playwright install chromium`。"
            )
        return BrowserUseAgent(llm=llm)
    return DummyBrowserAgent()


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    ap = argparse.ArgumentParser()
    ap.add_argument("--agent", default="dummy",
                    choices=["dummy", "realistic", "browseruse"])
    ap.add_argument("--dataset", default=os.path.join(here, "dataset_p2.json"))
    ap.add_argument("--report", default=os.path.join(here, "report_p2.json"))
    ap.add_argument("--trials", type=int, default=1)
    ap.add_argument("--judge", action="store_true",
                    help="用真实 LLM-as-Judge 替换 completion 占位检查（需 openai + key）")
    ap.add_argument("--llm-model", default=None, help="browseruse 用 LLM 模型名")
    ap.add_argument("--llm-base-url", default=None, help="browseruse 用 LLM 端点")
    ap.add_argument("--llm-key", default=None, help="browseruse 用 LLM API Key")
    args = ap.parse_args()

    # 可选 M4：统一 Tracer（缺失自动降级）
    tracer = get_tracer()

    # 可选 LLM-as-Judge
    judge = None
    if args.judge:
        from judge import LLMJudge
        judge = LLMJudge()
        if judge.available():
            print("[judge] 已启用真实 LLM-as-Judge（completion 维度）")
        else:
            print("[judge] 未检测到 OPENAI_API_KEY / openai 包，回退到占位启发式。")
            judge = None

    adapter = build_adapter(args.agent, args)
    adapter.tracer = tracer  # 注入埋点（若为 None 则不打点）

    dataset = load_dataset(args.dataset)
    report = evaluate(adapter, dataset, trials=args.trials, judge=judge)
    if tracer is not None:
        tracer.flush()

    # 包成 {subset: cases} 形状，兼容 feedback.py
    out = {"p2": report}
    json.dump(out, open(args.report, "w", encoding="utf-8"), ensure_ascii=False, indent=2)

    passed = sum(1 for r in report if r["passed"])
    edge = [r for r in report if r["edge"]]
    edge_pass = sum(1 for r in edge if r["passed"])
    print(f"=== P2 评测结果（agent={args.agent}, judge={'llm' if judge else 'heuristic'}）===")
    print(f"总通过率：{passed}/{len(report)} ({passed/len(report):.0%})")
    print(f"边缘用例：{edge_pass}/{len(edge)} 通过")
    print(f"报告已写出 -> {args.report}")
    print("\n失败用例（含原因）：")
    for r in report:
        if not r["passed"]:
            failed = [k for k, v in r["checks"].items() if not v]
            print(f"  [{r['id']}] {r['task'][:30]!r}  失败项={failed}")
            extra = r["checks"].get("completion_reason")
            if extra:
                print(f"         judge: {extra[:60]}")

    # 顺带跑门禁（退出码透传：阻断=1，通过=0）
    from quality_gate_p2 import gate
    print()
    sys.exit(gate(args.report))


if __name__ == "__main__":
    main()
