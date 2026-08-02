"""
平台 M5：Web 平台化骨架（文档 09 M5 里程碑）

零依赖（仅标准库 http.server），把本地评测变成一个「可点开看的仪表盘 + 可触发运行的 API」。
今天就能跑，不需要 Flask/FastAPI、不需要前端框架。

功能：
  - GET  /                     仪表盘：加载报告、查看通过率/各维度/失败下钻
  - GET  /api/report?path=...  返回报告统计 JSON（给前端/外部调用）
  - POST /api/eval/run         {agent, dataset, trials, judge} 触发一次 P2 评测，返回报告+统计
  - POST /api/dataset/upload   {json} 上传/覆盖数据集（写入 p2/uploads/）

运行：
    cd starter/platform
    python web.py                 # 默认 http://127.0.0.1:8000
    python web.py --port 9000

打开浏览器访问 http://127.0.0.1:8000 即可。点「运行 P2 评测」会在服务端跑 harness，
结果实时回显；点「加载报告」可回看历史 report_*.json。
"""

import os
import sys
import json
import html
import argparse
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse, parse_qs

HERE = os.path.dirname(os.path.abspath(__file__))
P2 = os.path.join(HERE, "..", "p2")
P2_UPLOADS = os.path.join(P2, "uploads")
os.makedirs(P2_UPLOADS, exist_ok=True)


# ---------------------------------------------------------------------------
# 统计聚合（兼容 P1 {regression,challenge} 与 P2 {p2} 两种报告形状）
# ---------------------------------------------------------------------------
def compute_stats(report):
    subsets = list(report.keys())
    total_cases, total_pass = 0, 0
    dims = {}
    edge_total = edge_pass = 0
    fails = []
    for subset, cases in report.items():
        for c in cases:
            total_cases += 1
            if c.get("passed"):
                total_pass += 1
            if c.get("edge"):
                edge_total += 1
                if c.get("passed"):
                    edge_pass += 1
            for k, v in (c.get("checks") or {}).items():
                if k == "completion_reason":
                    continue
                d = dims.setdefault(k, {"pass": 0, "total": 0})
                d["total"] += 1
                if v:
                    d["pass"] += 1
            if not c.get("passed"):
                fails.append({
                    "subset": subset,
                    "id": c.get("id"),
                    "task": c.get("task") or c.get("input"),
                    "intent": c.get("intent"),
                    "checks": {k: v for k, v in (c.get("checks") or {}).items()
                               if k != "completion_reason"},
                    "reason": (c.get("checks") or {}).get("completion_reason"),
                    "answer": c.get("answer"),
                })
    rate = (total_pass / total_cases) if total_cases else 1.0
    dim_rates = {k: (round(d["pass"] / d["total"], 4) if d["total"] else 1.0)
                 for k, d in dims.items()}
    return {
        "subsets": subsets,
        "total": total_cases,
        "passed": total_pass,
        "pass_rate": rate,
        "dimensions": dim_rates,
        "edge_total": edge_total,
        "edge_pass": edge_pass,
        "edge_rate": (edge_pass / edge_total) if edge_total else None,
        "failures": fails,
    }


# ---------------------------------------------------------------------------
# 触发一次 P2 评测（服务端进程内执行 harness）
# ---------------------------------------------------------------------------
def run_eval(agent="dummy", dataset=None, trials=1, judge=False):
    sys.path.insert(0, P2)
    from harness import evaluate, load_dataset
    from adapter import DummyBrowserAgent, RealisticAgent, get_tracer

    agent = agent or "dummy"
    if agent == "realistic":
        ad = RealisticAgent()
    else:
        ad = DummyBrowserAgent()
    ad.tracer = get_tracer()

    ds_path = dataset or os.path.join(P2, "dataset_p2.json")
    data = load_dataset(ds_path)

    j = None
    if judge:
        from judge import LLMJudge
        j = LLMJudge()
        if not j.available():
            j = None
    report_list = evaluate(ad, data, trials=int(trials), judge=j)
    if ad.tracer is not None:
        ad.tracer.flush()

    report = {"p2": report_list}
    out_path = os.path.join(P2, "report_p2.json")
    json.dump(report, open(out_path, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    return out_path, compute_stats(report)


# ---------------------------------------------------------------------------
# HTML 渲染（浅色主题，纯 CSS 柱状图，无前端框架）
# ---------------------------------------------------------------------------
PAGE = """<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Agent 测试平台 · M5 仪表盘</title>
<style>
  :root {{
    --bg:#f7f8fa; --card:#fff; --ink:#1f2329; --muted:#6b7280;
    --line:#e5e7eb; --ok:#16a34a; --bad:#dc2626; --accent:#2563eb; --warn:#d97706;
  }}
  * {{ box-sizing:border-box; }}
  body {{ margin:0; background:var(--bg); color:var(--ink);
    font:14px/1.6 -apple-system,"Segoe UI",Roboto,"PingFang SC","Microsoft YaHei",sans-serif; }}
  header {{ background:var(--card); border-bottom:1px solid var(--line); padding:14px 22px; }}
  header h1 {{ margin:0; font-size:18px; }}
  header small {{ color:var(--muted); }}
  main {{ max-width:1080px; margin:0 auto; padding:22px; }}
  .card {{ background:var(--card); border:1px solid var(--line); border-radius:10px;
    padding:18px; margin-bottom:18px; }}
  .row {{ display:flex; gap:12px; flex-wrap:wrap; align-items:center; }}
  .stat {{ flex:1; min-width:140px; background:var(--card); border:1px solid var(--line);
    border-radius:10px; padding:14px 16px; }}
  .stat .n {{ font-size:26px; font-weight:700; }}
  .stat .l {{ color:var(--muted); font-size:12px; }}
  input,select,textarea,button {{ font:inherit; padding:8px 10px; border:1px solid var(--line);
    border-radius:8px; background:#fff; color:var(--ink); }}
  button {{ background:var(--accent); color:#fff; border:none; cursor:pointer; }}
  button.ghost {{ background:#fff; color:var(--accent); border:1px solid var(--accent); }}
  label {{ color:var(--muted); font-size:12px; margin-right:6px; }}
  .bar {{ height:14px; background:var(--line); border-radius:7px; overflow:hidden; margin:4px 0 10px; }}
  .bar > i {{ display:block; height:100%; background:var(--ok); }}
  .bar.bad > i {{ background:var(--bad); }}
  .kv {{ display:flex; justify-content:space-between; font-size:13px; }}
  table {{ width:100%; border-collapse:collapse; font-size:13px; }}
  th,td {{ text-align:left; padding:8px 10px; border-bottom:1px solid var(--line); vertical-align:top; }}
  th {{ color:var(--muted); font-weight:600; }}
  .tag {{ display:inline-block; padding:1px 7px; border-radius:6px; font-size:11px;
    background:#eef2ff; color:var(--accent); margin-right:4px; }}
  .tag.bad {{ background:#fef2f2; color:var(--bad); }}
  .tag.ok {{ background:#f0fdf4; color:var(--ok); }}
  details {{ margin:6px 0; }}
  summary {{ cursor:pointer; color:var(--accent); }}
  pre {{ background:#0f172a; color:#e2e8f0; padding:10px; border-radius:8px; overflow:auto; }}
  .muted {{ color:var(--muted); }}
</style></head>
<body>
<header><h1>Agent 测试平台 · M5 仪表盘</h1>
<small>零依赖 Web 平台骨架 · 对应文档 09 M5 里程碑</small></header>
<main>

  <div class="card">
    <div class="row">
      <label>报告路径</label>
      <input id="path" style="flex:2;min-width:260px"
        placeholder="如 ../p2/report_p2.json" value="{path}">
      <button onclick="loadReport()">加载报告</button>
      <button class="ghost" onclick="document.getElementById('run').style.display='block'">运行 P2 评测</button>
    </div>

    <div id="run" style="display:none; margin-top:14px; padding-top:14px; border-top:1px solid var(--line);">
      <div class="row">
        <label>Agent</label>
        <select id="agent"><option value="dummy">dummy（含缺陷）</option>
          <option value="realistic">realistic（正确）</option></select>
        <label>数据集</label>
        <input id="dataset" style="flex:1;min-width:200px" placeholder="留空用 dataset_p2.json">
        <label>trials</label><input id="trials" value="1" style="width:64px">
        <label><input type="checkbox" id="judge"> LLM-as-Judge</label>
        <button onclick="runEval()">运行</button>
      </div>
      <div class="row" style="margin-top:10px">
        <label>上传数据集(JSON)</label>
        <textarea id="ds" rows="3" style="flex:1;min-width:300px"
          placeholder="请粘贴用例数组 JSON（结构见 dataset_p2.json），例如单条：id / task / intent / expected_tools ..."></textarea>
        <button class="ghost" onclick="uploadDS()">上传</button>
      </div>
    </div>
  </div>

  <div id="dash">{dash}</div>
</main>

<script>
function esc(s){{ return (s==null?'':String(s)).replace(/[&<>]/g,c=>({{'&':'&amp;','<':'&lt;','>':'&gt;'}}[c])); }}
async function loadReport() {{
  const p = document.getElementById('path').value;
  const r = await fetch('/api/report?path=' + encodeURIComponent(p));
  const j = await r.json();
  render(j, p);
}}
async function runEval() {{
  const body = {{
    agent: document.getElementById('agent').value,
    dataset: document.getElementById('dataset').value || null,
    trials: +document.getElementById('trials').value || 1,
    judge: document.getElementById('judge').checked,
  }};
  const r = await fetch('/api/eval/run', {{method:'POST',
    headers:{{'Content-Type':'application/json'}}, body: JSON.stringify(body)}});
  const j = await r.json();
  document.getElementById('path').value = j.path;
  render(j.stats, j.path);
}}
async function uploadDS() {{
  const txt = document.getElementById('ds').value;
  const r = await fetch('/api/dataset/upload', {{method:'POST',
    headers:{{'Content-Type':'application/json'}}, body: JSON.stringify({{json: txt}})}});
  const j = await r.json();
  alert(j.ok ? ('已写入 '+j.path+'，可点「运行 P2 评测」使用') : ('失败：'+j.error));
}}
function bar(rate) {{
  const pct = (rate*100).toFixed(0);
  const cls = rate>=1 ? '' : 'bad';
  return '<div class="bar '+cls+'"><i style="width:'+pct+'%"></i></div>';
}}
function render(j, path) {{
  if (j.error) {{ document.getElementById('dash').innerHTML = '<div class="card">错误：'+esc(j.error)+'</div>'; return; }}
  const pr = (j.pass_rate*100).toFixed(0);
  let h = '<div class="row">';
  h += '<div class="stat"><div class="n">'+pr+'%</div><div class="l">总通过率（'+j.passed+'/'+j.total+'）</div></div>';
  h += '<div class="stat"><div class="n">'+j.subsets.join(', ')+'</div><div class="l">子集</div></div>';
  if (j.edge_total) h += '<div class="stat"><div class="n">'+(j.edge_rate!=null?(j.edge_rate*100).toFixed(0):'-')+'%</div><div class="l">边缘用例（'+j.edge_pass+'/'+j.edge_total+'）</div></div>';
  h += '</div>';

  h += '<div class="card"><h3 style="margin-top:0">各维度通过率</h3>';
  for (const [k,v] of Object.entries(j.dimensions)) {{
    h += '<div class="kv"><span>'+esc(k)+'</span><span>'+ (v*100).toFixed(0) +'%</span></div>';
    h += bar(v);
  }}
  h += '</div>';

  h += '<div class="card"><h3 style="margin-top:0">失败用例下钻（'+j.failures.length+'）</h3>';
  if (!j.failures.length) h += '<p class="muted">无失败 🎉</p>';
  h += '<table><tr><th>ID</th><th>任务/输入</th><th>未通过维度</th></tr>';
  for (const f of j.failures) {{
    const bad = Object.keys(f.checks).filter(k=>!f.checks[k]);
    let tags = bad.map(k=>'<span class="tag bad">'+esc(k)+'</span>').join('');
    if (f.reason) tags += '<span class="tag">judge: '+esc(f.reason.slice(0,40))+'</span>';
    h += '<tr><td>'+esc(f.id)+'</td><td>'+esc(f.task)+
         (f.intent?' <span class="tag">'+esc(f.intent)+'</span>':'')+'</td><td>'+tags+'</td></tr>';
    if (f.answer) h += '<tr><td></td><td colspan="2" class="muted">答：'+esc(f.answer.slice(0,80))+'</td></tr>';
  }}
  h += '</table></div>';
  document.getElementById('dash').innerHTML = h;
}}
{{INIT}}
</script>
</body></html>"""


def render_dash(stats=None, path=""):
    dash = ""
    if stats is None:
        dash = '<div class="card muted">输入报告路径后点「加载报告」，或在右上「运行 P2 评测」触发一次评测。</div>'
    else:
        dash = ""  # 实际由前端 JS 渲染；服务端预渲染一版静态摘要
        # 静态摘要（无 JS 也能看）
        pr = f"{stats['pass_rate']*100:.0f}%"
        dash = f'<div class="card"><b>总通过率 {pr}</b> （{stats["passed"]}/{stats["total"]}）'
        dash += f' · 子集：{", ".join(stats["subsets"])} · 失败：{len(stats["failures"])}'
        if stats["edge_total"]:
            dash += f' · 边缘 {stats["edge_pass"]}/{stats["edge_total"]}'
        dash += '<br><span class="muted">维度：' + "，".join(
            f'{k} {v*100:.0f}%' for k, v in stats["dimensions"].items()) + '</span></div>'
    init = ""
    if stats is not None:
        init = "render(" + json.dumps(stats, ensure_ascii=False) + "," + json.dumps(path, ensure_ascii=False) + ");"
    return PAGE.format(path=html.escape(path or ""), dash=dash, INIT=init)


# ---------------------------------------------------------------------------
# HTTP 处理
# ---------------------------------------------------------------------------
class Handler(BaseHTTPRequestHandler):
    def _send(self, code, body, ctype="application/json; charset=utf-8"):
        if isinstance(body, (dict, list)):
            body = json.dumps(body, ensure_ascii=False)
        if isinstance(body, str):
            body = body.encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        u = urlparse(self.path)
        if u.path == "/" or u.path == "":
            q = parse_qs(u.query)
            path = q.get("path", [""])[0]
            stats = None
            if path:
                try:
                    full = path if os.path.isabs(path) else os.path.join(HERE, path)
                    report = json.load(open(full, encoding="utf-8"))
                    stats = compute_stats(report)
                except Exception as e:
                    stats = {"error": str(e)}
            self._send(200, render_dash(stats, path), "text/html; charset=utf-8")
        elif u.path == "/api/report":
            q = parse_qs(u.query)
            path = q.get("path", [""])[0]
            if not path:
                return self._send(400, {"error": "missing path"})
            try:
                full = path if os.path.isabs(path) else os.path.join(HERE, path)
                report = json.load(open(full, encoding="utf-8"))
                return self._send(200, {"path": path, "stats": compute_stats(report)})
            except Exception as e:
                return self._send(404, {"error": str(e)})
        else:
            self._send(404, {"error": "not found"})

    def do_POST(self):
        u = urlparse(self.path)
        length = int(self.headers.get("Content-Length", 0))
        raw = self.rfile.read(length) if length else b"{}"
        try:
            payload = json.loads(raw or b"{}")
        except Exception:
            payload = {}

        if u.path == "/api/eval/run":
            try:
                path, stats = run_eval(
                    agent=payload.get("agent", "dummy"),
                    dataset=payload.get("dataset"),
                    trials=payload.get("trials", 1),
                    judge=bool(payload.get("judge")),
                )
                rel = os.path.relpath(path, HERE).replace("\\", "/")
                return self._send(200, {"path": rel, "stats": stats})
            except Exception as e:
                return self._send(500, {"error": str(e)})

        elif u.path == "/api/dataset/upload":
            try:
                data = json.loads(payload.get("json", "null"))
                if not isinstance(data, list):
                    return self._send(400, {"ok": False, "error": "json 必须是用例数组"})
                out = os.path.join(P2_UPLOADS, "dataset_upload.json")
                json.dump(data, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
                rel = os.path.relpath(out, HERE).replace("\\", "/")
                return self._send(200, {"ok": True, "path": rel, "count": len(data)})
            except Exception as e:
                return self._send(400, {"ok": False, "error": str(e)})
        else:
            self._send(404, {"error": "not found"})

    def log_message(self, *a):
        pass  # 安静


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=8000)
    ap.add_argument("--host", default="127.0.0.1")
    args = ap.parse_args()
    srv = HTTPServer((args.host, args.port), Handler)
    print(f"M5 Web 平台已启动： http://{args.host}:{args.port}")
    print("按 Ctrl+C 停止。")
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        print("\n已停止。")


if __name__ == "__main__":
    main()
