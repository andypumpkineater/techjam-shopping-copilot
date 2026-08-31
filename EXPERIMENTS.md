# Experiment Policy
Every meaningful algorithmic change gets an experiment ID.
Prefer one hypothesis per experiment.
Record negative results too.
Do not silently delete failed experiments.

## E000 — Official Weak BM25 Baseline
Files Changed:
None.

Decision:
REFERENCE BASELINE

Status: BASELINE

Hypothesis:
None. This establishes the untouched official reference point.

Implementation:
Official `starter/agent.py` unchanged.

Evaluation:
`python -m evaluator.local_evaluator`

Overall Metrics:
- HitRate@10: 0.125
- MRR: 0.068034
- MTTC: 9.81
- Efficiency: 0.119
- TechnicalScore: 0.10671

Scenario Metrics:
- buying: HitRate@10 0.2375, MRR 0.126508, MTTC 8.625
- browsing: HitRate@10 0.025, MRR 0.004514, MTTC 10.75
- intent_override: HitRate@10 0.133333, MRR 0.104167, MTTC 10.066667
- boundary: HitRate@10 0.0, MRR 0.0, MTTC 11.0

Observations:
- Buying performs much better than Browsing.
- Browsing is nearly non-functional.
- Boundary has zero hits.
- Baseline does not use clarification, conversation history, user profile, or reranking.

## E001 — Category-aware lexical retrieval

Status: KEEP

Hypothesis:
Using category evidence from the runtime user message as a strong lexical
retrieval signal, while retaining graceful catalog-derived relaxation and
a small global lexical insurance route, improves retrieval performance
over the official unscoped BM25 baseline.

Files Changed:
- starter/agent.py

Evaluation Command:
python -m evaluator.local_evaluator

E000:
HitRate@10: 0.125
MRR: 0.068034
MTTC: 9.81
Efficiency: 0.119
TechnicalScore: 0.106710

E001:
HitRate@10: 0.160
MRR: 0.066704
MTTC: 9.46
Efficiency: 0.154
TechnicalScore: 0.130811

Delta:
HitRate@10: +0.035
MRR: -0.001330
MTTC: -0.35 (earlier first hits)
Efficiency: +0.035
TechnicalScore: +0.024101

Scenario results:

buying:
HR@10 0.275
MRR 0.136577
MTTC 8.25

browsing:
HR@10 0.075
MRR 0.012996
MTTC 10.25

intent_override:
HR@10 0.133333
MRR 0.045833
MTTC 10.066667

boundary:
HR@10 0.0
MRR 0.0
MTTC 11.0

Decision rationale:
KEEP because E001 materially improved TechnicalScore, HitRate@10, and
first-hit timing while remaining within the retrieval-only experiment
scope.

Known regression:
Overall MRR decreased slightly, and intent_override MRR decreased
materially while its HitRate remained flat. Do not tune E001 to repair
this. Carry the regression forward as a ranking / conversational-state
problem for later milestones.

Correctness fix:
After the first evaluator run, the reserved-slot merge was fixed so that
if the primary route under-fills, the global BM25 route backfills to
top_k. The official evaluator was rerun on the final code and all overall
and scenario metrics were identical. The fix did not change evaluated
metrics.

Next:
E002 — Clarification Channel.

## E002 — Clarification Channel

Status: KEEP

Hypothesis:
Opening a legitimate clarification channel with a simple deterministic,
label-free attribute-question policy allows later customer replies to
contain useful runtime information, improving retrieval over E001 even
before multi-turn evidence accumulation is implemented.

Experimental change:
Only `ask_attribute` behavior changed.

Fixed pre-registered sequence:

Turn 1: material
Turn 2: color
Turn 3: size
Turn 4: style
Turn 5: budget
Turn 6: feature
Turn 7: use_case
Turn 8: other
Turn 9: None
Turn 10: None

The policy was frozen before evaluation and was not tuned after seeing
public metrics.

No evidence accumulation, conversation history, adaptive question policy,
reranking, intent-override logic, or boundary-specific logic was added.

Files Changed:
- starter/agent.py

Evaluation Command:
python -m evaluator.local_evaluator

E001 baseline:
HitRate@10: 0.160
MRR: 0.066704
MTTC: 9.46
Efficiency: 0.154
TechnicalScore: 0.130811

E002:
HitRate@10: 0.555
MRR: 0.244496
MTTC: 7.16
Efficiency: 0.384
TechnicalScore: 0.427649

Delta vs E001:
HitRate@10: +0.395
MRR: +0.177792
MTTC: -2.30 (better / earlier first hits)
Efficiency: +0.230
TechnicalScore: +0.296838

Scenario metrics:

buying:
HR@10: 0.5375
MRR: 0.267133
MTTC: 6.475

browsing:
HR@10: 0.575
MRR: 0.233552
MTTC: 7.0375

intent_override:
HR@10: 0.466667
MRR: 0.238333
MTTC: 8.866667

boundary:
HR@10: 0.8
MRR: 0.169444
MTTC: 8.5

Decision:
KEEP.

Interpretation:
The experiment strongly supports opening the clarification channel.
It does NOT establish that this particular attribute ordering is optimal.

The large gain should be interpreted in light of the published simulator
mechanics: legitimate clarification replies can contain highly
product-specific lexical evidence, making them much more useful to the
existing BM25 retrieval than E001's information-free reply.

The agent itself does not access ground truth or hidden intent-card fields;
it receives disclosed text only through the legitimate runtime
`user_message` channel.

Important limitations:
- Retrieval still uses only the current turn's message.
- Prior disclosed evidence is forgotten.
- Earlier category evidence can therefore disappear on later turns.
- E002 contains no intent-override semantics.
- E002 contains no boundary-specific reasoning.
- The strong public boundary result must NOT be described as solving
  boundary behavior; it is an observed evaluator result under the
  published simulator mechanics.

Next hypothesis:
E003 will test whether accumulating legitimate runtime evidence across
turns improves further over E002.

## E003 — Meaningful Multi-turn Evidence Accumulation

Status: KEEP

Hypothesis:
Persisting meaningful legitimate runtime evidence across turns, while
deterministically excluding published information-free reply templates,
improves retrieval over E002's current-message-only behavior.

Experimental change:

E003 introduced minimal per-session append-only runtime evidence state.

Admission policy:
- Turn 1 is always retained.
- Later user messages are retained unless they begin with one of the three
  published information-free/no-preference prefixes.
- Admitted messages are stored raw and append-only.
- No override/conflict resolution is performed.

Accumulated query:
- admitted messages are joined oldest to newest;
- the existing E001/E002 `_terms()` logic is applied;
- existing lexical deduplication is unchanged;
- existing 40-term cap is unchanged.

Important:
E003 tests meaningful evidence accumulation with deterministic exclusion of
published information-free replies.

Do NOT describe E003 as raw conversation-history concatenation alone.

Frozen behavior:
- E001 retrieval otherwise unchanged.
- E002 fixed clarification sequence unchanged.
- no reranking.
- no adaptive clarification.
- no intent-override semantics.
- no boundary-specific behavior.
- no recency weighting.
- no query-term-cap changes.

Files Changed:
- starter/agent.py

E002 baseline:

HitRate@10: 0.555
MRR: 0.244496
MTTC: 7.16
Efficiency: 0.384
TechnicalScore: 0.427649

E003:

HitRate@10: 0.835
MRR: 0.498681
MTTC: 5.01
Efficiency: 0.599
TechnicalScore: 0.686904

Delta vs E002:

HitRate@10: +0.280
MRR: +0.254185
MTTC: -2.15 (better / earlier first hits)
Efficiency: +0.215
TechnicalScore: +0.259255

Scenario metrics:

buying:
HR@10: 0.8625
MRR: 0.485913
MTTC: 4.3375

browsing:
HR@10: 0.825
MRR: 0.456205
MTTC: 5.3125

intent_override:
HR@10: 0.8
MRR: 0.630278
MTTC: 5.2

boundary:
HR@10: 0.8
MRR: 0.545833
MTTC: 7.4

Decision:
KEEP.

Interpretation:

The experiment strongly supports preserving meaningful runtime evidence
across turns rather than retrieving from each clarification reply in
isolation.

All overall metrics improved materially.

The intent_override bucket also improved substantially in this public run,
despite append-only stale/conflicting evidence being structurally possible.

Do NOT conclude that override handling is unnecessary.

The correct conclusion is only that, on this evaluation, the benefit of
preserving multi-turn evidence outweighed the harm from unresolved stale
or conflicting evidence.

Known limitations:

1. Append-only stale/conflicting evidence.
   An intent override can leave both old and new intent terms in the query.

2. No evidence supersession or conflict resolution.

3. Oldest-first 40-term cap.
   Later evidence may be truncated once 40 unique lexical terms are reached.

Do NOT infer from MTTC that the term cap was rarely reached.
This evaluation does not establish how often truncation affected queries.

4. The information-free filter is based on published fixed reply prefixes,
   not semantic no-preference understanding.

No public-target-specific tuning, ground-truth access, scenario-specific
logic, or hidden-field access was used by the agent.

## E004 — Coverage-aware Lightweight Reranking

Status: KEEP

Milestone:
M4 — Ranking

Hypothesis:
Among the exact candidates already returned by E003, candidates covering
more distinct accumulated evidence units should rank above candidates that
match fewer evidence units, improving MRR without changing candidate
membership.

Experimental change:

E004 introduced a pure same-set reranking pass over the final E003
recommendation ids.

One admitted E003 message = one evidence unit.

Evidence terms:
- existing `_terms(message)`
- empty units ignored

Candidate product terms:
existing `_terms()` over the concatenation of:
- title
- categories
- features
- details
- store
- description

Coverage:

coverage(P) =
number of evidence units whose term set has a non-empty intersection with
P's product-term set.

Each evidence unit receives binary covered/not-covered credit.

Ranking:
1. coverage descending
2. original E003 order preserved for ties via stable sorting

No:
- IDF
- field weights
- BM25 blending
- overlap thresholds
- semantic parsing
- candidate-pool expansion
- candidate replacement
- caching

Candidate membership was intentionally frozen.

Frozen behavior:
- E001 retrieval unchanged
- E002 clarification sequence unchanged
- E003 evidence admission and accumulation unchanged
- no override semantics
- no boundary-specific logic
- no adaptive clarification

Files Changed:
- starter/agent.py

E003 baseline:

HitRate@10: 0.835
MRR: 0.498681
MTTC: 5.01
Efficiency: 0.599
TechnicalScore: 0.686904

E004:

HitRate@10: 0.835
MRR: 0.518149
MTTC: 5.01
Efficiency: 0.599
TechnicalScore: 0.692745

Delta vs E003:

HitRate@10: +0.000000
MRR: +0.019468
MTTC: +0.00
Efficiency: +0.000
TechnicalScore: +0.005841

Scenario metrics:

buying:
HR@10: 0.8625
MRR: 0.494782
MTTC: 4.3375

browsing:
HR@10: 0.825
MRR: 0.474727
MTTC: 5.3125

intent_override:
HR@10: 0.8
MRR: 0.677302
MTTC: 5.2

boundary:
HR@10: 0.8
MRR: 0.575
MTTC: 7.4

Decision:
KEEP.

Mechanism interpretation:

HitRate@10, MTTC, and Efficiency remained exactly unchanged while MRR
improved.

This is consistent with E004 behaving as the intended same-set reranker:
candidate membership stayed fixed while ordering improved.

The TechnicalScore increase is attributable to the MRR increase:
0.3 * 0.019468 ~= 0.0058404, consistent with the observed +0.005841.

Do NOT claim coverage-aware ranking in general is optimal.

This experiment validates only the specific plain, unweighted,
binary-per-evidence-unit lexical coverage rule tested here.

Known limitations:

1. Generic-token false coverage.
   A candidate may receive credit through an attribute/scaffold word without
   matching the actual disclosed value.

2. Long-text overcoverage.
   Verbose product text has more opportunities for lexical intersection.

3. Scaffold-token contamination.
   Useful disclosure messages still contain conversational scaffolding that
   may contribute spurious lexical overlap.

4. Common / one-token evidence units may provide nearly constant coverage
   across candidates.

5. No IDF, field weighting, semantic constraint parsing, or value-specific
   matching.

6. Performance:
   `_product_terms()` currently performs uncached per-candidate SQL lookup
   and tokenization. The official evaluator completed successfully, but the
   run exceeded Claude Code's 120-second foreground Bash window and continued
   in the background.

Treat this as an engineering/performance limitation, not a ranking
correctness failure.

Smoke-test note:
Two issues discovered during validation were bugs in the temporary test
harness/fixtures, not in starter/agent.py. They were corrected before the
official evaluator run; final smoke tests all passed.

## E005 — Explicit Intent Override Reset

Status: REVERT

Milestone:
M5 — Conversation Intelligence

Hypothesis:
When the runtime user explicitly replaces their prior intent, discarding
pre-override accumulated evidence before retrieval may improve performance
over E004's append-only evidence state.

Tested policy:

Override detector:

`ignore\s+(?:my|our)\s+(?:earlier|previous|prior)\s+preferences?`

case-insensitive, operating only on runtime `user_message`.

On detection:

- erase all pre-override session evidence;
- append the current override message as the new evidence root;
- build the same turn's query from the reset evidence state;
- resume normal E003 accumulation afterwards.

No scenario labels, ground truth, target ids, hidden fields, or adaptive
logic were used.

Frozen:
- E001 retrieval
- E002 clarification sequence
- E003 normal evidence admission/accumulation
- E004 coverage reranking

Files Changed:
- starter/agent.py

Evaluation Command:
python -m evaluator.local_evaluator

E004 baseline:

HitRate@10: 0.835
MRR: 0.518149
MTTC: 5.01
Efficiency: 0.599
TechnicalScore: 0.692745

E005 result:

HitRate@10: 0.795
MRR: 0.455204
MTTC: 5.5
Efficiency: 0.55
TechnicalScore: 0.644061

Delta vs E004:

HitRate@10: -0.040000
MRR: -0.062945
MTTC: +0.49 (worse / later first hits)
Efficiency: -0.049000
TechnicalScore: -0.048684

Scenario metrics:

buying:
HR@10: 0.8625
MRR: 0.494782
MTTC: 4.3375

browsing:
HR@10: 0.825
MRR: 0.474727
MTTC: 5.3125

intent_override:
HR@10: 0.533333
MRR: 0.257672
MTTC: 8.466667

boundary:
HR@10: 0.8
MRR: 0.575
MTTC: 7.4

Mechanism check:

buying, browsing, and boundary remained bit-identical to E004.

Only intent_override changed materially, and it regressed:

E004 intent_override:
HR@10: 0.8
MRR: 0.677302
MTTC: 5.2

E005 intent_override:
HR@10: 0.533333
MRR: 0.257672
MTTC: 8.466667

Decision:
REVERT.

Interpretation:

The experiment rejects the tested ERASE-ALL override policy.

Do NOT interpret this as evidence that intent-override semantics are
unnecessary.

The supported conclusion is narrower:

removing all pre-override evidence destroys useful accumulated retrieval /
ranking signal strongly enough to outweigh any benefit from eliminating
stale conflicting evidence.

A future override-aware system would need finer-grained treatment such as
preserving useful non-conflicting evidence while superseding conflicting
evidence.

That more semantic policy was NOT tested here.

Do not claim it would necessarily improve performance.

Next:
E006 — Adaptive attribute selection (per Architecture v1.1 roadmap; current
best system remains E004).

## E006 — Adaptive Catalog-Side Clarification

Status: KEEP

Milestone:
M5 — Conversation Intelligence

Baseline:
E004 — Coverage-aware Lightweight Reranking

Hypothesis:

Choosing the next specific clarification attribute adaptively from
catalog-side differentiation in the current E004 candidate set can acquire
useful constraints earlier than E002's fixed specific-attribute order.

Tested policy:

Adaptive-scored attributes:

- material
- color
- style
- feature
- use_case

Not adaptively scored:

- size
- budget

Never scored:

- category
- brand

For each adaptive attribute and current final E004 candidate:

value(attribute, product) =
product terms intersect frozen attribute vocabulary

An attribute is adaptively eligible only when:

usable_count >= 2
and
distinct_count >= 2

Ranking score:

(distinct_count, usable_count)

Tie order:

material
color
style
feature
use_case

If no adaptive attribute is eligible:

fall back to the first not-yet-asked specific attribute from the original
E002 order:

material
color
size
style
budget
feature
use_case

Only after all seven specific attributes are exhausted:

ask `other` once.

Then:
ask_attribute = None.

Per-session asked-attribute state controls clarification only.

No retrieval, evidence, reranking, override, boundary-specific, LLM,
embedding, or price-index behavior was added.

The adaptive vocabulary was preregistered/frozen before evaluation and was
not tuned afterward.

Files Changed:
- starter/agent.py

Evaluation Command:
python -m evaluator.local_evaluator

E004 baseline:

HitRate@10:       0.835
MRR:              0.518149
MTTC:             5.01
Efficiency:       0.599
TechnicalScore:   0.692745

E006 result:

HitRate@10:       0.835
MRR:              0.522579
MTTC:             4.515
Efficiency:       0.6485
TechnicalScore:   0.703974

Delta vs E004:

HitRate@10:       +0.000000
MRR:              +0.004430
MTTC:              -0.495
Efficiency:       +0.0495
TechnicalScore:   +0.011229

Scenario results:

buying:
HR@10: 0.8625
MRR: 0.502108
MTTC: 3.900

browsing:
HR@10: 0.825
MRR: 0.479415
MTTC: 4.675

intent_override:
HR@10: 0.8
MRR: 0.658135
MTTC: 5.333333

boundary:
HR@10: 0.8
MRR: 0.625
MTTC: 5.700

Scenario deltas vs E004:

buying:
HR@10: +0.000
MRR: +0.007326
MTTC: -0.4375

browsing:
HR@10: +0.000
MRR: +0.004688
MTTC: -0.6375

intent_override:
HR@10: +0.000
MRR: -0.019167
MTTC: +0.133333

boundary:
HR@10: +0.000
MRR: +0.050000
MTTC: -1.700

Decision:
KEEP.

Interpretation:

E006 left aggregate and per-scenario HitRate@10 unchanged while improving
overall MRR, MTTC, Efficiency, and TechnicalScore.

This is consistent with the intended mechanism:
adaptive question selection did not add retrieval coverage, but changed
the conversation trajectory so useful constraints were often acquired
earlier.

The largest MTTC improvement occurred in boundary, followed by browsing
and buying.

Intent_override regressed slightly in MRR and MTTC. Override semantics
therefore remain a known limitation; E005's failed erase-all policy remains
reverted.

Do not claim adaptive clarification is optimal or semantic.

Important latency correction:

E006's selector creates a LOCAL per-call dictionary so each current
candidate's `_product_terms()` is computed only once for all five adaptive
attributes.

However, this is still an ADDITIONAL `_product_terms()` lookup per candidate
after E004's `_coverage_rerank()` has already performed its own lookup.

Therefore E006 does add approximately one additional product-term SQL /
tokenization operation per candidate per turn.

The local reuse prevents roughly five repeated attribute-specific lookups
per candidate, but does not eliminate the additional E006 lookup entirely.

This is a known performance limitation for M6. It was not optimized as part
of this experiment.

Next:
M6 — Ablation / Robustness. No E007 algorithm experiment was planned at
this point; algorithm capability development froze after E006 per the
human decision recorded in PROJECT_STATE.md. (That freeze was later
explicitly lifted by a new human decision on 2026-08-31 for one
preregistered post-v1.1 experiment — see "E007 — Candidate Pool Expansion
before Coverage Reranking (PREREGISTERED)" below and PROJECT_STATE.md
"Human Decision — Freeze Lifted (2026-08-31)".)

## M6 — Robustness, Reproducibility, and Performance

This is NOT E007. M6 added no new algorithm capability: no retrieval,
ranking, clarification, evidence, or override change was made. Current best
algorithm remains E006.

### Frozen algorithm baseline

E006 — Adaptive Catalog-Side Clarification

Canonical metrics:

HitRate@10:       0.835
MRR:              0.522579
MTTC:             4.515
Efficiency:       0.6485
TechnicalScore:   0.703974

Scenarios:

buying:
HR@10 0.8625
MRR 0.502108
MTTC 3.900

browsing:
HR@10 0.825
MRR 0.479415
MTTC 4.675

intent_override:
HR@10 0.8
MRR 0.658135
MTTC 5.333333

boundary:
HR@10 0.8
MRR 0.625
MTTC 5.700

### Robustness verification

PASS for:

- deterministic outputs across fresh Agent instances;
- interleaved session isolation;
- reset isolation;
- recommendation validity and uniqueness;
- clarification exhaustion;
- 10-turn stability;
- no observed exception in tested/evaluator paths.

Known edge case:

An empty or punctuation-only initial user message yields zero
recommendations because no lexical expression is produced.

This remains unfixed.

Classified as a defensive robustness gap relative to the architecture's
"Always ten" invariant, not an observed official-evaluator blocker.

Also recorded:

The architecture's internal Guard/degradation component is not fully
implemented. The official evaluator provides its own exception boundary.
No exception occurred in M6 tests or the canonical evaluator.

No M6 capability change was made to address either issue.

### Determinism caveat

Empirical determinism passed in the current environment.

Some SQLite ordering paths do not contain explicit deterministic
secondary tie-breakers, so cross-SQLite-version ordering is not formally
guaranteed for exact ties.

No ordering semantics were changed in M6.

### Reproducibility environment

- Python 3.11.15
- SQLite 3.53.4
- catalog: 50,000 rows
- unique parent_asin: 50,000
- evaluator command:
  `python3 -m evaluator.local_evaluator`

Catalog prerequisite:

`data/catalog.jsonl` is not committed and must be obtained from the
official release according to data/README.md.

Checksum wording:

"The organizer checksum verified the downloaded compressed
`catalog.jsonl.gz`. The current decompressed `data/catalog.jsonl` has a
different expected hash because it is a different byte representation."

No new cryptographic verification of the decompressed JSONL is claimed.

Values, labeled by which file each belongs to:

Organizer compressed artifact SHA-256 (catalog.jsonl.gz):
07fd142631fd6b03e2b4d09988c3eb7d53720e9d57010c79db48eeaada50a8f8

Current local decompressed JSONL SHA-256 (data/catalog.jsonl):
da979b05a68af864cb0dcf9ee6a81c010c7e66a57978ad286c7a2e005fc69a67

### Performance finding

Before optimization:

Official 200-session evaluator:
313.42s real

Identified hotspot:

`_product_terms(parent_asin)` repeatedly executes the same catalog-static
SQLite lookup and tokenization from both E004 reranking and E006
clarification selection.

### Accepted M6 optimization

Implemented ONE pure per-Agent-instance memoization cache for
`_product_terms(parent_asin)`.

Cache semantics:

- first request executes the exact original SQL/tokenization computation;
- stores the exact frozenset result;
- later calls for the same parent_asin return that result;
- cache belongs to immutable catalog/Agent lifetime;
- session reset does not clear it.

No changes to:

- SQL query
- tokenizer
- product text composition
- retrieval
- candidate membership
- BM25
- category logic
- evidence
- E004 reranking
- E006 clarification
- override handling

Files Changed:
- starter/agent.py

### Behavioral equivalence

Baseline E006 vs memoized version:

- public sessions compared: 200 / 200
- turns compared: 870
- mismatch count: 0

Compared exactly:

- message
- ask_attribute
- ordered recommendations
- usage

### Post-optimization evaluator

Official evaluator after memoization:

72.97s real
72.38s user
exit code 0

Performance:

313.42s -> 72.97s

- 240.45 seconds saved
- 76.7% wall-clock reduction
- 4.30x speedup

All overall and scenario metrics remained bit-identical to E006.

Decision:
KEEP.

Interpretation:

This is an engineering optimization only, not a new algorithm experiment
and not E007.

M6 introduced no new recommendation or conversation capability.

No further performance optimization is planned before submission.

Next (as recorded at M6 completion):
M7 — Submission. Algorithm and performance behavior were frozen; no E007
was planned.

This was the prior human decision. It was explicitly lifted by a new human
decision on 2026-08-31 for one preregistered post-v1.1 experiment. See
"E007 — Candidate Pool Expansion before Coverage Reranking" immediately
below and PROJECT_STATE.md "Human Decision — Freeze Lifted (2026-08-31)"
for the full record and discipline. E007 was implemented, evaluated once
against the official evaluator, and REVERTED by human decision — current
best remains E006 + M6 memoization. Further post-v1.1 experiments still
require explicit human approval; algorithm development is not to be marked
frozen again unless the human makes that decision.

## E007 — Candidate Pool Expansion before Coverage Reranking

Status: REVERT

Classification: post-Architecture-v1.1 experiment (see PROJECT_STATE.md
"Human Decision — Freeze Lifted (2026-08-31)"). Not part of the original
Architecture v1.1 E001-E006 roadmap.

Baseline: E006 — Adaptive Catalog-Side Clarification, plus the accepted M6
`_product_terms()` memoization.

Hypothesis: the current lexical retrieval cutoff is too shallow for the
E004 coverage-aware reranker. `starter/agent.py::respond()` truncated the
candidate list to `top_k` (10) before calling `_coverage_rerank()`, both on
the category-scoped path (`ids = ids[:top_k]` after primary/insurance
slot-filling and backfill) and the unscoped path (`_unscoped_query(...,
top_k)` retrieved exactly `top_k` directly). A relevant product ranked just
outside that Top10 lexical cutoff could never be seen, let alone promoted,
by the reranker. E007 tested whether giving the SAME frozen coverage
reranker a larger lexical candidate pool improves final Top10 retrieval/
ranking quality: retrieve a larger candidate pool with the SAME E001
retrieval routes, apply the SAME E004 coverage reranker to that larger
pool, then truncate to the contract `top_k` only after reranking.

Pre-registered policy (ONE pool size, no tuning):
- `POOL_MULTIPLIER = 2`
- official `top_k = 10`
- internal pool = 20
- category-aware capacities: primary = 14, global insurance = 6
- unscoped retrieval depth = 20
- same E004 coverage reranker (unmodified)
- truncate to final Top10 after reranking
- E006 clarification selector sees only the final Top10, never the
  internal 20-candidate pool
- no other algorithm change

Frozen (unchanged): E001 retrieval semantics (TOKEN_RE, STOPWORDS,
`_terms`, FTS fields, BM25 expression/weights, category detection/
hierarchy/relaxation, global insurance concept, dominant root behavior);
E003 evidence accumulation; E004 `_evidence_units`/`_product_terms`/
coverage formula/stable sort; E006 adaptive vocabularies/score/fallback
order/`_asked_attributes`; M6 `_product_terms` memoization semantics. No
IDF, field weighting, embeddings, dense retrieval, LLM reranking, override
handling, personalization, or new clarification logic.

Validation: 26 / 26 smoke checks passed. The mechanism worked correctly in
isolation, including a synthetic label-free rescue case where a candidate
outside the original Top10 lexical rank was promoted into the final Top10
by the unchanged coverage reranker once the pool was expanded to 20.

### E006 baseline

HitRate@10:       0.835
MRR:              0.522579
MTTC:             4.515
Efficiency:       0.6485
TechnicalScore:   0.703974

Runtime: 72.97s real

### E007 result

HitRate@10:       0.805
MRR:              0.497075
MTTC:             4.94
Efficiency:       0.606
TechnicalScore:   0.672822

Runtime: 102.17s real

Delta vs E006:

HitRate@10:       -0.030000
MRR:              -0.025504
MTTC:             +0.425  (worse)
Efficiency:       -0.0425
TechnicalScore:   -0.031152
Runtime:          +29.20s (~1.40x slower)

Scenario results:

buying:
HR@10 0.800, MRR 0.477371, MTTC 4.4375

browsing:
HR@10 0.8125, MRR 0.440491, MTTC 4.9125

intent_override:
HR@10 0.733333, MRR 0.631481, MTTC 5.966667

boundary:
HR@10 1.000, MRR 0.704167, MTTC 6.100

Scenario deltas vs E006:

buying:      HR@10 -0.0625,    MRR -0.024737, MTTC +0.5375
browsing:    HR@10 -0.0125,    MRR -0.038924, MTTC +0.2375
intent_override: HR@10 -0.066667, MRR -0.026654, MTTC +0.633334
boundary:    HR@10 +0.200,     MRR +0.079167, MTTC +0.400

Decision: REVERT.

Interpretation:

The experiment rejects the tested 2x candidate-depth policy when paired
with the current E004 binary lexical coverage reranker. Do NOT conclude
that deeper retrieval is inherently harmful. The narrower supported
conclusion is: giving the current unweighted coverage reranker a
substantially noisier 20-item lexical pool causes enough harmful
promotions/displacement to outweigh the rescue opportunities it creates.
The synthetic mechanism test proves deeper-pool rescue is possible, but the
public-set net effect is negative in three of four scenario buckets
(buying, browsing, intent_override) and on every overall metric; only
`boundary` (n=10) improved on HR@10/MRR, and even there MTTC got worse.

This result suggests candidate-depth expansion should not be revisited
unless ranking quality itself is first improved. Do not claim that any
future IDF/field-aware reranker would necessarily solve this — that is
untested. No alternate pool size was tested; none should be tested without
a new, separately-authorized preregistration.

Discipline followed: preregistered before evaluation; evaluator run exactly
once; no repeated public-set tuning of pool size; no alternate pool sizes
tested (15/30/40/50 etc.); reverted per the pre-registered fallback rule.
Further post-v1.1 experiments still require explicit human approval.

## E008 — Candidate-Local IDF-aware Reranking (PREREGISTERED)

Status: PREREGISTERED / NOT YET IMPLEMENTED

Classification: human-approved post-Architecture-v1.1 experiment (see
PROJECT_STATE.md "Human Decision — Freeze Lifted (2026-08-31)"). This does
not reopen or rewrite E007 history: E007 remains REVERTED, and E008 does
NOT retry candidate-pool expansion.

Baseline: E006 — Adaptive Catalog-Side Clarification, plus the accepted M6
`_product_terms()` memoization. Current best remains E006 + M6 memoization
until E008 is evaluated and an explicit KEEP decision is recorded.

Hypothesis: E007 showed that the current binary/unweighted E004 coverage
reranker cannot safely exploit a noisier, deeper Top20 lexical pool. The
narrower hypothesis tested here is that, with the ORIGINAL E006 candidate
membership held exactly frozen, ranking ties within that same candidate set
can be improved by preferring evidence matches that are rarer / more
discriminative among the current candidates, rather than by changing which
candidates are considered.

Candidate-set invariant (strict): E008 changes ranking order ONLY. Candidate
membership must remain EXACTLY the ids `_coverage_rerank()` receives under
E006 — no deeper pool, no extra candidate, no removed candidate. The final
recommendation set must therefore be identical to E006 for the same turn;
only the order among that fixed set may differ.

Frozen (unchanged): E001 retrieval (lexical retrieval, BM25, scoped/global
routing, 7/3 slots, relaxation, candidate depth, tokenizer, STOPWORDS,
FTS/index); E003 evidence admission/accumulation/40-term cap; E004's
definition of one evidence unit and its existing binary coverage count
(retained as the PRIMARY ranking signal); E004/E006 candidate membership;
E006 adaptive clarification vocabularies/attribute scoring/asked-attribute
state/fallback; M6 `_product_terms()` memoization. E007 remains REVERTED;
its `POOL_MULTIPLIER` and expanded candidate depth are NOT reintroduced. No
field weighting, title boosting, dense retrieval, embeddings, LLM
reranking, semantic parsing, override handling, personalization, router, or
new clarification logic is added.

Preregistered IDF policy (Python stdlib only, candidate-local, one fixed
formula, not tuned after evaluation):

For the current E006 candidate ids only (no global 50k-product IDF index,
no `_build_index()` change, no FTS vocab table):

```
N = number of current candidates
df(t) = number of current candidates whose _product_terms(candidate)
        contains term t
idf(t) = ln((N + 1) / (df(t) + 1)) + 1
```

Preregistered rarity score (per-evidence-unit, not per-term, to avoid
rewarding a verbose product for matching many words from one message):

For each evidence unit U (same E004 units) and candidate product P, with
`overlap(U, P) = U ∩ product_terms(P)`:

```
per-unit rarity contribution =
    0                              if overlap(U, P) is empty
    max(idf(t) for t in overlap)   otherwise

rarity_score(P) = sum of per-unit rarity contributions across all
                  evidence units
```

`coverage(P)` (E004's existing binary count of evidence units with
non-empty overlap) is unchanged and remains the PRIMARY ranking signal.

Preregistered sort key (strictly lexicographic, coverage dominant):

```
1. coverage(P) descending
2. rarity_score(P) descending
3. original E006 lexical/rerank input order, stable
```

A candidate with coverage 3 must always outrank a candidate with coverage
2 regardless of rarity; IDF/rarity resolves ordering only among candidates
tied on coverage. No third ranking signal and no weighted combination of
coverage and rarity are added.

Expected invariants (candidate membership is frozen, so these should hold
exactly unless isolation is broken): HitRate@10 identical to E006; MTTC
identical to E006 (first-hit membership per turn is unchanged); Efficiency
identical to E006 (derived from MTTC); `ask_attribute` trajectory identical
to E006 (`_select_attribute()` scores the final candidate SET, not rank
order, per turn). If any of these four channels changes, treat it as a
correctness/isolation warning first — do not rationalize it as an intended
E008 effect. The primary expected mechanism channel is MRR (via reordering
within tied-coverage groups), which can move TechnicalScore only through
its 0.30 * MRR term.

Performance: reuse `_product_terms()` once per candidate per rerank call
(shared across coverage, candidate-local df, and rarity computation); do
not call `_product_terms()` repeatedly per evidence term; do not add any
new persistent cache beyond the existing M6 cache. No separate performance
experiment is bundled into E008.

Evaluation rule (preregistered before evaluation, one official run only):

```
python -m evaluator.local_evaluator
```

E006 + M6 baseline to compare against:

HitRate@10:       0.835
MRR:              0.522579
MTTC:             4.515
Efficiency:       0.6485
TechnicalScore:   0.703974

buying:           HR@10 0.8625 / MRR 0.502108 / MTTC 3.900
browsing:         HR@10 0.825  / MRR 0.479415 / MTTC 4.675
intent_override:  HR@10 0.8    / MRR 0.658135 / MTTC 5.333333
boundary:         HR@10 0.8    / MRR 0.625     / MTTC 5.700

Primary E008 mechanism metric: MRR. Final KEEP/REVERT decision is made on
overall TechnicalScore. No IDF formula tuning after seeing results — no
alternate global IDF, different smoothing, weighted coverage/rarity
combination, or field weighting is to be tried inside this experiment.

Discipline: preregistered before implementation or evaluation; exactly one
official evaluator run planned; if E008 does not KEEP, revert to E006 + M6
unchanged; further post-v1.1 experiments beyond E008 still require explicit
human approval.

Next: implement per this preregistration, run the one official evaluator
pass, and record the KEEP/REVERT outcome here.
