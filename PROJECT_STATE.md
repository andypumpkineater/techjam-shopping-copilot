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
E002 — Clarification Channel: fixed, deterministic, label-free
`ask_attribute` sequence layered on the frozen E001 category-aware lexical
retriever (`starter/agent.py`, modified). Status: complete / KEEP. See
EXPERIMENTS.md for full record.

# Current Best Metrics

Overall (sample_count 200):
- HitRate@10: 0.555
- MRR: 0.244496
- MTTC: 7.16
- Efficiency: 0.384
- TechnicalScore: 0.427649

Scenario metrics:
- buying: HitRate@10 0.5375, MRR 0.267133, MTTC 6.475
- browsing: HitRate@10 0.575, MRR 0.233552, MTTC 7.0375
- intent_override: HitRate@10 0.466667, MRR 0.238333, MTTC 8.866667
- boundary: HitRate@10 0.8, MRR 0.169444, MTTC 8.5

E001 (prior best): HitRate@10 0.160, MRR 0.066704, MTTC 9.46,
Efficiency 0.154, TechnicalScore 0.130811.
E000 baseline (for reference): HitRate@10 0.125, MRR 0.068034, MTTC 9.81,
Efficiency 0.119, TechnicalScore 0.10671. Full delta and scenario
comparison in EXPERIMENTS.md.

Known E001 regression (still present, not addressed by E002): overall MRR
had decreased slightly at E001, and intent_override MRR had decreased
materially while its HitRate remained flat. Carried forward as a ranking /
conversation-state problem for later milestones. See EXPERIMENTS.md for
detail.

Key remaining limitation (E002): the clarification channel now elicits
useful runtime disclosures, but retrieval remains current-message-only, so
previous-turn evidence — including the opening category cue — is forgotten
on later turns. Do not claim boundary or intent_override behavior is
solved; the strong public boundary/intent_override numbers are an observed
evaluator result under the published simulator mechanics, not evidence of
boundary- or override-specific reasoning (E002 implements neither).

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

Running (`starter/agent.py`, modified per E001 + E002):
- in-memory SQLite FTS5/BM25 index over the full catalog
- catalog-derived category index (full / last2 / last1 / segment
  granularities) with taxonomy-consistent relaxation and a small
  always-reachable global lexical insurance route (E001, KEEP)
- stateless across turns
- current-message-only retrieval (no conversation history) — unchanged by
  E002; still the key remaining limitation
- `user_profile` ignored
- fixed, deterministic, label-free clarification sequence indexed purely by
  `turn` (E002, KEEP): material, color, size, style, budget, feature,
  use_case, other, then none on turns 9-10. No adaptive selection, no
  evidence accumulation, no intent-override or boundary-specific logic
- no reranking
- no multi-turn state

Designed, not yet implemented — Architecture v1.1, finalized at M2:
`docs/M2_SYSTEM_DESIGN.md`. E001 implements the Retriever component's
category-scoped primary route, relaxation, and insurance route as described
there. E002 implements the ClarificationPolicy component's minimal M3
fixed-order form. Remaining, not yet implemented: adaptive attribute
selection, conversation-history accumulation and intent-override supersede
semantics, and constraint-coverage reranking. Intent override will default
to superseding only conflicting evidence (category included, not
privileged) once implemented. Full E001–E006 roadmap and milestone
ownership boundaries (M3 Retrieval / M4 Ranking / M5 Conversation
Intelligence / M6 Ablation / M7 Submission) are in that document.

# Known Baseline Weaknesses

Evidence only:
- no multi-turn state — retrieval is still current-message-only, so
  previous-turn evidence (including the opening category cue) is forgotten
  on later turns
- no evidence accumulation across turns
- `user_profile` ignored
- no intent-override state management
- lexical retrieval only
- clarification question order is fixed, not adaptive

# Safety Status
- evaluator untouched
- frozen data untouched
- baseline reproducible

# Current Task
E002 — Clarification Channel (fixed, deterministic, label-free
`ask_attribute` sequence; retrieval and ranking frozen at E001) is complete
and KEPT (see EXPERIMENTS.md for full record and rationale). Do not claim
boundary or intent_override behavior is solved by E002 — the observed
gains in those buckets are a result of the published simulator mechanics,
not boundary- or override-specific reasoning in the agent.
Next planned experiment: E003 — Multi-turn Evidence Accumulation (carry
legitimately disclosed runtime evidence across turns into the query; E002
clarification policy held fixed).

# Next Milestone
M3 continues with E003 — Multi-turn Evidence Accumulation. M4 — Ranking
(constraint-coverage reranking, field weighting) follows once the M3
experiment set (E001–E003) is complete.

# Open Questions

