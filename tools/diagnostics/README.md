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
| `d012_paraphrase_stress.py` | **CANCELLED — built, never run, no citable result.** Does a ranking rule's *advantage* survive reworded user messages? |

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
#   Always pass two NAMED snapshots. See "Result snapshots" below.
python3 -m evaluator.local_evaluator --output results_myexperiment.json
python3 -m tools.diagnostics.d5_paired_delta \
    docs/diagnostics/E011_SESSIONS.json results_myexperiment.json --show-sessions

# D012  paraphrase stress -- CANCELLED, see "D012 discipline" below before running
python3 -m tools.diagnostics.d012_paraphrase_stress --limit 20          # smoke
python3 -m tools.diagnostics.d012_paraphrase_stress \
    --json docs/diagnostics/D012_PARAPHRASE_STRESS.json

# invariant check for a ranking-only experiment
python3 -m tools.diagnostics.invariant_check dump --out trace_before.json
#   ... apply the candidate change ...
python3 -m tools.diagnostics.invariant_check dump --out trace_after.json
python3 -m tools.diagnostics.invariant_check compare \
    trace_before.json trace_after.json --expect ranking-only
```

Each tool accepts `--limit N` for a fast smoke run and `--json PATH` to persist
machine-readable output.

## Result snapshots — never use a bare `results.json` as a baseline

D-5 is a required input for every E-class KEEP/REVERT decision, so its *before*
side must be reproducible. Two rules:

1. **Working evaluator output is scratch.** Every `results*.json` in the repo
   root is gitignored and carries no meaning beyond "whatever I ran last". A
   file named `results.json` will silently be several experiments stale, and a
   D-5 run against it produces a wrong-but-plausible transition matrix that
   nothing will flag.
2. **Authoritative per-session outcomes are named and tracked**, under
   `docs/diagnostics/`:

   | Snapshot | Agent |
   |---|---|
   | `E006_M6_SESSIONS.json` | E006 + M6 (TS 0.703974) |
   | `E010_SESSIONS.json` | E010 (TS 0.743145) |
   | `E011_SESSIONS.json` | E011 (TS 0.796939) |
   | `E012_SESSIONS.json` | E012 (TS 0.818056) |
   | `E013_SESSIONS.json` | E013, current best (TS 0.839920) |

   These are the evaluator's own output, committed verbatim and never
   hand-edited. Each holds the 200-entry `sessions` array D-5 needs.
   Add one per KEEP; a REVERTED experiment does not earn a snapshot.

Ground-truth boundary: a `sessions` entry contains only `sample_id`,
`scenario_type`, `hit`, `first_hit_turn`, `best_rank`, and `reciprocal_rank`
— no target id, no `ground_truth`, no catalog ASIN of any kind. These files are
strictly less sensitive than the aggregate scores already published in
`EXPERIMENTS.md`.

Note that `E006_M6_BASELINE.json` is a different artifact: it holds R009's
curated aggregate metrics and diagnostic tables, and has **no** `sessions`
array, so D-5 cannot run against it.

## D012 discipline -- CANCELLED, and the rewriter is frozen

**D012 was cancelled on 2026-08-31 and has no result.** The official FAQ
(`docs/final_evaluation_faq.md`, upstream `9c9e7c9`) states in section 1 that the
final 800-sample evaluation uses the same deterministic customer-message
templates as the published evaluator, and that "No undisclosed natural-language
paraphrases are introduced." That falsifies the one assumption D012 exists to
test, so the risk it measures does not exist in the final evaluation.

The tool was built and its invariants are tested, but it was **never run to a
result**: only a 20-session smoke run and a sweep aborted after 5 of 12
configurations, neither recorded. **No number it produces may be cited.** The
"Results" section of `EXPERIMENTS.md`'s D012 entry is empty on purpose. Running it
requires new human authorization and a fresh reading of the FAQ. The rest of this
section documents the discipline that would apply if it ever is run.

`_paraphrase.py` is the one component of D012 that could fabricate its own
conclusion: a rewrite rule chosen to be unusually kind or unusually cruel to one
scorer decides the answer before any session is replayed. Two rules hold it:

1. **Every family, constant, and word list was written into `EXPERIMENTS.md`
   ("D012 -- Paraphrase Stress") and committed *before* `_paraphrase.py`
   existed.** None of it may be retuned after seeing a result. A family that
   produces an uninteresting curve is a reported result, not a reason to retune.
2. **The a priori bias of each family is declared in that same preregistration.**
   Every content family is structurally harder on a contiguous-n-gram rule than on
   a binary per-unit bag-of-words rule, and `shuffle` and `filler` are
   bag-of-words-neutral *by construction*. D012 is therefore biased against the
   phrase rule on purpose, which is exactly why its verdict reads the surviving
   advantage `A(r) = TS(phrase_n4) - TS(cov)` rather than raw degradation.

The rewriter receives `(message, sample_id, turn)` and nothing else -- no sample,
no product, no target, no catalog handle -- and satisfies a runtime-checked
vocabulary-closure invariant:

    _terms(out) subset-of  _terms(in) | FILLER | {t+"s", t[:-1] for t in _terms(in)}

so it cannot introduce information the user's own message did not already carry.
That is the structural reason it cannot become a ground-truth channel.

Read two limits with any D012 result. It is *mechanical perturbation* (order,
morphology, omission, hedging), not semantic paraphrase -- no offline
paraphraser is available under the no-network / no-new-dependency constraints, so
synonym substitution is out of scope. And `cov`'s flat response is **saturation**,
not bag-of-words virtue: it credits a unit whenever the candidate shares one token
with it, so it has little dynamic range to lose under any perturbation.

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
