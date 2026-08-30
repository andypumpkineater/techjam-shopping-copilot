# Current Milestone
M3 — Retrieval (complete: E001–E003 KEEP). M4 — Ranking next per Architecture v1.1 roadmap.

# Environment
- macOS
- Python 3.11 virtual environment at `.venv`
- official catalog downloaded and checksum verified
- official evaluator successfully reproduced
- upstream: official TechJam repository
- origin: our public submission repository
- current branch: dev
# Current Best System
E003 — Meaningful Multi-turn Evidence Accumulation: minimal per-session
append-only runtime evidence, admitted per a deterministic rule that always
retains turn 1 and excludes three published information-free reply
templates, accumulated oldest-to-newest into the frozen E001/E002
`_terms()` → dedup → 40-term-cap query pipeline (`starter/agent.py`,
modified). Status: complete / KEEP. See EXPERIMENTS.md for full record.

# Current Best Metrics

Overall (sample_count 200):
- HitRate@10: 0.835
- MRR: 0.498681
- MTTC: 5.01
- Efficiency: 0.599
- TechnicalScore: 0.686904

Scenario metrics:
- buying: HitRate@10 0.8625, MRR 0.485913, MTTC 4.3375
- browsing: HitRate@10 0.825, MRR 0.456205, MTTC 5.3125
- intent_override: HitRate@10 0.8, MRR 0.630278, MTTC 5.2
- boundary: HitRate@10 0.8, MRR 0.545833, MTTC 7.4

E002 (prior best): HitRate@10 0.555, MRR 0.244496, MTTC 7.16,
Efficiency 0.384, TechnicalScore 0.427649.
E001: HitRate@10 0.160, MRR 0.066704, MTTC 9.46,
Efficiency 0.154, TechnicalScore 0.130811.
E000 baseline (for reference): HitRate@10 0.125, MRR 0.068034, MTTC 9.81,
Efficiency 0.119, TechnicalScore 0.10671. Full delta and scenario
comparison in EXPERIMENTS.md.

Known E001 regression: overall MRR had decreased slightly at E001, and
intent_override MRR had decreased materially while its HitRate remained
flat. E003's intent_override MRR (0.630278) has since improved
substantially in this public run alongside overall evidence accumulation,
but this does not establish that override handling is solved — see
EXPERIMENTS.md interpretation and limitations.

Key remaining limitation (E003): evidence accumulation is append-only with
no supersession or conflict resolution, so an intent override can leave
both old and new intent terms in the accumulated query; the oldest-first
40-term cap is unchanged and could truncate later evidence in longer
sessions (this evaluation does not establish how often, if ever, that
occurred). Do not claim boundary or intent_override behavior is solved;
the strong public boundary/intent_override numbers are an observed
evaluator result under the published simulator mechanics plus evidence
accumulation, not evidence of boundary- or override-specific reasoning
(E003 implements neither).

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

Running (`starter/agent.py`, modified per E001 + E002 + E003):
- in-memory SQLite FTS5/BM25 index over the full catalog
- catalog-derived category index (full / last2 / last1 / segment
  granularities) with taxonomy-consistent relaxation and a small
  always-reachable global lexical insurance route (E001, KEEP)
- fixed, deterministic, label-free clarification sequence indexed purely by
  `turn` (E002, KEEP): material, color, size, style, budget, feature,
  use_case, other, then none on turns 9-10. No adaptive selection, no
  intent-override or boundary-specific logic
- persistent meaningful multi-turn runtime evidence (E003, KEEP): minimal
  per-session append-only evidence list; turn 1 always admitted; later
  messages admitted unless they match one of three published
  information-free reply prefixes; admitted evidence joined oldest-to-newest
  and fed through the unchanged E001/E002 `_terms()` → dedup → 40-term-cap
  query pipeline. No supersession, no conflict resolution, no recency
  weighting.
- `user_profile` ignored
- no reranking

Designed, not yet implemented — Architecture v1.1, finalized at M2:
`docs/M2_SYSTEM_DESIGN.md`. E001 implements the Retriever component's
category-scoped primary route, relaxation, and insurance route as described
there. E002 implements the ClarificationPolicy component's minimal M3
fixed-order form. E003 implements SessionEvidence's minimal M3 append-only
plumbing (evidence accumulation), not its full M5 semantics. Remaining, not
yet implemented: adaptive attribute selection, intent-override supersede
semantics, and constraint-coverage reranking. Intent override will default
to superseding only conflicting evidence (category included, not
privileged) once implemented. Full E001–E006 roadmap and milestone
ownership boundaries (M3 Retrieval / M4 Ranking / M5 Conversation
Intelligence / M6 Ablation / M7 Submission) are in that document.

# Known Baseline Weaknesses

Evidence only:
- append-only evidence can retain stale/conflicting intent — no
  intent-override supersession
- no adaptive clarification — question order is fixed, not adaptive
- no reranking
- no boundary-specific semantics
- unchanged oldest-first 40-term cap — later evidence may be truncated in
  longer sessions; this has not been measured
- `user_profile` ignored
- lexical retrieval only

# Safety Status
- evaluator untouched
- frozen data untouched
- baseline reproducible

# Current Task
E003 — Meaningful Multi-turn Evidence Accumulation (minimal per-session
append-only runtime evidence, deterministic exclusion of published
information-free reply templates; E001 retrieval and E002 clarification
sequence held frozen) is complete and KEPT (see EXPERIMENTS.md for full
record and rationale). Do not claim intent-override or boundary behavior is
solved by E003 — append-only accumulation carries no supersession or
conflict resolution, and the observed scenario gains are an outcome under
the published simulator mechanics plus evidence accumulation, not
override- or boundary-specific reasoning in the agent.

# Next Milestone
Per the Architecture v1.1 roadmap (`docs/M2_SYSTEM_DESIGN.md` §D), the M3
experiment set (E001–E003) is now complete. M4 — Ranking follows next, per
roadmap: E004 — coverage-aware reranking over the E003 pool (rank by how
many accumulated constraints a product satisfies, MRR primary metric),
watching for long generic text over-scoring on coverage (may need
IDF-aware weighting). E003's oldest-first 40-term cap and append-only
override contamination remain open items for later milestones (M4/M5) per
the roadmap, not solved here.

# Open Questions

