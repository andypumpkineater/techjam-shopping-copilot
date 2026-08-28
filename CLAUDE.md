# Project
TikTok TechJam 2026 Track 4 — Conversational E-Commerce Search.

# Primary Objective
Improve the official TechnicalScore while producing a coherent, reproducible, rule-compliant shopping agent.

# Official Metrics

```text
HitRate@10 = successful sessions / N
MRR        = sum(1 / target_rank, misses = 0) / N
MTTC       = mean(first_hit_turn, misses = 11)
Efficiency = clip((11 - MTTC) / 10, 0, 1)
TechnicalScore = 0.50 * HitRate@10 + 0.30 * MRR + 0.20 * Efficiency
```

A hit requires exact `parent_asin` equality within the first 10 valid, deduped
recommendations. TechnicalScore is computed on aggregate MTTC, not per-scenario.
Scenario metrics (buying / browsing / intent_override / boundary) are reported
separately for HitRate@10, MRR, and MTTC only — no separate scenario Efficiency
or TechnicalScore.

# Hard Safety Rules

- Never modify evaluator code.
- Never modify public labels.
- Never modify the frozen catalog.
- Never read `ground_truth` or hidden target labels from Agent code.
- Never exploit leaked labels.
- Never commit API keys or secrets.
- Only recommend valid catalog `parent_asin` values.
- Respect the 10-turn protocol.
- Do not assume final judging has network access.
- Report model/token/cost information honestly.

# Engineering Rules

- Understand before modifying.
- Prefer small measurable experiments.
- One major hypothesis per experiment.
- Run the official evaluator after meaningful algorithmic changes.
- Compare against current best metrics.
- Check `git status` and `git diff` after Agent work.
- No major refactor without a plan.
- No new dependency without justification.
- Prefer reproducible/offline approaches when competitive.
- Never claim improvement without evaluator evidence.

# File Boundaries

- `starter/agent.py` and our new helper modules may be modified.
- `evaluator/`, the frozen catalog, and public labels must remain untouched.
- Our own docs/tests/helper modules may be added.

# Standard Experiment Loop

PLAN → IMPLEMENT → EVALUATE → RECORD → KEEP or REVERT

# Experiment Report Format

```text
Experiment ID
Hypothesis
Files Changed
Implementation
Evaluation Command
HitRate@10
MRR
MTTC
Efficiency
TechnicalScore
Scenario Metrics
Regression / Bugs
Decision: KEEP / REVERT
Next Question
```

See `PROJECT_STATE.md` for current status and `EXPERIMENTS.md` for the experiment log.
