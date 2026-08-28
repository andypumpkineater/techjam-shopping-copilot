# Current Milestone
M0 — Operational readiness and AI collaboration workflow

# Environment
- macOS
- Python 3.11 virtual environment at `.venv`
- official catalog downloaded and checksum verified
- official evaluator successfully reproduced
- current branch: dev
- upstream: official TechJam repository
- origin: our public submission repository

# Current Best System
Official weak BM25 starter (`starter/agent.py`, unmodified).

# Current Best Metrics

Overall (sample_count 200):
- HitRate@10: 0.125
- MRR: 0.068034
- MTTC: 9.81
- Efficiency: 0.119
- TechnicalScore: 0.10671

Scenario metrics:
- buying: HitRate@10 0.2375, MRR 0.126508, MTTC 8.625
- browsing: HitRate@10 0.025, MRR 0.004514, MTTC 10.75
- intent_override: HitRate@10 0.133333, MRR 0.104167, MTTC 10.066667
- boundary: HitRate@10 0.0, MRR 0.0, MTTC 11.0

# Current Architecture

Only describes the existing starter:
- in-memory SQLite FTS5/BM25 index over the full catalog
- stateless across turns
- current-message-only retrieval (no conversation history)
- `user_profile` ignored
- no clarification questions (`ask_attribute` always `null`)
- no reranking
- no multi-turn state

# Known Baseline Weaknesses

Evidence only:
- Browsing performance extremely weak
- Boundary has zero hits
- no multi-turn state
- no clarification
- `user_profile` ignored
- no intent-override state management
- lexical retrieval only

# Safety Status
- evaluator untouched
- frozen data untouched
- baseline reproducible

# Current Task
Complete M0 by establishing persistent AI memory, Git discipline, and experiment logging.

# Next Milestone
M1 — Independently understand and explain evaluator and baseline behavior.

# Open Questions

