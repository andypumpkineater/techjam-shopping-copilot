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
