# Offline Diagnostics (R009)

Read-only analysis tooling. **Nothing here runs on the scored path.** These
scripts exist so that a hypothesis can be rejected in minutes instead of
consuming an official-evaluator experiment slot.

## Ground truth boundary — non-negotiable

These scripts read `ground_truth` from `data/public_set.jsonl` and re-derive the
evaluator's hidden intent cards, because that is what offline error analysis
requires. `CLAUDE.md` permits exactly this and forbids the converse.

`ground_truth`, hidden intent cards, target ids, and anything derived from them
must **never** reach:

- `starter/agent.py`
- runtime query construction
- runtime ranking
- runtime clarification
- runtime session state
- any runtime lookup table or mapping

How the boundary is held in code: the `Agent` is driven **only** through its
public contract — `reset(session_id, user_profile)` and
`respond(session_id, user_message, turn, top_k)` — with user messages produced by
the published simulator. The target id is used solely to *locate* the target in
a result list **after** the agent has already answered. The agent never receives
it, directly or indirectly.

Two read-only couplings to agent internals are deliberate and documented in
`_replay.py`: reading `Agent._sessions[session_id]` to reconstruct the exact
query the agent built, and reading `Agent._product_terms()`. Both raise loudly if
the agent's shape changes, rather than silently reporting different numbers.
`verify_agent_bm25_weights()` likewise fails if `starter/agent.py` stops using
the BM25 weighting the diagnostics reconstruct.

## Tools

| Tool | Question it answers |
|---|---|
| `d1_candidate_oracle.py` | Is the bottleneck candidate **recall** or **ranking**? |
| `d2_reranker_bounds.py` | How much TechnicalScore headroom does ranking hold, per pool depth? |
| `d3_counterfactual_bench.py` | Would this ranking rule have helped — without spending an official run? |
| `d5_paired_delta.py` | What actually moved between two official runs, session by session? |
| `invariant_check.py` | Did the code really change only what the preregistration claimed? |

`_replay.py` is the shared session-replay core. All of D-1/D-2/D-3 and the
invariant checker use it, so a change there affects every diagnostic
consistently — that is the point. Four private copies would drift, and a drifted
replay silently invalidates cross-diagnostic comparison.

## Commands

Run from the repository root. Standard library only; no new dependency.

```bash
# D-1  candidate recall vs ranking
python3 -m tools.diagnostics.d1_candidate_oracle
python3 -m tools.diagnostics.d1_candidate_oracle --limit 20 --depth 200

# D-2  ranking headroom / oracle upper bounds
python3 -m tools.diagnostics.d2_reranker_bounds

# D-3  counterfactual reranker bench (CLOSED scorer registry — see below)
python3 -m tools.diagnostics.d3_counterfactual_bench
python3 -m tools.diagnostics.d3_counterfactual_bench --pool 60 \
    --scorers phrase_n2,phrase_n3,phrase_n4,phrase_n8

# D-5  paired session delta between two official runs
python3 -m evaluator.local_evaluator --output results_before.json
python3 -m evaluator.local_evaluator --output results_after.json
python3 -m tools.diagnostics.d5_paired_delta results_before.json results_after.json \
    --show-sessions

# invariant check for a ranking-only experiment
python3 -m tools.diagnostics.invariant_check dump --out trace_before.json
#   ... apply the candidate change ...
python3 -m tools.diagnostics.invariant_check dump --out trace_after.json
python3 -m tools.diagnostics.invariant_check compare \
    trace_before.json trace_after.json --expect ranking-only
```

Each tool accepts `--limit N` for a fast smoke run and `--json PATH` to persist
machine-readable output.

## D-3 discipline

**D-3 is a falsification tool, not an optimizer.** Its scorer registry is
deliberately *closed*: it contains only rules that were already run and reported
in the 2026-08-31 architecture audit. Passing an unregistered name is an error,
by design.

Do not use it to sweep weights or n-gram lengths in bulk, to try many variants
and keep whichever tops the 200 public sessions, or to hill-climb the public set.
That is public-set overfitting with extra steps, and — unlike an ordinary bug —
it would not show up as a local regression, which is what makes it dangerous.

A positive D-3 delta is a reason to **preregister an experiment**. It is never
itself evidence of an improvement. Only an E-class run against the official
evaluator can support a KEEP.

## Known conservative bias

The replay stops when the *real* agent hits, exactly as the evaluator does. Turns
after that are never played, so a counterfactual rule is never credited for a
turn the real agent did not reach. This biases counterfactual scores **downward**
— the safe direction.

Do not "fix" this by playing extra turns: the disclosure stream depends on the
agent's own `ask_attribute` choices, so under a different ranking those turns
would not have existed either.

## What a diagnostic result is and is not

- A diagnostic **can** establish that a change is not worth an official run.
- A diagnostic **cannot** establish that a change works.
- Diagnostic evidence and runtime-experiment evidence are recorded separately in
  `EXPERIMENTS.md` and must never be conflated.
