# Current Milestone
M3 — Retrieval

# Environment
- macOS
- Python 3.11 virtual environment at `.venv`
- official catalog downloaded and checksum verified
- official evaluator successfully reproduced
- upstream: official TechJam repository
- origin: our public submission repository
- current branch: dev
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

# Reference Documents
- `docs/sources/TRACK4_PROBLEM_STATEMENT.md` — vision-level problem statement
  (directional only: dual-track routing, hybrid/LLM semantic ranking, dynamic
  context programming). Not authoritative for scoring or interface behavior.
- Authoritative scoring/interface spec: `docs/competition_specification.md`,
  `docs/agent_api_contract.json`, `docs/evaluation_config.json`,
  `evaluator/local_evaluator.py`.
- See CLAUDE.md → "Reference Document Hierarchy" for the precedence rule.

# Current Architecture

Two layers: what's running, and what's designed but not yet implemented.

Running (`starter/agent.py`, unmodified):
- in-memory SQLite FTS5/BM25 index over the full catalog
- stateless across turns
- current-message-only retrieval (no conversation history)
- `user_profile` ignored
- no clarification questions (`ask_attribute` always `null`)
- no reranking
- no multi-turn state

Designed, not yet implemented — Architecture v1.1, finalized at M2:
`docs/M2_SYSTEM_DESIGN.md`. Key decisions: category-scoped lexical retrieval as the primary route,
with size-triggered relaxation (path → last-2 → last-1 → segment → global) for
under-generality, PLUS a small always-reachable global lexical insurance route
to catch a wrong-but-large scope that relaxation cannot detect (reserved-slot
merge, no RRF). Intent override defaults to superseding only conflicting
evidence (category included, not privileged). Full E001–E006 roadmap and
milestone ownership boundaries (M3 Retrieval / M4 Ranking / M5 Conversation
Intelligence / M6 Ablation / M7 Submission) are in that document.

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
E001 — Category-scoped lexical retrieval with graceful relaxation and a small
always-reachable global lexical insurance route. Retrieval only: no
clarification, state, or reranking changes. Not yet implemented in
`starter/agent.py` (working tree is currently clean / matches E000).

# Next Milestone
M4 — Ranking (constraint-coverage reranking, field weighting), after E001 is
implemented and evaluated.

# Open Questions

