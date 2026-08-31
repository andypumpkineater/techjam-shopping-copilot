# Current Milestone — M7 Submission / Deliverables (2026-08-31)

**Milestone advanced from M6 to M7 by human decision on 2026-08-31.** Everything
below this section is retained unedited as the chronological record; where an
older section still says "M7 — Submission remains deferred", that statement was
true when written and is superseded by this one.

## Position

**Updated 2026-09-01 — see "E013 Outcome (2026-09-01)" below for the full
record; this Position block is kept current, not historical.**

- **Final current algorithm: E013** — Resolution/Clarification Coupling
  (clause-level evidence units + front-loaded `other`), running on top of
  E012 + E011 + E010 + E006 + M6 + E004 + E003 + E002 + E001.
- **E013 status: KEEP** (human decision, 2026-09-01).
- **Official TechnicalScore: 0.839920** — HitRate@10 0.960, MRR 0.641067,
  MTTC 2.620, Efficiency 0.838, over the 200 public sessions.
- Evaluator run at commit (post-`954f491`, pre-E013-commit): output
  `results_e013.json`, wall clock 411.19 s real. Per-session snapshot:
  `docs/diagnostics/E013_SESSIONS.json`.
- E005, E007, E008 remain REVERTED. D012 remains CANCELLED with no result.
- E012 (TechnicalScore 0.818056) is prior best, unchanged in its own record
  below, and is the full-rollback point for E013 — **both** coupled halves plus
  the original test, never one half.
- E013 is the project's highest-coupling change to date (audit overfitting risk
  "medium", vs E012's "lowest"). Two dependencies on simulator semantics are
  disclosed in the EXPERIMENTS.md record and must appear in the final report:
  the clause delimiter `;` coincides with `customer_reply()`'s own join
  character, and `other` uses that function's wildcard branch.

## Algorithm freeze for submission preparation (historical — lifted 2026-09-01)

**This freeze was lifted by human decision on 2026-09-01.** See "Algorithm
freeze lifted (2026-09-01)" under "M7 progress" below. This section is
retained unedited as the record of what was in force from 2026-08-31 to
2026-09-01.

**Algorithm capability development is frozen for the duration of submission
preparation** (human decision, 2026-08-31). No change to candidate generation,
BM25, pool depth, reranking, the proximity formula, `N_MAX`, clarification
policy, `_select_attribute()`, evidence accumulation, override behavior, category
logic, `STOPWORDS`/tokenizer, or retrieval/ranking weights. No new E-class
experiment. No public-set tuning.

`starter/agent.py` is untouched. The only changes made during submission
preparation are documentation, packaging, and provenance files that do not touch
the scored path.

A comment/docstring-only correction to `starter/agent.py` was authorized during
PHASE 2B, applied, and then **withdrawn by human decision** so that the submitted
agent source stays byte-identical to the evaluated one. Two stale comments (a
"weak baseline" class docstring and a `user_profile` personalization comment)
therefore remain in the file and are noted in the final report's limitations
rather than corrected in place.

Whether algorithm capability development reopens after submission preparation was
**not decided** at the time this section was written. It has since been decided:
see "Algorithm freeze lifted (2026-09-01)" below.

## Submission source provenance

**STALE as of 2026-09-01 — this block describes the E011-era submission and has
not been re-established since.** `starter/agent.py` has changed twice since it
was written (E012 KEEP, E013 KEEP), so the hash below is no longer the current
agent's. No submission-ready checkpoint exists at present (see "M7 progress"),
so nothing is currently mis-stated to a judge; re-deriving the hash, updating
`docs/REPRODUCIBILITY.md` section 10 and `docs/PROVENANCE.json` is an open M7
item. The original text follows unedited.

The submitted `starter/agent.py` is **byte-identical** to the agent evaluated for
the E011 result:

- evaluated (commit `093078d`): `cb46d467a114c87ef002613219be45f509e7ecbc292af15858229e1d168d0d92`
- submitted: `cb46d467a114c87ef002613219be45f509e7ecbc292af15858229e1d168d0d92`

Same file, same hash, no divergence. `EXPERIMENTS.md` needed no edit and received
none. Full statement: `docs/REPRODUCIBILITY.md` section 10 and
`docs/PROVENANCE.json`.

## Official documentation authority

Upstream `9c9e7c9` ("Publish Track 4 final evaluation FAQ") was merged into `dev`
as `fbe8ca3` on 2026-08-31. `docs/final_evaluation_faq.md` now exists in-branch
and is authoritative for final-evaluation matters it covers; the pre-merge copies
of `docs/submission_rules.md` and `docs/competition_specification.md` are
superseded history. See CLAUDE.md, "Reference Document Hierarchy". The merge
touched no runtime, evaluator, or data file.

## M7 progress

Completed in submission preparation so far:

- official documentation synchronization (merge `fbe8ca3`);
- CLAUDE.md authority hierarchy and network rule updated to match the official FAQ;
- `requirements.txt` — explicit no-third-party-dependency manifest;
- `docs/REPRODUCIBILITY.md` — environment, catalog prerequisite, setup, evaluator
  command, measured metrics, runtime, cost, determinism limits, final-results
  retention procedure, and commit/SHA provenance procedure;
- `docs/PROVENANCE.json` — one manifest binding every retained result to
  the commit, agent SHA-256, evaluator command, artifact SHA-256, and metrics,
  with each artifact labeled official or diagnostic;
- a narrowed `.gitignore` rule (`results*.json` -> `/results*.json`), so that a
  tracked artifact under `docs/` can no longer be swallowed by the root-scratch
  ignore;
- `README.md` rewritten judge-facing (commit `6482e70`) — no longer the
  organizer's starter README, no longer describes the weak BM25 baseline;
- `docs/DEMO_SESSION.md` — the reproducible multi-turn demo session required by
  `docs/final_evaluation_faq.md` section 7 (commit `c0039e6`);
- `tests/test_agent.py` — contract and session-isolation coverage for Agent
  (commit `52ba564`).

Not yet done: final technical report, figures, repository consistency audit,
cold-start reproduction, and the final submission checklist.

**A submission-ready checkpoint has NOT yet been established.** The remaining
items above are still open.

## Algorithm freeze lifted (2026-09-01)

**Human decision, 2026-09-01: the algorithm capability freeze declared above
("Algorithm freeze for submission preparation") is lifted.** Submission
preparation continues in parallel, but `starter/agent.py` may now be modified
again under the same experiment discipline used for E007–E011 (preregister in
EXPERIMENTS.md before any runtime change, run the official evaluator, record
KEEP/REVERT). This does not rewrite the M7 freeze record above, which stands
as the decision that was in force from 2026-08-31 to 2026-09-01. The next
authorized experiment is E012 — see EXPERIMENTS.md.

## Open items requiring human input

- Team roster and contributions (required by `docs/competition_specification.md`,
  "Final Deliverables"). Not fabricated; a placeholder will be used until supplied.
- Repository visibility — unverified from the working environment. No document
  claims public accessibility until confirmed.
- Catalog Release location — our fork carries no git tags; the upstream tag
  `participant-kit` exists at `2a6cc8e`. Reproduction instructions point at the
  organizer's upstream repository pending confirmation.
- `dev` -> `main` merge and push remain deferred by human decision.

# Milestone Record — M3 through M6 (historical; superseded by M7 above)
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
E008 — Candidate-Local IDF-aware Reranking was likewise implemented,
evaluated once, and REVERTED; its change was also discarded without being
committed, so `starter/agent.py` is at the E006 + M6 code. R009 —
Diagnostic / Research Infrastructure (2026-08-31) then added
`tools/diagnostics/` and `docs/diagnostics/E006_M6_BASELINE.md` with **no
runtime change**, reproducing the E006 + M6 baseline exactly. E010 —
Proximity-aware Reranking was then preregistered, implemented, evaluated
once, and **KEPT** by human decision on 2026-08-31 (see "E010 Outcome"
below). E011 — Candidate Pool Expansion under a Proximity Reranker was then
preregistered (committed in `2fd8ff0` before any runtime change), implemented,
evaluated once, and **KEPT** by human decision on 2026-08-31 (see "E011
Outcome" below). Current best algorithm is now **E011 + E010 + E006 + M6**,
and `starter/agent.py` carries the E011 change. E011's preregistration
declared itself the last capability experiment and a KEEP would freeze the
algorithm there; the human has decided **not** to execute that freeze — see
"Human Decision — Preregistered E011 Freeze Not Executed (2026-08-31)".

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

E006 baseline (the current best at the time of E007):
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

## E008 Outcome (2026-08-31)

Status: **REVERT** (human decision, 2026-08-31). Full record:
EXPERIMENTS.md "E008 — Candidate-Local IDF-aware Reranking".

E008 — Candidate-Local IDF-aware Reranking was a human-approved
post-Architecture-v1.1 experiment extension, like E007 before it;
Architecture v1.1 (`docs/M2_SYSTEM_DESIGN.md`) remains historical and
unchanged, and still originally ends at E006. This does not rewrite E007
history: E007 remains REVERTED.

Tested hypothesis: with the ORIGINAL E006 candidate membership held
exactly frozen and E004 coverage kept as the PRIMARY ranking signal,
ranking ties among equal-coverage candidates could be improved by
preferring evidence matches that are rarer / more discriminative among
the current candidate set, using a candidate-local IDF over the exact
E006 candidate ids only (no global catalog IDF index). E008 did NOT retry
candidate-pool expansion and did NOT reintroduce E007's `POOL_MULTIPLIER`.

E006 + M6 baseline (the current best at the time of E008):
HitRate@10 0.835, MRR 0.522579, MTTC 4.515, Efficiency 0.6485,
TechnicalScore 0.703974. Runtime 72.97s real.

E008 result:
HitRate@10 0.835, MRR 0.424498, MTTC 4.515, Efficiency 0.6485,
TechnicalScore 0.674549. Runtime 73.52s real.

Delta vs E006: HitRate@10 +0.000000, MRR -0.098081, MTTC +0.000
(unchanged), Efficiency +0.0000 (unchanged), TechnicalScore -0.029425,
runtime +0.55s (no meaningful runtime impact).

Scenario MRR deltas vs E006: buying -0.055541, browsing -0.105987,
intent_override -0.200913 (largest), boundary -0.066667. All four
scenario HitRate@10 and MTTC values remained bit-identical to E006.

Key finding: the implementation correctly isolated the preregistered
mechanism — candidate membership frozen, E004 coverage remained primary,
candidate-local IDF rarity only broke equal-coverage ties. Validation: all
smoke tests passed, and a direct E006-vs-E008 isolation replay over 40
public sessions / 400 turns showed 0 recommendation-set mismatches, 0
ask_attribute mismatches, and 379/400 turns with changed internal order
(confirming the mechanism actively engaged). Despite this clean isolation,
candidate-local IDF tie-breaking materially reduced MRR in every scenario
bucket while preserving HitRate@10, MTTC, Efficiency, and the
ask_attribute trajectory exactly. The supported conclusion is narrow:
within an already lexically retrieved ~Top10 pool, local rarity is a poor
proxy for target relevance and performs substantially worse than
preserving the pre-existing lexical/BM25 order among equal-coverage
candidates. Do not conclude that all IDF, global corpus IDF, field-aware
ranking, or semantic reranking is harmful — none of those were tested.

Thus, **as of E008**, the best ranking behavior remained E004 coverage
reranking with stable preservation of the incoming lexical/BM25 order on
coverage ties (i.e. no secondary tiebreak signal beyond input order), and the
production/best code target remained E006 + M6 memoization
unchanged, and `starter/agent.py` is at that code. The E008 change was
discarded without being committed; the file is byte-identical to the M6
commit `c8cc1e2` and contains no IDF-aware reranking. Verified during R009
(2026-08-31) by code inspection, not by document: `git diff -- starter/
agent.py` empty, `git diff c8cc1e2 HEAD -- starter/agent.py` empty,
SHA-256 `8615fd21…45e3a67a`, no `idf`/`rarity`/`POOL_MULTIPLIER` symbols
present, and `_coverage_rerank()` sorting on `-coverage` alone with no
secondary rarity key.

E007 remains REVERTED. E008 is now REVERTED. Do not yet declare algorithm
experimentation frozen unless explicitly directed by the human; further
post-v1.1 experiments still require explicit human approval.

## E010 Outcome (2026-08-31)

Status: **KEEP** (human decision, 2026-08-31). Full record: EXPERIMENTS.md
"E010 — Proximity-aware Reranking". Preregistration was committed in
`5035018` before `starter/agent.py` was touched.

E010 is the third human-approved post-Architecture-v1.1 experiment, after
E007 and E008. Architecture v1.1 (`docs/M2_SYSTEM_DESIGN.md`) remains
historical and unchanged and still originally ends at E006. This does not
rewrite E007 or E008 history: both remain REVERTED.

Tested hypothesis: every ranking signal used to date is a bag of words and
is invariant to word order. With candidate membership held exactly frozen,
ranking by the length of the longest contiguous n-gram of an evidence unit
(n in [2, 4], `N_MAX = 4` preregistered and frozen) appearing in the
candidate's own normalized token stream — with E004 coverage demoted from
primary key to tiebreak — improves ranking quality.

E006 + M6 baseline (prior best):
HitRate@10 0.835, MRR 0.522579, MTTC 4.515, Efficiency 0.6485,
TechnicalScore 0.703974. Runtime 73.4s.

E010 result (new best at the time; superseded by E011 below):
HitRate@10 0.835, MRR 0.653149, MTTC 4.515, Efficiency 0.6485,
TechnicalScore 0.743145. Runtime 101.4s.

Delta vs E006 + M6: HitRate@10 +0.000000, MRR **+0.130570**, MTTC +0.000,
Efficiency +0.0000, TechnicalScore **+0.039171**, runtime +28.0s (~1.39x
slower, reported not optimized — the preregistration forbade bundling a
performance experiment).

Scenario MRR deltas: buying +0.152699, browsing +0.128859, boundary
+0.125000, intent_override +0.077976. All four buckets improved. All four
scenario HitRate@10 and MTTC values are bit-identical to E006.

**Structural finding — E010 is a pure-MRR experiment by construction.**
`_coverage_rerank()` receives exactly the ids that are returned (`ids` is
already sliced to `ids[:top_k]` before the call). With pool depth frozen at
10, reordering can only move the target *within* the returned ten, never
across the top-10 boundary. HitRate@10, MTTC, and Efficiency are therefore
necessarily unchanged, and TechnicalScore delta equals exactly
`0.30 * MRR delta`. The preregistration had anticipated that `first_hit_turn`
might change; it did not and could not. Consequently the correct ceiling for
E010 is D-2's "perfect order, current top-10" bound (**+0.093726**), not
D-3's `phrase_n4` counterfactual (+0.1096), which requires pool depth 100.
E010 captured 41.8% of its actual ceiling. The D-3 figure was never used as
a target, prediction, or success criterion.

Validation: 27 mechanism smoke checks passed, including bit-identity of
`_proximity_score()` with R009's D-3 `phrase_n4` scorer across 720
(message-set, product) pairs and of `_product_stream()` with D-3's
`normalized_text()` across 400 real products. The invariant check
(`--expect ranking-only`) returned **PASS** over 200 sessions / 870 turns:
candidate membership changed 0/870, `ask_attribute` changed 0/870, order
changed 610/870 (mechanism strongly engaged), `first_hit_turn` changed in 0
sessions. Because the trajectory is provably frozen, the offline trace
predicted the official result bit-exactly before the evaluator was run.

D-5 paired transition matrix (n=200): miss→hit 0, **hit→miss 0**, rank
improved **53**, rank regressed **1**, unchanged 113, miss→miss 33. Scored
rank 1 rises 82 → 112; ranks 9–10 fall 8 → 0. The single regression is
`public_0080` (intent_override, rank 2 → 4), consistent with the known
unresolved append-only-evidence limitation — a proximity match against a
stale pre-override phrase can outrank the post-override target. One session,
not a cluster.

Key finding: within the candidate set the agent already returns, word-order
proximity is a materially better ranking signal than bag-of-words overlap.
This is the first signal dimension tested that was not already exhausted,
and it is consistent with R009's diagnostic finding that every bag-of-words
re-weighting lands within ±0.02. Do **not** conclude that `N_MAX = 4` is
optimal (no other value was run officially), that proximity-first is the
best key order (only the preregistered order was run), that deeper candidate
pools would now pay off (E007 remains REVERTED and untested under this
ranker), that intent override or boundary behavior is solved (neither
received new logic), or that E008's conclusion is overturned (E008 rejected
candidate-local IDF as a tiebreak *under* coverage; E010 replaces the
primary key with a different signal class — the two are not in competition).

**That open risk is now retired.** E010 was kept with one named scoring risk:
a rule keyed on contiguous n-grams is a priori more paraphrase-sensitive than
the bag-of-words rule it replaced, and the public set could not detect it. The
official FAQ (`docs/final_evaluation_faq.md`, upstream `9c9e7c9`) §1 states that
the final 800 samples use the same deterministic customer-message templates as
the published evaluator, and that "No undisclosed natural-language paraphrases
are introduced." The D012 paraphrase stress test was preregistered, built, and
then **CANCELLED without ever being run to a result** (EXPERIMENTS.md, "D012 —
Paraphrase Stress", Cancellation). There is no D012 number and none may be
cited. The highest-value next investigation is now **E011 — candidate pool
depth**, which has actual D-2 oracle support: pool 100 prices a perfect-reranker
ceiling of 0.9609 against 0.7672 at pool 10, and E010 is capped by the top-10 it
reorders (ceiling +0.093726, of which 41.8% is captured). E011 requires its own
preregistration and human authorization; E007's pool expansion failed under the
old ranker for reasons E010 does not address, so this is not a re-run of E007.

E007 remains REVERTED. E008 remains REVERTED. E010 is KEPT. Algorithm
development is not frozen; further post-v1.1 experiments still require
explicit human approval.

## E011 Outcome (2026-08-31)

Status: **KEEP** (human decision, 2026-08-31). Full record: EXPERIMENTS.md
"E011 — Candidate Pool Expansion under a Proximity Reranker". Preregistration
was committed in `2fd8ff0` before `starter/agent.py` was touched.

E011 is the fourth human-approved post-Architecture-v1.1 experiment, after
E007, E008 and E010. E007 and E008 remain REVERTED; E010 is KEPT and runs
underneath E011.

Tested hypothesis: the ranker is no longer the limiting factor, so giving the
same E010 proximity reranker a deeper candidate pool converts into a
HitRate@10 gain — the metric E010 was structurally unable to move.

E010 baseline (prior best): HitRate@10 0.835, MRR 0.653149, MTTC 4.515,
Efficiency 0.6485, TechnicalScore 0.743145. Runtime 101.4s.

E011 result (new best): HitRate@10 0.930, MRR 0.625462, MTTC 3.785,
Efficiency 0.7215, TechnicalScore 0.796939. Runtime 282.9s.

Delta vs E010: HitRate@10 **+0.095000**, MRR **−0.027687**, MTTC **−0.730**,
Efficiency +0.0730, TechnicalScore **+0.053794**, runtime +181.5s (2.79x
slower, reported not optimized).

Scenario deltas: buying HR +0.0625 / MRR −0.049137 / MTTC −0.712; browsing
HR +0.1250 / MRR −0.023844 / MTTC −0.900; intent_override HR +0.0667 /
MRR −0.009405 / MTTC −0.533; boundary HR +0.2000 / MRR +0.058333 /
MTTC −0.100. HitRate@10 and MTTC improved in all four buckets; MRR fell in
three. `boundary` reaching HR@10 1.0 is n = 10 and supports no conclusion.

**Where the MRR loss came from — decomposed exactly (residual 4.9e−10).**
miss→hit +0.036187, hit→hit improved +0.005417, hit→hit **regressed −0.069290**,
hit→miss **exactly 0.000000**. The entire loss is 26 retained hits losing rank;
not one point comes from a lost hit. 11 of the 26 started at rank 1 and 5 of
those fell to rank 8. The 19 new hits land low (mean rank 4.58, only 4 at
rank 1, 6 at ranks 7–9), which is why +19 hits buys much HitRate@10 and MTTC
but little MRR. The 26 regressions are uniformly spread — 10.0 / 13.8 / 13.8 /
10.0 % of boundary / browsing / buying / intent_override — not clustered.

Validation: 23 mechanism smoke checks passed, including that the pool is
genuinely 50 deep (119/119 turns) and that truncation follows the rerank
(83/119 turns promote a candidate from below pool rank 10 into the returned
ten). The invariant check was run **without** `--expect` and was explicitly
**not** a gate — `--expect ranking-only` fails by construction here, as the
preregistration stated. Four channels over 200 sessions / 706 turns: membership
changed 633, order-only changed 0, `ask_attribute` changed 248, target rank
changed 87; 74 sessions changed `first_hit_turn` and turn count. The genuine
warning signal — a turn whose top-10 is unchanged but whose `ask_attribute`
changed — occurred **0 times**, so every clarification change is downstream of
a candidate-list change, as the declared mechanism requires. The offline replay
predicted all five official metrics bit-exactly *despite* the trajectory
diverging on 74 sessions, which validates R009's replay core under trajectory
change and not merely under a frozen dialogue.

**Key finding — the bottleneck is now almost entirely ordering.** HitRate@10
0.930 attains 99.5% of D-2's perfect-reranker recall bound at pool 50 (0.935).
Of the 0.106261 TechnicalScore separating E011 from that pool-50 oracle
(0.903200), 87.4% is MRR, 10.3% MTTC, and 2.4% HitRate@10. At pool 10 the R009
diagnosis was "ranking, not recall" with recall still worth ~1 point; at pool 50
the recall term is worth 0.0025 of TechnicalScore in total.

**Key finding — E010 and E011 are complementary and their order was
load-bearing.** E010 moved MRR only (+0.130570, HitRate@10 and MTTC frozen by
construction). E011 moved HitRate@10 and MTTC and gave back 21.2% of E010's MRR
gain. E007 made the *same* architectural move — deepen the pool — under the
binary E004 coverage ranker and regressed −0.031 on every overall metric; E011
made it under the E010 proximity ranker and gained +0.054. Ordering strength is
a **precondition** for pool expansion, not an independent axis, and E007's
failure was a sequencing error rather than a hypothesis error. This confirms
E007's narrow stated conclusion and refutes the broader reading that deeper
retrieval is harmful per se.

**Recorded gap in the decision criterion.** The preregistered gate tested for a
hit→miss cluster; hit→miss was zero, so it had nothing to bite on. The run's
only reverse signal — 26 rank regressions worth −0.069290 MRR — is a phenomenon
the gate does not measure. The conclusion is unchanged (the regressions are
uniformly spread, and unlike a hidden scenario collapse an MRR loss is already
priced into the 0.30 × MRR term the KEEP threshold is measured on, so +0.053794
is net of it), but the omission is recorded: "gate passed" is not "nothing
regressed", and a future preregistration should state which regression modes its
gate covers. The criterion was applied as written and not reinterpreted after
seeing results.

**Deviations from the preregistration**, both recorded in EXPERIMENTS.md rather
than absorbed: (1) step 5, the D-3 pool-50 prescreen, was dropped by human
decision as redundant once a full replay of the real agent had produced every
metric — the started D-3 run was killed and produced no output, so there is no
E011 D-3 number and none may be cited; (2) the scoped path's global-BM25 fetch
depth was rescaled with the pool (`top_k * 5` → `POOL_DEPTH * 5`, 50 → 250) to
stop actual pool depth becoming data-dependent, and was then *measured* to make
no difference — over 224 scoped turns the two depths produce byte-identical
pools.

Do **not** conclude that 50 is the right depth (one preregistered value, no
sweep), that 70/30 is the right composition at this depth (held from E001 to
avoid a second variable), that `N_MAX = 4` is optimal (still frozen, still never
swept officially), that intent override or boundary behavior is solved (neither
received new logic; intent_override remains the weakest bucket at HR@10 0.867),
or that the MRR regression is harmless in general (it is priced into *this*
metric set; a deployment weighting top-1 precision more heavily would score the
trade differently).

E007 remains REVERTED. E008 remains REVERTED. E010 and E011 are KEPT.

# Human Decision — Preregistered E011 Freeze Not Executed (2026-08-31)

The committed E011 preregistration (`2fd8ff0`) declared E011 to be "the LAST
capability experiment", with the algorithm freezing at E011 on KEEP and at E010
on REVERT. E011 was KEPT.

**New HUMAN decision on 2026-08-31: that freeze is not executed.** Algorithm
capability development stays open and options are retained.

This does not rewrite the preregistration, which stands unedited as the
chronological record of what was committed before the experiment ran — the same
treatment given to the original post-E006 freeze when it was lifted (see "Human
Decision — Freeze Lifted (2026-08-31)" above). What changes is only what happens
next.

Discipline, unchanged from the earlier lift:
- **any further capability experiment requires separate explicit human
  authorization and its own separate preregistration**;
- algorithm development is not to be marked frozen again unless the human makes
  that decision;
- no repeated public-set tuning; no silent E011b with another pool depth.

**Factual position on remaining headroom — a statement of evidence, not an
authorization for any next experiment.** D-2 prices a perfect reranker at pool
100 at TechnicalScore 0.9609, against 0.9032 at pool 50, so the pool-depth
direction still carries measurable oracle headroom. Against that, E011's own
observed direction is that deepening the pool *costs* MRR (−0.027687 at 10 → 50,
entirely through rank regressions among retained hits), so a deeper pool would
not be expected to redeem that oracle ceiling proportionally. Separately, 87.4%
of what remains at pool 50 is ordering rather than recall. These facts point in
different directions; none of them is an experiment authorization.

# E012 Outcome (2026-09-01)

Status: **KEEP** (human decision, 2026-09-01). Full record: EXPERIMENTS.md
"E012 — Candidate Pool Expansion 50 -> 100". Preregistration was committed in
`ff8cb44` before `starter/agent.py` was touched.

E012 is the fifth human-approved post-Architecture-v1.1 experiment, after
E007, E008, E010 and E011. It was authorized by the "Algorithm freeze lifted
(2026-09-01)" human decision recorded above, which reopened capability
development after E011's preregistered freeze was declared but explicitly not
executed (see "Human Decision — Preregistered E011 Freeze Not Executed" above).

Tested hypothesis: E011's own record extrapolated that deepening the pool
costs MRR roughly in proportion to depth, based on the single 10 -> 50 data
point. E012 tested whether that linear extrapolation holds from 50 to 100
under the same E010 proximity reranker, by changing exactly three constants
(`POOL_DEPTH` 50 -> 100, `PRIMARY_SLOTS` 35 -> 70, `INSURANCE_SLOTS` 15 -> 30)
with zero logic changes — confirmed by `git diff` showing only those constants
and their comments changed.

E011 baseline (prior best): HitRate@10 0.930, MRR 0.625462, MTTC 3.785,
Efficiency 0.7215, TechnicalScore 0.796939. Runtime 282.9s.

E012 result (new best): HitRate@10 0.965, MRR 0.623520, MTTC 3.575,
Efficiency 0.7425, TechnicalScore 0.818056. Runtime 444.30s.

Delta vs E011: HitRate@10 **+0.035000**, MRR **-0.001942**, MTTC **-0.210**,
Efficiency +0.0210, TechnicalScore **+0.021117**, runtime +161.4s (~1.57x
slower, reported not optimized per preregistration).

**The offline full-dynamic-replay prediction was bit-identical to the official
result** on every metric (TS 0.818056, HR@10 0.965, MRR 0.623520, MTTC 3.575),
and runtime matched closely (predicted 444s, measured 444.30s). This is the
second time this replay methodology (trajectory divergence allowed, not a
frozen-dialogue counterfactual) has predicted an official evaluator result
exactly, after E011. The official run was still performed and is the basis
for this decision, per the preregistration.

D-5 paired transition matrix vs `docs/diagnostics/E011_SESSIONS.json` (n=200):
miss->hit 7, **hit->miss 0**, rank improved 1, rank regressed 8, unchanged 177,
miss->miss 7. The 8 rank regressions are spread 3/80 buying, 3/80 browsing,
2/30 intent_override, 0/10 boundary — no cluster in any bucket.

**Key finding — E011's linear-cost extrapolation was wrong; the true relationship
is sublinear.** The 10 -> 50 step (E011) cost -0.027687 MRR. The 50 -> 100 step
(E012) cost only -0.001942 MRR — 7.0% of the per-step rate a linear reading of
E011 would imply. HitRate@10 continued climbing (+0.035 on top of E011's own
+0.095) and MTTC continued falling, while MRR held almost flat. 50 was not
close to a local optimum for this architecture.

**This does not establish pool depth is free of cost**: 8 sessions still lost
rank among retained hits, the same mechanism as E011 (more pool candidates,
more opportunities to outrank the target under the proximity key). The
per-depth-unit cost appears to be shrinking, not zero, and no per-session
inspection of the regressions was performed.

Do **not** conclude that 100 is the optimal depth (a preregistered offline
50->200 sweep showed marginal gain flattening past 100 — +0.0059 from 100->200
vs +0.0211 from 50->100 — which motivated stopping at 100, but no further depth
was run against the official evaluator), that 70/30 is the right composition at
this depth (held from E001/E011, not swept), that `N_MAX = 4` is optimal (still
frozen), or that intent_override or boundary behavior is solved (intent_override
HitRate@10 rose to 0.9 from 0.867, but its MRR/MTTC dynamics were not separately
analyzed beyond the D-5 table; boundary is n=10 and every session in it was
unchanged by E012).

E007 and E008 remain REVERTED. E010, E011 and E012 are KEPT. E013/E014 (from
the post-E011 audit, Artifact 37161e21) remain unauthorized and out of scope
for this decision; any further capability experiment requires separate explicit
human authorization and its own preregistration.

# E013 Outcome (2026-09-01)

Status: **KEEP** (human decision, 2026-09-01). Full record: EXPERIMENTS.md
"E013 — Resolution/Clarification Coupling (clause-level evidence units +
front-loaded `other`)". Preregistration was committed in `954f491` before
`starter/agent.py` was touched.

E013 is the sixth human-approved post-Architecture-v1.1 experiment, after E007,
E008, E010, E011 and E012. It was authorized by the "Algorithm freeze lifted
(2026-09-01)" decision recorded above together with the 2026-09-01
authorization block in the post-E011 ranking-bottleneck audit (Artifact
`37161e21`), which chose clarification option (b) and authorized revising one
existing test.

**Preregistered and executed as ONE indivisible experiment.** The audit's
offline 2x2, all four arms on the same E012 pool-100 baseline, measured clause
splitting alone at **-0.0042**, first-two-turns `other` alone at **-0.0017**,
and the pair at **+0.0212** — an interaction term of +0.0271. Run as two
sequential experiments, the first would have REVERTed on -0.0042 and, by the
E007/E011 "do not test a second value if the first fails" discipline, cancelled
the second, permanently closing the gain. The bundling was declared up front in
the preregistration following the E011 precedent, not discovered afterwards.

Coupled change (exactly two, zero other behavior lines):
1. `_evidence_units()` / `_evidence_token_lists()` split each admitted message
   into clauses on `[;:.!?•]` and `", "` before `_terms()`, with a whole-message
   fallback when no non-blank clause remains. Both use the identical splitter so
   the one-to-one alignment E010's proximity path requires is preserved.
2. `_select_attribute()` returns `"other"` on turns 1 and 2 and hands back to
   the existing E006 adaptive logic from turn 3, with `_asked_attributes`
   bookkeeping unchanged (so turn 2 is a deliberate repeat).

`POOL_DEPTH`, the 70/30 composition, BM25, `N_MAX`, the proximity formula, the
sort key, and E003 evidence *admission* are byte-identical — confirmed by
`git diff`.

E012 baseline (prior best): HitRate@10 0.965, MRR 0.623520, MTTC 3.575,
Efficiency 0.7425, TechnicalScore 0.818056. Runtime 444.30s.

E013 result (new best): HitRate@10 0.960, MRR 0.641067, MTTC 2.620,
Efficiency 0.838, TechnicalScore 0.839920. Runtime 411.19s.

Delta vs E012: HitRate@10 -0.005, **MRR +0.017547**, **MTTC -0.955**,
Efficiency +0.0955, TechnicalScore **+0.021864**, runtime -33.1s (slightly
faster despite more evidence units — the proximity loop breaks at the first
matching n-gram, which happens sooner on shorter units).

**Key finding — the post-E012 bottleneck was score resolution, and the two
channels moved exactly as the coupling predicted.** E011 and E012 each bought
HitRate@10 by spending MRR (-0.0277 and -0.0019). E013 is the **first
experiment to raise MRR** (+0.0175), and it did so without touching the
proximity formula, the sort key, the pool, or any retrieval signal — only by
letting each disclosed constraint occupy its own evidence unit. Rank-1 sessions
went 97 -> 104. Separately, MTTC fell by nearly a full turn, with the mechanism
directly visible in the first-hit-turn histogram: turn-2 hits 38 -> 94 and the
entire tail past turn 6 eliminated, consistent with two open-ended turns
exhausting a 4-constraint card disclosed 2 at a time.

D-5 paired transition matrix vs `docs/diagnostics/E012_SESSIONS.json` (n=200):
miss->hit 3, **hit->miss 4**, rank improved 39, rank regressed 43, unchanged
107, miss->miss 4. The 4 hit->miss sessions are spread buying 2/80, browsing
1/80, intent_override 1/30, boundary 0/10 — no bucket above a 3.3% loss rate,
so no cluster under the preregistered definition. **This is the first non-zero
hit->miss count since E010** (E011 and E012 each had zero) and was put to the
human explicitly before the KEEP rather than absorbed into the rule text.

**This does not establish that the change is free.** 43 sessions lost rank
against 39 that gained; MRR rose because the gains were larger per session, not
because the change is uniformly good. Three of the four lost sessions were
marginal hits already (ranks 10, 10, 8). No per-session diagnosis of the
regressions was performed.

Do **not** conclude that two `other` turns is the optimal count (no other count
was run officially), that the clause delimiter set is tuned or tunable (it was
fixed before evaluation and must not be adjusted now the result is known), that
the +0.0271 interaction term generalizes beyond pool 100 under this reranker,
or that the four hit->miss sessions are benign (they pass the distribution test;
they were not diagnosed).

**Methodological result, recorded separately:** the offline replay core that
predicted E011 and E012 bit-exactly predicted E013 only approximately (TS
0.839220 vs 0.839920; MTTC 2.655 vs 2.620). It remains a good predictor but is
now demonstrably approximate, and the divergence appeared where theory says it
should — E013 is the first change in which the agent's own question alters the
simulator's disclosure path from turn 1. Future preregistrations should cite
replay numbers as approximate.

**Authorized test revision.**
`tests/test_agent.py::test_an_attribute_is_never_asked_twice_in_one_session`
was replaced by `test_the_clarification_schedule_opens_wide_then_narrows`. The
old test encoded a self-imposed E002 policy as if it were a contract
requirement; neither `docs/agent_api_contract.json` nor
`evaluator/local_evaluator.py` prohibits repeating a question. The human
authorized the revision on 2026-09-01 on condition it be recorded explicitly.
The new test pins what is actually required. No other test was modified. Full
suite: 37 tests, all passing.

E007 and E008 remain REVERTED. E010, E011, E012 and E013 are KEPT. **No further
capability experiment is authorized.** The post-E011 audit's stop list (§12)
closes `N_MAX` tuning, field-weighted proximity, tie-break sort keys,
intent_override semantics, `user_profile` personalization, D012, and
bag-of-words reweighting; §14 judges the remaining tie-collapse headroom
unreachable without a signal class the human's 2026-09-01 "no model/API"
decision excludes. Two non-experimental obligations remain open: writing the
audit's exact-substring dependency into the final report's limitations (and
updating `docs/M2_SYSTEM_DESIGN.md`, whose overfitting rule #1 it contradicts),
and presenting the `other` half as a product insight with its
`customer_reply()` dependence disclosed alongside.

# Environment
- macOS
- Python 3.11 virtual environment at `.venv`
- official catalog downloaded and checksum verified
- official evaluator successfully reproduced
- upstream: official TechJam repository
- origin: our public submission repository
- current branch: dev
# Current Best System

E013 — Resolution/Clarification Coupling: two inseparable changes on top of
E012's pool-100 retrieval. (1) One admitted message is split into clauses on
`[;:.!?•]` and `", "` before tokenization, so each disclosed constraint becomes
its own evidence unit and scores its own proximity n-gram instead of sharing
one. (2) `_select_attribute()` asks the open-ended `"other"` on turns 1 and 2,
then hands back to E006's adaptive logic from turn 3. Neither half works alone
(-0.0042 and -0.0017 offline); together +0.0219 official. Retrieval, pool depth,
BM25, `N_MAX`, the proximity formula, the sort key, and evidence admission are
unchanged from E012. Status: complete / KEEP. TechnicalScore 0.839920 —
HitRate@10 0.960, MRR 0.641067, MTTC 2.620, Efficiency 0.838. See EXPERIMENTS.md
for full record.

Prior best: E012 — Candidate Pool Expansion 50 -> 100: identical mechanism to E011 below,
at double the depth. `POOL_DEPTH = 100` (was 50), `PRIMARY_SLOTS = 70` (was
35), `INSURANCE_SLOTS = 30` (was 15) — the 70/30 ratio established at E001 is
unchanged, only the depth it operates at doubles. No other line in
`starter/agent.py` changed: the global-BM25 fetch depth that sources the
insurance slots (`max(POOL_DEPTH * 5, primary_slots + insurance_slots)`) is a
dependent quantity of `POOL_DEPTH` under E011's existing formula and rescales
automatically (250 -> 500). Status: complete / KEEP. TechnicalScore 0.818056.
See EXPERIMENTS.md for full record.

Prior best: E011 — Candidate Pool Expansion under a Proximity Reranker
(unchanged as a mechanism, still running underneath E012 at the new depth).

E011 — Candidate Pool Expansion under a Proximity Reranker: retrieval fills an
internal `POOL_DEPTH = 50` candidate pool instead of the contract's `top_k`
(10), the E010 proximity reranker orders the whole pool, and only then is the
list cut to 10. Pool composition holds E001's 70/30 split at the new depth —
`PRIMARY_SLOTS = 35` category-scoped, `INSURANCE_SLOTS = 15` global lexical
insurance — and both retrieval paths changed together, so the unscoped path
(`detected is None`) also retrieves 50; leaving it at 10 would have made
retrieval depth a hidden variable. Because the reranker now selects all ten
returned ids from the merged pool, the guaranteed global-insurance slots become
a property of *pool composition* rather than of the *output*; that coupling is
inseparable from pool expansion and was declared in the preregistration rather
than left implicit. Everything E010 and earlier established is unchanged:
`N_MAX = 4`, the proximity formula, the `(proximity, coverage, incoming order)`
sort key, BM25 weights, `_terms()`/`STOPWORDS`, the 40-term cap, category
detection and relaxation, `_select_attribute()`, evidence admission, and
override handling (still none). Status: complete / KEEP. TechnicalScore
0.796939. See EXPERIMENTS.md for full record.

Note one intrinsic coupling: asking the same relaxation ladder for 35 primary
ids instead of 7 makes it climb to broader category levels more often. No
relaxation code changed; this follows from the deeper primary capacity.

Prior best: E010 — Proximity-aware Reranking (unchanged, still running
underneath E011 as the ranking rule — see "Current Architecture" below).

E010 — Proximity-aware Reranking: a pure same-set reorder of the candidate ids
by word-order proximity. For each admitted evidence unit (one
E003 message = one unit, the E004 definition, but order-preserving), the
candidate scores the length of the longest contiguous n-gram of that unit's
token sequence, n in [2, `N_MAX = 4`], occurring in the candidate's own
normalized, space-padded token stream (`_product_stream()`, the same six
indexed fields and same `_terms()` tokenization as `_product_terms()`,
memoized per Agent instance following the M6 pattern). Unit contributions
sum; a unit with no matching n-gram contributes 0. Unigrams are excluded by
construction — a single-token match is bag-of-words overlap, which E004's
coverage already scores. `_coverage_rerank()` sorts on
`(proximity DESC, coverage DESC, incoming lexical order stable)`, so E004
coverage is retained but demoted from primary key to tiebreak. Candidate
membership, pool depth, the 7/3/10 slot structure, BM25 weights, `_terms()`,
`STOPWORDS`, category detection and relaxation, `_select_attribute()`,
evidence admission, override handling, and candidate routing were all
unchanged **at E010**. Status: complete / KEEP, still running as E011's ranking
rule. Note that E011 has since changed pool depth (10 → 50) and the slot
structure (7/3 output slots → 35/15 pool capacities), so the freeze list in
this paragraph describes E010's own experiment, not the current system. See
EXPERIMENTS.md for full record.

Prior best: E006 — Adaptive Catalog-Side Clarification (unchanged, still
running underneath E010 and E011 — see "Current Architecture" below).

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

Prior best before E006: E004 — Coverage-aware Lightweight Reranking (its
coverage count is unchanged and still running underneath E010/E011, demoted to
the secondary sort key — see "Current Architecture" below).

# Current Best Metrics

Overall (sample_count 200) — E013:
- HitRate@10: 0.960
- MRR: 0.641067
- MTTC: 2.620
- Efficiency: 0.838
- TechnicalScore: 0.839920

Scenario metrics:
- buying: HitRate@10 0.95, MRR 0.577996, MTTC 2.2
- browsing: HitRate@10 0.975, MRR 0.633408, MTTC 2.375
- intent_override: HitRate@10 0.933333, MRR 0.809722, MTTC 4.2
- boundary: HitRate@10 1.0, MRR 0.700952, MTTC 3.2

Runtime 411.19s, slightly faster than E012's 444.30s despite the extra evidence
units (the proximity loop breaks at the first matching n-gram, which happens
sooner on shorter units).

E013 mechanism check / D-5 vs E012 (n=200): miss->hit 3, hit->miss 4, rank
improved 39, rank regressed 43, unchanged 107, miss->miss 4. MRR delta
**+0.017547** — the first experiment in the project to move MRR upward — and
MTTC delta **-0.955**. The 4 hit->miss sessions are the first non-zero count
since E010; they are spread buying 2/80, browsing 1/80, intent_override 1/30,
boundary 0/10, no bucket above 3.3%, so no cluster under the preregistered
definition. Note that 43 sessions lost rank against 39 gained: MRR rose because
the gains were larger per session, not because the change is uniformly good.
Full record: EXPERIMENTS.md "E013".

E012 (prior best): HitRate@10 0.965, MRR 0.623520, MTTC 3.575,
Efficiency 0.7425, TechnicalScore 0.818056. Runtime 444.30s.

Scenario metrics at E012:
- buying: HitRate@10 0.9625, MRR 0.604162, MTTC 2.925
- browsing: HitRate@10 0.9875, MRR 0.585645, MTTC 3.5
- intent_override: HitRate@10 0.9, MRR 0.714537, MTTC 4.833333
- boundary: HitRate@10 1.0, MRR 0.808333, MTTC 5.6

E012 mechanism check / D-5 vs E011 (n=200): miss->hit 7, hit->miss 0, rank
improved 1, rank regressed 8, unchanged 177, miss->miss 7. MRR delta -0.001942
(only 7.0% of the 10->50 per-step MRR cost E011 recorded), MTTC delta -0.210.
No hit->miss cluster; 8 rank regressions spread 3/80 buying, 3/80 browsing,
2/30 intent_override, 0/10 boundary. Full record: EXPERIMENTS.md "E012".

E011 (prior best): HitRate@10 0.930, MRR 0.625462, MTTC 3.785,
Efficiency 0.7215, TechnicalScore 0.796939. Runtime 282.9s.

Scenario metrics at E011:
- buying: HitRate@10 0.925, MRR 0.605670, MTTC 3.1875
- browsing: HitRate@10 0.95, MRR 0.584430, MTTC 3.775
- intent_override: HitRate@10 0.866667, MRR 0.726706, MTTC 4.800
- boundary: HitRate@10 1.0, MRR 0.808333, MTTC 5.600

E011 mechanism check: HitRate@10 +0.095000 and MTTC −0.730 improved in all
four scenario buckets; MRR fell −0.027687 overall (three buckets down, boundary
up). The MRR loss decomposes **exactly** (residual 4.9e−10): miss→hit
contributed +0.036187, hit→hit improved +0.005417, and hit→hit **regressed
−0.069290**. hit→miss contributed exactly 0.000000 — no session that hit under
E010 misses under E011. The whole MRR loss is 26 retained hits losing rank, not
one lost hit; a deeper pool injects candidates that outrank the target under the
proximity key. Those 26 regressions are uniformly spread across buckets —
boundary 1/10 (10.0%), browsing 11/80 (13.8%), buying 11/80 (13.8%),
intent_override 3/30 (10.0%) — so they are not a cluster under any reading.
D-5: miss→hit 19, hit→miss **0**, rank improved 3, rank regressed 26,
unchanged 138, miss→miss 14. Per-session outcomes tracked verbatim as
`docs/diagnostics/E011_SESSIONS.json`.

**Headroom position at pool 50.** HitRate@10 0.930 is **99.5%** of D-2's
perfect-reranker recall bound at the same depth (0.935) — candidate
availability at this depth is essentially exhausted. Of the 0.106261
TechnicalScore still separating E011 from the pool-50 oracle (0.903200),
**87.4% is MRR** (0.092861), 10.3% MTTC (0.010900), and only 2.4% HitRate@10
(0.002500). The remaining opportunity at this depth is ordering, not recall.

E010 (prior best): HitRate@10 0.835, MRR 0.653149, MTTC 4.515,
Efficiency 0.6485, TechnicalScore 0.743145. Runtime 101.4s.

Scenario metrics at E010:
- buying: HitRate@10 0.8625, MRR 0.654807, MTTC 3.900
- browsing: HitRate@10 0.825, MRR 0.608274, MTTC 4.675
- intent_override: HitRate@10 0.8, MRR 0.736111, MTTC 5.333333
- boundary: HitRate@10 0.8, MRR 0.750000, MTTC 5.700

E010 mechanism check (as measured at E010, against E006 + M6): HitRate@10,
MTTC, and Efficiency were bit-identical to E006 in aggregate and in every
scenario bucket — necessarily so, because at that time `_coverage_rerank()`
reordered exactly the ten ids that were returned, so the target could never
cross the top-10 boundary (see "E010 Outcome" above). Only MRR moved
(+0.130570), and TechnicalScore's +0.039171 gain was attributable to the MRR
term alone (0.30 × 0.130570 = 0.039171). All four scenario buckets improved on
MRR. D-5: 53 sessions rank-improved, 1 regressed, 0 hit→miss. **That
construction no longer holds:** E011 reranks a 50-deep pool and cuts to 10
afterwards, so the target can now cross the boundary in both directions, which
is exactly how E011 moved HitRate@10.

E006 (prior best): HitRate@10 0.835, MRR 0.522579, MTTC 4.515,
Efficiency 0.6485, TechnicalScore 0.703974.

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
EXPERIMENTS.md E005 for the full record. At the time of E005, the current best
system remained E004 unchanged; E006 has since been tested and KEPT (see
below), and E010 and E011 have since been kept on top of it. The current best
system is **E011** — see "Current Best System" / "Current Best Metrics" above.

# Reference Documents
- `docs/sources/TRACK4_PROBLEM_STATEMENT.md` — vision-level problem statement
  (directional only: dual-track routing, hybrid/LLM semantic ranking, dynamic
  context programming). Not authoritative for scoring or interface behavior.
- Authoritative scoring/interface spec: `docs/competition_specification.md`,
  `docs/agent_api_contract.json`, `docs/evaluation_config.json`,
  `evaluator/local_evaluator.py`.
- `docs/final_evaluation_faq.md` (merged from upstream `9c9e7c9`) — authoritative
  for the final-evaluation process, code freeze, network/API/credential policy,
  hardware and runtime expectations, data policy, and submission/judging
  clarifications. Supersedes earlier submission/process wording on the matters it
  covers.
- `docs/REPRODUCIBILITY.md` — environment, catalog prerequisite, evaluator
  command, measured metrics, retention and provenance procedures.
- `docs/PROVENANCE.json` — result-to-code binding manifest for every
  retained run, with each artifact labeled official or diagnostic.
- See CLAUDE.md → "Reference Document Hierarchy" for the precedence rule.

# Current Architecture

Two layers: what's running, and what's designed but not yet implemented.

Running (`starter/agent.py`, modified per E001 + E002 + E003 + E004 + E006 +
E010 + E011 + E012; E005, E007, and E008 tested and reverted):
- in-memory SQLite FTS5/BM25 index over the full catalog
- catalog-derived category index (full / last2 / last1 / segment
  granularities) with taxonomy-consistent relaxation and an always-reachable
  global lexical insurance route (E001, KEEP). Since E012 the split is
  70 primary / 30 insurance **pool capacities** at `POOL_DEPTH = 100` (E011
  introduced the 35/15-at-50 pool-capacity model; E012 doubled the depth,
  holding the 70/30 ratio), not 7/3 output slots. Asking the same relaxation
  ladder for 70 ids instead of 7 makes it climb to broader category levels
  more often — an intrinsic consequence of the deeper capacity, not a
  relaxation-logic change
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
  count are unchanged from E003 — ordering only. Since E010 this count is
  the SECONDARY sort key, not the primary one.
- same-set proximity-aware reranking (E010, KEEP): scores each candidate by
  the summed length of the longest contiguous n-gram (n in [2, 4]) of each
  admitted evidence unit occurring in the candidate's own normalized,
  space-padded token stream, and sorts on
  `(proximity DESC, coverage DESC, incoming order stable)`. Backed by
  `_product_stream()` with a per-Agent-instance memoization cache following
  the M6 pattern (catalog-static, never cleared by `reset()`). At E010 this
  reordered exactly the returned top-10 and could therefore move MRR only.
  **Since E011 it reranks the full pool before truncation (100-deep since
  E012), so it can and does move HitRate@10 and MTTC as well.** The rule
  itself — `N_MAX = 4`, the proximity formula, the sort key — is
  byte-identical to E010.
- deep-pool candidate generation with post-rerank truncation (E011, KEEP;
  depth doubled at E012, KEEP): both retrieval paths fill an internal
  `POOL_DEPTH = 100` pool (70 category-scoped + 30 global insurance,
  backfilled from the global list when the primary route under-fills; the
  unscoped `detected is None` path likewise retrieves 100), the E010 reranker
  orders the whole pool, and the cut to the contract `top_k = 10` happens
  **after** the rerank. The contract `top_k` is untouched — the depth is
  internal. Consequence: the reranker now chooses all ten returned ids from
  the merged pool, so the global-insurance guarantee is a property of pool
  composition rather than of the output (declared at E011; unchanged in kind
  at E012, just deeper).
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

Algorithm capability at M6 was E006. The M6 cache does not constitute E007.
(E010 and then E011 have since been KEPT; the current best is **E011** — see
"E011 Outcome" above. The M6 findings below are unaffected and are not
reverted, and the `_product_terms()` cache still runs underneath E011.)

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
REVERTED (see "E007 Outcome" above), which left E006 as the best algorithm
at that point, and `starter/agent.py` was restored to the pre-E007
(E006 + M6) code. E008 was likewise evaluated and REVERTED, its change
discarded without being committed. E010 was then evaluated and **KEPT**, so
`starter/agent.py` now carries E010 on top of E006 + M6 (see "E010 Outcome"
above). No restoration step is outstanding. M7 — Submission remains
deferred.

# Known Baseline Weaknesses

- intent override still lacks semantic conflicting-evidence supersession —
  append-only evidence can retain stale/conflicting intent; an erase-all
  reset was tested at E005 and REVERTED for regressing intent_override, so
  this limitation is unresolved. E006's own intent_override MRR/MTTC
  regressed slightly vs E004, consistent with this being unaddressed. After
  E011 intent_override remained the weakest bucket (HitRate@10 0.867 against
  0.925–1.000 elsewhere); after E012 it rose to 0.9, though this was not
  separately attributed to any override-specific logic (none was added)
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
  scaffold word without matching the actual disclosed value (E004). E010
  demotes coverage to a tiebreak, which reduces but does not remove this
- **paraphrase sensitivity is unmeasured — a real-world/product limitation,
  no longer a scoring risk**: ranking on contiguous n-grams is a priori more
  brittle to rewording than the bag-of-words rule it replaced. The official FAQ
  §1 retires this as a *scoring* risk by guaranteeing that the final 800 samples
  introduce no undisclosed natural-language paraphrases, and D012 was cancelled
  unrun on that basis. Note precisely what was retired: the question "will the
  private set reword?" (answered: no), **not** the question "is the mechanism
  robust to rewording?" (still unmeasured, and would matter immediately against
  real users). Keep this for the final report's Limitations section — the tooling
  to measure it exists and is frozen (`tools/diagnostics/_paraphrase.py`)
- E010's proximity score is unnormalized by candidate text length, so a
  verbose product has more surface in which to contain a phrase; no length
  penalty was tested. **E011/E012 make this matter more**, since the rule now
  arbitrates 100 candidates instead of 10
- **deepening the pool costs MRR, but the cost is sublinear in depth (E011 →
  E012 correction)**: 10 → 50 (E011) gained +0.095 HitRate@10 and −0.730 MTTC
  but lost −0.027687 MRR, entirely through 26 retained hits losing rank (11 of
  them from rank 1, 5 falling to rank 8). E011's record extrapolated this
  roughly linearly ("bounds how far the depth direction can be pushed"). E012
  (50 → 100) tested that extrapolation directly and refuted it: MRR cost was
  only −0.001942, 7.0% of the 10→50 per-step rate, while HitRate@10 gained a
  further +0.035 and MTTC fell further. Zero hits have ever been lost across
  either step. The cost is priced into TechnicalScore and is not zero, but it
  does not scale the way E011 alone suggested
- **the remaining headroom at pool 50 was ordering, not recall (E011); pool
  100 pushes recall further before hitting the same wall**: at pool 50,
  HitRate@10 0.930 was 99.5% of D-2's pool-50 recall bound (0.935), and 87.4%
  of the TechnicalScore gap to that oracle was the MRR term. E012's HitRate@10
  0.965 shows recall was not in fact exhausted at 50 — deeper pools can still
  move it, at a shrinking MRR cost. Whether ordering is now the binding
  constraint at pool 100 has not been separately measured
- E012 costs ~1.57x evaluator wall clock versus E011 (282.9s → 444.30s; ~6.05x
  versus E006 + M6's 73.4s), reported and not optimized — the preregistration
  forbade bundling a performance experiment. No per-response timeout applies
  in the final evaluation (FAQ §3)
- `POOL_DEPTH = 100` was one preregistered human-chosen value (following
  `POOL_DEPTH = 50` at E011); no depth beyond 100 was run officially. An
  offline (non-official) 50→200 sweep showed marginal TS gain flattening past
  100, which motivated stopping there, but that sweep is not evidence for a
  KEEP/REVERT decision on its own. The 70/30 pool composition was held from
  E001 rather than tested at this depth
- E010 costs ~1.39x evaluator wall clock (73.4s → 101.4s), reported and not
  optimized — the preregistration forbade bundling a performance experiment
- `N_MAX = 4` was preregistered and frozen; no other value has been run
  against the official evaluator, so it is not known to be optimal
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

> **Superseded 2026-08-31.** The milestone is now M7 — Submission /
> Deliverables; see the top of this file. The text below is retained as the
> record of the position at the end of E011.

E011 — Candidate Pool Expansion under a Proximity Reranker is complete and
KEPT (see "E011 Outcome" above and EXPERIMENTS.md for the full record). It is
the current best system, TechnicalScore 0.796939. `starter/agent.py` carries
the change; the preregistration was committed in `2fd8ff0` before
implementation. Per-session outcomes are tracked as
`docs/diagnostics/E011_SESSIONS.json`. No task is in flight.

E011's preregistration declared it the last capability experiment and a KEEP
would freeze the algorithm there. The human has decided not to execute that
freeze — see "Human Decision — Preregistered E011 Freeze Not Executed
(2026-08-31)" above. Algorithm development remains open; any further capability
experiment needs separate human authorization and its own preregistration.

The prior task notes below are retained as historical record.

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
record. E006 completes M5 capability development. It still runs underneath the
current best system, which is **E011** (see "Current Best System"/"Current Best
Metrics" above); E006 has not been the current best since E010.

# Next Milestone

> **Superseded 2026-08-31.** M7 — Submission is no longer deferred; it is the
> current milestone. See the top of this file. The text below is retained as
> the chronological record.

**Current position (read this first; the rest of this section is a
chronological record and its older present-tense statements are superseded):
E011 — Candidate Pool Expansion under a Proximity Reranker is KEPT and is the
current best system (TechnicalScore **0.796939**). `starter/agent.py` carries
E011 on top of E010 + E006 + M6. Next milestone is M7 — Submission, still
deferred pending the human's direction. D012 (paraphrase stress) was
preregistered, built, and CANCELLED unrun after the official FAQ §1 retired the
risk it measured; it has no result and none may be cited. E011's own
preregistration declared it the last capability experiment, freezing the
algorithm on KEEP; the human decided on 2026-08-31 **not** to execute that
freeze (see "Human Decision — Preregistered E011 Freeze Not Executed
(2026-08-31)" above). Algorithm development is not frozen; further post-v1.1
experiments still require explicit human approval and separate
preregistration.**

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
was preregistered, implemented, evaluated once, and REVERTED by human
decision on 2026-08-31 (see "E008 Outcome (2026-08-31)" above and
EXPERIMENTS.md for the full record); current best remains E006 + M6
memoization, and `starter/agent.py` is at that code (the E008 change was
discarded without being committed — verified during R009, see "E008
Outcome" above). No restoration step is outstanding. M7 remains deferred
pending the human's direction. Algorithm development is not to be marked
frozen again unless the human makes that decision, and further post-v1.1
experiments still require explicit human approval.

R009 — Diagnostic / Research Infrastructure (2026-08-31) has since been
completed: `tools/diagnostics/` (D-1 candidate oracle, D-2 perfect-reranker
bounds, D-3 counterfactual bench, D-5 paired session delta, invariant
checker) and `docs/diagnostics/E006_M6_BASELINE.md`. R009 changed no
runtime code and reproduced the E006 + M6 baseline exactly. See
EXPERIMENTS.md "R009".

A third post-v1.1 experiment, E010 — Proximity-aware Reranking, was
preregistered (committed in `5035018` before any runtime change),
implemented, evaluated once, and **KEPT** by human decision on 2026-08-31
(see "E010 Outcome (2026-08-31)" above and EXPERIMENTS.md for the full
record). TechnicalScore 0.703974 → 0.743145 (+0.039171), entirely through
MRR (+0.130570); HitRate@10, MTTC, and Efficiency are unchanged by
construction. `starter/agent.py` now carries E010; E007 and E008 remain
REVERTED. R009's diagnostic tooling made this the first experiment gated by
an invariant check and a D-5 paired transition matrix before the KEEP call,
and the frozen-trajectory replay predicted the official result bit-exactly.

A fourth post-v1.1 experiment, E011 — Candidate Pool Expansion under a
Proximity Reranker, was preregistered (committed in `2fd8ff0` before any
runtime change), implemented, evaluated once, and **KEPT** by human decision on
2026-08-31 (see "E011 Outcome (2026-08-31)" above and EXPERIMENTS.md for the
full record). TechnicalScore 0.743145 → **0.796939** (+0.053794), through
HitRate@10 (+0.095000) and MTTC (−0.730) against an MRR cost (−0.027687);
hit→miss was zero. `starter/agent.py` now carries E011 on top of E010; E007 and
E008 remain REVERTED. This was the first experiment since E001 to move
HitRate@10 at all, and it confirms that E007's pool-expansion failure was
ranker-limited rather than depth-limited. Two preregistration deviations are
recorded in EXPERIMENTS.md rather than absorbed (the dropped D-3 prescreen and
the rescaled global fetch depth, the latter measured to change nothing).

# Open Questions


1. ~~**Does E010's gain survive paraphrase?**~~ **RETIRED BY OFFICIAL FAQ §1**
   (`docs/final_evaluation_faq.md`, upstream `9c9e7c9`, 2026-08-31): the final
   800 samples use the same deterministic customer-message templates as the
   published evaluator, and "No undisclosed natural-language paraphrases are
   introduced." D012 was preregistered, built, and cancelled without ever being
   run to a result; there is no D012 number and none may be cited.
   **The block this question placed on further ranking work is lifted** — its
   "should be answered before any further ranking work" no longer applies.
   Two limits on that release, both binding:
   - It unblocks the **pool-depth direction only** (question 3 below, E011).
     It is not a general licence to resume ranking changes.
   - **`N_MAX` stays frozen. Question 2 does NOT unfreeze.** The FAQ said
     nothing about n-gram length, and E010's `N_MAX = 4` was preregistered
     before results were seen. Changing it now would be tuning a parameter
     after seeing its result, on the public set — exactly the hill-climbing
     `CLAUDE.md` and the D-3 discipline forbid. Any `N_MAX` change still needs
     a separately authorized preregistration.
   What survives is a non-scoring limitation: whether the *mechanism* is robust
   to rewording is still unmeasured and belongs in the final report's
   Limitations, not in the scoring risk register (see "Known Baseline
   Weaknesses").
2. Is `N_MAX = 4` the right length? Preregistered and frozen for E010; no
   other value has been run officially. R009's counterfactual suggested n=3
   captures ~84% of n=8, but that is fixed-trajectory diagnostic evidence.
   Any sweep needs a new authorized preregistration and must not become
   public-set hill-climbing.
3. ~~**Is candidate pool depth now worth revisiting?**~~ **ANSWERED BY E011
   (2026-08-31): yes, at 10 → 50.** E011 expanded the internal pool to 50 under
   the E010 proximity ranker with truncation after reranking, and was KEPT at
   TechnicalScore 0.743145 → 0.796939 (+0.053794): HitRate@10 +0.095000,
   MTTC −0.730, MRR −0.027687, hit→miss 0. E007's failure was ranker-limited,
   not depth-limited. What the answer does **not** cover: whether a depth beyond
   50 pays (untested; D-2 prices a pool-100 oracle at 0.9609 vs 0.9032 at
   pool 50, but E011's observed direction is that deepening *costs* MRR, so the
   ceiling would not be redeemed proportionally), and whether 70/30 is the right
   composition at this depth (held from E001, never tested). Any further depth or
   composition change needs separate authorization and its own preregistration —
   E011's own preregistration forbade a second depth, and while the human has
   declined to execute E011's freeze, that is not itself an authorization.
4. Intent override still has no supersession. It held E010's only regression
   (`public_0080`), and the erase-all variant was rejected at E005. The
   architecture's supersede-only-conflicting default remains unimplemented and
   untested. After E011 it is the weakest scenario bucket (HitRate@10 0.867
   against 0.925–1.000 elsewhere), and it gained the least from pool expansion
   (+0.0667 HitRate@10 versus browsing's +0.1250) — consistent with stale
   pre-override evidence limiting what a deeper pool can recover.
5. No run-to-run variance estimate exists (D-6 planned), so small deltas
   such as E004's +0.0058 and E006's +0.0112 have never been separated from
   noise. E010's +0.0392 and E011's +0.0538 are large enough that this does not
   affect either KEEP, but it still bounds how finely future results can be
   read.
6. Private-set generalization remains unknown.
7. **The remaining headroom is now ordering, and no untested ordering idea is
   queued.** At pool 50, 87.4% of the TechnicalScore gap to the perfect-reranker
   oracle is the MRR term, 10.3% MTTC, 2.4% HitRate@10 — recall is effectively
   exhausted at this depth. E011 also showed the two directions trade against
   each other: the deeper pool bought HitRate@10 by giving back 21.2% of E010's
   MRR gain. Any future ranking work would have to beat proximity-with-coverage-
   tiebreak on a 50-deep pool, and R009's diagnostic finding still stands that
   every bag-of-words re-weighting tested lands within ±0.02. This is a
   statement of where the remaining opportunity sits, not a plan or an
   authorization.
