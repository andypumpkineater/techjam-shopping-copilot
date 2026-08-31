"""D-3 Counterfactual Reranker Bench -- falsify a ranking hypothesis offline.

=============================================================================
DISCIPLINE -- THIS IS A FALSIFICATION TOOL, NOT AN OPTIMIZER
=============================================================================
D-3 exists so that a ranking hypothesis can be REJECTED in minutes instead of
consuming a full official-evaluator experiment slot (E007 and E008 each burned
one to learn a single scalar).

It must NOT be used to:
  * sweep weights, thresholds, or n-gram lengths in bulk;
  * try many variants and keep whichever tops the 200 public sessions;
  * hill-climb the public set in leaderboard style.

That is public-set overfitting with extra steps, and it would not show up as a
local regression -- which is exactly what makes it dangerous. The scorer
registry below is CLOSED: it contains only rules that were already run and
reported in the 2026-08-31 architecture audit. Adding a scorer is a deliberate
act that belongs to a preregistered hypothesis, not to a tuning session.

A D-3 result never establishes that a change works. It can establish that a
change is NOT worth an official run. Only an E-class experiment against the
official evaluator can support a KEEP.
=============================================================================

What it measures
----------------
Same agent, same evidence stream, same dialogue trajectory, same candidate pool.
Only the final top-10 selection/ordering rule changes. A session "hits" at the
first gated turn where the rule places the target in the top 10.

Known conservative bias: the replay stops when the real agent hits, so a rule is
never credited for turns the real agent never played. See _replay.py.

Runtime agent is NOT modified. See _replay.py for the ground-truth boundary.

Usage
-----
    python -m tools.diagnostics.d3_counterfactual_bench
    python -m tools.diagnostics.d3_counterfactual_bench --pool 60 --scorers phrase_n2,phrase_n3,phrase_n4,phrase_n8
    python -m tools.diagnostics.d3_counterfactual_bench --limit 20 --json out.json
"""
from __future__ import annotations

import argparse
import json
import math
from collections import Counter

from starter.agent import _terms, _text
from tools.diagnostics._replay import (
    DEFAULT_CATALOG,
    DEFAULT_DATASET,
    build_agent,
    first_gated_turn,
    load_fixtures,
    replay,
    scenario_split,
    summarize,
)

CATALOG_FIELDS = ("title", "categories", "features", "details", "store", "description")


# ---------------------------------------------------------------- global IDF
def build_global_idf(catalog_path):
    """Document frequency over the full 50k catalog (E008 used a CANDIDATE-LOCAL
    IDF instead; this is the global variant, which the audit measured separately)."""
    df: Counter[str] = Counter()
    total = 0
    with open(catalog_path, encoding="utf-8") as handle:
        for line in handle:
            product = json.loads(line)
            total += 1
            for term in frozenset(
                _terms(" ".join(_text(product.get(f)) for f in CATALOG_FIELDS))
            ):
                df[term] += 1
    idf = {t: math.log((total + 1) / (c + 1)) + 1 for t, c in df.items()}
    return idf, math.log(total + 1) + 1


# ---------------------------------------------------------------- phrase text
def normalized_text(agent, parent_asin, cache):
    """Product text as a padded token stream, so an n-gram test is a substring
    test with word boundaries."""
    if parent_asin not in cache:
        row = agent.connection.execute(
            "SELECT title, categories, features, details, store, description "
            "FROM products WHERE parent_asin = ?",
            (parent_asin,),
        ).fetchone()
        cache[parent_asin] = (
            " " + " ".join(_terms(" ".join(str(v) for v in row))) + " " if row else " "
        )
    return cache[parent_asin]


def ngrams(tokens, n_max):
    """Contiguous n-grams, longest first, so the first hit is the longest match."""
    out = []
    for n in range(min(n_max, len(tokens)), 1, -1):
        for i in range(len(tokens) - n + 1):
            out.append((n, " " + " ".join(tokens[i:i + n]) + " "))
    return out


# ---------------------------------------------------------------- the registry
# CLOSED SET -- every entry was run and reported in the 2026-08-31 audit.
def _make_scorers():
    def cov(state):
        return lambda p: sum(1 for u in state["units"] if state["pt"][p] & u)

    def frac(state):
        return lambda p: sum(len(state["pt"][p] & u) / len(u) for u in state["units"])

    def gidf(state):
        idf, default = state["idf"], state["idf_default"]
        ev = state["ev"]
        return lambda p: sum(idf.get(t, default) for t in (state["pt"][p] & ev))

    def full(state):
        return lambda p: sum(1 for u in state["units"] if u <= state["pt"][p])

    def cov_gidf(state):
        c, g = cov(state), gidf(state)
        return lambda p: (c(p), g(p))

    def full_frac(state):
        f, r = full(state), frac(state)
        return lambda p: (f(p), r(p))

    def phrase(n_max):
        def factory(state):
            grams = [ngrams(u, n_max) for u in state["unit_tokens"]]

            def score(p):
                text = state["text"](p)
                total = 0
                for gs in grams:
                    best = 0
                    for n, g in gs:
                        if n <= best:
                            break
                        if g in text:
                            best = n
                            break
                    total += best
                return total

            return score

        return factory

    return {
        "bm25": None,  # pool order as-is
        "cov": cov,
        "frac": frac,
        "gidf": gidf,
        "full": full,
        "cov+gidf": cov_gidf,
        "full+frac": full_frac,
        "phrase_n2": phrase(2),
        "phrase_n3": phrase(3),
        "phrase_n4": phrase(4),
        "phrase_n8": phrase(8),
    }


SCORERS = _make_scorers()
NEEDS_IDF = {"gidf", "cov+gidf"}
NEEDS_TEXT = {"phrase_n2", "phrase_n3", "phrase_n4", "phrase_n8"}


def _negate(value):
    return tuple(-v for v in value) if isinstance(value, tuple) else -value


def main() -> None:
    parser = argparse.ArgumentParser(description="D-3 Counterfactual Reranker Bench")
    parser.add_argument("--catalog", default=str(DEFAULT_CATALOG))
    parser.add_argument("--dataset", default=str(DEFAULT_DATASET))
    parser.add_argument("--pool", type=int, default=100, help="candidate pool depth")
    parser.add_argument(
        "--scorers",
        default=",".join(SCORERS),
        help=f"comma-separated subset of the CLOSED registry: {','.join(SCORERS)}",
    )
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--json", dest="json_out", default=None)
    args = parser.parse_args()

    selected = [s.strip() for s in args.scorers.split(",") if s.strip()]
    unknown = [s for s in selected if s not in SCORERS]
    if unknown:
        raise SystemExit(
            f"unknown scorer(s) {unknown}. The registry is intentionally closed; "
            f"available: {', '.join(SCORERS)}. Adding one belongs to a "
            f"preregistered hypothesis, not to a tuning session."
        )

    samples, catalog_ids, categories, products = load_fixtures(
        args.catalog, args.dataset, args.limit
    )
    agent = build_agent(args.catalog)

    idf, idf_default = ({}, 0.0)
    if any(s in NEEDS_IDF for s in selected):
        print("  building global catalog IDF ...", flush=True)
        idf, idf_default = build_global_idf(args.catalog)
    text_cache: dict[str, str] = {}

    def probe(ctx):
        pool = ctx.pool(args.pool)
        result = {"pool_rank": (pool.index(ctx.target) + 1) if ctx.target in pool else None}
        if ctx.target not in pool:
            return result
        units = ctx.evidence_units()
        state = {
            "units": units,
            "unit_tokens": [_terms(m) for m in ctx.messages if _terms(m)],
            "ev": frozenset().union(*units) if units else frozenset(),
            "pt": {p: ctx.product_terms(p) for p in pool},
            "idf": idf,
            "idf_default": idf_default,
            "text": lambda p: normalized_text(ctx.agent, p, text_cache),
        }
        for name in selected:
            if name == "bm25":
                result["r_bm25"] = result["pool_rank"]
                continue
            score = SCORERS[name](state)
            order = sorted(range(len(pool)), key=lambda i: _negate(score(pool[i])))
            result["r_" + name] = [pool[i] for i in order].index(ctx.target) + 1
        return result

    traces = list(replay(samples, catalog_ids, categories, products, agent, probe))

    observed = {t.sample_id: (t.hit_turn, t.best_rank) for t in traces}
    baseline = summarize(list(observed.values()))
    base_ts = baseline["technical_score"]

    results = {}
    for name in selected:
        key = "r_" + name
        outcomes = {}
        for trace in traces:
            turn, rank = first_gated_turn(
                trace,
                lambda rec, k=key: rec.probe[k]
                if (rec.probe.get(k) is not None and rec.probe[k] <= 10)
                else None,
            )
            outcomes[trace.sample_id] = (turn, rank)
        results[name] = {
            "overall": summarize(list(outcomes.values())),
            "scenario": scenario_split(traces, outcomes),
        }

    print(f"\n=== D-3 Counterfactual Reranker Bench (n={len(traces)}, pool depth {args.pool}) ===")
    print("Same evidence stream and dialogue; only the top-10 selection rule differs.")
    print("Override-gated. UPPER-BOUND-FREE: these are real rules, not oracles.\n")
    header = f"{'scorer':<14}{'HR@10':>8}{'MRR':>10}{'MTTC':>8}{'Eff':>8}{'TS':>10}{'vs base':>10}"
    print(header)
    print("-" * len(header))
    print(
        f"{'[observed]':<14}{baseline['hit_rate_at_10']:>8.4f}{baseline['mrr']:>10.6f}"
        f"{baseline['mttc']:>8.3f}{baseline['efficiency']:>8.4f}{base_ts:>10.6f}"
        f"{0.0:>+10.4f}"
    )
    for name in selected:
        s = results[name]["overall"]
        print(
            f"{name:<14}{s['hit_rate_at_10']:>8.4f}{s['mrr']:>10.6f}{s['mttc']:>8.3f}"
            f"{s['efficiency']:>8.4f}{s['technical_score']:>10.6f}"
            f"{s['technical_score'] - base_ts:>+10.4f}"
        )

    print("\n  Reminder: a positive delta here is a reason to PREREGISTER an "
          "experiment,\n  never a reason to claim an improvement.")

    if args.json_out:
        payload = {
            "sample_count": len(traces),
            "pool_depth": args.pool,
            "observed_baseline": baseline,
            "scorers": {n: results[n]["overall"] for n in selected},
            "scenario": {n: results[n]["scenario"] for n in selected},
        }
        with open(args.json_out, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=1)
        print(f"\n  wrote {args.json_out}")


if __name__ == "__main__":
    main()
