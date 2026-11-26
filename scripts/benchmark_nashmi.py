"""Score NASHMI's existing safe golden scenarios and report real per-component latency.

Run from project root, with the profiled API running on port 8001:
    python scripts/benchmark_nashmi.py --url http://127.0.0.1:8001

Reports are not produced when any scenario fails, or the trace count mismatches.
"""
import argparse
import json
import math
import statistics
import sys
import time
import uuid
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from evals.run_evals import evaluate, send_chat, validate_scenarios  # noqa: E402

DATASET = ROOT / "evals" / "golden_scenarios.json"
TRACE = ROOT / "evals" / "performance_trace.jsonl"
REPORT = ROOT / "evals" / "performance_report.json"
TABLE = ROOT / "evals" / "performance_table.md"


def stats(values):
    if not values:
        return None
    ordered = sorted(values)
    return {
        "samples": len(values),
        "mean_ms": round(statistics.mean(values), 1),
        "median_ms": round(statistics.median(values), 1),
        "p95_ms": round(ordered[max(0, math.ceil(0.95 * len(values)) - 1)], 1),
    }


def extract_traces(start_offset):
    with TRACE.open("r", encoding="utf-8") as handle:
        handle.seek(start_offset)
        return [json.loads(line) for line in handle if line.strip()]


def summarize_traces(traces):
    components = defaultdict(list)
    node_names = set()
    for trace in traces:
        for entry in trace["samples"]:
            name = entry["component"]
            components[name].append(float(entry["ms"]))
            if name.startswith("node."):
                node_names.add(name)
    # Notes: node timings include downstream LLM/DB operations; they overlap
    # with graph and HTTP totals. SQL is cursor execution time, not full ORM time.
    order = ["http.chat", "langgraph.invoke", "node.classify_intent", "ollama.chat", "sql.execute"]
    for name in sorted(node_names):
        if name not in order:
            order.append(name)
    return {name: stats(components[name]) for name in order if components[name]}


def table_for(summary):
    display = {
        "http.chat": "End-to-end `/chat` server processing",
        "langgraph.invoke": "LangGraph invocation",
        "node.classify_intent": "Intent classification node",
        "ollama.chat": "Ollama LLM call",
        "sql.execute": "SQL cursor execution (per query)",
    }
    lines = ["# NASHMI Measured Performance", "", "| Component | Samples | Mean | Median | P95 |", "|---|---:|---:|---:|---:|"]
    for key, values in summary.items():
        label = display.get(key, key.replace("node.", "LangGraph node: "))
        lines.append(f"| {label} | {values['samples']} | {values['mean_ms']} ms | {values['median_ms']} ms | {values['p95_ms']} ms |")
    lines += ["", "Measured locally on the profiled API using the existing read-only golden search scenarios.",
              "Timings overlap (node, LLM, SQL, graph, HTTP); do not add rows together.",
              "SQL duration measures DB cursor execution, not complete SQLAlchemy ORM work.",
              "HTTP duration is server-side processing; it excludes client/network overhead.",
              "A component with no samples is omitted rather than assigned invented values.",
              "Golden scenarios can contain multiple turns, so scenario duration differs from request duration."]
    return "\n".join(lines) + "\n"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", default="http://127.0.0.1:8001")
    parser.add_argument("--max", type=int, default=None)
    parser.add_argument("--timeout", type=float, default=90)
    args = parser.parse_args()

    if not TRACE.exists():
        raise SystemExit("Profiler trace file not found. Start scripts/profile_nashmi_api.py first.")
    start_offset = TRACE.stat().st_size
    scenarios = json.loads(DATASET.read_text(encoding="utf-8"))
    validate_scenarios(scenarios)
    if args.max is not None:
        scenarios = scenarios[:max(0, args.max)]
    failures = []
    count_requests = 0
    api_durations = []
    for scenario in scenarios:
        session_id = "perf-" + uuid.uuid4().hex
        actual = None
        checks = []
        try:
            for index, msg in enumerate(scenario["turns"]):
                start = time.perf_counter()
                actual = send_chat(args.url, "USER-001", session_id, msg, scenario["language"], args.timeout)
                api_durations.append(round((time.perf_counter() - start) * 1000, 3))
                count_requests += 1
                expected_step = scenario.get("step_checks", {}).get(str(index))
                if expected_step is not None:
                    checks.extend(evaluate(expected_step, actual))
            checks.extend(evaluate(scenario["expected"], actual))
            passed = bool(checks) and all(c["passed"] for c in checks)
        except Exception as exc:
            passed = False
            print(f"ERROR {scenario['id']}: {type(exc).__name__}: {exc}")
        print(f"{'PASS' if passed else 'FAIL'} {scenario['id']}")
        if not passed:
            failures.append(scenario["id"])

    if failures:
        raise SystemExit(f"STOP: {len(failures)} scenarios failed; no performance report generated: {failures}")
    traces = extract_traces(start_offset)
    if len(traces) != count_requests or any(t.get("http_status") != 200 for t in traces):
        raise SystemExit(f"STOP: got {len(traces)} profiling traces for {count_requests} requests, or a non-200 status. No report generated.")
    summary = summarize_traces(traces)
    if "langgraph.invoke" not in summary or "http.chat" not in summary:
        raise SystemExit("STOP: essential timers missing. No report generated.")
    report = {"scenario_count": len(scenarios), "passed": len(scenarios), "requests": count_requests,
              "client_http_ms": stats(api_durations), "components": summary,
              "notes": ["All timing values are observed samples, not estimates.",
                        "Server HTTP time excludes network latency.",
                        "Component timings overlap and must not be summed."]}
    REPORT.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    TABLE.write_text(table_for(summary), encoding="utf-8")
    print(f"PASS {len(scenarios)}/{len(scenarios)} scenarios; {count_requests} HTTP requests")
    print("REPORT:", REPORT)
    print("TABLE:", TABLE)
    print(TABLE.read_text(encoding="utf-8"))


if __name__ == "__main__":
    main()
