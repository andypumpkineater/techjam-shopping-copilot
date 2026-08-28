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


Next:
No experiment selected yet.
System design has not started.
