"""Experiment invariant checker -- does the code do what the preregistration claims?

Why this exists
---------------
Every recent experiment asserted an isolation property, and the assertion was
checked by hand or not at all:

  * E004/E008 claimed "candidate membership frozen, ordering only".
  * E007 claimed "same retrieval routes, deeper pool" -- but it also silently
    changed the 7/3 reserved-slot split to 14/6, which removed the guaranteed
    global-insurance slots from the returned top-10. That confound was never
    caught, and it makes E007's negative result hard to attribute.

This tool makes such claims mechanically checkable BEFORE the official run, by
comparing two turn-level traces keyed on (sample_id, turn) across four channels:

    candidate membership   -- the SET of returned ids
    recommendation order   -- the ORDERED list of returned ids
    ask_attribute          -- the dialogue trajectory
    target rank            -- where the target landed

A ranking-only experiment must show: membership identical, ask_attribute
identical, order changed. Anything else is a correctness warning first, not an
intended effect.

Runtime agent is NOT modified. See _replay.py for the ground-truth boundary.

Usage
-----
    # on the baseline checkout
    python -m tools.diagnostics.invariant_check dump --out trace_e006.json

    # after applying the candidate change
    python -m tools.diagnostics.invariant_check dump --out trace_e010.json

    python -m tools.diagnostics.invariant_check compare trace_e006.json trace_e010.json
    python -m tools.diagnostics.invariant_check compare a.json b.json --expect ranking-only
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

EXPECTATIONS = {
    # channel -> must be identical (True) / must change somewhere (False) / free (None)
    "ranking-only": {"membership": True, "order": False, "ask": True},
    "clarification-only": {"membership": None, "order": None, "ask": False},
    "identical": {"membership": True, "order": True, "ask": True},
}


def do_dump(args) -> None:
    samples, catalog_ids, categories, products = load_fixtures(
        args.catalog, args.dataset, args.limit
    )
    agent = build_agent(args.catalog)
    traces = [
        t.as_dict()
        for t in replay(samples, catalog_ids, categories, products, agent, probe=None)
    ]
    payload = {"sample_count": len(traces), "traces": traces}
    with open(args.out, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=1)
    turns = sum(len(t["turns"]) for t in traces)
    hits = sum(1 for t in traces if t["hit_turn"] is not None)
    print(f"wrote {args.out}: {len(traces)} sessions, {turns} turns, {hits} hits")


def do_compare(args) -> None:
    with open(args.before, encoding="utf-8") as handle:
        before = {t["sample_id"]: t for t in json.load(handle)["traces"]}
    with open(args.after, encoding="utf-8") as handle:
        after = {t["sample_id"]: t for t in json.load(handle)["traces"]}

    shared = sorted(set(before) & set(after))
    if set(before) != set(after):
        print(f"!! session sets differ ({len(set(before) ^ set(after))} unmatched)")

    counts = {"turns": 0, "membership": 0, "order": 0, "ask": 0, "rank": 0}
    examples: dict[str, list[str]] = {k: [] for k in ("membership", "order", "ask", "rank")}
    hit_turn_changed = []
    turn_count_changed = []

    for sid in shared:
        b, a = before[sid], after[sid]
        if b["hit_turn"] != a["hit_turn"]:
            hit_turn_changed.append(f"{sid} {b['hit_turn']}->{a['hit_turn']}")
        if len(b["turns"]) != len(a["turns"]):
            turn_count_changed.append(f"{sid} {len(b['turns'])}->{len(a['turns'])}")
        for bt, at in zip(b["turns"], a["turns"]):
            counts["turns"] += 1
            tag = f"{sid}#t{bt['turn']}"
            if set(bt["ranked"]) != set(at["ranked"]):
                counts["membership"] += 1
                if len(examples["membership"]) < 5:
                    examples["membership"].append(tag)
            elif bt["ranked"] != at["ranked"]:
                counts["order"] += 1
                if len(examples["order"]) < 5:
                    examples["order"].append(tag)
            if bt["ask_attribute"] != at["ask_attribute"]:
                counts["ask"] += 1
                if len(examples["ask"]) < 5:
                    examples["ask"].append(
                        f"{tag} {bt['ask_attribute']}->{at['ask_attribute']}")
            if bt["target_rank_top10"] != at["target_rank_top10"]:
                counts["rank"] += 1
                if len(examples["rank"]) < 5:
                    examples["rank"].append(
                        f"{tag} {bt['target_rank_top10']}->{at['target_rank_top10']}")

    total = counts["turns"]
    print(f"\n=== Invariant check ({len(shared)} sessions, {total} comparable turns) ===")
    print(f"  candidate membership changed : {counts['membership']:4d} / {total}")
    print(f"  order changed (same set)     : {counts['order']:4d} / {total}")
    print(f"  ask_attribute changed        : {counts['ask']:4d} / {total}")
    print(f"  target rank changed          : {counts['rank']:4d} / {total}")
    print(f"  sessions with different first_hit_turn: {len(hit_turn_changed)}")
    print(f"  sessions with different turn count    : {len(turn_count_changed)}")
    for channel, items in examples.items():
        if items:
            print(f"    e.g. {channel}: {', '.join(items)}")
    if hit_turn_changed[:5]:
        print(f"    e.g. first_hit_turn: {', '.join(hit_turn_changed[:5])}")

    if args.expect:
        rules = EXPECTATIONS[args.expect]
        print(f"\n  Expectation '{args.expect}':")
        ok = True
        for channel, must_be_identical in rules.items():
            observed = counts[channel]
            if must_be_identical is True and observed != 0:
                print(f"    FAIL  {channel} must be identical, but {observed} turns differ")
                ok = False
            elif must_be_identical is False and observed == 0:
                print(f"    FAIL  {channel} was expected to change, but nothing changed "
                      f"-- the mechanism may not be engaging at all")
                ok = False
            else:
                print(f"    ok    {channel}")
        if args.expect == "ranking-only" and hit_turn_changed:
            print(f"    NOTE  {len(hit_turn_changed)} sessions changed first_hit_turn. "
                  f"With frozen membership this is possible only if rank crossed the "
                  f"top-10 boundary -- verify it is intended.")
        print(f"\n  RESULT: {'PASS' if ok else 'FAIL -- investigate before the official run'}")
        raise SystemExit(0 if ok else 1)


def main() -> None:
    parser = argparse.ArgumentParser(description="Experiment invariant checker")
    sub = parser.add_subparsers(dest="cmd", required=True)

    d = sub.add_parser("dump", help="replay and write a turn-level trace")
    d.add_argument("--catalog", default=str(DEFAULT_CATALOG))
    d.add_argument("--dataset", default=str(DEFAULT_DATASET))
    d.add_argument("--limit", type=int, default=None)
    d.add_argument("--out", required=True)
    d.set_defaults(func=do_dump)

    c = sub.add_parser("compare", help="compare two traces channel by channel")
    c.add_argument("before")
    c.add_argument("after")
    c.add_argument("--expect", choices=sorted(EXPECTATIONS), default=None)
    c.set_defaults(func=do_compare)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
