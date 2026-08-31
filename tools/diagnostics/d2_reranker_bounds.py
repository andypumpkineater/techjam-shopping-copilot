"""D-2 Perfect-Reranker Upper Bound -- how much headroom does ranking hold?

Question answered
-----------------
If an oracle placed the target at rank 1 whenever it is inside a depth-P
candidate pool, what TechnicalScore would the system reach? This converts
"ranking is weak" into a number, and prices candidate-pool depth: the gap
between P=10 and P=100 is exactly what a wider retrieve-then-rerank stage buys.

Two bounds are reported:
  * KEEP-MEMBERSHIP -- perfectly reorder only the 10 ids the agent already
    returns. HR@10 and MTTC are unchanged by construction; only MRR moves.
    This is the headroom available WITHOUT touching candidate generation.
  * POOL DEPTH P -- hit at the first (gated) turn where the target is within
    the agent's own unscoped BM25 top-P, scored at rank 1.

Both honor the intent_override gate: an override session cannot convert before
its override turn (evaluator/local_evaluator.py:234, :252, :259).

These are UPPER BOUNDS, not predictions. No real reranker reaches them.

Runtime agent is NOT modified. See _replay.py for the ground-truth boundary.

Usage
-----
    python -m tools.diagnostics.d2_reranker_bounds
    python -m tools.diagnostics.d2_reranker_bounds --limit 20 --json out.json
"""
from __future__ import annotations

import argparse
import json

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

POOL_DEPTHS = (10, 20, 30, 50, 100, 200)


def main() -> None:
    parser = argparse.ArgumentParser(description="D-2 Perfect-Reranker Upper Bound")
    parser.add_argument("--catalog", default=str(DEFAULT_CATALOG))
    parser.add_argument("--dataset", default=str(DEFAULT_DATASET))
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--json", dest="json_out", default=None)
    args = parser.parse_args()

    samples, catalog_ids, categories, products = load_fixtures(
        args.catalog, args.dataset, args.limit
    )
    agent = build_agent(args.catalog)
    max_depth = max(POOL_DEPTHS)

    def probe(ctx):
        return {"deep_rank": ctx.target_rank_in_pool(max_depth)}

    traces = list(replay(samples, catalog_ids, categories, products, agent, probe))

    # --- observed baseline (the real agent, replayed) ---
    observed = {t.sample_id: (t.hit_turn, t.best_rank) for t in traces}
    baseline = summarize(list(observed.values()))

    # --- bound A: keep the agent's exact membership, order it perfectly ---
    keep_membership = {
        t.sample_id: ((t.hit_turn, 1) if t.hit_turn is not None else (None, None))
        for t in traces
    }
    bound_membership = summarize(list(keep_membership.values()))

    # --- bound B: perfect reranker over a depth-P pool ---
    bounds = {}
    for depth in POOL_DEPTHS:
        outcomes = {}
        for trace in traces:
            turn, _ = first_gated_turn(
                trace,
                lambda rec, d=depth: 1
                if (rec.probe.get("deep_rank") is not None and rec.probe["deep_rank"] <= d)
                else None,
            )
            outcomes[trace.sample_id] = (turn, 1 if turn is not None else None)
        bounds[depth] = {
            "overall": summarize(list(outcomes.values())),
            "scenario": scenario_split(traces, outcomes),
        }

    base_ts = baseline["technical_score"]
    print(f"\n=== D-2 Perfect-Reranker Upper Bound (n={len(traces)}) ===")
    print("Same agent, same evidence stream, same dialogue. Only ordering is oracle.\n")
    header = f"{'bound':<34}{'HR@10':>8}{'MRR':>10}{'MTTC':>8}{'Eff':>8}{'TS':>10}{'vs base':>10}"
    print(header)
    print("-" * len(header))

    def row(label, summary):
        delta = summary["technical_score"] - base_ts
        print(
            f"{label:<34}{summary['hit_rate_at_10']:>8.4f}{summary['mrr']:>10.6f}"
            f"{summary['mttc']:>8.3f}{summary['efficiency']:>8.4f}"
            f"{summary['technical_score']:>10.6f}{delta:>+10.4f}"
        )

    row("observed agent (replayed)", baseline)
    row("perfect order, current top-10", bound_membership)
    for depth in POOL_DEPTHS:
        row(f"perfect reranker, pool depth {depth}", bounds[depth]["overall"])

    print("\n  Scenario breakdown at pool depth 100:")
    for name, summary in bounds[100]["scenario"].items():
        print(
            f"    {name:<16} n={summary['sample_count']:<4} "
            f"HR {summary['hit_rate_at_10']:.4f}  MRR {summary['mrr']:.6f}  "
            f"MTTC {summary['mttc']:.3f}"
        )

    if args.json_out:
        payload = {
            "sample_count": len(traces),
            "observed_baseline": baseline,
            "bound_keep_membership_perfect_order": bound_membership,
            "bounds_by_pool_depth": {
                str(d): bounds[d]["overall"] for d in POOL_DEPTHS
            },
            "scenario_at_depth_100": bounds[100]["scenario"],
        }
        with open(args.json_out, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=1)
        print(f"\n  wrote {args.json_out}")


if __name__ == "__main__":
    main()
