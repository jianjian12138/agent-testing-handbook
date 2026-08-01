"""
平台 M4：Trace 可观测层（对应文档 07 / 文档 09 M4 里程碑）

目标：给 Agent 的「规划 → 调工具 → 生成」每一步都打点，形成一条可回放的 Trace。
无论你用 Langfuse 还是 OpenTelemetry，都复用**同一套埋点代码**，靠环境变量切换后端。

三种后端（get_tracer() 自动选择，埋点代码不用改）：
1. LocalRecorder（默认，零依赖）
   - 把每个 span 写进 traces.jsonl，再用 render_traces.py 生成独立瀑布图 HTML
   - 今天就能跑，不需要任何 pip 安装、不需要账号
2. OtelRecorder（需 pip install opentelemetry-sdk opentelemetry-exporter-otlp）
   - 数据发往 OTEL_EXPORTER_OTLP_ENDPOINT
   - 该端点可指向本地 collector，或 Langfuse 的 OTLP 端点
     （https://cloud.langfuse.com/api/public/otel，配合 LANGFUSE_PUBLIC_KEY/SECRET）
3. LangfuseRecorder（需 pip install langfuse，并设置 LANGFUSE_PUBLIC_KEY/SECRET/HOST）
   - 走 Langfuse 原生 SDK，自带水瀑图 + 成本/打分面板

统一 API（埋点只写这一套）：
    tracer = get_tracer()
    with tracer.root("agent.run", input=user_input) as root:
        with root.span("plan", input=...) as sp:
            sp.set_attribute("tool", "query_order")
        with root.span("tool:query_order", input=..., output=...) as tsp:
            tsp.set_attribute("faithful", True)
"""

import os
import sys
import json
import time
import uuid


# ---------------------------------------------------------------------------
# 统一埋点原语
# ---------------------------------------------------------------------------
class Span:
    """一次调用/一个步骤的记录单元。作为 context manager 使用。"""

    KINDS = ("root", "plan", "tool", "llm", "answer")

    def __init__(self, tracer, recorder, name, kind, parent, input=None, attributes=None):
        self.tracer = tracer
        self.recorder = recorder
        self.name = name
        self.kind = kind if kind in self.KINDS else "tool"
        self.trace_id = parent.trace_id if parent else uuid.uuid4().hex
        self.span_id = uuid.uuid4().hex
        self.parent_id = parent.span_id if parent else None
        self.input = input
        self.output = None
        self.attributes = dict(attributes or {})
        self.status = "ok"
        self.start = time.time() * 1000
        self.end = None

    def __enter__(self):
        self.recorder.begin_span(self)
        return self

    def __exit__(self, exc_type, exc, tb):
        if exc_type is not None:
            self.status = "error"
            self.attributes["error"] = f"{exc_type.__name__}: {exc}"
        self.end = time.time() * 1000
        self.recorder.end_span(self)
        return False  # 不吞异常

    def set_attribute(self, key, value):
        self.attributes[key] = value

    def span(self, name, kind="tool", input=None, attributes=None):
        """在 current span 下开一个子 span。"""
        return Span(self.tracer, self.recorder, name, kind, self, input, attributes)

    def to_dict(self):
        return {
            "trace_id": self.trace_id,
            "span_id": self.span_id,
            "parent_id": self.parent_id,
            "name": self.name,
            "kind": self.kind,
            "input": self.input,
            "output": self.output,
            "start": round(self.start, 3),
            "end": round(self.end, 3) if self.end else None,
            "duration_ms": round(self.end - self.start, 2) if self.end else None,
            "status": self.status,
            "attributes": self.attributes,
        }


class Tracer:
    def __init__(self, recorder):
        self.recorder = recorder

    def root(self, name, kind="root", input=None, attributes=None):
        return Span(self, self.recorder, name, kind, None, input, attributes)

    def flush(self):
        self.recorder.flush()


# ---------------------------------------------------------------------------
# 后端 1：LocalRecorder（零依赖，默认）
# ---------------------------------------------------------------------------
class LocalRecorder:
    def __init__(self, path="traces.jsonl"):
        self.path = path
        self._f = open(path, "w", encoding="utf-8")  # 每次新建 Tracer 都覆盖旧文件

    def begin_span(self, span):
        pass

    def end_span(self, span):
        self._f.write(json.dumps(span.to_dict(), ensure_ascii=False) + "\n")
        self._f.flush()

    def flush(self):
        try:
            self._f.close()
        except Exception:
            pass


# ---------------------------------------------------------------------------
# 后端 2：OtelRecorder（可选，需安装 opentelemetry 包）
# ---------------------------------------------------------------------------
class OtelRecorder:
    def __init__(self):
        from opentelemetry import trace as otel_trace
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import BatchSpanProcessor
        from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
        from opentelemetry.trace import set_span_in_context

        endpoint = os.environ.get("OTEL_EXPORTER_OTLP_ENDPOINT")
        provider = TracerProvider()
        provider.add_span_processor(BatchSpanProcessor(OTLPSpanExporter(endpoint=endpoint)))
        otel_trace.set_tracer_provider(provider)
        self._otel = otel_trace.get_tracer("agent-testing")
        self._set_ctx = set_span_in_context
        self._active = {}  # our span_id -> otel span
        print(f"[OtelRecorder] OTLP endpoint={endpoint}")

    def begin_span(self, span):
        parent_ctx = None
        if span.parent_id and span.parent_id in self._active:
            parent_ctx = self._set_ctx(self._active[span.parent_id])
        ot = self._otel.start_span(span.name, context=parent_ctx)
        self._active[span.span_id] = ot

    def end_span(self, span):
        ot = self._active.pop(span.span_id, None)
        if not ot:
            return
        if span.input is not None:
            ot.set_attribute("input", json.dumps(span.input, ensure_ascii=False))
        if span.output is not None:
            ot.set_attribute("output", json.dumps(span.output, ensure_ascii=False))
        for k, v in span.attributes.items():
            try:
                ot.set_attribute(k, v)
            except Exception:
                ot.set_attribute(k, str(v))
        if span.status == "error":
            ot.set_status(ot.status.ERROR)
        ot.end()

    def flush(self):
        from opentelemetry import trace as otel_trace
        try:
            otel_trace.get_tracer_provider().shutdown()
        except Exception:
            pass


# ---------------------------------------------------------------------------
# 后端 3：LangfuseRecorder（可选，需安装 langfuse 包）
# ---------------------------------------------------------------------------
class LangfuseRecorder:
    def __init__(self):
        from langfuse import Langfuse

        self._lf = Langfuse()  # 读 LANGFUSE_PUBLIC_KEY / SECRET / HOST 环境变量
        self._active = {}      # our span_id -> (trace_id, observation_id, kind)

    def begin_span(self, span):
        parent = self._active.get(span.parent_id) if span.parent_id else None
        if parent is None:
            # 根：建一条 trace
            trace = self._lf.trace(name=span.name, input=span.input)
            self._active[span.span_id] = (trace.id, None, "trace")
            return
        parent_trace_id, _, _ = parent
        # 子：建一个 generation/span
        obs = self._lf.span(
            trace_id=parent_trace_id,
            name=span.name,
            input=span.input,
            metadata={"kind": span.kind},
        )
        self._active[span.span_id] = (parent_trace_id, obs.id, "span")

    def end_span(self, span):
        rec = self._active.pop(span.span_id, None)
        if not rec:
            return
        trace_id, obs_id, kind = rec
        if kind == "trace":
            self._lf.trace(id=trace_id, output=span.output,
                           metadata={"status": span.status, **span.attributes})
        else:
            self._lf.span(id=obs_id, trace_id=trace_id, output=span.output,
                          metadata={"status": span.status, **span.attributes})

    def flush(self):
        self._lf.flush()


# ---------------------------------------------------------------------------
# 后端选择
# ---------------------------------------------------------------------------
def get_tracer():
    """按环境变量选后端；可选后端缺失时自动降级到本地零依赖后端。"""
    if os.environ.get("LANGFUSE_PUBLIC_KEY"):
        try:
            return Tracer(LangfuseRecorder())
        except ImportError:
            print("[warn] 未安装 langfuse，请用 `pip install langfuse`；降级到 LocalRecorder")
        except Exception as e:
            print(f"[warn] Langfuse 初始化失败：{e}；降级到 LocalRecorder")
    if os.environ.get("OTEL_EXPORTER_OTLP_ENDPOINT"):
        try:
            return Tracer(OtelRecorder())
        except ImportError:
            print("[warn] 未安装 opentelemetry，请用 `pip install opentelemetry-sdk "
                  "opentelemetry-exporter-otlp`；降级到 LocalRecorder")
        except Exception as e:
            print(f"[warn] OTel 初始化失败：{e}；降级到 LocalRecorder")
    return Tracer(LocalRecorder())


if __name__ == "__main__":
    # 自测：无依赖跑通一条 trace
    t = get_tracer()
    with t.root("demo", input="查订单 12345") as r:
        with r.span("plan", kind="plan", input="查订单 12345") as sp:
            sp.set_attribute("tool", "query_order")
            sp.output = {"tool": "query_order", "ids": ["12345"]}
        with r.span("tool:query_order", kind="tool", input={"order_id": "12345"}) as tsp:
            tsp.output = {"status": "配送中"}
            tsp.set_attribute("faithful", True)
        r.output = {"answer": "配送中"}
    t.flush()
    print("self-test OK -> traces.jsonl")
