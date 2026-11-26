# NASHMI — Bilingual AI Travel Booking Assistant

**Local-first GenAI portfolio project · Saudi Arabia–focused · English / العربية**

NASHMI is a conversational travel-booking MVP that helps users search **flights, hotels, and restaurants**, inspect availability, review a booking preview, and explicitly confirm a reservation. It combines **LangGraph conversation orchestration**, **FastAPI**, **Ollama-based local language understanding**, and **PostgreSQL-backed deterministic booking tools**.

> **Project status: local MVP / portfolio demonstration.** NASHMI uses local seeded inventory, not live airline, hotel, or restaurant suppliers. It is **not** a production travel-booking service. Payments, verified user authentication, live supplier APIs, and coordinated cross-service disruption recovery are future work.

<!-- Add a screenshot you own to docs/images/nashmi-demo.png, then uncomment:
![NASHMI web interface](docs/images/nashmi-demo.png)
-->

---

## Overview

NASHMI demonstrates how an LLM-powered interface can support a stateful business workflow **without letting the LLM make authoritative reservation decisions**.

The local MVP supports:

- Flight, hotel, and restaurant discovery using local inventory
- Conversational collection of missing trip details and multi-turn follow-ups
- English and Arabic interactions evaluated with defined golden scenarios
- Availability calendars and browser-based selection controls
- Booking preview **before** a database-changing confirmation
- Explicit confirmation, persisted booking status, and local booking history
- Preview cancellation and booking audit events
- Repeat-confirmation idempotency in tested booking paths
- Transactional safeguards against competing flight reservations
- Request IDs, HTTP status/latency logs, and evaluation reports

The project is intended as a **production-minded learning and portfolio system**, not a supplier-connected booking product.

---

## Quick Start

### Requirements

- Python **3.11**
- Docker with Compose (reusing your existing PostgreSQL image is fine)
- Ollama with a **locally installed model supported by your configuration**

```bash
git clone https://github.com/arzamabid/nashmi-ai-travel-assistant.git
cd nashmi-ai-travel-assistant

python3.11 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"

cp .env.example .env
```

Edit `.env` with **your own local development database credentials**. Its `DATABASE_URL` password must match the PostgreSQL role password in your database. Never commit `.env`.

```bash
# Starts the database service configured in docker-compose.yml.
docker compose up -d postgres

# Initialize and seed the local database using the repository scripts.
# Review existing database contents before running seeders again.
python -m db.init_db
# Example available seed scripts:
# python -m db.seed_users
# python -m db.seed_flights
# python -m db.seed_hotels
# python -m db.seed_restaurants
# python -m db.seed_restaurant_slots

# Start the API and browser demo.
python -m uvicorn apps.api.main:app --reload
```

Open **http://127.0.0.1:8000/**. A health check is available at **`GET /health`**.

**Setup note:** Database initialization and seed scripts are repository-specific; check their implementations and any instructions in `CALENDAR_SETUP.md` before running them on an existing database. **Do not remove PostgreSQL volumes or rerun destructive seed operations to troubleshoot.** The local Ollama model must already be installed or be installed separately with your approval; setup does not download a model automatically.

---

## Architecture

```text
User (browser, English / Arabic)
           |
           v
  Browser UI (apps/web)
           |
           v
       FastAPI (apps/api)
           |
           v
  LangGraph conversation state
      |                |
      v                v
  Ollama LLM       Deterministic tools
 (understanding)   (search / validate /
                    preview / confirm)
                           |
                           v
                     PostgreSQL
                users · inventory · bookings
                  booking_items · audit_events

  Evaluation runner ---> FastAPI /chat
  Observability <------ HTTP request middleware
```

### Architectural boundaries

| Layer | Responsibility |
| --- | --- |
| Browser | Travel search, calendar interaction, previews, booking history |
| FastAPI | HTTP endpoints and request/response handling |
| LangGraph | Conversational state, intent routing, follow-up context and transitions |
| Ollama | Local language understanding and parameter extraction |
| Deterministic tools | Availability, request validation, preview, confirmation, cancellation |
| PostgreSQL / SQLAlchemy | Inventory, transaction boundaries, reservation state and audit records |
| Evaluator | Repeatable scripted conversations, field/state checks and latency reports |

**Design principle:** the LLM interprets the request; application code decides whether an inventory mutation is allowed.

For additional engineering context, see [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) if you add the companion document provided with this README.

---

## Why LangGraph?

Travel requests are multi-turn and stateful. A user might specify a destination first, change a date later, or switch between flights and hotels. A state graph makes those transitions explicit and testable.

```text
User request
    ↓
Intent / service selection
    ↓
Extract and merge travel parameters
    ↓
Missing information? ── yes ──> Ask follow-up ──> Resume
    |
    no
    ↓
Search availability and show choices
    ↓
Create booking preview
    ↓
Explicit user confirmation?
    ├── no  ──> Remain pending / cancel preview
    └── yes ──> Transactional booking confirmation
                       ↓
               Persist state + audit
```

This is a conceptual view of the implemented MVP paths, not a claim that all possible travel disruption flows already exist.

---

## Main Travel Workflows

### Flights

Users can provide origin, destination, travel date, passengers and other supported details conversationally, inspect locally seeded flights, then request a booking preview. Confirmation performs an atomic seat-availability check.

### Hotels

Users can search for lodging using location, dates and relevant preferences, inspect calendar availability and create/confirm a preview. Hotel confirmation uses transactional room-inventory checks across selected nights.

### Restaurants

Users can search restaurant options, inspect available time slots and preview/confirm reservations. A reserved slot is updated through the deterministic booking path.

### Booking history and cancellation scope

Confirmed reservations are persisted and appear in the local **My Bookings** view. **Preview cancellation** is supported and audited. This does **not** mean the full confirmed-reservation cancellation/refund/rescheduling lifecycle or external supplier reconciliation is implemented.

---

## Booking Integrity and Safety

### Explicit confirmation

Creating a preview does not make it a confirmed booking. The confirmation functions require explicit authorization of the action (`confirmed=True`).

### Inventory protection

Flight confirmation uses a conditional SQL inventory decrement: seats are reduced only if enough remain. The update, booking-status change, and audit insertion are performed transactionally.

### Idempotency

Repeated confirmation of an **already confirmed** booking returns the existing confirmation rather than deducting inventory again in the verified paths.

### Booking ownership

A booking's database owner is checked against the **supplied** `user_id` before confirmation. The isolated authorization test verifies that a different supplied user ID is rejected.

> **Security boundary:** supplied user IDs are **not** independently authenticated identities. The local demo uses a demo user context. Real login, authorization at every API boundary, and protection against user-ID impersonation are required before any public deployment.

### Auditability

Local database audit events capture important lifecycle events including `booking_preview_created`, `booking_confirmed`, and `booking_preview_cancelled`.

---

## Technology Stack

| Area | Technologies |
| --- | --- |
| AI orchestration | LangGraph, local Ollama |
| Backend | Python 3.11, FastAPI, Pydantic |
| Persistence | PostgreSQL 16, SQLAlchemy, psycopg |
| Infrastructure | Docker, Docker Compose |
| Web demo | Browser UI under `apps/web/` |
| Evaluation | Golden-scenario JSON, Python runner, JSON results |
| Tests | pytest, mocked unit tests, isolated PostgreSQL integration tests |
| Observability | FastAPI request IDs, status/latency logging, database audit events |

---

## Quality Assurance and Evaluation

### Golden conversational evaluation

The most recent reported local run (26 November 2026) used **50 defined golden scenarios**:

| Metric | Observed result |
| --- | ---: |
| Scenario success | **50 / 50 (100%)** |
| English scenarios | 37 / 37 |
| Arabic scenarios | 13 / 13 |
| State accuracy | 100% within the scenario suite |
| Field accuracy | 100% within the scenario suite |
| Errors | 0 |
| Latency p50 | **1,684.8 ms** |
| Latency p95 | **3,631.5 ms** |

Categories in the evaluated set include flight, hotel and restaurant extraction; context switches and recovery; short follow-ups; Arabic interactions; and date, time and quantity robustness.

Run the evaluator **with the local API already running**:

```bash
python evals/run_evals.py
```

Sources: `evals/golden_scenarios.json` and the generated `evals/latest_report.json`.

**Interpretation:** 100% is the result **on these 50 scenarios**, not a claim of 100% real-world reliability. Local latency is sensitive to model warm-up, machine load and the scenario mix; these figures are not service-level guarantees.

### Security and booking regression

| Check | Verified result | Test scope |
| --- | --- | --- |
| Competing first-time flight reservations | **PASS** | Two different pending previews competing for two remaining seats |
| Flight inventory consistency | **PASS** | Only one confirmation succeeds; seats deducted once |
| Confirmation audit event | **PASS** | Exactly one `booking_confirmed` event |
| Booking ownership | **PASS** | Different supplied user ID cannot confirm the tested reservation |
| Additional invalid-booking cases | **10 / 10 PASS** | Mocked validation suite |
| Targeted confirmation + validation unit regression | **14 passed** | Reported local run |
| Targeted isolated integration regression | **2 passed** | Reported local run |

These are **targeted tests**; they are not a substitute for a full security assessment or end-to-end supplier testing.

Run the safe mocked validation tests:

```bash
python -m pytest \
  tests/test_booking_confirmation.py \
  tests/test_booking_validation_security.py -v -rs
```

For integration tests that create and mutate booking data, point `DATABASE_URL` to an independently initialized **`nashmi_test`** database; do **not** run those tests against `nashmi`:

```bash
# Set DATABASE_URL to your isolated test DB using your own credentials.
# Confirm the database name is exactly nashmi_test before running.
python -m pytest \
  tests/test_flight_booking_concurrency.py \
  tests/test_booking_authorization.py -v -rs
```

Some older tests call the real database directly. **Avoid running the entire suite against a populated development database until its fixtures are isolated.**

See [`docs/QA_REPORT.md`](docs/QA_REPORT.md) for the extended test-scope notes if that companion document is included.

---

## Observability

The MVP includes HTTP request IDs, response status and latency logging. The booking layer also records database audit events. This supports debugging local requests and investigating changes to reservation state.

Future engineering hardening should add distributed traces, failure dashboards, secrets redaction policies, alerting and realistic load measurements.

---

## Repository Structure

```text
nashmi-ai-travel-assistant/
├── agent/
│   ├── graph/              # LangGraph workflow and state
│   ├── llm/                # LLM-backed extraction
│   ├── nodes/              # Travel-service and booking nodes
│   └── utils/              # Date / parameter / follow-up utilities
├── apps/
│   ├── api/                # FastAPI, calendars, bookings, observability
│   └── web/                # Browser demo interface
├── db/
│   ├── models/             # User, inventory, booking, audit models
│   ├── session.py          # SQLAlchemy engine/session
│   └── seed_*.py           # Local demo data scripts
├── evals/
│   ├── golden_scenarios.json
│   ├── run_evals.py
│   └── latest_report.json
├── scripts/                # Debug and seed utilities
├── tests/                  # Unit and integration tests
├── tools/                  # Deterministic booking/search tools + schemas
├── docker-compose.yml
├── .env.example
├── pyproject.toml
└── README.md
```

---

## Design Principles

**Deterministic booking rules.** Language-model output never serves as the inventory source of truth.

**Explicit user approval.** A preview and a confirmed reservation are distinct states.

**Transactional state.** Related inventory, booking-status and audit changes belong within a controlled database transaction.

**Local-first development.** The prototype avoids requiring paid hosted inference or live supplier accounts for its local demo.

**Evidence before claims.** Evaluation results are reported alongside scope and limitations.

**Incremental engineering.** Build an MVP first; expand with production authentication, integration, deployment and operational controls afterward.

---

## Known Limitations

This is a **local portfolio prototype**, not a ready-to-deploy marketplace or travel agency system.

- Local/seeded flight, hotel and restaurant inventory; no actual provider reservations
- No production-grade authentication or independently verified caller identity
- Demo booking history tied to a local user context
- No real payment gateway or charge/refund reconciliation
- Confirmed booking cancellation/rescheduling and trip-wide disruption recovery are not complete
- No verified high-contention coverage across all hotel/restaurant inventory cases
- No production load testing, monitoring stack or CI/CD qualification claimed
- Evaluation set is limited to its defined scenarios and development environment

---

## Roadmap

1. **Authentication and API authorization:** validated identities, per-resource permissions, secure session management.
2. **Connected supplier adapters:** provider inventory, reservations, cancellations, reconciliation and policy handling.
3. **Cross-service disruption recovery:** flight cancellation or rescheduling propagates to hotel and restaurant decisions with user approval and provider policy checks.
4. **Provider-triggered replacement booking:** hotel/restaurant cancellation prompts same-date, same-criteria alternatives.
5. **Resilience:** idempotency across all write operations, retries/backoff, compensating actions, and failure recovery.
6. **Production engineering:** isolated CI tests, Ruff/quality gates, deployment, observability dashboards, security reviews and load testing.

---

## Portfolio Focus

NASHMI is designed to illustrate the differences between **conversational intelligence** and **business-system correctness**: structured state, transactional writes, inventory consistency, evaluation, and honest system boundaries. The same architecture can be extended toward a multi-agent travel platform, but the current MVP intentionally keeps booking decisions deterministic.

---

## Disclaimer

NASHMI is a software engineering and AI portfolio project for demonstration and learning. Local inventory and confirmations do not represent purchases, tickets, hotel stays or restaurant reservations with external providers. No payment collection or travel fulfillment is implied.

<!-- NASHMI_PERFORMANCE_START -->
## Measured local performance

NASHMI was benchmarked on **26 November 2026** using the existing bilingual golden search evaluation suite. **All 50/50 scenarios passed** across **81 HTTP `/chat` requests**. The benchmark ran against a locally hosted FastAPI application instrumented for LangGraph, Ollama and SQL cursor timings.

| Component | Samples | Mean | Median | P95 |
|---|---:|---:|---:|---:|
| End-to-end `/chat` server processing | 81 | 1,204.1 ms | 1,096.4 ms | 1,837.4 ms |
| LangGraph invocation | 81 | 1,201.8 ms | 1,094.3 ms | 1,835.5 ms |
| Intent classification node | 81 | 0.0 ms | 0.0 ms | 0.0 ms |
| Ollama LLM call | 81 | 1,188.0 ms | 1,085.9 ms | 1,788.0 ms |
| SQL cursor execution (per query) | 143 | 2.3 ms | 1.7 ms | 6.2 ms |

**Service-level node breakdown**

| LangGraph node | Samples | Mean | Median | P95 |
|---|---:|---:|---:|---:|
| Flight parameter extraction | 40 | 1,040.7 ms | 997.7 ms | 1,384.9 ms |
| Hotel parameter extraction | 18 | 1,415.8 ms | 1,256.0 ms | 1,968.7 ms |
| Restaurant parameter extraction | 23 | 1,266.1 ms | 1,139.3 ms | 1,788.4 ms |
| Flight search | 6 | 12.1 ms | 9.8 ms | 25.0 ms |
| Hotel search | 6 | 10.2 ms | 8.9 ms | 16.2 ms |
| Restaurant search | 8 | 9.3 ms | 7.6 ms | 16.5 ms |

**Interpretation:** In this local test, Ollama model inference dominated measured request latency. The near-zero intent-classification measurement represents the measured classifier node, not a separate model benchmark. SQL duration measures cursor execution only, excluding connection acquisition and some SQLAlchemy ORM work.

**Methodology and limitations:** Tests used the existing read-only golden *search* scenarios, including multi-turn English and Arabic conversations. This is not an independent 81-scenario test; **50 scenarios generated 81 HTTP requests**. Server-side `/chat` processing excludes client/network latency. Timings for HTTP, graph, nodes, LLM and SQL overlap and **must not be added together**. P95 values describe this particular local run and are not production SLOs. Booking confirmations, payment, cancellation and concurrent load are outside the scope of this performance run. Full local results are generated at `evals/performance_report.json` and `evals/performance_table.md`.
<!-- NASHMI_PERFORMANCE_END -->
