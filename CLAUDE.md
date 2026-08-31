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

# Reference Document Hierarchy

- Authoritative / executable spec (source of truth for scoring and interface
  behavior), by what each document governs:
  - `docs/competition_specification.md` — the task, the evaluation protocol,
    and the system contract.
  - `docs/final_evaluation_faq.md` — the final-evaluation process, code freeze,
    network / API / credential policy, hardware and runtime expectations, data
    and derived-artifact policy, and submission / judging clarifications.
  - `docs/agent_api_contract.json` — the machine-readable Agent interface.
  - `docs/evaluation_config.json` — the scoring configuration.
  - `evaluator/local_evaluator.py` — the executable semantics of the published
    evaluator. When in doubt about scoring or interface behavior, the
    evaluator code wins.
- Where `docs/final_evaluation_faq.md` explicitly covers a final-evaluation
  matter, it supersedes earlier submission or process wording elsewhere in the
  documentation set. That precedence is limited to the matters the FAQ actually
  covers and does not extend beyond them.
- `docs/sources/TRACK4_PROBLEM_STATEMENT.md` is a vision-level problem
  statement (directional goals: dual-track routing, hybrid/LLM semantic
  ranking, dynamic context programming, etc.). It is **not** an executable
  spec and does not define scoring. Its "Coverage / Precision / Efficiency"
  language maps loosely to HitRate@10 / MRR / MTTC but is not a formula
  source — use the Official Metrics section above instead.
- If the two documents appear to disagree, the operational spec + evaluator
  behavior always take precedence for anything affecting `TechnicalScore`.
  Treat the problem statement only as design inspiration for architecture
  and direction, never as a scoring or interface reference.

# Hard Safety Rules

- Never modify evaluator code.
- Never modify public labels.
- Never modify the frozen catalog.
- Never read `ground_truth` or hidden target labels from Agent code.
- Never exploit leaked labels.
- Never commit API keys or secrets.
- Only recommend valid catalog `parent_asin` values.
- Respect the 10-turn protocol.
- Final evaluation permits network access and external APIs per
  `docs/final_evaluation_faq.md` §2. Our final scored path deliberately
  remains offline, stdlib-only, deterministic, and model-free as a design
  choice, not as an organizer-imposed restriction.
- Report model/token/cost information honestly.
- Never hard-code public sample IDs, target mappings, evaluator-generated hidden fields, or public-set-specific simulator behavior to inflate local scores.

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
- Never commit or push unless explicitly instructed by the human.
- For read-only tasks, the expected result is zero repository diff; verify with `git status` and `git diff`.

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
