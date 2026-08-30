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
E001 — Category-aware lexical retrieval with catalog-derived relaxation and
a global lexical insurance route (`starter/agent.py`, modified). See
EXPERIMENTS.md for full record.

# Current Best Metrics

Overall (sample_count 200):
- HitRate@10: 0.160
- MRR: 0.066704
- MTTC: 9.46
- Efficiency: 0.154
- TechnicalScore: 0.130811

Scenario metrics:
- buying: HitRate@10 0.275, MRR 0.136577, MTTC 8.25
- browsing: HitRate@10 0.075, MRR 0.012996, MTTC 10.25
- intent_override: HitRate@10 0.133333, MRR 0.045833, MTTC 10.066667
- boundary: HitRate@10 0.0, MRR 0.0, MTTC 11.0

E000 baseline (for reference): HitRate@10 0.125, MRR 0.068034, MTTC 9.81,
Efficiency 0.119, TechnicalScore 0.10671. Full delta and scenario
comparison in EXPERIMENTS.md.

Known E001 regression: overall MRR decreased slightly, and intent_override
MRR decreased materially while its HitRate remained flat. Not repaired
inside E001 by design; carried forward as a ranking / conversation-state
problem for later milestones. See EXPERIMENTS.md for detail.

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

Running (`starter/agent.py`, modified per E001):
- in-memory SQLite FTS5/BM25 index over the full catalog
- catalog-derived category index (full / last2 / last1 / segment
  granularities) with taxonomy-consistent relaxation and a small
  always-reachable global lexical insurance route (E001, KEEP)
- stateless across turns
- current-message-only retrieval (no conversation history)
- `user_profile` ignored
- no clarification questions (`ask_attribute` always `null`)
- no reranking
- no multi-turn state

Designed, not yet implemented — Architecture v1.1, finalized at M2:
`docs/M2_SYSTEM_DESIGN.md`. E001 implements the Retriever component's
category-scoped primary route, relaxation, and insurance route as described
there. Remaining, not yet implemented: clarification channel and adaptive
attribute selection, conversation-history accumulation and intent-override
supersede semantics, and constraint-coverage reranking. Intent override
will default to superseding only conflicting evidence (category included,
not privileged) once implemented. Full E001–E006 roadmap and milestone
ownership boundaries (M3 Retrieval / M4 Ranking / M5 Conversation
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
E001 — Category-aware lexical retrieval with graceful catalog-derived
relaxation and a small always-reachable global lexical insurance route is
complete and KEPT (see EXPERIMENTS.md for full record and rationale).
Next planned experiment: E002 — Clarification Channel (emit a non-null
`ask_attribute` under a fixed, label-free rule; retrieval and ranking
frozen at E001).

# Next Milestone
M3 continues with E002 — Clarification Channel, then E003 — Evidence
Accumulation. M4 — Ranking (constraint-coverage reranking, field
weighting) follows once the M3 experiment set (E001–E003) is complete.

# Open Questions

