"""NASHMI golden-scenario evaluator (stdlib only).

Usage:
    python evals/run_evals.py --url http://127.0.0.1:8000
    python evals/run_evals.py --self-test

Requires a running local NASHMI API and a demo user USER-001 for live mode.
Avoids booking selection/confirmation actions. Each scenario gets a fresh session.
NOTE: searches still read inventory and may trigger normal API logging; no
selection or confirmation is performed by this runner.
"""
import argparse
import json
import sys
import time
import uuid
from collections import Counter
from pathlib import Path
from statistics import median
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

DATASET = Path(__file__).with_name("golden_scenarios.json")
REPORT = Path(__file__).with_name("latest_report.json")


def get_path(value, dotted):
    for key in dotted.split("."):
        if not isinstance(value, dict):
            return None
        value = value.get(key)
    return value


def evaluate(expected, actual):
    """Return scored checks, retaining missing/incorrect values for debugging."""
    checks = []
    for key in ("intent", "status"):
        if key in expected:
            checks.append({"name": key, "expected": expected[key], "actual": actual.get(key),
                           "passed": actual.get(key) == expected[key], "kind": "state"})
    for key, target in expected.get("fields", {}).items():
        observed = get_path(actual, key)
        checks.append({"name": key, "expected": target, "actual": observed,
                       "passed": observed == target, "kind": "field"})
    return checks


def send_chat(url, user_id, session_id, message, language, timeout):
    payload = json.dumps({"user_id": user_id, "session_id": session_id,
                          "message": message, "language": language}).encode("utf-8")
    req = Request(f"{url.rstrip('/')}/chat", data=payload,
                  headers={"Content-Type": "application/json"}, method="POST")
    with urlopen(req, timeout=timeout) as response:
        data = json.load(response)
    if not isinstance(data, dict):
        raise ValueError("Expected JSON object from /chat")
    return data


UNSAFE_ACTIONS = (
    "option ", "confirm booking", "confirm the booking", "yes, confirm",
    "cancel booking", "cancel it", "تأكيد الحجز", "أكد الحجز", "احجز الآن",
    "option", "yes confirm", "confirm", "book now", "select ", "أؤكد", "اختر",
)


def validate_scenarios(scenarios):
    ids = set()
    for case in scenarios:
        if case["id"] in ids:
            raise ValueError(f"Duplicate scenario ID: {case['id']}")
        ids.add(case["id"])
        if not case.get("turns") or not case.get("expected"):
            raise ValueError(f"Incomplete scenario: {case['id']}")
        for turn in case["turns"]:
            text = turn.strip().lower()
            if any(text.startswith(action) for action in UNSAFE_ACTIONS):
                raise ValueError(f"Unsafe booking action in {case['id']}: {turn}")
        for step in case.get("step_checks", {}):
            if not 0 <= int(step) < len(case["turns"]):
                raise ValueError(f"Invalid step index in {case['id']}: {step}")


def run(scenarios, sender):
    report = []
    for scenario in scenarios:
        session_id = "eval-" + uuid.uuid4().hex
        started = time.perf_counter()
        try:
            actual = None
            checks = []
            for index, message in enumerate(scenario["turns"]):
                actual = sender(session_id, message, scenario["language"])
                step_expected = scenario.get("step_checks", {}).get(str(index))
                if step_expected is not None:
                    for check in evaluate(step_expected, actual):
                        check["name"] = f"turn_{index + 1}." + check["name"]
                        checks.append(check)
            checks.extend(evaluate(scenario["expected"], actual))
            passed = bool(checks) and all(c["passed"] for c in checks)
            error = None
        except (HTTPError, URLError, TimeoutError, ValueError, OSError) as exc:
            checks, passed, error = [], False, f"{type(exc).__name__}: {exc}"
        entry = {"id": scenario["id"], "category": scenario["category"],
                 "language": scenario["language"], "passed": passed,
                 "latency_ms": round((time.perf_counter() - started) * 1000, 1),
                 "checks": checks, "error": error}
        report.append(entry)
        print(f"{'PASS' if passed else 'FAIL'}  {scenario['id']}  ({entry['latency_ms']} ms)")
        if error:
            print("      ", error)
        for check in checks:
            if not check["passed"]:
                print(f"       {check['name']}: expected={check['expected']!r}, actual={check['actual']!r}")
    return report


def summarize(report):
    scenario_count = len(report)
    state = [c for entry in report for c in entry["checks"] if c["kind"] == "state"]
    fields = [c for entry in report for c in entry["checks"] if c["kind"] == "field"]
    rate = lambda passed, total: round(100 * passed / total, 1) if total else None
    def by_group(key):
        groups = sorted({e[key] for e in report})
        return {g: {"passed": sum(e["passed"] for e in report if e[key] == g),
                    "total": sum(e[key] == g for e in report),
                    "success_pct": rate(sum(e["passed"] for e in report if e[key] == g),
                                        sum(e[key] == g for e in report))} for g in groups}
    durations = sorted(e["latency_ms"] for e in report)
    return {"scenarios": scenario_count, "passed": sum(e["passed"] for e in report),
            "scenario_success_pct": rate(sum(e["passed"] for e in report), scenario_count),
            "state_accuracy_pct": rate(sum(c["passed"] for c in state), len(state)),
            "field_accuracy_pct": rate(sum(c["passed"] for c in fields), len(fields)),
            "errors": sum(e["error"] is not None for e in report),
            "latency_p50_ms": round(median(durations), 1) if durations else None,
            "latency_p95_ms": durations[max(0, (95 * len(durations) + 99) // 100 - 1)] if durations else None,
            "by_language": by_group("language"), "by_category": by_group("category"),
            "failures_by_category": dict(Counter(e["category"] for e in report if not e["passed"]))}


def self_test():
    expected = {"intent": "flight_search", "fields": {"flight_request.passengers": 2}}
    actual = {"intent": "flight_search", "flight_request": {"passengers": 2}}
    assert all(c["passed"] for c in evaluate(expected, actual))
    assert any(not c["passed"] for c in evaluate(expected, {"intent": "hotel_search"}))
    test_scenarios = [{"id": "TEST", "category": "self_test", "language": "en", "turns": ["Find a flight"],
                       "expected": {"intent": "flight_search"},
                       "step_checks": {"0": {"intent": "flight_search"}}}]
    validate_scenarios(test_scenarios)
    observed = run(test_scenarios, lambda session, msg, lang: {"intent": "flight_search"})
    assert summarize(observed)["scenario_success_pct"] == 100
    print("PASS evaluator self-test (no NASHMI API needed)")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", default="http://127.0.0.1:8000")
    parser.add_argument("--user-id", default="USER-001")
    parser.add_argument("--timeout", type=float, default=90.0)
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--list", action="store_true", help="List scenario IDs without API requests")
    parser.add_argument("--category", help="Only run this category")
    parser.add_argument("--language", choices=["en", "ar"], help="Only run this language")
    parser.add_argument("--max", type=int, help="Run only the first N selected scenarios")
    args = parser.parse_args()
    if args.self_test:
        self_test()
        return 0
    scenarios = json.loads(DATASET.read_text(encoding="utf-8"))
    validate_scenarios(scenarios)
    if args.category:
        scenarios = [s for s in scenarios if s["category"] == args.category]
    if args.language:
        scenarios = [s for s in scenarios if s["language"] == args.language]
    if args.max is not None:
        scenarios = scenarios[:max(0, args.max)]
    if args.list:
        for scenario in scenarios:
            print(f"{scenario['id']}  [{scenario['language']}]  {scenario['category']}")
        print(f"TOTAL: {len(scenarios)}")
        return 0
    if not scenarios:
        print("No scenarios matched the selection", file=sys.stderr)
        return 2
    print(f"Running {len(scenarios)} golden scenarios against {args.url}")
    sender = lambda session, msg, lang: send_chat(args.url, args.user_id, session, msg, lang, args.timeout)
    report = run(scenarios, sender)
    summary = summarize(report)
    REPORT.write_text(json.dumps({"summary": summary, "results": report}, indent=2, ensure_ascii=False), encoding="utf-8")
    print("\nMETRICS:", json.dumps(summary, indent=2))
    print("Report:", REPORT)
    return 0 if summary["passed"] == len(scenarios) else 1


if __name__ == "__main__":
    sys.exit(main())
