"""Run a separately instrumented NASHMI API, without changing application code.

Usage (from project root): python scripts/profile_nashmi_api.py --port 8001
This is LOCAL-ONLY diagnostics. No message text or database values are recorded.
"""
import argparse
import contextvars
import functools
import inspect
import json
import sys
import threading
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
TRACE_PATH = ROOT / "evals" / "performance_trace.jsonl"
_current = contextvars.ContextVar("nashmi_perf", default=None)
_file_lock = threading.Lock()


def record(component, elapsed_ms):
    trace = _current.get()
    if trace is not None:
        trace["samples"].append({"component": component, "ms": round(elapsed_ms, 3)})


def time_callable(name, func):
    if inspect.iscoroutinefunction(func):
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            start = time.perf_counter()
            try:
                return await func(*args, **kwargs)
            finally:
                record(name, (time.perf_counter() - start) * 1000)
        return async_wrapper

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start = time.perf_counter()
        try:
            return func(*args, **kwargs)
        finally:
            record(name, (time.perf_counter() - start) * 1000)
    return wrapper


def install():
    # Patch BEFORE importing the application: graph nodes and `from ollama import chat`
    # are bound during module imports and graph compilation.
    import ollama
    from langgraph.graph import StateGraph

    original_ollama_chat = ollama.chat
    ollama.chat = time_callable("ollama.chat", original_ollama_chat)

    original_add_node = StateGraph.add_node

    @functools.wraps(original_add_node)
    def add_node(self, *args, **kwargs):
        # NASHMI uses graph.add_node("name", callable).
        if args and isinstance(args[0], str) and len(args) >= 2 and callable(args[1]):
            node_name = args[0]
            args = (node_name, time_callable("node." + node_name, args[1]), *args[2:])
        elif isinstance(kwargs.get("action"), type(lambda: None)) and args:
            node_name = str(args[0])
            kwargs["action"] = time_callable("node." + node_name, kwargs["action"])
        return original_add_node(self, *args, **kwargs)

    StateGraph.add_node = add_node

    from db.session import engine
    from sqlalchemy import event

    @event.listens_for(engine, "before_cursor_execute")
    def before_sql(conn, cursor, statement, parameters, context, executemany):
        context._nashmi_perf_sql_start = time.perf_counter()

    @event.listens_for(engine, "after_cursor_execute")
    def after_sql(conn, cursor, statement, parameters, context, executemany):
        start = getattr(context, "_nashmi_perf_sql_start", None)
        if start is not None:
            record("sql.execute", (time.perf_counter() - start) * 1000)

    from apps.api import main as api_module

    class TimedGraph:
        def __init__(self, original):
            self._original = original

        def invoke(self, *args, **kwargs):
            return time_callable("langgraph.invoke", self._original.invoke)(*args, **kwargs)

        def __getattr__(self, item):
            return getattr(self._original, item)

    api_module.nashmi_graph = TimedGraph(api_module.nashmi_graph)
    app = api_module.app

    @app.middleware("http")
    async def profile_chat(request, call_next):
        if request.url.path != "/chat":
            return await call_next(request)
        trace = {"samples": [], "http_status": None}
        token = _current.set(trace)
        start = time.perf_counter()
        try:
            response = await call_next(request)
            trace["http_status"] = response.status_code
            return response
        except Exception:
            trace["http_status"] = 500
            raise
        finally:
            record("http.chat", (time.perf_counter() - start) * 1000)
            with _file_lock:
                TRACE_PATH.parent.mkdir(parents=True, exist_ok=True)
                with TRACE_PATH.open("a", encoding="utf-8") as handle:
                    handle.write(json.dumps(trace, separators=(",", ":")) + "\n")
            _current.reset(token)

    return app


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=8001)
    args = parser.parse_args()
    app = install()
    import uvicorn
    print(f"Profiling NASHMI at http://127.0.0.1:{args.port}")
    print(f"Trace file: {TRACE_PATH}")
    uvicorn.run(app, host="127.0.0.1", port=args.port, workers=1, reload=False)


if __name__ == "__main__":
    main()
