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

## E008 — Candidate-Local IDF-aware Reranking

Status: REVERT

Classification: human-approved post-Architecture-v1.1 experiment (see
PROJECT_STATE.md "Human Decision — Freeze Lifted (2026-08-31)"). This does
not reopen or rewrite E007 history: E007 remains REVERTED, and E008 did
NOT retry candidate-pool expansion.

Baseline: E006 — Adaptive Catalog-Side Clarification, plus the accepted M6
`_product_terms()` memoization.

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

Tested IDF policy (Python stdlib only, candidate-local, one fixed
formula, not tuned after evaluation):

For the current E006 candidate ids only (no global 50k-product IDF index,
no `_build_index()` change, no FTS vocab table):

```
N = number of current candidates
df(t) = number of current candidates whose _product_terms(candidate)
        contains term t
idf(t) = ln((N + 1) / (df(t) + 1)) + 1
```

Tested rarity score (per-evidence-unit, not per-term, to avoid
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

Tested sort key (strictly lexicographic, coverage dominant):

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

No IDF formula tuning after seeing results — no alternate global IDF,
different smoothing, weighted coverage/rarity combination, or field
weighting was tried inside this experiment.

Discipline followed: preregistered before implementation; implemented per
the preregistration; exactly one official evaluator run performed; no
formula tuning after seeing results; reverted per the pre-registered
fallback rule.

Validation:

All smoke tests passed.

A direct E006-vs-E008 isolation replay over:
- 40 public sessions
- 400 turns

showed:
- 0 recommendation-set mismatches
- 0 ask_attribute mismatches
- 379 / 400 turns with changed internal recommendation order

Therefore the mechanism actively changed ranking while preserving the
intended candidate-set / dialogue invariants.

### E006 + M6 baseline

HitRate@10:       0.835
MRR:              0.522579
MTTC:             4.515
Efficiency:       0.6485
TechnicalScore:   0.703974

Runtime: 72.97s real

### E008 result

HitRate@10:       0.835
MRR:              0.424498
MTTC:             4.515
Efficiency:       0.6485
TechnicalScore:   0.674549

Runtime: 73.52s real

Delta vs E006:

HitRate@10:       +0.000000
MRR:              -0.098081
MTTC:             +0.000
Efficiency:       +0.0000
TechnicalScore:   -0.029425
Runtime:          +0.55s (no meaningful runtime impact)

Scenario results:

buying:
HR@10 0.8625
MRR 0.446567
MTTC 3.900

browsing:
HR@10 0.825
MRR 0.373428
MTTC 4.675

intent_override:
HR@10 0.8
MRR 0.457222
MTTC 5.333333

boundary:
HR@10 0.8
MRR 0.558333
MTTC 5.700

Scenario MRR deltas vs E006:

buying:          -0.055541
browsing:        -0.105987
intent_override: -0.200913
boundary:        -0.066667

All four scenario HR@10 and MTTC values are bit-identical to E006.

Decision: REVERT.

Interpretation:

The experiment rejects candidate-local lexical rarity as a secondary
tie-break for the current E006 Top10 candidate set.

The strong isolation invariants held:

- candidate membership unchanged;
- HitRate@10 unchanged;
- MTTC unchanged;
- Efficiency unchanged;
- ask_attribute trajectory unchanged.

Therefore the MRR regression is attributable to changed ranking order, not
a retrieval or dialogue-side leak.

The supported conclusion is narrow: within an already lexically retrieved
~Top10 pool, local rarity is a poor proxy for target relevance and
performs substantially worse than preserving the pre-existing lexical/BM25
order among equal-coverage candidates.

Do NOT conclude that:
- all IDF is harmful;
- global corpus IDF is harmful;
- field-aware ranking is harmful;
- semantic reranking is harmful.

Those mechanisms were not tested.

Next: current best remains E006 + M6 memoization, unchanged. Further
post-v1.1 experiments beyond E008 still require explicit human approval.

## R009 — Diagnostic / Research Infrastructure

Status: COMPLETE

Type: **R / Diagnostic Infrastructure. NOT an Agent Experiment.**

This is not an E-class experiment. It has no performance hypothesis, changes no
runtime behavior, and its expected TechnicalScore impact is exactly zero. It does
not supersede or reopen E007 or E008, both of which remain REVERTED.

### Hypothesis

None — no performance hypothesis is under test.

The objective is to move already-verified offline diagnostic capability out of an
ephemeral session scratchpad and into the repository, so that later experiments
can perform candidate-recall, ranking-upper-bound, counterfactual, paired-delta,
and invariant analysis from a reproducible, version-controlled base.

Motivation: E007 and E008 each consumed a full official-evaluator experiment slot
(preregistration, implementation, one official run, documentation) and returned a
single scalar of roughly -0.03. The same questions are answerable offline in
minutes. R009 buys that capability once.

### Runtime change

**None.**

`starter/agent.py` is untouched. Verified by code inspection, not by document:

- `git diff -- starter/agent.py` — empty
- `git diff c8cc1e2 HEAD -- starter/agent.py` — empty (identical to the M6 commit)
- SHA-256 `8615fd2164bf5dbfa46b2baf802b6a6ebeb70503aa692d0d2e1f77a145e3a67a`
- no `idf` / `rarity` / `POOL_MULTIPLIER` / `math.log` symbols present
- `_coverage_rerank()` sorts on `-coverage` alone, no secondary rarity key

No retrieval, ranking, clarification, evidence, override, BM25 weighting,
candidate-pool, slot-structure, tokenizer, or STOPWORDS change was made.

### Files added

- `tools/diagnostics/_replay.py` — shared offline session-replay core
- `tools/diagnostics/d1_candidate_oracle.py` — D-1
- `tools/diagnostics/d2_reranker_bounds.py` — D-2
- `tools/diagnostics/d3_counterfactual_bench.py` — D-3
- `tools/diagnostics/d5_paired_delta.py` — D-5
- `tools/diagnostics/invariant_check.py` — experiment invariant checker
- `tools/diagnostics/README.md` — usage and the ground-truth boundary
- `docs/diagnostics/E006_M6_BASELINE.md` / `.json` — baseline snapshot

### Ground truth boundary

The diagnostics read `ground_truth` from `data/public_set.jsonl` and re-derive
the evaluator's hidden intent cards. This is permitted only because it is offline
error analysis. `ground_truth` and anything derived from it must never reach
`starter/agent.py`, runtime query construction, runtime ranking, runtime
clarification, runtime state, or any runtime mapping.

Held in code: the Agent is driven only through `reset()` and `respond()`, with
messages produced by the published simulator. The target id is used solely to
locate the target in a result list after the agent has already answered. Two
read-only couplings to agent internals (`_sessions`, `_product_terms`) plus a
BM25-weight guard raise loudly rather than silently reporting different numbers
if the runtime changes shape. Documented in `tools/diagnostics/README.md` and in
the `_replay.py` module docstring.

### D-3 discipline

The D-3 scorer registry is deliberately CLOSED and contains only rules already
run and reported in the 2026-08-31 audit. Passing an unregistered scorer name is
an error, by design. D-3 must not be used to sweep parameters in bulk, to try
many variants and keep the public-set maximum, or to hill-climb the 200 public
sessions. A positive D-3 delta is grounds to preregister an experiment; it is
never itself evidence of improvement.

### Expected TechnicalScore impact

**Exactly zero.**

### Regression criterion and result

R009 could not be declared complete unless the official evaluator reproduced the
E006 + M6 baseline. Result: **PASS**, identical in every field.

Command: `python3 -m evaluator.local_evaluator`

HitRate@10 0.835 · MRR 0.522579 · MTTC 4.515 · Efficiency 0.6485 ·
TechnicalScore 0.703974 · runtime 73.4 s

buying HR 0.8625 / MRR 0.502108 / MTTC 3.900; browsing HR 0.825 / MRR 0.479415 /
MTTC 4.675; intent_override HR 0.8 / MRR 0.658135 / MTTC 5.333333; boundary
HR 0.8 / MRR 0.625 / MTTC 5.700.

All 200 per-session outcomes (hit, first_hit_turn, best_rank) are bit-identical
to the prior baseline run — 0 mismatches, confirmed with D-5.

### Reproduction of the audit's conclusions from the repository tools

D-1 and D-3 reproduce the 2026-08-31 audit **exactly**: Recall@10 0.805 /
Recall@20 0.875 / Recall@50 0.935 / Recall@100 0.990 / Recall@200 0.995 /
Recall@500 1.000; and every pool-100 bag-of-words scorer plus every pool-60
phrase scorer matches to six decimal places.

**One discrepancy was found, investigated, and explained — not silently
accepted.** D-2's pool-depth bounds came out 0.005–0.007 lower than the audit's
table. Root cause: the audit's pool-depth oracle table was computed **without**
the intent_override gate, while its other two tables were gated. R009 applies the
gate consistently, matching `evaluator/local_evaluator.py:234, :252, :259`. Both
values were reproduced from the same source data: the ungated path returns the
audit's numbers exactly, the gated path returns R009's exactly. Query
reconstruction, session simulation, candidate depth, and target-rank definition
are identical; the gate is the sole difference. The R009 gated values supersede
the audit's table. The qualitative conclusion is unaffected.

### Evidence classification — important

The snapshot records diagnostic evidence and runtime-experiment evidence
separately and must not be read as conflating them.

Diagnostic evidence establishes that every bag-of-words re-weighting tested
(binary coverage, per-unit term recall, global catalog IDF, full-unit
containment, two pairwise combinations) lands within roughly ±0.02 of the current
system. That signal dimension appears substantially exhausted, consistent with
both E007 and E008 failing while re-weighting it.

Diagnostic evidence does **not** establish that proximity / phrase ranking
improves the agent. **E010 remains a preregistered hypothesis that has NOT been
run.** No official evaluator run exists for any proximity rule. The `phrase_*`
figures are counterfactual measurements on a fixed dialogue trajectory; a real
implementation would change the candidate set, hence `_select_attribute`, hence
what the simulator discloses, hence every later turn. Only an E-class official
run can support a KEEP.

### Decision

KEEP (infrastructure). No runtime behavior was changed, so there is nothing to
revert.

Next: E010 — Proximity-aware Reranking, in a fresh window from this clean
checkpoint. R009 deliberately stopped short of implementing it.

## E010 — Proximity-aware Reranking

Status: **KEEP** (human decision, 2026-08-31)

The preregistration below (through "Decision rule") was written and committed
in `5035018` before `starter/agent.py` was touched. It is reproduced unedited;
results begin at "Implementation" below it.

Classification: human-approved post-Architecture-v1.1 experiment, the third
after E007 and E008 (see PROJECT_STATE.md "Human Decision — Freeze Lifted
(2026-08-31)"). This does not reopen or rewrite E007 or E008 history: both
remain REVERTED. E010 does NOT retry candidate-pool expansion, does NOT
reintroduce E007's `POOL_MULTIPLIER`, and does NOT reintroduce E008's
candidate-local IDF.

Baseline: E006 — Adaptive Catalog-Side Clarification, plus the accepted M6
`_product_terms()` memoization. `starter/agent.py` SHA-256
`8615fd2164bf5dbfa46b2baf802b6a6ebeb70503aa692d0d2e1f77a145e3a67a`,
commit `c8cc1e2`, baseline metrics HitRate@10 0.835 / MRR 0.522579 /
MTTC 4.515 / Efficiency 0.6485 / TechnicalScore 0.703974.

### Hypothesis

Every ranking signal the system has used to date is a bag of words. E004
counts how many evidence units overlap a candidate at all; E008 tried
weighting those overlaps by candidate-local rarity. Both are invariant to
word order: "running shoes for wide feet" and "feet wide for shoes running"
produce identical scores against every candidate.

The hypothesis under test is that **word order carries ranking signal the
bag-of-words dimension cannot express**, and that scoring a candidate by the
length of the longest contiguous n-gram of the user's message appearing in
the product's own normalized text — without changing which candidates are
considered — will improve MRR and HitRate@10.

Prior evidence and its class: R009's D-3 counterfactual bench measured
`phrase_n4` at +0.1096 TechnicalScore over the observed agent at pool depth
100 and +0.0924 at pool depth 60. **That is diagnostic evidence on a fixed
dialogue trajectory and is explicitly NOT a prediction of this experiment's
result.** A real implementation changes the candidate order, hence
`_select_attribute()`, hence what the simulator discloses, hence every later
turn — a feedback loop the counterfactual cannot model. D-3 additionally
biases downward by never playing turns after the real agent's hit. The
counterfactual figure is the reason to preregister E010; it is not a
baseline to be compared against, and an official result far below +0.11 is
fully consistent with the hypothesis holding.

### Candidate-set invariant (strict)

E010 changes ranking order ONLY. Candidate membership must remain EXACTLY
the ids `_coverage_rerank()` receives under E006 — no deeper pool, no extra
candidate, no removed candidate, no change to how `ids` is assembled before
the rerank call. The recommendation SET for a given turn must be identical
to E006's; only the order within that fixed set may differ.

### Frozen (unchanged)

- pool depth and the 7/3/10 slot structure (`PRIMARY_SLOTS`,
  `INSURANCE_SLOTS`, `top_k`), including the backfill branch
- BM25 field weights `bm25(products, 0.0, 6.0, 4.0, 2.5, 2.5, 1.5, 1.0)`
- `_terms()` and `STOPWORDS`
- category detection, `_CATEGORY_LEVELS` / `_DETECTION_LEVELS`, the
  relaxation ladder, and `_dominant_root()`
- `_select_attribute()`, `_attribute_score()`, `_ATTRIBUTE_VOCAB`,
  `_ASK_SEQUENCE`, `_SPECIFIC_ATTRIBUTES`, `_asked_attributes` state
- E003 evidence admission (`_is_information_free`, `_INFO_FREE_PREFIXES`),
  accumulation, and the oldest-first 40-term query cap
- intent-override handling (still none) and candidate-generation routing
- E004's definition of one evidence unit and its binary coverage count
  (retained as a ranking signal, demoted to secondary — see below)
- M6 `_product_terms()` memoization, kept byte-identical

No field weighting, dense retrieval, embeddings, LLM reranking, semantic
parsing, override handling, personalization, or new clarification logic is
added. No new dependency: Python standard library only.

### Permitted change (exactly three things)

1. A new product normalized **token stream** accessor,
   `_product_stream(parent_asin) -> str`, returning
   `" " + " ".join(_terms(<same six indexed fields>)) + " "` — the same
   tokenization `_product_terms()` already applies, but order-preserving and
   space-padded so that an n-gram test is a substring test with word
   boundaries. Backed by its own per-Agent-instance memoization cache
   (`_product_stream_cache`), reusing the M6 pattern exactly: catalog-static,
   immutable for the Agent's lifetime, never cleared by `reset()`.
   `_product_terms()` and its M6 cache are left untouched.

2. A new `_proximity_score(unit_grams, parent_asin) -> int` implementing the
   rule defined below.

3. `_coverage_rerank()`'s sort key only.

### Tested proximity rule (frozen; n_max = 4, preregistered)

`N_MAX = 4`. **This value is preregistered and will not be changed after
seeing any result.** No sweep over n_max is part of E010; no `phrase_n3`,
`phrase_n8`, or any other length will be tried inside this experiment.

Evidence unit token sequences use the same units as E004 — one admitted
message is one unit — but keep token ORDER, where E004 keeps only the set:

```
unit_tokens = [_terms(m) for m in session_messages if _terms(m)]
```

Units that tokenize to nothing are dropped, exactly as `_evidence_units()`
already drops them, so the unit lists stay aligned one-to-one with E004's
coverage units.

For each unit, its contiguous n-grams for n from `min(N_MAX, len(tokens))`
down to 2, longest first. Unigrams are excluded by construction: a
single-token match is bag-of-words overlap, which E004's coverage already
scores, so including it would not add an order signal.

```
proximity(P) = sum over units U of longest_match(U, P)

longest_match(U, P) = the largest n in [2, N_MAX] such that some contiguous
                      n-gram of U's token sequence occurs, with word
                      boundaries, in _product_stream(P)
                    = 0 if no such n exists
```

### Tested sort key (strictly lexicographic)

```
1. proximity(P) descending
2. coverage(P) descending          (E004's existing binary unit count)
3. incoming order, stable          (E001/E003 lexical order into the rerank)
```

Proximity is the PRIMARY key and coverage the secondary tiebreak. This is a
deliberate reversal of E008's coverage-dominant key: E008's hypothesis was
that coverage was right and only its ties needed help, and it failed. E010's
hypothesis is that the bag-of-words dimension is substantially exhausted
(R009's diagnostic finding: every re-weighting tested lands within ±0.02)
and that order is a stronger signal, so coverage is demoted to tiebreak
rather than kept dominant. No third signal, no weighted blend of proximity
and coverage.

The existing early return when there are no evidence units is retained;
with no units both scores are trivially zero and the incoming order stands.

### Expected channels — and what would be a warning

Unlike E008, E010 is NOT expected to leave HitRate@10 and MTTC untouched.
Candidate membership is frozen, but reordering can move the target across
the top-10 boundary in either direction, and a changed first-hit turn is
therefore an intended effect, not an isolation break. Concretely:

- `membership` must be identical — any change here is an isolation FAILURE
- `ask_attribute` must be identical **in the invariant-check replay**, which
  holds the dialogue fixed; `_select_attribute()` scores the candidate SET,
  not its order, so a difference there is an isolation FAILURE
- `order` must change somewhere, or the mechanism is not engaging
- `first_hit_turn` / `target rank` **may** change — expected and intended

Note the scope of that second point. In the official evaluator the
`ask_attribute` trajectory **can** legitimately diverge from E006, because a
changed rank changes which turn the session ends on and therefore which
disclosures follow. The invariant check is a fixed-trajectory replay, so
within it the trajectory must hold; the official run is under no such
constraint. These two statements are not in conflict and must not be
conflated when reading the results.

### Performance

Build each unit's n-gram list ONCE per `_coverage_rerank()` call and reuse it
across all candidates; do not rebuild per candidate. `_product_stream()` is
memoized per Agent instance. One extra SQL SELECT per distinct candidate
`parent_asin` over the entire run is accepted (bounded by the number of
distinct candidates ever surfaced, not by turns). No new persistent cache
beyond that one. No separate performance experiment is bundled into E010; a
runtime regression is to be reported, not optimized away mid-experiment.

### Procedure (preregistered, in order)

1. This preregistration is committed before `starter/agent.py` is touched.
2. `python3 -m tools.diagnostics.invariant_check dump --out trace_e006.json`
   on the baseline code, then the same after the change, then
   `compare ... --expect ranking-only`. **Must PASS** before proceeding. The
   tool's `NOTE` about changed `first_hit_turn` under frozen membership is
   expected here and is intended (see above), not a failure.
3. D-3 offline prescreen.
4. Exactly ONE official evaluator run:
   `python3 -m evaluator.local_evaluator --output results_e010.json`
5. `python3 -m tools.diagnostics.d5_paired_delta results.json
   results_e010.json --show-sessions` — the paired transition matrix is
   presented to the human BEFORE any KEEP/REVERT discussion.

### Decision rule (preregistered)

KEEP requires BOTH: (a) TechnicalScore strictly above the E006 + M6 baseline
0.703974 on the single official run, and (b) no scenario-bucket collapse in
the D-5 paired matrix. A TechnicalScore gain well below D-3's +0.11
counterfactual delta is still a KEEP if both conditions hold — the
counterfactual is not a target. If either condition fails, REVERT to E006 +
M6 and discard the change.

No parameter tuning after seeing results. No E010b with a different `N_MAX`,
a different key order, or a weighted blend without a new, separately
authorized preregistration.

---

### Implementation

Files changed: `starter/agent.py` only (84 insertions, 6 deletions). No
evaluator, catalog, label, or diagnostic-tool change. SHA-256 moves from
`8615fd21…45e3a67a` (E006 + M6) to
`ec58f9f4cf0fea1e225e56e9e3d977334f88723c77e38b7928294abaf25e43a1`.

Exactly the three permitted changes, and nothing else:

1. `_product_stream(parent_asin)` + `_product_stream_cache`, following the M6
   memoization pattern. `_product_terms()` and its M6 cache are byte-identical
   to E006.
2. `_evidence_token_lists()`, `_unit_ngrams()`, `_proximity_score()`, and the
   module constant `N_MAX = 4`.
3. `_coverage_rerank()`'s sort key, now
   `(-proximity, -coverage)` under a stable sort.

`_evidence_units()` — E004's frozen unit definition — is unchanged and still
supplies the coverage term; `_evidence_token_lists()` is its order-preserving
counterpart and applies the identical empty-unit filter, so the two stay
aligned one-to-one. The n-gram lists are built once per `_coverage_rerank()`
call and reused across candidates.

Verified untouched by `git diff`: BM25 field weights, `_terms()`, `STOPWORDS`,
`PRIMARY_SLOTS`/`INSURANCE_SLOTS` and the backfill branch, category detection
and the relaxation ladder, `_select_attribute()`/`_attribute_score()`/
`_ATTRIBUTE_VOCAB`, evidence admission and the 40-term cap, and
candidate-generation routing.

### Mechanism validation (before the official run)

27 smoke checks, all passing. The two that matter most:

- `_proximity_score()` is **bit-identical** to R009's D-3 `phrase_n4` scorer
  across 720 (message-set, product) pairs drawn from the real catalog.
- `_product_stream()` is bit-identical to D-3's `normalized_text()` across 400
  real products, and its token set equals `_product_terms()` exactly.

Also verified: no unigrams emitted; grams ordered longest-first; the score caps
at 4 for a 10-token verbatim quote; word-boundary safety (`"un ning"` does not
match `" running "`); order sensitivity (a forward 3-token product phrase scores
3, its reversal scores less, while the bag-of-words view of the two is
identical); `reset()` does not clear the catalog-static stream cache;
punctuation-only evidence still returns no recommendations without crashing.

### Invariant check — PASS

```bash
python3 -m tools.diagnostics.invariant_check dump --out trace_e006.json   # baseline
#   ... apply E010 ...
python3 -m tools.diagnostics.invariant_check dump --out trace_e010.json
python3 -m tools.diagnostics.invariant_check compare \
    trace_e006.json trace_e010.json --expect ranking-only
```

200 sessions, 870 comparable turns:

| channel | result |
|---|---|
| candidate membership changed | **0 / 870** |
| order changed (same set) | **610 / 870** |
| ask_attribute changed | **0 / 870** |
| target rank changed | 57 / 870 |
| sessions with different first_hit_turn | **0** |
| sessions with different turn count | 0 |

`RESULT: PASS`.

### Structural finding — E010 is a pure-MRR experiment by construction

The preregistration anticipated that `first_hit_turn` might change even with
frozen membership, if a rank crossed the top-10 boundary. **It did not, and
under this experiment's frozen pool depth it could not.**

`_coverage_rerank()` receives exactly the ids that are returned: `ids` is
already sliced to `ids[:top_k]` before the rerank call. With pool depth frozen
at 10 (a preregistered freeze), reordering can only move the target *within*
the returned ten — never across the top-10 boundary. Therefore HitRate@10,
MTTC, and Efficiency are necessarily bit-identical to E006, and

```
TechnicalScore delta = 0.30 * MRR delta = 0.30 * 0.130570 = 0.039171
```

exactly, which is what the official run returned.

Consequence for interpretation: **the correct ceiling for E010 is D-2's
"perfect order, current top-10" bound (+0.093726), not D-3's `phrase_n4`
counterfactual (+0.1096), which requires pool depth 100.** E010 captured
41.8 % of its actual ceiling — (0.653149 − 0.522579) / (0.835 − 0.522579).
The D-3 figure was never used as a target, a prediction, or a success
criterion.

### Offline prediction was exact

Because the trajectory is provably frozen (membership, `ask_attribute`, turn
count, and `first_hit_turn` all unchanged), the E010 invariant trace predicted
the official result **bit-exactly** — TS 0.743145, MRR 0.653149 — before the
evaluator was run. The E006 trace likewise reproduces the official E006
baseline exactly (0.703974 / 0.522579). This is a fidelity check on R009's
replay core, not an independent confirmation of the result.

### D-3 prescreen

```bash
python3 -m tools.diagnostics.d3_counterfactual_bench --pool 10 \
    --scorers bm25,cov,phrase_n4
```

| scorer | HR@10 | MRR | MTTC | TS |
|---|---|---|---|---|
| *(observed — now the E010 agent)* | 0.8350 | 0.653149 | 4.515 | 0.743145 |
| `bm25` | 0.8050 | 0.521002 | 4.840 | 0.682001 |
| `cov` | 0.8050 | 0.535488 | 4.840 | 0.686346 |
| `phrase_n4` | 0.8050 | 0.637756 | 4.840 | 0.717027 |

Two readings, which must not be conflated. The three counterfactual rows sit
below the observed agent because D-3's pool-10 is the *unscoped* BM25 top-10,
which lacks the agent's category-scoped 7 slots (HR@10 0.805 vs 0.835) — they
are not comparable to the agent's own candidate set. What *is* a clean
like-for-like comparison is the three rules against each other on that one
identical set: `phrase_n4` MRR 0.637756 > `cov` 0.535488 > `bm25` 0.521002.
That ordering is consistent with the live result. Note also that the
`[observed]` row is the E010 agent, since D-3 replays the live runtime; it is
not comparable to R009's `[observed]` row.

### Evaluation command (exactly one official run)

```bash
python3 -m evaluator.local_evaluator --output results_e010.json
```

### Results

| Metric | E006 + M6 | E010 | Delta |
|---|---|---|---|
| HitRate@10 | 0.835000 | 0.835000 | +0.000000 |
| MRR | 0.522579 | **0.653149** | **+0.130570** |
| MTTC | 4.515 | 4.515 | +0.000 |
| Efficiency | 0.6485 | 0.6485 | +0.0000 |
| **TechnicalScore** | 0.703974 | **0.743145** | **+0.039171** |

Reported token usage: 0 prompt / 0 completion (no model on the scored path).

### Scenario metrics

| Scenario | n | HR@10 | Δ | MRR | Δ | MTTC | Δ |
|---|---|---|---|---|---|---|---|
| buying | 80 | 0.8625 | +0.0000 | 0.654807 | +0.152699 | 3.900 | +0.000 |
| browsing | 80 | 0.8250 | +0.0000 | 0.608274 | +0.128859 | 4.675 | +0.000 |
| intent_override | 30 | 0.8000 | +0.0000 | 0.736111 | +0.077976 | 5.333333 | +0.000 |
| boundary | 10 | 0.8000 | +0.0000 | 0.750000 | +0.125000 | 5.700 | +0.000 |

All four buckets improved on MRR. HitRate@10 and MTTC are bit-identical to
E006 in every bucket, as the structural finding above requires.

### D-5 paired session delta

```bash
python3 -m tools.diagnostics.d5_paired_delta results.json results_e010.json \
    --show-sessions
```

| Transition | n |
|---|---|
| miss→hit | 0 |
| **hit→miss** | **0** |
| hit→hit rank improved | **53** |
| hit→hit rank regressed | **1** |
| hit→hit unchanged | 113 |
| miss→miss | 33 |

Per scenario: buying 22 improved / 0 regressed; browsing 26 / 0; boundary 2 / 0;
intent_override 3 / **1**.

Scored-rank distribution over the 167 hits: rank 1 rises 82 → **112**, and
ranks 9–10 fall 8 → **0**. Largest migrations: 8→1 (7 sessions), 2→1 (7), 3→1
(4), 5→1 (4), 7→1 (3), 6→3 (3).

The single regression is `public_0080` (intent_override), rank 2 → 4, first hit
turn unchanged at 4, costing 0.25 reciprocal rank. It is one session, not a
cluster, and is consistent with the known unresolved limitation that evidence
accumulation is append-only with no supersession — a proximity match against a
stale pre-override phrase can outrank the post-override target. E010 adds no
override handling and does not claim to.

### Regression / bugs

None found. No crash, no contract violation, no invalid or duplicate
`parent_asin`, no change to the returned recommendation count.

Runtime cost, reported honestly and **not** optimized away mid-experiment (the
preregistration forbade bundling a performance experiment): official evaluator
wall clock 73.4 s → **101.4 s**, about 1.39x slower. The cost is the substring
scan of each candidate's full token stream, plus one extra SQL SELECT per
distinct candidate `parent_asin` over the run. This remains far below any
evaluation limit and roughly a third of the pre-M6 313 s. No optimization was
attempted; if one is wanted it belongs in a separate, separately-recorded
change.

One test-authoring slip worth recording: an early smoke assertion expected 3
surviving evidence units from a 5-message fixture; the correct count is 2
(`"a I the to"` tokenizes to nothing under `_terms()`). The assertion was
wrong, not the code — the substantive alignment checks against
`_evidence_units()` passed both before and after the fix.

### Decision: KEEP

Both preregistered conditions met: (a) TechnicalScore 0.743145 is strictly
above the 0.703974 baseline; (b) no scenario-bucket collapse — `hit→miss` is 0,
all four buckets improved on MRR, and the sole regression is one session.

This is the largest single-experiment gain since E003, and the first ranking
change since E004 to improve rather than regress MRR. New best system: **E010 —
Proximity-aware Reranking**, running on top of E006 + M6.

### What this establishes, and what it does not

**Established.** Within the candidate set the agent already returns, word-order
proximity is a materially better ranking signal than bag-of-words overlap.
Scoring by the longest contiguous evidence n-gram (n ≤ 4) present in a
candidate's own text, with E004 coverage demoted to a tiebreak, raised MRR by
+0.130570 with zero hit→miss transitions. This is the first signal dimension
tested that was not already exhausted, and it is consistent with R009's
diagnostic finding that every bag-of-words re-weighting lands within ±0.02.

**Not established.**

- That `N_MAX = 4` is optimal. It was preregistered and frozen; no other value
  was run against the official evaluator, and none may be without a new
  authorized preregistration. R009's counterfactual suggested `n3` captures
  ~84 % of `n8`, but that is diagnostic evidence on a fixed trajectory.
- That proximity-first is better than coverage-first as a key *order*. Only the
  preregistered `(proximity, coverage)` order was run.
- That deeper candidate pools would now pay off. E007's pool expansion remains
  REVERTED and untested under this ranker. D-2 prices the opportunity — pool
  100 moves the perfect-reranker ceiling from 0.767 to 0.961 — but that is an
  oracle bound, not a prediction, and E007 failed for reasons this experiment
  does not address. It would require a new preregistration.
- That intent override or boundary behavior is solved. Neither received any
  new logic; both buckets moved only through the shared ranking change, and
  intent_override holds the experiment's only regression.
- That E008's conclusion is overturned. E008 rejected candidate-local IDF as a
  tiebreak *under* coverage; E010 replaces coverage as the primary key with a
  different signal class. The two are not in competition and E008 remains
  REVERTED.
- Private-set generalization. The paraphrase stress test (D012) that would
  probe whether phrase matching is brittle to rewording remains **unrun**, and
  is now the most valuable open diagnostic: a rule keyed on contiguous n-grams
  is a priori more paraphrase-sensitive than a bag of words, and the public set
  cannot detect that.

### Next question

Run D012 (paraphrase stress) before anything else. E010's gain is real on the
public set, but a contiguous-n-gram rule is structurally more exposed to
rewording than the bag-of-words rule it replaced, and nothing measured so far
would reveal that. If D012 shows the gain survives paraphrase, the next
candidate is a separately preregistered look at whether pool depth is now worth
revisiting given a ranker that can exploit it.
