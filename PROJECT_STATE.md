# Current Milestone
M3 — Retrieval (complete: E001–E003 KEEP). M4 — Ranking (complete: E004
KEEP) per Architecture v1.1 roadmap. M5 — Conversation Intelligence next;
see "Next Milestone" below.

# Environment
- macOS
- Python 3.11 virtual environment at `.venv`
- official catalog downloaded and checksum verified
- official evaluator successfully reproduced
- upstream: official TechJam repository
- origin: our public submission repository
- current branch: dev
# Current Best System
E004 — Coverage-aware Lightweight Reranking: a pure same-set reranking pass
over the exact E003 candidate ids. One admitted E003 message is treated as
one evidence unit; a candidate's coverage score is the count of evidence
units whose terms (`_terms()`) non-trivially intersect the candidate's
indexed terms (`_terms()` over title/categories/features/details/store/
description); candidates are sorted by coverage descending with a stable
sort preserving original E003 order on ties. No IDF, field weights, or
candidate-pool changes. Status: complete / KEEP. See EXPERIMENTS.md for
full record.

# Current Best Metrics

Overall (sample_count 200):
- HitRate@10: 0.835
- MRR: 0.518149
- MTTC: 5.01
- Efficiency: 0.599
- TechnicalScore: 0.692745

Scenario metrics:
- buying: HitRate@10 0.8625, MRR 0.494782, MTTC 4.3375
- browsing: HitRate@10 0.825, MRR 0.474727, MTTC 5.3125
- intent_override: HitRate@10 0.8, MRR 0.677302, MTTC 5.2
- boundary: HitRate@10 0.8, MRR 0.575, MTTC 7.4

E003 (prior best): HitRate@10 0.835, MRR 0.498681, MTTC 5.01,
Efficiency 0.599, TechnicalScore 0.686904.
E002: HitRate@10 0.555, MRR 0.244496, MTTC 7.16,
Efficiency 0.384, TechnicalScore 0.427649.
E001: HitRate@10 0.160, MRR 0.066704, MTTC 9.46,
Efficiency 0.154, TechnicalScore 0.130811.
E000 baseline (for reference): HitRate@10 0.125, MRR 0.068034, MTTC 9.81,
Efficiency 0.119, TechnicalScore 0.10671. Full delta and scenario
comparison in EXPERIMENTS.md.

E004 mechanism check: HitRate@10, MTTC, and Efficiency are bit-identical to
E003; only MRR moved (+0.019468), consistent with E004 being a pure
same-set reorder of the E003 candidate ids rather than a change to
retrieval or candidate membership. TechnicalScore's +0.005841 gain is
attributable to the MRR term alone (0.3 × 0.019468 ≈ 0.0058404).

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

Running (`starter/agent.py`, modified per E001 + E002 + E003 + E004):
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
- same-set coverage-aware lightweight reranking (E004, KEEP): reorders the
  final E003 candidate ids by count of admitted evidence units (one E003
  message = one unit) whose terms overlap the candidate's indexed terms
  (title/categories/features/details/store/description); binary per-unit
  credit, stable sort, no IDF or field weights. Candidate membership and
  count are unchanged from E003 — ordering only.
- `user_profile` ignored

Designed, not yet implemented — Architecture v1.1, finalized at M2:
`docs/M2_SYSTEM_DESIGN.md`. E001 implements the Retriever component's
category-scoped primary route, relaxation, and insurance route as described
there. E002 implements the ClarificationPolicy component's minimal M3
fixed-order form. E003 implements SessionEvidence's minimal M3 append-only
plumbing (evidence accumulation), not its full M5 semantics. E004
implements a minimal slice of the Reranker component (plain lexical
constraint-coverage only), not its IDF-weighted or field-weighted variants.
Remaining, not yet implemented: adaptive attribute selection and
intent-override supersede semantics. Intent override will default to
superseding only conflicting evidence (category included, not privileged)
once implemented. Full E001–E006 roadmap and milestone ownership boundaries
(M3 Retrieval / M4 Ranking / M5 Conversation Intelligence / M6 Ablation /
M7 Submission) are in that document.

# Known Baseline Weaknesses

Evidence only:
- append-only evidence can retain stale/conflicting intent — no
  intent-override supersession
- no adaptive clarification — question order is fixed, not adaptive
- no boundary-specific semantics
- unchanged oldest-first 40-term cap — later evidence may be truncated in
  longer sessions; this has not been measured
- `user_profile` ignored
- lexical retrieval only
- naive coverage can over-credit generic/scaffold terms: a candidate can
  receive coverage credit through an attribute-name or conversational
  scaffold word without matching the actual disclosed value (E004)
- uncached coverage product-term extraction has noticeable evaluator-time
  overhead: `_product_terms()` does an uncached per-candidate SQL lookup
  and tokenization per turn (E004); the official evaluator run completed
  successfully but exceeded the 120-second foreground window and finished
  in the background

# Safety Status
- evaluator untouched
- frozen data untouched
- baseline reproducible

# Current Task
E004 — Coverage-aware Lightweight Reranking (a pure same-set reorder of the
final E003 candidate ids by plain, unweighted lexical constraint coverage;
E001 retrieval, E002 clarification sequence, and E003 evidence admission/
accumulation held frozen) is complete and KEPT (see EXPERIMENTS.md for full
record and rationale). HitRate@10, MTTC, and Efficiency are unchanged from
E003; MRR and TechnicalScore improved. Do not claim coverage-aware ranking
in general is optimal, or that IDF/field weighting would necessarily help —
only the specific plain rule tested here is validated. Do not claim
intent-override or boundary behavior is solved by E004 — it inherits E003's
append-only evidence with no supersession or conflict resolution, and adds
no override- or boundary-specific reasoning.

# Next Milestone
Per the Architecture v1.1 roadmap (`docs/M2_SYSTEM_DESIGN.md` §D), the M4
experiment set is now complete: E004 was the sole M4-numbered experiment in
the roadmap table, and the "Sequencing logic" note (§D) states "E005–E006
are M5 semantics and policy" — the roadmap does not list any further
M4-numbered experiment between E004 and E005. The next experiment per the
roadmap is therefore **E005 — Intent override** (M5 — Conversation
Intelligence): "Intent override is best handled by superseding conflicting
constraints," tested as three variants — (a) supersede-conflicting
[default], (b) demote, (c) erase-all — primary metric the `intent_override`
scenario bucket, with all three variants recorded per §D ("this is where
v1.0 was wrong"). This is a milestone transition (M4 → M5); no roadmap
conflict was found. E003's oldest-first 40-term cap, append-only evidence
contamination, and E004's generic-token/scaffold coverage limitations
remain open items for later milestones per the roadmap, not solved here.

# Open Questions

