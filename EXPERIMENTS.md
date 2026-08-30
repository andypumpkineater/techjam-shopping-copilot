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
