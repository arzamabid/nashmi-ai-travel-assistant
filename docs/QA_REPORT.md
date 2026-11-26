# NASHMI — QA Evidence and Remaining Risks

**As of:** 26 November 2026  
**Evidence type:** User-reported local runs and inspected test/code excerpts. No independent execution against the user's Mac was possible.

## Latest verified reports

| Area | Evidence | Result |
| --- | --- | --- |
| Golden dataset | `evals/golden_scenarios.json` / `evals/latest_report.json` | 50/50 scenarios passed (37 EN, 13 AR) |
| Latency | Same evaluation run | p50 1,684.8 ms; p95 3,631.5 ms |
| Flight concurrency | `tests/test_flight_booking_concurrency.py` | 1 passed; one of two competing *different* previews confirmed |
| Authorization at booking function | `tests/test_booking_authorization.py` | 1 passed; other supplied user ID rejected |
| Invalid booking cases | `tests/test_booking_validation_security.py` | 10 passed; mocked tests |
| Targeted regression | Combined existing confirmation/validation + isolated integration tests | PASS reported; individual counts not supplied |

## Test isolation

The concurrency and ownership integration tests were executed using the isolated PostgreSQL `nashmi_test` database, configured through an ephemeral `DATABASE_URL` override. The normal environment was restored afterward with `unset DATABASE_URL`. Other preview tests may connect to the regular database and should not be included in a wide regression without fixture isolation.

## What has **not** been established

- Secure caller authentication and prevention of `user_id` impersonation at API boundaries.
- All high-concurrency hotel and restaurant inventory paths, or same-preview concurrent first-confirmation behavior.
- End-to-end provider integration, billing, refunds, provider cancellation, and cross-service saga compensation.
- Broader scenario reliability beyond the supplied golden suite.
- Production deployment security, resilient secrets, distributed tracing, and load testing.

## Release recommendation

**Suitable for local MVP demonstration and clearly scoped portfolio presentation. Not cleared for public production booking deployment.**

Before publishing: verify setup commands against the repository, capture clean UI screenshots, remove secrets and local database credentials from Git history, confirm repository license, and rerun tests on a reproducible test environment.
