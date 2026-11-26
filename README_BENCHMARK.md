# NASHMI: reproducible local latency benchmark

This package adds performance measurement **without modifying** existing API, booking, LangGraph, Ollama, or golden-evaluation source code. It needs only packages already installed by NASHMI.

## Install

Unzip the package at the root of your `nashmi` project. It adds:

- `scripts/profile_nashmi_api.py` — launches a separate, instrumented NASHMI API on `127.0.0.1:8001` (one worker)
- `scripts/benchmark_nashmi.py` — runs your existing safe golden scenarios against the profiled API, validates results and writes metrics

## Use (two PyCharm terminal tabs)

Terminal 1:

```bash
cd ~/nashmi
unset DATABASE_URL
python scripts/profile_nashmi_api.py --port 8001
```

Terminal 2, first smoke test:

```bash
cd ~/nashmi
unset DATABASE_URL
python scripts/benchmark_nashmi.py --max 2
```

If both scenarios PASS and a table is displayed, run the full benchmark:

```bash
python scripts/benchmark_nashmi.py
```

The full benchmark writes:

- `evals/performance_report.json` (aggregates)
- `evals/performance_table.md` (ready-to-copy Markdown table)
- `evals/performance_trace.jsonl` (per-request sample lists, no message text)

**No automatic Git commit or push** occurs.

## Coverage and interpretation

- `http.chat` is **server-side** request time: not network RTT.
- `langgraph.invoke` measures total graph invocation.
- `node.classify_intent` measures the intent-classification graph node.
- Other graph nodes are captured as `node.<name>`; extraction node timing includes downstream work.
- `ollama.chat` is a complete Ollama client call and includes its local communication.
- `sql.execute` measures each SQLAlchemy SQL cursor execution, not the entire ORM operation.
- Component timings **overlap** and should not be added together.
- A sample is measured per invocation; the number of SQL/LLM samples can differ from the number of requests.
- The tool checks every golden scenario against expected state/fields; **it refuses to publish a performance report if scenarios fail**.
- The existing `evals/latest_report.json` is left untouched.
- Existing golden scenarios may make read requests and normal API logging may still occur. They intentionally prohibit booking selection/confirmation/cancellation actions.

## Limitation

The server uses temporary process-level instrumentation (no instrumentation code is added to application modules). We have syntax-checked these files in the preparation environment, **but cannot run NASHMI's real Ollama/PostgreSQL stack on your Mac**, so the first 2-scenario smoke test is required. If it fails, send the traceback; do not publish numbers from that run.

Use the measured report, hardware details, model and run date in the GitHub README. Avoid presenting golden-scenario P50 as single-turn latency; the original evaluator times complete multi-turn scenarios.
