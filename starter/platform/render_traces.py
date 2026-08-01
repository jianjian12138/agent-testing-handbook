"""
把 traces.jsonl 渲染成**独立**的瀑布图 HTML（零依赖，双击即可在浏览器打开）。

- 不依赖任何 CDN / 服务器：数据以 JSON 内联进 <script>
- 左栏是按层级缩进的 span 树，右栏是时间轴水瀑（x = 相对开始时间，宽 = 耗时）
- 点击任意 span 展开它的 input / output / attributes 明细

运行：python render_traces.py traces.jsonl traces_report.html
（demo_trace.py 会自动调用它）
"""

import json
import sys

KIND_COLOR = {
    "root": "#6366f1",
    "plan": "#0ea5e9",
    "tool": "#10b981",
    "llm": "#f59e0b",
    "answer": "#ec4899",
}

TEMPLATE = r"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Agent Trace 瀑布图</title>
<style>
  :root { --bg:#ffffff; --fg:#1f2937; --muted:#6b7280; --line:#e5e7eb; --card:#f9fafb; }
  * { box-sizing: border-box; }
  body { margin:0; font-family: -apple-system, "Segoe UI", "PingFang SC", "Microsoft YaHei", sans-serif;
         background:var(--bg); color:var(--fg); font-size:13px; }
  header { padding:16px 20px; border-bottom:1px solid var(--line); }
  header h1 { margin:0 0 4px; font-size:18px; }
  header .meta { color:var(--muted); font-size:12px; }
  .summary { padding:10px 20px; display:flex; gap:16px; flex-wrap:wrap; }
  .pill { background:var(--card); border:1px solid var(--line); border-radius:999px; padding:4px 12px; }
  .pill.bad { color:#b91c1c; border-color:#fecaca; background:#fef2f2; }
  .trace { margin:12px 20px 28px; border:1px solid var(--line); border-radius:10px; overflow:hidden; }
  .trace > .t-head { background:var(--card); padding:8px 14px; font-weight:600; border-bottom:1px solid var(--line); }
  .row { display:flex; align-items:center; border-top:1px solid var(--line); cursor:pointer; }
  .row:hover { background:#f3f4f6; }
  .lbl { width:42%; padding:6px 10px 6px 14px; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }
  .dot { display:inline-block; width:9px; height:9px; border-radius:50%; margin-right:7px; vertical-align:middle; }
  .track { position:relative; flex:1; height:30px; }
  .bar { position:absolute; top:7px; height:16px; border-radius:4px; min-width:4px; }
  .dur { position:absolute; right:6px; top:7px; font-size:11px; color:var(--muted); }
  .detail { display:none; padding:10px 16px 14px 50px; background:#fafafa; border-top:1px dashed var(--line); }
  .detail pre { white-space:pre-wrap; word-break:break-all; background:#fff; border:1px solid var(--line);
                border-radius:6px; padding:8px 10px; margin:6px 0 0; font-size:12px; }
  .detail .k { color:var(--muted); margin-top:6px; }
  .open .detail { display:block; }
  .err { color:#b91c1c; }
</style>
</head>
<body>
<header>
  <h1>Agent Trace 瀑布图</h1>
  <div class="meta">由 starter/platform/render_traces.py 生成 · 数据源 traces.jsonl</div>
</header>
<div class="summary" id="summary"></div>
<div id="traces"></div>

<script id="data" type="application/json">__DATA__</script>
<script>
const DATA = JSON.parse(document.getElementById('data').textContent);
const COLOR = __COLOR__;

function depthOf(span, byId) {
  let d = 0, p = span.parent_id, guard = 0;
  while (p && byId[p] && guard < 50) { d++; p = byId[p].parent_id; guard++; }
  return d;
}
function esc(s) {
  return String(s).replace(/[&<>]/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;'}[c]));
}

let totalTraces = 0, badFaith = 0, totalSpans = 0;

DATA.forEach(trace => {
  totalTraces++;
  const spans = trace.spans;
  const byId = {};
  spans.forEach(s => byId[s.span_id] = s);
  let tmin = Infinity, tmax = -Infinity;
  spans.forEach(s => { tmin = Math.min(tmin, s.start); tmax = Math.max(tmax, s.end ?? s.start); });
  const spanMs = (tmax - tmin) || 1;

  const card = document.createElement('div');
  card.className = 'trace';
  const head = document.createElement('div');
  head.className = 't-head';
  head.textContent = 'Trace ' + trace.trace_id.slice(0, 8) + '  ·  ' + spans.length + ' spans';
  card.appendChild(head);

  spans.forEach(s => {
    totalSpans++;
    if (s.attributes && s.attributes.faithful === false) badFaith++;
    const d = depthOf(s, byId);
    const color = COLOR[s.kind] || '#9ca3af';
    const left = ((s.start - tmin) / spanMs) * 100;
    const width = Math.max(((s.duration_ms ?? 0) / spanMs) * 100, 0.6);

    const row = document.createElement('div');
    row.className = 'row';

    const lbl = document.createElement('div');
    lbl.className = 'lbl';
    lbl.innerHTML = '<span class="dot" style="background:' + color + '"></span>' +
                    '&nbsp;'.repeat(d) + esc(s.name) +
                    (s.status === 'error' ? ' <span class="err">⚠</span>' : '');

    const track = document.createElement('div');
    track.className = 'track';
    const bar = document.createElement('div');
    bar.className = 'bar';
    bar.style.left = left + '%';
    bar.style.width = width + '%';
    bar.style.background = color;
    const dur = document.createElement('div');
    dur.className = 'dur';
    dur.textContent = (s.duration_ms ?? 0) + ' ms';
    track.appendChild(bar); track.appendChild(dur);

    const wrap = document.createElement('div');
    wrap.style.flex = '1';
    wrap.appendChild(track);

    row.appendChild(lbl);
    row.appendChild(wrap);

    const detail = document.createElement('div');
    detail.className = 'detail';
    detail.innerHTML =
      '<div class="k">kind: ' + esc(s.kind) + '</div>' +
      '<div class="k">input:</div><pre>' + esc(JSON.stringify(s.input, null, 2)) + '</pre>' +
      '<div class="k">output:</div><pre>' + esc(JSON.stringify(s.output, null, 2)) + '</pre>' +
      '<div class="k">attributes:</div><pre>' + esc(JSON.stringify(s.attributes, null, 2)) + '</pre>';

    row.addEventListener('click', () => row.classList.toggle('open'));

    const rowWrap = document.createElement('div');
    rowWrap.appendChild(row);
    rowWrap.appendChild(detail);
    card.appendChild(rowWrap);
  });

  document.getElementById('traces').appendChild(card);
});

const sum = document.createElement('div');
sum.className = 'summary';
sum.innerHTML =
  '<span class="pill">Trace 数：' + totalTraces + '</span>' +
  '<span class="pill">Span 数：' + totalSpans + '</span>' +
  '<span class="pill' + (badFaith ? ' bad' : '') + '">不忠实(Faithful=false)：' + badFaith + '</span>';
document.getElementById('summary').appendChild(sum);
</script>
</body>
</html>
"""


def load(jsonl_path):
    spans = []
    with open(jsonl_path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                spans.append(json.loads(line))
    traces = {}
    for s in spans:
        traces.setdefault(s["trace_id"], []).append(s)
    for tid in traces:
        traces[tid].sort(key=lambda x: x["start"])
    return list(traces.values())


def render(jsonl_path="traces.jsonl", out_path="traces_report.html"):
    traces = load(jsonl_path)
    html = TEMPLATE.replace("__DATA__", json.dumps(traces, ensure_ascii=False))
    html = html.replace("__COLOR__", json.dumps(KIND_COLOR, ensure_ascii=False))
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(html)
    return out_path


if __name__ == "__main__":
    src = sys.argv[1] if len(sys.argv) > 1 else "traces.jsonl"
    dst = sys.argv[2] if len(sys.argv) > 2 else "traces_report.html"
    print("rendered ->", render(src, dst))
