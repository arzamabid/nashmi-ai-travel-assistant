# NASHMI Evaluations V3 — 50 golden scenarios

This package **replaces only** `evals/golden_scenarios.json` and `evals/run_evals.py`.
It carries forward all 30 V2 scenarios unchanged and adds 20 robustness cases, for a total of 50.

## Install
Back up your existing `evals/` files and copy the two files in this ZIP to the existing `nashmi/evals/` folder. Do not replace any other NASHMI files.

## Run
With your **local** FastAPI (`127.0.0.1:8000`) and existing Ollama server running:

```bash
python evals/run_evals.py --self-test
python evals/run_evals.py --list
python evals/run_evals.py
python evals/run_evals.py --language ar
python evals/run_evals.py --category context_recovery
```

The runner overwrites `evals/latest_report.json` on each full/filtered run. To preserve a baseline, copy it to another filename **before running a filter**.

## How to interpret results
V2 had **30/30 PASS** in your previous run. The 20 V3 expectations are **new hypotheses** and have NOT been verified against your running installation. Failures may reveal product bugs or cases where we need to refine the golden expectation. Do **not** change prompts automatically based on a failure without inspecting actual output.

The metrics measure these 50 *specific* cases, not general production accuracy. The 20 new cases comprise 12 English and 8 Arabic; the full 50-case count is displayed by `--list`. This is still not representative of all users.

## Safety boundaries
The runner sends only search and browse requests (no option selection, confirmation, or cancellation). It creates a new conversation session per scenario. However, it exercises your actual chat API and therefore may add normal access logs; run only on your local demo environment. It does **not** prove booking authorization, simultaneous first-confirmation safety, or prompt-injection resistance. Those require separate isolated database and mocked/integration suites. Do not point this runner at production.

## Next phase after results
1. Inspect V3 failures (including ambiguous city/date correction behavior).
2. Build a **separate transaction-isolated security/evaluation fixture** for invalid passengers, impossible dates, explicit cancellation and unauthorized booking attempts.
3. Add measured booking-safety and language-quality metrics, not only intent/field exact match.

No new packages, images, or models required.
