# NASHMI Measured Performance

| Component | Samples | Mean | Median | P95 |
|---|---:|---:|---:|---:|
| End-to-end `/chat` server processing | 4 | 1654.8 ms | 1282.3 ms | 3066.5 ms |
| LangGraph invocation | 4 | 1651.6 ms | 1280.2 ms | 3060.2 ms |
| Intent classification node | 4 | 0.0 ms | 0.0 ms | 0.1 ms |
| Ollama LLM call | 4 | 1594.6 ms | 1172.9 ms | 3052.1 ms |
| SQL cursor execution (per query) | 7 | 4.5 ms | 3.4 ms | 12.4 ms |
| LangGraph node: ask_flight_follow_up | 3 | 0.0 ms | 0.0 ms | 0.0 ms |
| LangGraph node: extract_flight | 4 | 1595.0 ms | 1173.2 ms | 3052.9 ms |
| LangGraph node: flight | 1 | 176.1 ms | 176.1 ms | 176.1 ms |
| LangGraph node: flight_availability | 1 | 23.8 ms | 23.8 ms | 23.8 ms |
| LangGraph node: start_session | 4 | 0.0 ms | 0.0 ms | 0.0 ms |

Measured locally on the profiled API using the existing read-only golden search scenarios.
Timings overlap (node, LLM, SQL, graph, HTTP); do not add rows together.
SQL duration measures DB cursor execution, not complete SQLAlchemy ORM work.
HTTP duration is server-side processing; it excludes client/network overhead.
A component with no samples is omitted rather than assigned invented values.
Golden scenarios can contain multiple turns, so scenario duration differs from request duration.
