"""D-5 Paired Session Delta -- what actually moved between two official runs?

Question answered
-----------------
A TechnicalScore delta is one scalar over 200 sessions. It cannot distinguish
"a broad small improvement" from "twelve sessions rescued and nine destroyed".
D-5 pairs the two runs session-by-session so a regression cluster cannot hide
behind a favourable mean.

This is the tool that should have gated the E007 and E008 KEEP/REVERT calls, and
it is a required input for every future E-class decision.

Input: two `results.json` files as written by `evaluator.local_evaluator`
(the `sessions` array: sample_id, scenario_type, hit, first_hit_turn, best_rank).
No ground truth or catalog access needed -- it reads evaluator output only.

Usage
-----
Always pass two NAMED snapshots. Do NOT use a bare `results.json` as the before
side: repo-root `results*.json` is gitignored scratch and will silently be
several experiments stale, yielding a wrong-but-plausible transition matrix that
nothing flags. Tracked baselines live in `docs/diagnostics/*_SESSIONS.json` --
see tools/diagnostics/README.md, "Result snapshots".

    python -m evaluator.local_evaluator --output results_myexperiment.json
    python -m tools.diagnostics.d5_paired_delta \
        docs/diagnostics/E010_SESSIONS.json results_myexperiment.json
    python -m tools.diagnostics.d5_paired_delta \
        docs/diagnostics/E006_M6_SESSIONS.json docs/diagnostics/E010_SESSIONS.json \
        --show-sessions
"""
from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict

MISS_TURN = 11
TRANSITIONS = (
    "miss->hit",
    "hit->miss",
    "hit->hit rank improved",
    "hit->hit rank regressed",
    "hit->hit unchanged",
    "miss->miss",
)


def load_sessions(path):
    with open(path, encoding="utf-8") as handle:
        payload = json.load(handle)
    if "sessions" not in payload:
        raise SystemExit(f"{path} has no `sessions` array -- is it an evaluator results.json?")
    return payload, {s["sample_id"]: s for s in payload["sessions"]}


def classify(before, after):
    b_hit, a_hit = bool(before["hit"]), bool(after["hit"])
    if not b_hit and a_hit:
        return "miss->hit"
    if b_hit and not a_hit:
        return "hit->miss"
    if not b_hit and not a_hit:
        return "miss->miss"
    b_rank, a_rank = before["best_rank"], after["best_rank"]
    if a_rank < b_rank:
        return "hit->hit rank improved"
    if a_rank > b_rank:
        return "hit->hit rank regressed"
    return "hit->hit unchanged"


def main() -> None:
    parser = argparse.ArgumentParser(description="D-5 Paired Session Delta")
    parser.add_argument("before")
    parser.add_argument("after")
    parser.add_argument("--show-sessions", action="store_true",
                        help="list the sample_ids in every non-neutral bucket")
    parser.add_argument("--json", dest="json_out", default=None)
    args = parser.parse_args()

    before_payload, before = load_sessions(args.before)
    after_payload, after = load_sessions(args.after)

    only_before = sorted(set(before) - set(after))
    only_after = sorted(set(after) - set(before))
    if only_before or only_after:
        print(f"!! session sets differ: {len(only_before)} only in before, "
              f"{len(only_after)} only in after")
    shared = sorted(set(before) & set(after))

    buckets: dict[str, list[str]] = defaultdict(list)
    per_scenario: dict[str, Counter] = defaultdict(Counter)
    rr_delta = 0.0
    turn_delta = 0.0
    rank_moves = []

    for sid in shared:
        b, a = before[sid], after[sid]
        label = classify(b, a)
        buckets[label].append(sid)
        per_scenario[b["scenario_type"]][label] += 1
        rr_delta += (a["reciprocal_rank"] - b["reciprocal_rank"])
        turn_delta += (
            (a["first_hit_turn"] if a["first_hit_turn"] is not None else MISS_TURN)
            - (b["first_hit_turn"] if b["first_hit_turn"] is not None else MISS_TURN)
        )
        if b["hit"] and a["hit"]:
            rank_moves.append(a["best_rank"] - b["best_rank"])

    n = len(shared)
    print(f"\n=== D-5 Paired Session Delta (n={n}) ===")
    print(f"  before: {args.before}   TS {before_payload.get('recommended_technical_score')}")
    print(f"  after : {args.after}   TS {after_payload.get('recommended_technical_score')}")
    ts_delta = (after_payload.get("recommended_technical_score", 0)
                - before_payload.get("recommended_technical_score", 0))
    print(f"  TechnicalScore delta: {ts_delta:+.6f}\n")

    print("  Transition matrix:")
    for label in TRANSITIONS:
        count = len(buckets[label])
        flag = ""
        if label == "hit->miss" and count:
            flag = "   <<< REGRESSION CLUSTER -- inspect before any KEEP"
        elif label == "hit->hit rank regressed" and count:
            flag = "   <<< MRR loss"
        print(f"    {label:<26} {count:4d}{flag}")

    print(f"\n  aggregate reciprocal-rank delta: {rr_delta:+.6f}  "
          f"(MRR delta {rr_delta / n:+.6f})")
    print(f"  aggregate first-hit-turn delta : {turn_delta:+.1f}  "
          f"(MTTC delta {turn_delta / n:+.4f})")
    if rank_moves:
        improved = sum(1 for m in rank_moves if m < 0)
        regressed = sum(1 for m in rank_moves if m > 0)
        print(f"  among {len(rank_moves)} hit->hit sessions: "
              f"{improved} improved, {regressed} regressed, "
              f"{len(rank_moves) - improved - regressed} unchanged")

    print("\n  Scenario breakdown:")
    for scenario in sorted(per_scenario):
        counts = per_scenario[scenario]
        total = sum(counts.values())
        parts = ", ".join(f"{k.replace('hit->hit ', '')} {v}"
                          for k, v in counts.items() if v)
        print(f"    {scenario:<16} n={total:<4} {parts}")

    if args.show_sessions:
        print("\n  Sessions by bucket:")
        for label in ("miss->hit", "hit->miss", "hit->hit rank improved",
                      "hit->hit rank regressed"):
            if buckets[label]:
                print(f"    {label}: {', '.join(buckets[label])}")

    if args.json_out:
        payload = {
            "sample_count": n,
            "technical_score_delta": round(ts_delta, 6),
            "mrr_delta": round(rr_delta / n, 6),
            "mttc_delta": round(turn_delta / n, 6),
            "transitions": {k: buckets[k] for k in TRANSITIONS},
            "scenario": {k: dict(v) for k, v in per_scenario.items()},
        }
        with open(args.json_out, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=1)
        print(f"\n  wrote {args.json_out}")


if __name__ == "__main__":
    main()
