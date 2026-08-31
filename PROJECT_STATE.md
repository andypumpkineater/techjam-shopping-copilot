# Current Milestone
M3 — Retrieval (complete: E001–E003 KEEP). M4 — Ranking (complete: E004
KEEP) per Architecture v1.1 roadmap. M5 — Conversation Intelligence
complete: E005 (erase-all intent-override reset) tested and REVERTED; E006
(adaptive catalog-side clarification) tested and KEPT. M6 — Robustness /
Reproducibility / Performance is now COMPLETE: robustness verification
PASS, reproducibility PASS in the current verified environment, and one
semantics-preserving `_product_terms()` memoization optimization KEPT (see
"M6 — Robustness, Reproducibility, and Performance" below and
EXPERIMENTS.md for the full record). M6 introduced no new algorithm
capability; current best algorithm remains E006. The prior human decision
freezing algorithm capability development after E006 (no E007 planned) was
explicitly lifted by a new human decision on 2026-08-31 for a single,
tightly time-boxed post-v1.1 experiment — see "Human Decision — Freeze
Lifted (2026-08-31)" below. That experiment, E007 — Candidate Pool
Expansion before Coverage Reranking, has since been implemented, evaluated
once, and REVERTED by human decision (see "E007 Outcome" below and
EXPERIMENTS.md for the full record); current best algorithm remains E006 +
M6 memoization, and `starter/agent.py` has been restored to that code —
the failed E007 change was discarded and E007's failure documentation
committed; the working tree was clean before E008 preregistration began.

# Human Decision — Freeze Lifted (2026-08-31)

Previous decision: algorithm capability development was frozen after E006
and no E007 was planned (recorded at M6 completion; see EXPERIMENTS.md "M6
— Robustness, Reproducibility, and Performance").

New HUMAN decision on 2026-08-31: that freeze is explicitly lifted for a
single, tightly time-boxed post-v1.1 experiment extension. This does not
rewrite history — Architecture v1.1's original roadmap ended at E006 and
remains a historical design record (`docs/M2_SYSTEM_DESIGN.md`,
unchanged), and past E000–E006 experiment records are unchanged.

Authorized next experiment: E007 — Candidate Pool Expansion before
Coverage Reranking.

Reason: the current E004/E006 pipeline reranks only the small lexical
candidate set it has already retrieved (truncated to `top_k` before
coverage reranking — see `starter/agent.py`). If a relevant product lies
just below the lexical Top10 cutoff, the E004 coverage reranker never gets
an opportunity to promote it. E007 tests whether giving the SAME frozen
coverage reranker a larger lexical candidate pool improves final Top10
retrieval/ranking quality. This is a post-Architecture-v1.1 experiment; it
does not mean Architecture v1.1 originally specified E007.

Current best remained E006 (see "Current Best Metrics" above) until E007
was actually evaluated; a REVERT decision has since been recorded (see
"E007 Outcome" immediately below). M6 robustness/performance findings
remain valid and are not reverted.

M7 — Submission remains deferred: E007 is finished (REVERT recorded), and
`starter/agent.py` has been restored to the pre-E007 (E006 + M6) code.
Further post-v1.1 experiments still require explicit human approval;
algorithm development is not to be marked frozen again unless the human
makes that decision.

Discipline for this extension:
- E007 is preregistered before evaluation (see EXPERIMENTS.md);
- no repeated public-set tuning of candidate pool size;
- if E007 fails (does not KEEP), revert to E006;
- do not silently launch an E007b with another pool size;
- further experiments beyond E007 require explicit human approval.

## E007 Outcome (2026-08-31)

Status: **REVERT** (human decision, 2026-08-31). Full record:
EXPERIMENTS.md "E007 — Candidate Pool Expansion before Coverage
Reranking".

E006 baseline (unchanged, current best):
HitRate@10 0.835, MRR 0.522579, MTTC 4.515, Efficiency 0.6485,
TechnicalScore 0.703974. Runtime 72.97s real.

E007 result:
HitRate@10 0.805, MRR 0.497075, MTTC 4.94, Efficiency 0.606,
TechnicalScore 0.672822. Runtime 102.17s real.

Delta vs E006: HitRate@10 -0.030000, MRR -0.025504, MTTC +0.425 (worse),
Efficiency -0.0425, TechnicalScore -0.031152, runtime +29.20s (~1.40x
slower).

Scenario deltas vs E006: buying HR@10 -0.0625/MRR -0.024737/MTTC +0.5375;
browsing HR@10 -0.0125/MRR -0.038924/MTTC +0.2375; intent_override
HR@10 -0.066667/MRR -0.026654/MTTC +0.633334; boundary HR@10 +0.200/
MRR +0.079167/MTTC +0.400 (only bucket that improved on HR@10/MRR; MTTC
still regressed there too).

Key finding: 2x lexical candidate depth (20 internal candidates) materially
regressed HR@10, MRR, MTTC/Efficiency, TechnicalScore, and runtime when
used with the current binary, unweighted E004 coverage reranker. The
implementation itself passed all 26 mechanism smoke tests, including a
synthetic label-free rescue case proving the promotion mechanism works in
isolation — but the public-set net effect was negative in three of four
scenario buckets and on every overall metric. Do not conclude deeper
retrieval is inherently harmful, or that ranking-quality improvements
(e.g. IDF/field weighting) would necessarily fix this — both are untested.
Candidate-depth expansion should not be revisited unless ranking quality
itself is first improved. No alternate pool size was tested, and none
should be without a new, separately-authorized preregistration.

Therefore current production/best code target remains E006 + M6
memoization, and `starter/agent.py` has been restored to that state — the
failed E007 change was discarded and this outcome documentation committed.

## E008 — Preregistered (2026-08-31)

New HUMAN decision on 2026-08-31: one further post-v1.1 experiment is
authorized, E008 — Candidate-Local IDF-aware Reranking. Status:
PREREGISTERED / NOT YET IMPLEMENTED. Full preregistration:
EXPERIMENTS.md "E008 — Candidate-Local IDF-aware Reranking (PREREGISTERED)".

This is a human-approved post-Architecture-v1.1 experiment extension, like
E007 before it; Architecture v1.1 (`docs/M2_SYSTEM_DESIGN.md`) remains
historical and unchanged, and still originally ends at E006. This does not
rewrite E007 history: E007 remains REVERTED.

Reason: E007 showed that the current binary/unweighted E004 coverage
reranker cannot safely exploit a noisier, deeper Top20 candidate pool. The
narrower next hypothesis is that, with the ORIGINAL E006 candidate
membership held exactly frozen, ranking ties can be improved by preferring
evidence matches that are rarer / more discriminative among the current
candidate set, using a candidate-local IDF over the exact E006 candidate
ids only (no global catalog IDF index). E008 does NOT retry candidate-pool
expansion and does NOT reintroduce E007's `POOL_MULTIPLIER`.

Current best remains E006 + M6 memoization (metrics above) until E008 is
implemented, evaluated exactly once against the official evaluator, and an
explicit KEEP or REVERT decision is recorded. Discipline: preregistered
before implementation; one official evaluator run; if E008 does not KEEP,
revert to E006 + M6; further post-v1.1 experiments beyond E008 still
require explicit human approval.

# Environment
- macOS
- Python 3.11 virtual environment at `.venv`
- official catalog downloaded and checksum verified
- official evaluator successfully reproduced
- upstream: official TechJam repository
- origin: our public submission repository
- current branch: dev
# Current Best System
E006 — Adaptive Catalog-Side Clarification: replaces E002's fixed,
turn-indexed `ask_attribute` sequence with adaptive, catalog-side selection
among five specific attributes (material, color, style, feature, use_case),
scored against the exact final E004 candidate ids for the current turn. An
attribute is scored by intersecting each candidate's `_product_terms()`
(computed once per candidate per call, reused across all five attributes —
no persistent cache) with a small frozen, catalog-general vocabulary; it is
eligible only when at least 2 candidates carry a usable value and those
values take at least 2 distinct forms, ranked by `(distinct_count,
usable_count)` with ties broken by a fixed enumeration order (material,
color, style, feature, use_case). `size` and `budget` remain legal specific
attributes but are not adaptively scored. When no attribute is adaptively
eligible, selection falls back to the first not-yet-asked specific
attribute in E002's original order (material, color, size, style, budget,
feature, use_case), then `other` once, then `None`. Per-session
asked-attribute state controls only clarification selection — no retrieval,
evidence, reranking, override, or boundary-specific behavior was added.
Status: complete / KEEP. See EXPERIMENTS.md for full record.

Prior best: E004 — Coverage-aware Lightweight Reranking (unchanged, still
running underneath E006 — see "Current Architecture" below).

# Current Best Metrics

Overall (sample_count 200):
- HitRate@10: 0.835
- MRR: 0.522579
- MTTC: 4.515
- Efficiency: 0.6485
- TechnicalScore: 0.703974

Scenario metrics:
- buying: HitRate@10 0.8625, MRR 0.502108, MTTC 3.900
- browsing: HitRate@10 0.825, MRR 0.479415, MTTC 4.675
- intent_override: HitRate@10 0.8, MRR 0.658135, MTTC 5.333333
- boundary: HitRate@10 0.8, MRR 0.625, MTTC 5.700

E006 mechanism check: HitRate@10 is bit-identical to E004 in aggregate and
in every scenario bucket, consistent with E006 changing only which
`ask_attribute` is selected and never the current turn's recommendations.
MRR (+0.004430), MTTC (-0.495), Efficiency (+0.0495), and TechnicalScore
(+0.011229) all improved vs E004. Scenario deltas vs E004: buying MRR
+0.007326 / MTTC -0.4375; browsing MRR +0.004688 / MTTC -0.6375;
intent_override MRR -0.019167 / MTTC +0.133333 (regressed); boundary MRR
+0.050000 / MTTC -1.700 (largest gain). Full record: EXPERIMENTS.md E006.

E004 (prior best): HitRate@10 0.835, MRR 0.518149, MTTC 5.01,
Efficiency 0.599, TechnicalScore 0.692745.
E003: HitRate@10 0.835, MRR 0.498681, MTTC 5.01,
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

E005 finding: an explicit-lexical-detection + erase-all pre-override reset
was tested against this E004 baseline and REVERTED — it regressed
intent_override HitRate@10, MRR, and MTTC materially (buying, browsing, and
boundary were unaffected), so overall TechnicalScore regressed to 0.644061.
This rejects erase-all specifically; it does not establish that intent
override is unsolvable, or that no override policy can help — see
EXPERIMENTS.md E005 for the full record. At the time of E005, current best
system remained E004 unchanged; E006 has since been tested and KEPT (see
below), and is now the current best system.

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

Running (`starter/agent.py`, modified per E001 + E002 + E003 + E004 + E006;
E005 tested and reverted):
- in-memory SQLite FTS5/BM25 index over the full catalog
- catalog-derived category index (full / last2 / last1 / segment
  granularities) with taxonomy-consistent relaxation and a small
  always-reachable global lexical insurance route (E001, KEEP)
- fixed, deterministic, label-free clarification sequence `_ASK_SEQUENCE`
  (E002, KEEP): material, color, size, style, budget, feature, use_case,
  other, then none on turns 9-10. Still present and byte-identical; no
  longer indexed directly by `turn` — retained as the fallback order and
  vocabulary source for E006 (below)
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
- adaptive, catalog-side clarification selection (E006, KEEP): replaces the
  turn-indexed lookup into `_ASK_SEQUENCE` with `_select_attribute()`,
  which scores five specific attributes (material, color, style, feature,
  use_case) against the exact final E004 candidate ids for the current
  turn using small frozen vocabularies, falls back to `_ASK_SEQUENCE`'s
  original seven-attribute order (including `size`/`budget`, never
  adaptively scored) when no attribute is adaptively eligible, then
  `other` once, then `None`. Per-session `_asked_attributes` state
  controls selection only. No retrieval, evidence, reranking, override, or
  boundary-specific logic added.
- `user_profile` ignored

Designed, not yet implemented — Architecture v1.1, finalized at M2:
`docs/M2_SYSTEM_DESIGN.md`. E001 implements the Retriever component's
category-scoped primary route, relaxation, and insurance route as described
there. E002 implements the ClarificationPolicy component's minimal M3
fixed-order form. E003 implements SessionEvidence's minimal M3 append-only
plumbing (evidence accumulation), not its full M5 semantics. E004
implements a minimal slice of the Reranker component (plain lexical
constraint-coverage only), not its IDF-weighted or field-weighted variants.
E006 implements the ClarificationPolicy component's adaptive M5 slice
(catalog-side pool partitioning for five specific attributes only; `size`/
`budget` remain fixed-order-only, `category`/`brand` remain unused).
Remaining, not yet implemented: intent-override supersede semantics.
Intent override will default to superseding only conflicting evidence
(category included, not privileged) once implemented; the erase-all
variant was tested at E005 and REVERTED, so the architecture's
supersede-conflicting default remains unimplemented and untested. Full
E001–E006 roadmap and milestone ownership boundaries (M3 Retrieval / M4
Ranking / M5 Conversation Intelligence / M6 Ablation / M7 Submission) are
in that document.

# M6 — Robustness, Reproducibility, and Performance

M6 — COMPLETE. Full record: EXPERIMENTS.md "M6 — Robustness,
Reproducibility, and Performance".

Robustness: PASS

Reproducibility: PASS in current verified environment

Performance optimization: KEEP

Evaluator wall-clock: 313.42s -> 72.97s, 4.30x speedup

Behavioral equivalence: 200 sessions / 870 turns / 0 mismatches

Algorithm capability remains E006. The M6 cache does not constitute E007.

The accepted optimization is a single pure per-Agent-instance memoization
cache for `_product_terms(parent_asin)` (catalog-static, immutable for the
Agent's lifetime, not cleared by session `reset()`), verified behaviorally
identical to frozen E006 across all 200 public sessions before being kept.

Known limitations:

- semantic intent-override conflict resolution remains unresolved;
- E006 lexical attribute vocabularies are heuristic;
- empty/punctuation-only evidence may produce zero recommendations;
- full internal Guard/degradation component remains unimplemented;
- exact SQLite tie ordering is empirically deterministic in current
  environment but not formally portable across all SQLite versions;
- private-set generalization remains unknown.

M6's own freeze/no-E007 declaration was the prior human decision. That
freeze has since been explicitly lifted on 2026-08-31 for one preregistered
post-v1.1 experiment (E007 — Candidate Pool Expansion) — see "Human
Decision — Freeze Lifted (2026-08-31)" above. E007 has been evaluated and
REVERTED (see "E007 Outcome" above); current best algorithm remains E006.
`starter/agent.py` has been restored to the pre-E007 (E006 + M6) code.
M7 — Submission remains deferred; see "E008 — Preregistered (2026-08-31)"
above for the current not-yet-authorized-for-M7 reason.

# Known Baseline Weaknesses

- intent override still lacks semantic conflicting-evidence supersession —
  append-only evidence can retain stale/conflicting intent; an erase-all
  reset was tested at E005 and REVERTED for regressing intent_override, so
  this limitation is unresolved. E006's own intent_override MRR/MTTC
  regressed slightly vs E004, consistent with this being unaddressed
- E006 uses small, hand-picked lexical attribute vocabularies (material,
  color, style, feature, use_case) — catalog-general but not exhaustive;
  `size` and `budget` are not adaptively scored at all
- no boundary-specific semantics
- unchanged oldest-first 40-term cap — later evidence may be truncated in
  longer sessions; this has not been measured
- `user_profile` ignored
- lexical retrieval only
- naive coverage can over-credit generic/scaffold terms: a candidate can
  receive coverage credit through an attribute-name or conversational
  scaffold word without matching the actual disclosed value (E004)
- Resolved at M6: `_product_terms()` was previously uncached, causing
  `_coverage_rerank()` (E004) and `_select_attribute()` (E006) to each
  perform their own per-candidate SQL lookup and tokenization per turn.
  M6 added a pure per-Agent-instance memoization cache for
  `_product_terms(parent_asin)`, verified behaviorally identical to E006
  across all 200 public sessions (0 mismatches) and KEPT; official
  evaluator wall-clock improved from 313.42s to 72.97s (4.30x). See
  EXPERIMENTS.md "M6 — Robustness, Reproducibility, and Performance".
- private-set generalization remains unknown

# Safety Status
- evaluator untouched
- frozen data untouched
- baseline reproducible

# Current Task
E004 — Coverage-aware Lightweight Reranking (a pure same-set reorder of the
final E003 candidate ids by plain, unweighted lexical constraint coverage;
E001 retrieval, E002 clarification sequence, and E003 evidence admission/
accumulation held frozen) remains complete and KEPT, and continues to run
underneath E006 unchanged (see EXPERIMENTS.md for full record and
rationale). HitRate@10, MTTC, and Efficiency were unchanged from E003 at
E004's own evaluation; MRR and TechnicalScore improved. Do not claim
coverage-aware ranking in general is optimal, or that IDF/field weighting
would necessarily help — only the specific plain rule tested here is
validated. Do not claim intent-override or boundary behavior is solved by
E004 — it inherits E003's append-only evidence with no supersession or
conflict resolution, and adds no override- or boundary-specific reasoning.

E005 — Explicit Intent Override Reset (M5 — Conversation Intelligence) was
tested and REVERTED: explicit lexical override detection (regex on runtime
`user_message`) combined with erasing all pre-override session evidence and
rebuilding the query from the override message alone regressed HitRate@10,
MRR, and MTTC on the `intent_override` bucket and regressed overall
TechnicalScore from 0.692745 to 0.644061, while buying, browsing, and
boundary stayed bit-identical to E004 (see EXPERIMENTS.md E005 for full
record, deltas, and interpretation). `starter/agent.py` was reverted to the
E004 code before E006 was built on top of it. Do not claim intent-override
supersession is impossible or not worth pursuing — this experiment rejects
only the erase-all variant, not finer-grained (supersede-only-conflicting)
approaches, which remain untested.

E006 — Adaptive Catalog-Side Clarification (M5 — Conversation Intelligence)
has since been tested and KEPT — see EXPERIMENTS.md E006 for the full
record. It is the current best system (see "Current Best System"/"Current
Best Metrics" above). E006 completes M5 capability development.

# Next Milestone
M5 — Conversation Intelligence is complete: E005 (erase-all override reset)
REVERTED, E006 (adaptive catalog-side clarification) KEPT. The
architecture's supersede-conflicting default override policy remains an
open, untested item — not solved, not scheduled for M6 or M7 — should a
future human decision revisit intent override. E003's oldest-first 40-term
cap, append-only evidence contamination, and E004's generic-token/scaffold
coverage limitations remain open items, not solved here. E006's extra
`_product_terms()` lookup is no longer uncached — see "M6 — Robustness,
Reproducibility, and Performance" above.

**This freeze was explicitly lifted by human decision on 2026-08-31 for one
preregistered post-v1.1 experiment: E007 — Candidate Pool Expansion before
Coverage Reranking. See "Human Decision — Freeze Lifted (2026-08-31)" above
for the full record and discipline. E007 has been implemented, evaluated
once, and REVERTED by human decision (see "E007 Outcome" above); current
best remains E006 + M6 memoization. Algorithm development is not to be
marked frozen again unless the human makes that decision, and further
post-v1.1 experiments still require explicit human approval.**

M6 — Robustness / Reproducibility / Performance is now COMPLETE (see "M6 —
Robustness, Reproducibility, and Performance" above and EXPERIMENTS.md for
the full record): robustness verification PASS, reproducibility PASS in
the current verified environment, and one semantics-preserving
`_product_terms()` memoization optimization KEPT (313.42s -> 72.97s, 4.30x
speedup, verified behaviorally identical to E006 across 200 sessions / 870
turns, 0 mismatches). M6 added no new algorithm capability.

Next milestone is **M7 — Submission**, still deferred: the freeze on
further algorithm capability development was explicitly lifted by human
decision on 2026-08-31 for one preregistered post-v1.1 experiment, E007 —
Candidate Pool Expansion before Coverage Reranking (see "Human Decision —
Freeze Lifted (2026-08-31)" above), which has now been evaluated and
REVERTED (see "E007 Outcome" above); `starter/agent.py` has been restored
to the pre-E007 (E006 + M6) code.

A second post-v1.1 experiment, E008 — Candidate-Local IDF-aware Reranking,
was preregistered by human decision on 2026-08-31 (see "E008 —
Preregistered (2026-08-31)" above and EXPERIMENTS.md for the full record).
Status: PREREGISTERED / NOT YET IMPLEMENTED. `starter/agent.py` has not
been modified for E008. M7 remains deferred pending E008's implementation,
evaluation, and KEEP/REVERT decision, or the human directing otherwise.

# Open Questions

