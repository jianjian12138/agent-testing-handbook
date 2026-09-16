# Agent Testing Handbook

> A practical transition roadmap + runnable starter kit for **senior automation test engineers** moving into Agent / LLM quality engineering.
> Version: v1.1 · Updated: 2026-09-15 · Repo: https://github.com/jianjian12138/agent-testing-handbook

[![Stars](https://img.shields.io/github/stars/jianjian12138/agent-testing-handbook?style=social)](https://github.com/jianjian12138/agent-testing-handbook/stargazers)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.11%2B-blue.svg)](https://www.python.org/)
[![CI Quality Gate](https://github.com/jianjian12138/agent-testing-handbook/actions/workflows/agent-eval.yml/badge.svg)](https://github.com/jianjian12138/agent-testing-handbook/actions/workflows/agent-eval.yml)
[![Docs](https://img.shields.io/badge/docs-12%20chapters-orange.svg)](docs/)

**[中文文档](README.md)**

---

## TL;DR

> You are not starting from zero — you are doing a **tech-stack pivot**: upgrading from "test engineer who writes assertions" to "Agent Quality Engineer (AI QE) who designs graders".
> This handbook is not a科普 read. It is an **actionable battle plan with runnable code** — you can run your first Agent eval on day one and watch it go red → green.

---

## What you get

- 📚 **11 progressive chapters** (cognitive shift → metrics → methodology → dataset engineering → tooling → production monitoring → 5 hands-on projects → platform build → references → 12-week checklist)
- 🧪 **A customer-service Agent with a built-in bug + full eval scaffolding** (`starter/`, **runs fully locally, no API key required**)
- 🚦 **A real CI quality gate**: the buggy version is automatically blocked by the pipeline, proving the gate is not a decoration
- 🕸️ **Zero-dependency Trace waterfall + Web dashboard**: see exactly which tool the Agent called and why it failed
- 🗺️ **A 12-week learning plan** with weekly tasks and acceptance criteria

---

## Who this is for / not for

| ✅ For you if… | ❌ Probably not if… |
| --- | --- |
| You are an automation/functional test engineer pivoting to Agent quality | You want to "learn to train LLMs in 3 days" |
| You know pytest / test-case design / CI but lack AI fundamentals | You are already an LLM algorithm engineer (too basic for you) |
| You want **shippable eval-engineering skills**, not toy demos | You only want concept diagrams and won't run code |
| You are building or evaluating an Agent test platform | — |

---

## 📂 Chapter map (read in order, or jump)

| # | Chapter | Solves | Effort |
| --- | --- | --- | --- |
| 01 | [Cognitive Shift: from automation to Agent testing](docs/01-认知迁移.md) | Mental model + terminology map | 1 day |
| 02 | [Anatomy of the Agent under test](docs/02-被测对象解剖.md) | 6 modules + failure modes | 3 days |
| 03 | [Metrics: what to measure](docs/03-指标体系.md) | 5-dimension framework + pass@k / pass^k | 3 days |
| 04 | [Methodology: how to evaluate](docs/04-评测方法论.md) | 3 grader types, LLM-as-Judge, Agent-as-Judge | 5 days |
| 05 | [Dataset engineering](docs/05-数据集工程.md) | 3 construction ways + golden set + layering | 4 days |
| 06 | [Toolchain in practice](docs/06-工具链实战.md) | DeepEval/promptfoo/RAGAS/Langfuse/Inspect AI | 5 days |
| 07 | [Observability & production monitoring](docs/07-可观测与生产监控.md) | OTel tracing + online eval + failure backflow | 4 days |
| 08 | [Five hands-on projects](docs/08-实战项目.md) | **Core** Hello Eval → multi-Agent eval | 5 weeks |
| 09 | [Building an Agent test platform](docs/09-平台搭建.md) | **Core** architecture + 6 milestones | 4 weeks |
| 10 | [References & Benchmark index](docs/10-资料索引.md) | Sources, papers, repos, benchmarks | as-needed |
| 11 | [12-week checklist](docs/11-学习计划打卡表.md) | Weekly tasks + acceptance | full |

Runnable starter code: [`starter/`](starter/) — a buggy customer-service Agent + full eval scaffolding (platform M1–M5 implemented, including **P2 open-source Agent eval** and a **zero-dependency `web.py` dashboard**).

---

## 🚀 Quick start (run your first Agent eval in 10 minutes)

```bash
git clone https://github.com/jianjian12138/agent-testing-handbook.git
cd agent-testing-handbook/starter

# Run the minimal eval (no API key, pure local)
pytest evals/test_p1_basic.py -v
# → you'll see test_fake_order_is_faithful FAIL:
#   the Agent fabricates an order status when the lookup is empty
#   (this is the "empty-result trap" / Faithfulness the handbook teaches)

# Fix the bug: point run_agent to run_agent_fixed, re-run → all green
```

> ✅ **Verified runnable** (Python 3.11, pytest 9.x): `2 passed, 1 failed` (buggy) → `3 passed` after fix.

Platform-level loop:

```bash
cd platform
python run_suite.py --report report.json               # buggy Agent: 18/20
python quality_gate.py report.json                    # 🚫 blocked (regression 90% < 100%)
AGENT_MODE=fixed python run_suite.py --report r2.json # fixed: 20/20
python quality_gate.py r2.json                        # ✅ passed
python demo_trace.py                                  # Trace waterfall → traces_report.html
```

Full commands in [`starter/README.md`](starter/README.md) (P2 open-source Agent eval, M5 Web dashboard).

---

## 🧭 12-week plan overview

| Phase | Weeks | Goal | Acceptance (excerpt) |
| --- | --- | --- | --- |
| I · Cognition & minimal loop | 1–2 | Run your first Agent eval | Explain how `ToolCorrectnessMetric` score is computed |
| II · Methodology & datasets | 3–5 | Design an eval plan independently | Judge vs human agreement ≥ 80% |
| III · Tooling & engineering | 6–8 | Eval as a CI gate | A deliberately degraded PR is blocked by pipeline |
| IV · Platformization | 9–12 | Build a demo-able platform | Non-tech colleague can self-serve an eval and read the report |

---

## 🛡️ Three common pitfalls

1. **Diving into Transformer papers** — you don't need to train models; focus on eval engineering.
2. **Chasing frameworks** — tools take 3 days; metrics & datasets are the real value. Pick one and go deep.
3. **Building a platform immediately** — a platform built before 500 real cases is guaranteed wrong. Run manually until it hurts.

---

## 🎯 Your differentiation

Most Agent evaluators fall into three camps: algorithm engineers (rough test cases), app developers (no quality methodology), traditional testers (lack AI literacy).
**You are the fourth: an Agent Quality Engineer who combines quality methodology + engineering + patched AI literacy** — a scarce role in 2026. Your edge is not "knowing DeepEval", but: designing a quality exit standard from scratch, operating a golden dataset, and building eval platforms the whole team reuses.

---

## 📎 Relation to other projects

This repo focuses on the **learning path + minimal runnable scaffolding for Agent / LLM eval engineering**. It is often confused with the author's other repos — clarified here:

| Project | What it is | How it differs |
| --- | --- | --- |
| **luban-test-skill** | An AI test-platform **generator** (FastAPI+LangGraph+Vue3; API/UI/DB/perf/security testing, RAG & LLM-as-Judge) | It is a "tool that builds eval platforms"; this handbook is "materials + exercises that make you an evaluator". Zero-dependency and learning-first. |
| aotutest / Testing / automation | Traditional automation testing practice | Traditional automation; this repo targets Agent/LLM quality engineering. |
| baize-agent | A local Agent runtime (pure Python stdlib) | It is one of the "Agents under test"; this handbook teaches you **how to evaluate** it. |

> In one line: **luban-test-skill helps you build the eval platform; this handbook helps you become the person who does the evaluating.** They complement, not replace, each other.

---

## ⚙️ Runs on GitHub (CI quality gate / P3)

`.github/workflows/agent-eval.yml` runs on every push/PR:

1. **Main gate** `quality-gate`: runs the production Agent (`AGENT_MODE=fixed`); must pass tiered gates or block merge.
2. **Gate self-check** `gate-catches-regression`: runs the deliberately buggy version (`AGENT_MODE=buggy`); the gate **must catch it** — proving it works.

Watch the gate catch a bad change:

```bash
git commit -am "chore: introduce a regression (demo CI block)" && git push
# → quality-gate turns red and blocks; gate-catches-regression shows "self-check passed"
```

---

## 📚 Sources

Synthesized from first-hand sources (full index in [Chapter 10](docs/10-资料索引.md)):

- Anthropic Engineering《Demystifying evals for AI agents》
- Microsoft Research《AgentEval》
- AWS《Agent-EvalKit》
- AliExpress Tech Agent evaluation system, Qborfy AI《AI Agent 评测工程实践》
- Framework docs: DeepEval / promptfoo / RAGAS / Langfuse / Opik / Inspect AI / Giskard

---

## 🤝 Contribute

Issues & PRs welcome. If this helped you, a **Star** is the best support ⭐

---

## 📄 License

[MIT](LICENSE) — free to learn, adapt, and use commercially; please keep attribution.
