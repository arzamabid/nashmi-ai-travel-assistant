# NASHMI Measured Performance

| Component | Samples | Mean | Median | P95 |
|---|---:|---:|---:|---:|
| End-to-end `/chat` server processing | 81 | 1204.1 ms | 1096.4 ms | 1837.4 ms |
| LangGraph invocation | 81 | 1201.8 ms | 1094.3 ms | 1835.5 ms |
| Intent classification node | 81 | 0.0 ms | 0.0 ms | 0.0 ms |
| Ollama LLM call | 81 | 1188.0 ms | 1085.9 ms | 1788.0 ms |
| SQL cursor execution (per query) | 143 | 2.3 ms | 1.7 ms | 6.2 ms |
| LangGraph node: ask_flight_follow_up | 34 | 0.0 ms | 0.0 ms | 0.0 ms |
| LangGraph node: ask_hotel_follow_up | 12 | 0.0 ms | 0.0 ms | 0.0 ms |
| LangGraph node: ask_restaurant_follow_up | 15 | 0.0 ms | 0.0 ms | 0.0 ms |
| LangGraph node: extract_flight | 40 | 1040.7 ms | 997.7 ms | 1384.9 ms |
| LangGraph node: extract_hotel | 18 | 1415.8 ms | 1256.0 ms | 1968.7 ms |
| LangGraph node: extract_restaurant | 23 | 1266.1 ms | 1139.3 ms | 1788.4 ms |
| LangGraph node: flight | 6 | 12.1 ms | 9.8 ms | 25.0 ms |
| LangGraph node: flight_availability | 6 | 12.9 ms | 13.6 ms | 21.8 ms |
| LangGraph node: hotel | 6 | 10.2 ms | 8.9 ms | 16.2 ms |
| LangGraph node: hotel_availability | 6 | 22.5 ms | 20.0 ms | 42.5 ms |
| LangGraph node: restaurant | 8 | 9.3 ms | 7.6 ms | 16.5 ms |
| LangGraph node: restaurant_availability | 8 | 18.8 ms | 17.7 ms | 28.6 ms |
| LangGraph node: start_session | 81 | 0.0 ms | 0.0 ms | 0.0 ms |

Measured locally on the profiled API using the existing read-only golden search scenarios.
Timings overlap (node, LLM, SQL, graph, HTTP); do not add rows together.
SQL duration measures DB cursor execution, not complete SQLAlchemy ORM work.
HTTP duration is server-side processing; it excludes client/network overhead.
A component with no samples is omitted rather than assigned invented values.
Golden scenarios can contain multiple turns, so scenario duration differs from request duration.
