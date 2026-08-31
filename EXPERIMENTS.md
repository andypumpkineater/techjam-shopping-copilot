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

> **Superseding note (2026-08-31).** The "new best system" sentence above is the
> chronological record as written at E010's close and is retained unedited. It is
> **superseded**: E011 — Candidate Pool Expansion under a Proximity Reranker was
> subsequently preregistered, implemented, evaluated once, and **KEPT**
> (TechnicalScore 0.743145 → **0.796939**). The current best system is E011,
> running on top of E010 + E006 + M6. E010 itself is not reverted or amended —
> it still runs underneath E011 as the ranking rule, and E011 changed only pool
> depth, pool composition, and the position of the `top_k` cut. Note that E011
> returned **−0.027687** of E010's **+0.130570** MRR gain (21.2 %) in exchange for
> +0.095 HitRate@10 and −0.730 MTTC, so E010's MRR figure above is no longer the
> system's MRR. See "E011 — Candidate Pool Expansion under a Proximity Reranker".

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
  *(Chronological record retained. This was subsequently tested: E011 got that
  new preregistration, expanded the pool 10 → 50 under this ranker, and was KEPT
  at +0.053794. The bullet stands as what was known at E010's close.)*
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

> **Superseding note (2026-08-31).** The paragraph above is retained as written
> and is the chronological record of what was decided at E010's close. It is
> **superseded**: D012 was preregistered, built, and **CANCELLED without ever
> being run to a result** after the official FAQ
> (`docs/final_evaluation_faq.md`, upstream `9c9e7c9`) §1 stated that the final
> 800 samples use the same deterministic customer-message templates as the
> published evaluator and that "No undisclosed natural-language paraphrases are
> introduced." There is no D012 result and no D012 number may be cited — see
> "D012 — Paraphrase Stress", Cancellation. The conditional second sentence
> therefore never resolved through D012; pool depth (E011) became the next
> candidate directly, on D-2 oracle evidence rather than on a D012 outcome.
> `N_MAX` remains frozen: the FAQ said nothing about n-gram length. This note
> does not rewrite E010's record, which stands as run and KEPT.

## D012 — Paraphrase Stress

Status: **CANCELLED** — premise falsified by the official FAQ before the
diagnostic was ever run. See "Cancellation" at the end of this section.
Originally: **PREREGISTERED** (this section committed before any code was written)

Type: **R / Diagnostic. NOT an Agent Experiment.**

No runtime code is changed. `starter/agent.py`, `evaluator/`, the frozen catalog,
and the public labels are untouched. Expected TechnicalScore impact is **exactly
zero**, and **no official evaluator run is performed in this cycle** — there is
no runtime change for it to measure.

### Question

E010 ranks candidates by the length of the longest contiguous evidence n-gram
(n in [2, 4]) appearing in a candidate's own token stream. It replaced E004's
bag-of-words coverage as the primary sort key and gained +0.130570 MRR /
+0.039171 TechnicalScore on the 200 public sessions.

A rule keyed on contiguous n-grams is *a priori* more exposed to rewording than
the bag-of-words rule it replaced. The public simulator quotes the target
product's own `features` / `details` text **verbatim** into user messages
(`evaluator/local_evaluator.py:154-185`, `:52-71`) — messages such as
`"For that, what matters is: Rubber sole; Shaft measures approximately 8.37\" from arch."`
are literal catalog strings. Exact-substring matching is unusually well served by
that, and the public set cannot reveal how much of E010's gain depends on it.

**The question is a difference, not a level.** "How much does E010 lose under
paraphrase?" is not decision-relevant on its own, because the bag-of-words rule
loses ground too. The decision-relevant quantity is whether E010's *advantage
over the rule it replaced* survives:

```
A(r) = TechnicalScore(phrase_n4, r) - TechnicalScore(cov, r)
```

evaluated on the same replay, same pool, same evidence stream, at rewrite rate
`r`. Note the identity

```
A(r) - A(0) = [TS_phrase(r) - TS_phrase(0)] - [TS_cov(r) - TS_cov(0)]
```

so `A` *is* the degradation differential; there is no second quantity to track.

### Hypothesis

None in the E-class sense — no performance hypothesis is under test and nothing
can be improved by running this. D012 asks a falsification question about an
already-KEPT experiment's stated open risk.

### Authority limit (preregistered, binding)

**No D012 verdict can revert E010.** Offline diagnostic evidence does not
overturn official-evaluator runtime evidence; that boundary is stated in R009
("Evidence classification — important") and in `tools/diagnostics/README.md`
("What a diagnostic result is and is not"). The strongest consequence available
to the worst possible D012 outcome is a **recommendation to draft a new,
separately authorized preregistration** (for example a proximity/coverage blend,
or a backoff to shorter n on sparse evidence). Conversely, a clean D012 result
does **not** establish private-set generalization; it retires one named risk and
nothing more.

### Design constraints (from the authorization)

1. `evaluator/` is not modified. The rewrite is applied **offline, in the D-*
   replay, to the `user_message` the simulator has already produced**, immediately
   before it is handed to `Agent.respond()`. The simulator's own state machine
   (`disclosed`, `boundary_used`, `override`) consumes nothing downstream of the
   rewrite and is untouched.
2. `tools/diagnostics/_replay.py` is reused. It gains one *additive, optional,
   default-`None`* `message_transform` hook; a fourth replay implementation is not
   written. With the hook unset, every existing caller (D-1, D-2, D-3,
   `invariant_check`) is byte-for-byte unaffected.
3. Offline, deterministic, seeded, Python standard library only. No new
   dependency, no network.
4. The **closed** D-3 scorer registry supplies the arms. **No scorer is added and
   `N_MAX` is not swept** — sweeping it here would be public-set hill-climbing,
   which `d3_counterfactual_bench.py`'s discipline block forbids.
5. Rewrite intensity is reported as a curve over rates 0.00 / 0.25 / 0.50 / 1.00.
6. `_replay.py`'s known conservative bias (the replay stops when the *real* agent
   hits) stands unmodified — see "Interaction with the conservative bias" below.

### Arms (closed registry, unchanged)

| arm | what it is | why it is here |
|---|---|---|
| `bm25` | pool order as-is | retrieval-side reference: isolates how much degradation comes from the *query* changing rather than from either ranking rule |
| `cov` | E004 binary per-unit coverage | **the control** — the bag-of-words rule E010 demoted |
| `phrase_n4` | longest contiguous n-gram, n ≤ 4 | **E010's rule**, verified bit-identical to `Agent._proximity_score()` over 720 pairs during E010 |

The `[observed]` row is the live E010 agent under the same paraphrased stream. It
is reported as context only: it **cannot** answer the differential question,
because there is no live `cov` agent to compare it against, and building one
would be a runtime change that D012 forbids.

### Pool depth

Headline **pool 10**. This is E010's actual operating regime: `_coverage_rerank()`
receives exactly the ids that are returned, so a reordering can only move the
target *within* the returned ten, HitRate@10 / MTTC / Efficiency cannot move, and
`TS delta = 0.30 x MRR delta`. Secondary **pool 100** on the mixed ensemble only,
as a depth-sensitivity check. Both depths are produced from a single replay per
configuration (depth 100 is fetched once and sliced).

### The rewriter — frozen specification

The rewriter is the only component of D012 that could fabricate its own
conclusion. It is therefore specified in full here, in the commit that precedes
the code, and **may not be retuned after any result is seen**.

It receives `(message, sample_id, turn, seed, families)` and **nothing else** —
no sample, no product, no target, no catalog handle. `sample_id` and `turn` are
used solely as hash salt.

**Eligibility.** A message is rewritten only if `not _is_information_free(message)`.
Rationale: the three information-free templates are dropped from evidence by E003
at every turn after the first; perturbing their prefixes would silently flip
`_is_information_free()` and promote boilerplate into evidence, confounding D012
with an E003 regression that has nothing to do with word order. Turn-1 messages
are always eligible (`initial_message()` never emits an information-free
template). The eligible set is exactly the evidence-bearing set.

**Selection, nested across rates.** For each eligible message,

```
u = int.from_bytes(sha256(f"{seed}|{sample_id}|{turn}|select").digest()[:8], "big") / 2**64
rewrite iff u < rate
```

so the messages rewritten at 0.25 are a **subset** of those at 0.50, a subset of
those at 1.00. The degradation curve therefore varies coverage of one fixed
message set, and is not confounded by a different sample of messages per level.

**Per-message RNG.** `random.Random(sha256(f"{seed}|{sample_id}|{turn}|apply").hexdigest())`,
re-seeded per message; families are applied in the fixed order below, so every
draw is deterministic.

**Word model.** `words = message.split()`; `alnum(w) = re.sub(r"[^A-Za-z0-9]", "", w)`;
`w` is a *content word* iff `_terms(w)` is non-empty. Clauses are the message
split on `(?<=[.;:,])\s+`, delimiters staying with the left clause.

**Families** (fixed order when composed):

1. `reorder` — if there are >= 2 clauses, rotate the clause sequence left by
   `1 + rng.randrange(n_clauses - 1)`. Within-clause word order is preserved.
2. `shuffle` — for each clause of `L >= 4` words, apply `ceil(L/4)` adjacent
   transpositions at distinct positions drawn by `rng.sample(range(L-1), k)`.
3. `morph` — plural toggle. Over content words whose `alnum` is purely alphabetic
   with length >= 4, pick `ceil(n/3)` by `rng.sample` and toggle: drop a trailing
   `s` when `alnum` ends in `s`, not in `ss`/`us`/`is`, and has length >= 5;
   otherwise append `s` unless it ends in `s`/`x`/`z`/`h`. Surrounding punctuation
   is preserved.
4. `drop` — delete `C // 8` content words (0 when `C < 8`), positions by
   `rng.sample`. Deliberately the mildest setting of the most destructive family.
5. `filler` — for each clause of >= 6 words, insert one word drawn by the RNG from
   the frozen list `("really", "kind", "sort", "general", "overall", "honestly")`
   at an RNG-chosen position. All six survive `_terms()` (length > 1, not in
   `STOPWORDS`).
6. `punct` — **placebo, never part of the mixed ensemble.** Replace each single
   space with two spaces and insert a space before each of `.,;:!?`. Provably
   token-neutral under `_terms()`: `[a-z0-9]+` runs are never split by inserting
   whitespace before a non-alphanumeric character, and never merged by adding
   whitespace.

**Mixed ensemble `mix`** = `reorder -> shuffle -> morph -> drop -> filler`, all five
applied to each selected message. "Rate" therefore means "fraction of
evidence-bearing user messages that are fully paraphrased".

**Vocabulary-closure invariant (asserted in the smoke test).** For every rewritten
message,

```
set(_terms(out)) subset-of  set(_terms(in)) union FILLER union {t+"s", t[:-1] : t in _terms(in)}
```

The rewriter can introduce no information that was not already in the user's own
message, plus six fixed English hedge words. This is the structural guarantee that
no `ground_truth`, catalog text, or target-derived string can enter through it.

### A priori bias of each family — stated before the run

| family | vocabulary-free | effect on `cov` | effect on `phrase_n4` | favors |
|---|---|---|---|---|
| `reorder` | yes | **exactly none** (per-unit token set invariant) | only grams straddling a clause boundary | `cov`, slightly |
| `shuffle` | yes | **exactly none** (a permutation preserves the token set) | strong | **`cov`, by construction** |
| `morph` | yes (rule-based) | weak (see saturation note) | strong — any gram containing the token dies | `cov`, structurally |
| `drop` | yes | weak (see saturation note) | strong | `cov`, structurally |
| `filler` | 6 frozen hedge words | ~none (a unit can only gain a token) | moderate — breaks grams spanning the insertion | `cov` |
| `punct` | yes | **exactly zero** | **exactly zero** | placebo |

Three admissions, recorded now so that neither can be mistaken for a post-hoc
excuse:

- **D012 is biased against E010 by design.** Every content family is structurally
  more damaging to `phrase_n4` than to `cov`, and two of them are `cov`-neutral by
  construction. "`phrase_n4` degrades more than `cov`" is therefore the *expected*
  outcome and is **not**, on its own, evidence of a problem. This is exactly why
  the decision criterion below is stated on the surviving advantage `A(1.0)` and
  not on raw degradation.
- **`cov`'s robustness is saturation, not bag-of-words virtue.** `cov` credits a
  unit if the candidate shares *one* token with it. Most candidates in a BM25 pool
  share at least one token with most units, so `cov` has very little dynamic range
  to lose under any perturbation. Its flat curve should be read as low resolution,
  not as strength.
- **This is mechanical perturbation, not semantic paraphrase.** No offline
  paraphraser is available under the no-network / no-new-dependency constraints, so
  lexical-semantic substitution ("waterproof" -> "water resistant") is out of scope.
  D012 bounds robustness to *surface* rewording (order, morphology, omission,
  hedging) only. Robustness to synonym substitution remains open and a private set
  could still expose it. A clean verdict must not be over-read past this line.

### Interaction with the conservative bias

`_replay.py` stops a session when the **real** agent hits, and is not modified.
Under paraphrase the real (E010) agent hits later or not at all, so *more* turns
are played and the counterfactual arms receive *more* evidence at high rewrite
rates than at rate 0. This inflates both counterfactual arms as `r` grows. It
applies to `cov` and `phrase_n4` identically, so `A(r)` is unaffected to first
order; absolute per-arm degradation figures are the ones it distorts, and they are
reported with that caveat rather than corrected.

### Run plan (12 replays, one process, one `Agent` instance)

The two agent caches (`_product_terms_cache`, `_product_stream_cache`) are pure
memoizations of catalog-static functions, so sharing one `Agent` across
configurations is bit-identical to separate processes and avoids 12 index builds.

- mixed ensemble, seed `20260831`, rates 0.00 / 0.25 / 0.50 / 1.00 — 4 replays
- each family alone at rate 1.00, seed `20260831`: `reorder`, `shuffle`, `morph`,
  `drop`, `filler`, `punct` — 6 replays
- mixed ensemble at rate 1.00, seeds `11` and `12` — 2 replays

### Validity gates — D012 is VOID unless all four pass

- **G1** rate 0.00 reproduces the D-3 rows for `[observed]`, `bm25`, `cov`,
  `phrase_n4` to six decimals, at both pool depths. (Proves the hook is a no-op
  when unused and that D012 sits on the same replay as R009.)
- **G2** the `punct` placebo at rate 1.00 is identical to rate 0.00 in every arm at
  both depths. (Proves the harness itself contributes no variance.)
- **G3** at rate 1.00 mixed, at least **80 %** of eligible messages differ from
  their original. (Proves the stress is real; a null result from an inert rewriter
  is worthless.)
- **G4** the vocabulary-closure invariant holds for 100 % of rewritten messages.
  (Proves no external information enters.)

### Decision rule (frozen before any result is seen)

On the mixed ensemble at pool 10, with `A(r)` as defined above:

| verdict | condition |
|---|---|
| **NOT SPECIALLY FRAGILE** | `A(1.0) > 0` **and** `A(1.0) >= 0.50 * A(0.0)` |
| **PARTIAL EROSION** | `0 < A(1.0) < 0.50 * A(0.0)` |
| **SPECIALLY FRAGILE** | `A(1.0) <= 0` |
| **INCONCLUSIVE** | the spread of `A(1.0)` over the three seeds is >= the distance from `A(1.0)` to the nearest verdict boundary |

Read plainly: E010 is *specially* fragile only if enough surface rewording makes
the bag-of-words rule it replaced catch or beat it. If both rules degrade by
comparable amounts and proximity stays ahead, the "contiguous n-grams are brittle"
risk is not established, whatever the absolute drop turns out to be.

No family may be added, removed, or reparameterized after the first full run. If a
family produces an uninteresting curve, that is a reported result.

### Files to be added

- `tools/diagnostics/_paraphrase.py` — the frozen rewriter
- `tools/diagnostics/d012_paraphrase_stress.py` — the driver
- one additive optional `message_transform` parameter on `_replay.py::replay()`
- `docs/diagnostics/D012_PARAPHRASE_STRESS.md` / `.json` — the named result
  snapshot (repo-root `results*.json` is gitignored scratch and is not used)

### Results

**None. The diagnostic was cancelled before it produced any result.** This
section is left empty deliberately: there is no D012 number, and any figure that
appears to be one is an artifact of aborted development work, not a result.

### Cancellation (2026-08-31)

**Status: CANCELLED (premise falsified by official FAQ §1, upstream `9c9e7c9`,
2026-08-31).**

The organizers published `docs/final_evaluation_faq.md` (upstream `9c9e7c9`)
after this preregistration was committed. Its §1 states that the final 800-sample
evaluation uses **the same deterministic customer-message templates as the
already-published evaluator**, and that *"No undisclosed natural-language
paraphrases are introduced."*

That is a direct answer to the question D012 was built to ask. D012's entire
value rested on one assumption — that the private set might reword user messages
in ways the 200 public sessions cannot reveal. The organizers have now stated
that it does not. The risk D012 was designed to measure **does not exist in the
final evaluation**, so running it would spend roughly half an hour of compute to
quantify the sensitivity of a ranking rule to an input distribution that will
never be presented to it.

This is a change in external information, **not** a defect in the design, the
tooling, or E010. Nothing about the preregistration was found to be wrong.

**What was built, and what was and was not run.** The tooling is complete and its
invariants are tested:

- `tools/diagnostics/_paraphrase.py` — the frozen rewriter, implementing the
  specification above exactly
- `tools/diagnostics/d012_paraphrase_stress.py` — the driver
- `tools/diagnostics/_replay.py` — one additive, optional, default-`None`
  `message_transform` hook
- `tests/test_paraphrase.py` — 12 property tests, all passing

Executed during development, and **not** citable as results: a 20-session smoke
run, and a full sweep that was aborted after 5 of its 12 configurations. Neither
was recorded, no `docs/diagnostics/D012_*.json` snapshot was ever written, and
**no number from either may be quoted, in this repository or anywhere else.** A
20-session sample cannot support any of the preregistered verdicts, and the
aborted sweep never reached its decision rule. The results section above is empty
and stays empty. D012 was **not** downgraded to a small-sample run to salvage a
finding; a cancellation is a cancellation.

**The preregistration is retained, not deleted.** Everything above the "Results"
heading is byte-identical to commit `600381e`, with the single exception of the
two-line status header at the top of this section, which points here. The design,
the frozen rewriter specification, the a priori bias table, the four validity
gates, and the decision rule are unedited. Retaining them records that the risk
E010 flagged was taken seriously enough to be designed against and frozen before
testing, and that it was retired by evidence rather than by neglect.

**Consequence for E010: none.** E010 remains KEPT on its official-evaluator
result (TechnicalScore 0.743145). D012 was never able to revert it — the
preregistered authority limit above says so explicitly — and it now has no
finding of any kind. The paraphrase-brittleness risk recorded in E010's "Not
established" list and in PROJECT_STATE.md's Open Question 1 is **retired by the
official FAQ**, not by this diagnostic.

**Residual value as future work.** The tooling is kept rather than reverted, for
three reasons:

1. The `message_transform` hook is a general capability: any future question of
   the form "how does the system behave when the input stream is perturbed"
   (truncation, noise, a different simulator) now costs a callable rather than a
   new replay implementation.
2. If the organizers ever revise the FAQ, or if this work is carried to a setting
   with real user messages, D012 can be run as specified with no redesign — the
   preregistration is already frozen, which is the expensive half.
3. The frozen-rewriter discipline (specification committed before code, a priori
   bias declared before running, a placebo arm, a vocabulary-closure invariant)
   is a reusable pattern for any future diagnostic whose instrument could
   otherwise be tuned to produce its own answer.

**Verification that cancelling changed nothing.** `starter/agent.py` is
untouched — SHA-256 `ec58f9f4cf0fea1e225e56e9e3d977334f88723c77e38b7928294abaf25e43a1`,
identical to E010. `evaluator/`, the frozen catalog, and the public labels are
untouched. With `message_transform` unset, the patched `_replay.py` reproduces
the pre-patch replay exactly: a post-patch full D-3 run at pool 10 returned
`[observed]` 0.743145, `bm25` 0.682001, `cov` 0.686346, `phrase_n4` 0.717027 —
bit-identical to the E010 prescreen table recorded above. No official evaluator
run was performed in this cycle, and none was warranted: there is no runtime
change for one to measure.

## E011 — Candidate Pool Expansion under a Proximity Reranker

Status: **PREREGISTERED** (written and committed before any implementation)

Type: E / Agent Experiment. Changes runtime behavior; decided by one official
evaluator run.

Classification: human-approved post-Architecture-v1.1 experiment, the fourth
after E007, E008 and E010. Declared in advance to be the **LAST capability
experiment**: on KEEP the algorithm freezes at E011, on REVERT it freezes at
E010. Remaining effort goes to submission deliverables. See PROJECT_STATE.md.

Baseline: E010 — Proximity-aware Reranking, on top of E006 + M6.
TechnicalScore 0.743145 (HR@10 0.835, MRR 0.653149, MTTC 4.515, Eff 0.6485).
`starter/agent.py` SHA-256 `ec58f9f4…f25e43a1`.

### Hypothesis

E007 expanded the candidate pool 10 -> 20 and regressed on every overall metric
(TechnicalScore -0.031). Its stated conclusion was narrow: *the binary,
unweighted E004 coverage reranker could not exploit a noisier deeper pool.* It
explicitly did not establish that deeper retrieval is harmful.

E010 replaced that ranker's primary key with contiguous-n-gram proximity and
gained +0.039, entirely through MRR — because with the pool frozen at 10, a
reranker can only reorder what retrieval already returned and can never promote
an item across the top-10 boundary (see E010, "E011 is a pure-MRR experiment by
construction").

**Hypothesis:** the ranker is no longer the limiting factor, so giving the same
E010 reranker a deeper candidate pool converts into a HitRate@10 gain — the
metric E010 was structurally unable to move.

Diagnostic support (D-2/D-3, `docs/diagnostics/E006_M6_BASELINE.md`; measured on
the E006 agent, override-gated): the perfect-reranker ceiling rises from 0.7672
at pool 10 to 0.9032 at pool 50; `phrase_n4` counterfactual TS rises from
0.682001 (bm25 order) to 0.796421 at pool 60.

**This is diagnostic evidence, not a prediction.** See "Why the counterfactual is
weaker here than it was for E010" below.

### Preregistered pool depth: 50 (ONE value, human decision)

`POOL_DEPTH = 50`. Internal pool only; the contract `top_k` stays 10.

D-3 measured `phrase_n4` as monotonically better at 100 than at 60 (+0.017), so
the direct counterfactual evidence favours a deeper pool than 50. 50 was chosen
anyway, for a reason specific to this experiment:

> E010's offline prediction was *exact* because its trajectory provably could not
> change. **E011's trajectory necessarily changes**: membership changes ->
> `_select_attribute()` sees different candidates -> `ask_attribute` changes ->
> what the simulator discloses changes -> every later turn changes. The
> fixed-trajectory counterfactual therefore has materially less predictive power
> here than it had for E010, and E007's failure mode — deeper-pool noise harming
> ranking in ways the counterfactual did not model — lives precisely in the part
> it cannot model.

Under a one-shot-then-freeze constraint, the more conservative 5x expansion is
preferred while its ceiling (0.9032) still leaves ~0.16 of headroom above the
current 0.743145. **No second pool depth will be tested if E011 fails.** That
discipline was established by E007 and is not reopened here.

### The coupled change that cannot be separated — declared, not hidden

Retrieve-wide-then-rerank **structurally removes the guaranteed global-insurance
slots from the OUTPUT**. Today 3 of the returned 10 are reserved for globally
strong lexical matches the category scope excluded; after E011 the reranker
chooses all 10 from the merged pool, so that guarantee becomes a pool-composition
property rather than an output property.

This is not separable from pool expansion — any reranker over a wider pool must
be allowed to choose the final 10 — so it is part of this minimal indivisible
experiment unit rather than a second, hidden variable.

**E007 had exactly this property and never disclosed it** (it also silently moved
the split from 7/3 to 14/6), which is one reason its negative result is hard to
attribute. E011 states it up front.

Mitigation: pool composition keeps the current 70/30 ratio — primary 35,
global insurance 15 — so the reranker selects from a pool built the same way,
only deeper.

### Permitted change (exactly these)

1. `POOL_DEPTH = 50`; category-path capacities primary 35 / insurance 15.
2. The unscoped path (`detected is None`) retrieves `POOL_DEPTH` instead of
   `top_k`. **Both paths must change together**; leaving the unscoped path at 10
   would make retrieval depth a hidden variable.
3. Truncate to `top_k` **after** reranking, not before.

### Frozen (unchanged)

BM25 field weights and expression; `TOKEN_RE`, `_terms`, `STOPWORDS`; the 40-term
cap; category detection, hierarchy and relaxation; `N_MAX = 4` and the proximity
formula; the lexicographic sort key `(proximity, coverage, incoming order)`;
E003 evidence admission and accumulation; `_select_attribute()` logic,
vocabularies and fallback order; M6 memoization semantics; override and boundary
handling (still none). No embeddings, no LLM, no new dependency, no network.

**`N_MAX` stays frozen.** The official FAQ retired the paraphrase risk, which
makes a longer n_max look attractive on D-3 (n8 > n4 by ~0.005 at pool 100).
Changing it now would (a) confound E011 with a second variable — the E007
mistake — and (b) be post-hoc public-set tuning of a preregistered constant.
Open Question 2 does not unfreeze.

### Expected channels — and what would be a warning

Unlike E010, E011 is **not** isolated. Membership changes by construction;
`ask_attribute` changes because `_select_attribute()` scores the final top-10;
the disclosure stream and therefore every later turn changes. HR@10, MRR and
MTTC may all move.

Therefore `invariant_check compare --expect ranking-only` **will FAIL by design
and must not be used as a gate here.** It is a descriptive tool for this
experiment. Run it without `--expect` and report the four channels.

The genuine warning signal is the opposite: **a turn whose top-10 is unchanged
but whose `ask_attribute` changed.** That cannot happen through this mechanism
and would indicate a leak or an unintended edit.

### Performance

Proximity scoring is O(pool x evidence units x n-grams), so a 5x pool is roughly
5x that work. E010 runs 101.4 s; 250-350 s is expected. FAQ §3 confirms the
final evaluation imposes no per-response timeout. **Runtime will be disclosed,
not optimised** — a mid-experiment optimisation would introduce a second
variable. Any optimisation belongs to a separate, later change.

### Procedure (preregistered, in order)

1. This preregistration is committed before implementation.
2. Implement only the three permitted changes.
3. Smoke-test the mechanism, including that the pool is genuinely 50 deep and
   that truncation happens after reranking.
4. `invariant_check dump` + `compare` (no `--expect`), report all four channels.
5. D-3 prescreen at pool 50 for context only — it is not a gate and cannot
   authorise a KEEP.
6. Exactly **one** official evaluator run:
   `python3 -m evaluator.local_evaluator --output results_e011.json`
7. D-5 paired delta vs the tracked E010 per-session snapshot; report the
   migration matrix **before** discussing KEEP/REVERT.

### Decision rule (preregistered)

- **KEEP** if TechnicalScore > 0.743145 **and** D-5 shows no hit->miss cluster.
- **REVERT** if TechnicalScore <= 0.743145, **or** a hit->miss cluster appears
  even alongside a TechnicalScore gain.
- A single isolated hit->miss session is not a cluster; a concentration within
  one scenario bucket is.
- On REVERT, restore E010 and freeze there. **Do not test another pool depth.**
- Either way, E011 is the last capability experiment.

### Interpretation set in advance

- **Success** confirms that E007's negative result was ranker-limited, not
  depth-limited, and that the two-stage retrieve-wide-then-rerank architecture
  needed a ranking signal strong enough to survive the extra noise.
- **Failure** would show that deeper pools hurt even under a proximity ranker —
  meaning the E007 result generalises further than its own narrow reading, and
  that the pool-10 ceiling of 0.7977 is close to the practical limit of this
  architecture. That is a publishable finding for the report either way.

### Deviations from the preregistration

Two, both recorded rather than absorbed.

**1. Step 5 (D-3 pool-50 prescreen) was dropped — human decision, 2026-08-31.**
The preregistered procedure listed a D-3 counterfactual prescreen at pool 50
"for context only". It was skipped as redundant: by that point a full 200-session
replay of the *real* E011 agent had already produced every official metric, which
strictly dominates D-3's fixed-trajectory counterfactual scorer — D-3 holds the
dialogue constant and scores a hypothetical rule over its own unscoped BM25 pool,
whereas the replay exercises the actual agent including the trajectory change that
D-3 cannot model. A D-3 run had been started and was killed mid-execution; it
produced no output. **There is no E011 D-3 number and none may be cited.**

**2. The scoped path's global-BM25 fetch depth was rescaled with the pool.**
Permitted change 1 named `POOL_DEPTH = 50` and capacities 35/15 but did not
mention the global fetch that *sources* the insurance slots, written as
`max(top_k * 5, primary_slots + insurance_slots)` = 50 under E010. `top_k` was
substituted with `POOL_DEPTH` consistently, giving `max(POOL_DEPTH * 5, …)` = 250.

**This is a necessary condition of pool expansion, not an incidental edit.** The
global fetch is a *dependent* quantity of `POOL_DEPTH`, not an independent
parameter, and the arithmetic forces it:

- The primary route occupies up to `PRIMARY_SLOTS = 35` of the 50 pool slots.
- The insurance branch then needs `INSURANCE_SLOTS = 15` global ids **after
  deduplication against primary**.
- When the primary route under-fills (a narrow scope that cannot relax further),
  the backfill branch draws from the same global list and can need up to **50**
  post-dedup ids to bring the pool to `POOL_DEPTH`.

So the global list must be able to yield up to 50 ids *that are not already in
primary*. A 50-deep fetch yields 50 ids **before** dedup, so every id it shares
with the 35-deep primary list is one the pool can no longer reach — in the worst
case it supplies as few as 15. The old value is therefore not merely conservative
at the new depth, it is **structurally insufficient**: retaining it would leave
`POOL_DEPTH` an aspiration rather than a guarantee, with the *actual* depth
varying by how much the category-scoped and global rankings happen to overlap on
a given turn. That is precisely the data-dependent hidden variable that permitted
change 2 exists to prevent, and it would have silently biased against exactly the
narrow-scope sessions pool expansion is meant to help. Scaling the source with the
pool is what makes "the pool is 50 deep" a checkable property — which is why the
preregistration's own step 3 could then verify it (119/119 turns at depth 50).

The change is also monotone, which is why it carries no behavioral risk: a deeper
fetch is identical to a shallower one whenever the shallower one sufficed, and
differs only where the shallower one would have under-filled.

**It was then measured rather than assumed.** Over **224 scoped turns the two
fetch depths produce byte-identical pools** — 0 membership differences, 0 order
differences, 0 under-fills either way. On the public set the 50-deep global list
always had ≥15 ids outside the primary list, so insurance always filled and
backfill never engaged. **The choice therefore had no effect on any E011 number
reported below**; the public set never exercises the case it protects against. It
is recorded as a deviation because the preregistration did not name it, and
explained here because a reader must be able to see that it is entailed by
`POOL_DEPTH = 50` rather than an unexplained third change.

### Implementation

Files changed: `starter/agent.py` only (36 insertions, 15 deletions). No
evaluator, catalog, label, or diagnostic-tool change. SHA-256 moves from
`ec58f9f4…f25e43a1` (E010) to
`cb46d467a114c87ef002613219be45f509e7ecbc292af15858229e1d168d0d92`.

Exactly the three permitted changes:

1. `POOL_DEPTH = 50`; `PRIMARY_SLOTS` 7 → 35, `INSURANCE_SLOTS` 3 → 15 (the 70/30
   ratio held), and the pool-assembly arithmetic retargeted from `top_k` to
   `POOL_DEPTH` — including the backfill bound and the global fetch (see
   Deviation 2).
2. The unscoped path (`detected is None`) retrieves `POOL_DEPTH`, not `top_k`.
3. `ids = self._coverage_rerank(session_id, ids)[:top_k]` — the cut to `top_k`
   now happens **after** the rerank.

Verified untouched by `git diff`: `N_MAX = 4`, `_unit_ngrams()`,
`_proximity_score()`, `_product_stream()` and its cache, the lexicographic sort
key, BM25 field weights, `_terms()`/`STOPWORDS`, the 40-term cap, E003 evidence
admission, category detection and the relaxation ladder, `_select_attribute()`
and its vocabularies, M6 memoization, and override/boundary handling (still none).

**An observed coupling the preregistration did not name.** Asking the *same*
relaxation ladder for 35 primary ids instead of 7 makes it climb more often, so
the "primary" portion of the pool is drawn from a broader category level more
frequently than under E010. Measured over 30 sessions: levels queried `last2` 109,
`last1` 13, `segment` 4, `full` 1, at 1.07 ladder steps per scoped turn. No code
governing relaxation was changed — this is intrinsic to a deeper primary capacity
and inseparable from pool expansion, and is recorded here for completeness.

### Mechanism validation (before the official run)

23 smoke checks, all passing. The two that the preregistration specifically
required:

- **The pool is genuinely 50 deep.** `_coverage_rerank()` received exactly 50
  candidates on **119/119** turns across 30 real sessions; `_relaxed_primary_ids()`
  was asked for 35 on every scoped turn; a crafted unscoped-path message confirmed
  `_unscoped_query(expression, 50)`.
- **Truncation happens after reranking.** On **83/119 turns (70%)** the returned
  top-10 contains at least one id that sat *below* pool rank 10 on entry —
  impossible if the cut preceded the rerank.

Also verified: rerank preserves membership and length; `_select_attribute()`
receives exactly `rerank_out[:top_k]`, never the 50-deep pool; every turn returns
≤10 deduped, valid catalog ids; punctuation-only evidence still returns no
recommendations without crashing; `N_MAX` still 4 and unigrams still excluded.

### Invariant check — descriptive, not a gate

As preregistered, `--expect ranking-only` would FAIL here by construction and was
**not** used as a gate. Run without `--expect`; 200 sessions, 706 comparable turns:

| channel | E010 → E011 |
|---|---|
| candidate membership changed | **633 / 706** |
| order changed (same set) | 0 / 706 |
| `ask_attribute` changed | **248 / 706** |
| target rank changed | 87 / 706 |
| sessions with different `first_hit_turn` | 74 |
| sessions with different turn count | 74 |

`order changed (same set) = 0` is not a null result: on the 73 turns where
membership held, ordering held too, so the whole ranked list was byte-identical
there.

**The genuine warning signal the preregistration named does not occur.** Cross-
tabulating the two channels:

| | ask identical | ask changed |
|---|---|---|
| **top-10 identical** | 73 | **0** ← the leak test |
| **top-10 changed** | 385 | 248 |

Zero turns changed `ask_attribute` while their top-10 stood still. Since
`_select_attribute()` scores only the returned ids, such a turn could not arise
through this mechanism and would have indicated a leak or an unintended edit.
All 248 `ask_attribute` changes sit on turns whose candidate list also moved —
the declared membership → `_select_attribute()` → disclosure → later-turns chain.

### Offline prediction was again exact

The E010 baseline trace reproduced the official E010 result bit-exactly
(TS 0.743145, MRR 0.653149), confirming replay fidelity. On that same replay E011
predicted TS 0.796939 / HR@10 0.930 / MRR 0.625462 / MTTC 3.785 / Eff 0.7215 —
**all five bit-identical to the official run below.**

This is a stronger result than E010's equivalent. E010's prediction was exact
because its trajectory provably could not change; E011's trajectory changes on 74
of 200 sessions, and the replay still matched. That validates R009's replay core
as faithful to `evaluate()` under trajectory divergence, not merely under a frozen
dialogue. It remains a fidelity check, not independent confirmation of the result.

### Evaluation command (exactly one official run)

```bash
python3 -m evaluator.local_evaluator --output results_e011.json
```

### Results

| Metric | E010 | E011 | Delta |
|---|---|---|---|
| HitRate@10 | 0.835000 | **0.930000** | **+0.095000** |
| MRR | 0.653149 | 0.625462 | **−0.027687** |
| MTTC | 4.515 | **3.785** | **−0.730** |
| Efficiency | 0.6485 | 0.7215 | +0.0730 |
| **TechnicalScore** | 0.743145 | **0.796939** | **+0.053794** |

Reported token usage: 0 prompt / 0 completion (no model on the scored path).

Runtime, **disclosed and not optimized** (the preregistration forbade bundling a
performance experiment): official evaluator wall clock 101.4 s → **282.9 s**,
about 2.79x slower, inside the preregistered 250–350 s expectation. The cost is
the proximity scan over a 5x deeper pool plus the corresponding growth in distinct
`_product_stream()` cache misses. FAQ §3 confirms no per-response timeout in the
final evaluation. Any optimization belongs to a separate, separately-recorded
change.

### Scenario metrics

| Scenario | n | HR@10 | Δ | MRR | Δ | MTTC | Δ |
|---|---|---|---|---|---|---|---|
| buying | 80 | 0.9250 | +0.0625 | 0.605670 | −0.049137 | 3.1875 | −0.712 |
| browsing | 80 | 0.9500 | +0.1250 | 0.584430 | −0.023844 | 3.775 | −0.900 |
| intent_override | 30 | 0.866667 | +0.0667 | 0.726706 | −0.009405 | 4.800 | −0.533 |
| boundary | 10 | **1.000000** | +0.2000 | 0.808333 | +0.058333 | 5.600 | −0.100 |

HitRate@10 and MTTC improved in **all four** buckets. MRR fell in three and rose
in boundary. `boundary` reaching 1.0 is n = 10 and cannot support a conclusion.

### D-5 paired session delta

```bash
python3 -m tools.diagnostics.d5_paired_delta \
    docs/diagnostics/E010_SESSIONS.json results_e011.json --show-sessions
```

| Transition | n |
|---|---|
| miss→hit | **19** |
| **hit→miss** | **0** |
| hit→hit rank improved | 3 |
| hit→hit rank regressed | **26** |
| hit→hit unchanged | 138 |
| miss→miss | 14 |

**miss→hit (19).** Rank distribution of the new hits: rank 1 → 4, rank 2 → 1,
rank 3 → 1, rank 4 → 5, rank 5 → 2, rank 7 → 1, rank 8 → 4, rank 9 → 1; mean 4.58,
median 4. Scenario: browsing 10, buying 5, boundary 2, intent_override 2. Only 4
of 19 land at rank 1 and 6 land at ranks 7–9 — these are targets that were outside
the top-10 entirely and are recovered *low*. That shape is why +19 hits buys a
great deal of HitRate@10 and MTTC but little MRR.

**hit→miss: zero.** Not "no cluster" — no session at all, in any bucket, that hit
under E010 misses under E011.

**hit→hit rank movement.**

| | n | mean move | range | Σ RR delta |
|---|---|---|---|---|
| improved | 3 | −2.33 | −3 … −1 | +1.083333 |
| regressed | **26** | **+4.19** | +1 … +9 | **−13.857937** |
| unchanged | 138 | — | — | 0 |

Most common regressions: `1→8` (5), `1→3` (4), `1→2` (4), `2→9` (2), `1→7`,
`2→7`, `1→4`, `6→7` (1 each). The damage is concentrated in rank-1 losses: 11 of
the 26 started at rank 1, and 5 of those fell to rank 8.

### MRR delta decomposition — exact

The only reverse signal in this experiment is the MRR drop, so it is decomposed
rather than described.

| Component | Σ RR delta | Contribution to MRR |
|---|---|---|
| miss→hit | +7.237302 | +0.036187 |
| hit→miss | +0.000000 | +0.000000 |
| hit→hit improved | +1.083333 | +0.005417 |
| **hit→hit regressed** | **−13.857937** | **−0.069290** |
| hit→hit unchanged | 0 | 0 |
| miss→miss | 0 | 0 |
| **TOTAL** | **−5.537302** | **−0.027687** |

Observed MRR delta from the evaluator's own aggregates: −0.027687. Reconstructed
from the 200 per-session outcomes: −0.027687. **Residual 4.9e−10** — the
decomposition is exact, so nothing unaccounted-for is moving MRR.

Gross positive +0.041603, gross negative −0.069290, net −0.027687.

**The entire MRR loss comes from one source: 26 retained hits losing rank. Not one
point of it comes from a lost hit.** A deeper pool injects candidates that outrank
the target under the proximity key — the same noise E007 encountered, except that
under a proximity ranker it costs *rank* rather than costing the *hit*.

**The 26 regressions are uniformly spread, not clustered:**

| Scenario | regressed / n | share of bucket |
|---|---|---|
| boundary | 1 / 10 | 10.0 % |
| browsing | 11 / 80 | 13.8 % |
| buying | 11 / 80 | 13.8 % |
| intent_override | 3 / 30 | 10.0 % |

10.0 / 13.8 / 13.8 / 10.0 % is close to the flattest distribution the data admits.
Whatever transition type the preregistered "concentration within one scenario
bucket" test is applied to, this is its opposite.

### Finding — the bottleneck has moved from recall to ordering, and is now nearly all ordering

At pool 50, HitRate@10 **0.930** stands against D-2's perfect-reranker recall
bound at the same depth, **0.935** — E011 attains **99.5 %** of the candidates
that a pool-50 oracle could ever convert. Candidate availability at this depth is
essentially exhausted.

Decomposing what remains between E011 (TS 0.796939) and the pool-50 oracle
(TS 0.903200), a gap of 0.106261:

| Source of the remaining gap | TS | share |
|---|---|---|
| MRR (0.625462 → 0.935) | 0.092861 | **87.4 %** |
| MTTC (3.785 → 3.240) | 0.010900 | 10.3 % |
| HitRate@10 (0.930 → 0.935) | 0.002500 | 2.4 % |
| total | 0.106261 | 100 % |

**Nearly seven-eighths of everything still available at this pool depth is
ordering, and MTTC — itself a function of how early the target is ranked into the
top-10 — accounts for most of the rest.** Deepening the pool further cannot
address that; only a better ranking rule can. This inverts R009's original
framing: at pool 10 the diagnosis was "ranking, not recall" with recall
nonetheless worth ~1 point; at pool 50 the recall term is worth 0.0025 of
TechnicalScore in total.

### Finding — E010 and E011 are complementary, and their order was load-bearing

| | HitRate@10 | MRR | MTTC | TechnicalScore |
|---|---|---|---|---|
| E010 (rank within a frozen top-10) | +0.000000 | **+0.130570** | +0.000 | +0.039171 |
| E011 (deepen the pool under that ranker) | **+0.095000** | **−0.027687** | **−0.730** | +0.053794 |
| combined vs E006 + M6 | +0.095000 | +0.102883 | −0.730 | +0.092965 |

The two experiments move disjoint metrics and in opposite directions on MRR. E010
was a pure-MRR experiment *by construction* — it reordered exactly the ten ids
that were returned, so it could never move HitRate@10. E011 breaks that ceiling by
letting the same ranker choose from 50, and pays for it by handing back
**21.2 %** of E010's MRR gain (−0.027687 of +0.130570; identically 21.2 % in TS
terms, 0.008306 of 0.039171). It buys HitRate@10 and MTTC with a fifth of the
ranking gain that made the deeper pool survivable in the first place.

**The sequence is now empirically supported, and the reverse sequence is E007.**
E007 deepened the pool 10 → 20 under the binary E004 coverage ranker and regressed
on every overall metric (−0.031). E011 deepened it 10 → 50 under the E010
proximity ranker and gained +0.054. Same architectural move, opposite outcome; the
ranker in between is the difference. This retroactively confirms E007's narrow
stated conclusion — *that* ranker could not exploit a noisier deeper pool — and
refutes the broader reading that deeper retrieval is harmful per se. Ordering
strength is a **precondition** for pool expansion, not an independent axis: the
two must be sequenced rank-first, and E007's failure was a sequencing error rather
than a hypothesis error.

### A gap in the preregistered decision criterion — recorded as a lesson

The KEEP/REVERT gate tested for a **hit→miss cluster**. This run produced zero
hit→miss transitions, so criterion (b) had nothing to bite on. But the run's only
reverse signal — 26 rank regressions worth −0.069290 MRR — is a *different*
phenomenon that the gate does not measure at all. **Satisfying the gate therefore
did not demonstrate the absence of a downside; it demonstrated the absence of the
one downside the gate was written to catch.**

The conclusion is unchanged on this evidence, for two independent reasons:

1. The regressions are uniformly distributed (10.0 / 13.8 / 13.8 / 10.0 % across
   the four buckets), so they fail the preregistered concentration test even if
   that test were applied to rank regressions rather than to hit→miss.
2. The MRR loss is **already priced into TechnicalScore**. Unlike a hidden
   scenario collapse, a rank regression is fully expressed in the 0.30 × MRR term
   the KEEP threshold is measured on. Criterion (a) has therefore already paid for
   it: +0.053794 is the figure net of −0.008306 of MRR damage.

That second point is also the reason the omission was easy to make, and is the
lesson worth carrying: a D-5 gate adds value precisely where the aggregate score
*hides* something. Hit→miss clusters qualify; rank regressions do not, because
MRR already exposes them. The gate was not wrong to focus on hit→miss — it was
incomplete in not saying so, which left "gate passed" looking like "nothing
regressed". A future E-class preregistration should state which regression modes
its gate covers and which are left to the aggregate metric. **The criterion was
not reinterpreted after seeing results; it was applied as written, and this note
records what it did not cover.**

### Regression / bugs

None found. No crash, no contract violation, no invalid or duplicate
`parent_asin`, no change to the returned recommendation count, `top_k` still 10 on
every turn. The only cost is runtime, disclosed above.

### Decision: KEEP

Human decision, 2026-08-31. Both preregistered conditions met:

- (a) TechnicalScore **0.796939 > 0.743145**, by +0.053794.
- (b) No hit→miss cluster — the count is **zero**, not merely unclustered.

New best system: **E011 — Candidate Pool Expansion under a Proximity Reranker**,
running on top of E010 + E006 + M6. Largest single-experiment gain since E003, and
the first experiment since E001 to move HitRate@10 at all. Per-session outcomes
are tracked verbatim as `docs/diagnostics/E011_SESSIONS.json`.

### What this establishes, and what it does not

**Established.** Under a word-order proximity ranker, expanding the internal
candidate pool 10 → 50 and truncating to `top_k` after reranking converts into
+0.095 HitRate@10 and −0.730 MTTC at a cost of −0.027687 MRR, net +0.053794
TechnicalScore, with zero sessions lost. E007's negative result was
**ranker-limited, not depth-limited**: the two-stage retrieve-wide-then-rerank
architecture needed a ranking signal strong enough to survive the extra noise, and
the sequencing rank-first-then-expand is load-bearing.

**Not established.**

- That 50 is the right depth. It was preregistered as a single human-chosen value
  and no other depth was run. D-2 prices pool 100 at a 0.9609 ceiling versus
  0.9032 at pool 50, so measurable headroom remains in this direction — but E011's
  own observed direction is that deepening *costs* MRR, so a deeper pool would not
  redeem that ceiling proportionally. Any further depth needs a new authorized
  preregistration.
- That the 70/30 primary/insurance composition is right at this depth. It was held
  from E001 to avoid a second variable; no other ratio was run.
- That `N_MAX = 4` is optimal. Still frozen, still never swept officially. Open
  Question 2 does not unfreeze, and the FAQ's retirement of paraphrase risk is not
  a licence to tune it.
- That intent override or boundary behavior is solved. Neither received any new
  logic. intent_override remains the weakest bucket at HR@10 0.867, and boundary's
  1.0 is n = 10.
- That the MRR regression is harmless in general. It is priced into
  TechnicalScore on *this* metric set; a deployment weighting top-1 precision more
  heavily would score this trade differently.
- Private-set generalization. n = 200, deterministic evaluator, no variance
  estimate (D-6 unbuilt).

### Next question

None authorized. E011 was preregistered as the last capability experiment, and
under that preregistration a KEEP freezes the algorithm here. The human has
elected not to execute that freeze — see PROJECT_STATE.md, "Human Decision —
Preregistered E011 Freeze Not Executed (2026-08-31)". Algorithm development
remains open, and any further capability experiment requires separate human
authorization and its own preregistration.

The factual position on remaining headroom, stated without recommending anything:
D-2 puts a perfect reranker at pool 100 at TS 0.9609 against 0.9032 at pool 50, so
the depth direction still carries measurable oracle headroom; and 87.4 % of what
remains at pool 50 is ordering, not recall. Those two facts point in different
directions and neither is an experiment authorization.
