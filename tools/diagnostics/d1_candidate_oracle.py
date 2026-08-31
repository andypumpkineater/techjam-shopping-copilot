"""D-1 Candidate Oracle -- is the bottleneck candidate recall, or ranking?

Question answered
-----------------
Using the agent's OWN accumulated query, how deep does one have to look in the
unscoped BM25 ranking before the target appears? If Recall@100 is high while
HR@10 is much lower, the target is reachable and the loss is in RANKING, not in
candidate generation -- which rules out an entire class of proposed work
(extra retrieval routes, synonym expansion, dense retrieval).

Metric definition
-----------------
For each session, the best (smallest) deep rank the target attains at ANY turn
the real agent played. Recall@N = fraction of sessions whose best deep rank <= N.
This is an upper bound on what any reranker restricted to a depth-N pool over
this query stream could achieve.

Runtime agent is NOT modified. See _replay.py for the ground-truth boundary.

Usage
-----
    python -m tools.diagnostics.d1_candidate_oracle
    python -m tools.diagnostics.d1_candidate_oracle --limit 20 --depth 200
    python -m tools.diagnostics.d1_candidate_oracle --json out.json
"""
from __future__ import annotations

import argparse
import json

from tools.diagnostics._replay import (
    DEFAULT_CATALOG,
    DEFAULT_DATASET,
    build_agent,
    load_fixtures,
    replay,
)

DEPTHS = (10, 20, 50, 100, 200, 500)


def main() -> None:
    parser = argparse.ArgumentParser(description="D-1 Candidate Oracle")
    parser.add_argument("--catalog", default=str(DEFAULT_CATALOG))
    parser.add_argument("--dataset", default=str(DEFAULT_DATASET))
    parser.add_argument("--depth", type=int, default=1000, help="deep probe depth")
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--json", dest="json_out", default=None)
    args = parser.parse_args()

    samples, catalog_ids, categories, products = load_fixtures(
        args.catalog, args.dataset, args.limit
    )
    agent = build_agent(args.catalog)

    def probe(ctx):
        return {"deep_rank": ctx.target_rank_in_pool(args.depth)}

    traces = list(replay(samples, catalog_ids, categories, products, agent, probe))
    n = len(traces)

    best: dict[str, int | None] = {}
    for trace in traces:
        ranks = [
            t.probe["deep_rank"] for t in trace.turns if t.probe.get("deep_rank") is not None
        ]
        best[trace.sample_id] = min(ranks) if ranks else None

    def reachable(depth: int) -> int:
        return sum(1 for v in best.values() if v is not None and v <= depth)

    recall = {d: reachable(d) / n for d in DEPTHS if d <= args.depth}

    print(f"\n=== D-1 Candidate Oracle (n={n}, probe depth {args.depth}) ===")
    print("Best deep BM25 rank of the target over the session, agent's own query.\n")
    buckets = [("1", 1, 1), ("2-3", 2, 3), ("4-10", 4, 10), ("11-20", 11, 20),
               ("21-50", 21, 50), ("51-100", 51, 100), (f"101-{args.depth}", 101, args.depth)]
    cumulative = 0
    for label, low, high in buckets:
        count = sum(1 for v in best.values() if v is not None and low <= v <= high)
        cumulative += count
        print(f"  {label:>12}  {count:4d}   cum {cumulative:4d} ({cumulative / n:.3f})")
    unreachable = sum(1 for v in best.values() if v is None)
    print(f"  {'>' + str(args.depth):>12}  {unreachable:4d}")

    print("\n  Recall@N (target reachable within top-N at some turn):")
    for depth, value in recall.items():
        print(f"    Recall@{depth:<5d} = {value:.3f}  ({reachable(depth)}/{n})")

    hits = [t for t in traces if t.hit_turn is not None]
    misses = [t for t in traces if t.hit_turn is None]
    print(f"\n  agent hits {len(hits)}/{n}, misses {len(misses)}/{n}")
    if misses:
        edges = [(10, "<=10"), (50, "11-50"), (200, "51-200")]
        edges = [(hi, label) for hi, label in edges if hi < args.depth]
        edges.append((args.depth, f"<= {args.depth}" if not edges
                      else f"{edges[-1][0] + 1}-{args.depth}"))
        band = {label: 0 for _, label in edges}
        band["unreachable"] = 0
        for trace in misses:
            v = best[trace.sample_id]
            if v is None:
                band["unreachable"] += 1
                continue
            for hi, label in edges:
                if v <= hi:
                    band[label] += 1
                    break
        print(f"  miss sessions by best deep rank: {band}")
    improvable = sum(
        1 for t in hits
        if best[t.sample_id] is not None and t.best_rank is not None
        and best[t.sample_id] < t.best_rank
    )
    print(f"  hits where a better deep rank existed at some turn: {improvable}/{len(hits)}")

    if args.json_out:
        payload = {
            "sample_count": n,
            "probe_depth": args.depth,
            "recall_at": {str(d): round(v, 6) for d, v in recall.items()},
            "best_deep_rank": best,
            "agent_hits": len(hits),
        }
        with open(args.json_out, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=1)
        print(f"\n  wrote {args.json_out}")


if __name__ == "__main__":
    main()
