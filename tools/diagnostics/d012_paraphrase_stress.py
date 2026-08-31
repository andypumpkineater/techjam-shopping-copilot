"""
###############################################################################
# BUILT BUT NEVER EXECUTED -- DO NOT QUOTE ANY NUMBER FROM THIS TOOL
###############################################################################
# D012 was CANCELLED on 2026-08-31 before it was ever run to a result. The
# official FAQ (docs/final_evaluation_faq.md, upstream 9c9e7c9) states in section
# 1 that the final 800-sample evaluation uses the same deterministic
# customer-message templates as the published evaluator, and that "No undisclosed
# natural-language paraphrases are introduced."
#
# That falsifies the single assumption this tool exists to test. The paraphrase
# risk it was built to measure DOES NOT EXIST in the final evaluation.
#
# Two runs happened during development and neither is a result: a 20-session
# smoke run, and a full sweep aborted after 5 of its 12 configurations. Nothing
# was recorded and no snapshot was written. **No number produced by this tool,
# then or later, may be cited** -- not in EXPERIMENTS.md, not in PROJECT_STATE.md,
# not in a report. The D012 "Results" section in EXPERIMENTS.md is empty on
# purpose and stays empty.
#
# The code is kept as future work, not as an unfinished task. If the organizers
# ever revise that FAQ, or if this is carried to a setting with real user
# messages, it can be run exactly as specified -- the preregistration in
# EXPERIMENTS.md ("D012 -- Paraphrase Stress") is frozen and needs no redesign.
# Running it requires new human authorization and a fresh reading of the FAQ.
###############################################################################

D012 Paraphrase Stress -- does E010's advantage survive surface rewording?

=============================================================================
WHAT THIS MEASURES: A DIFFERENCE, NOT A LEVEL
=============================================================================
E010 ranks by the longest contiguous evidence n-gram (n <= 4) found in a
candidate's own token stream, replacing E004's binary per-unit bag-of-words
coverage as the primary sort key. A contiguous-n-gram rule is a priori more
exposed to rewording, and the public simulator quotes the target product's own
features/details text VERBATIM into user messages -- which flatters exact
substring matching in a way a private set might not.

"How much does E010 drop under paraphrase?" is not decision-relevant on its own,
because the bag-of-words rule drops too. The decision-relevant quantity is

    A(r) = TechnicalScore(phrase_n4, r) - TechnicalScore(cov, r)

on the same replay, same pool, same evidence stream, at rewrite rate r. Since

    A(r) - A(0) = [dTS_phrase(r)] - [dTS_cov(r)]

this single number IS the degradation differential. E010 is *specially* fragile
only if enough rewording lets `cov` catch or beat `phrase_n4`.

RULES OF ENGAGEMENT (preregistered, EXPERIMENTS.md "D012 -- Paraphrase Stress")
  * No runtime change. Expected TechnicalScore impact exactly zero.
  * No evaluator change -- the rewrite is applied offline, in this replay, to the
    user_message the simulator has already produced.
  * The D-3 scorer registry is reused UNCHANGED. No scorer is added and N_MAX is
    not swept: sweeping it here would be public-set hill-climbing.
  * No D012 verdict may revert E010. Offline diagnostic evidence does not
    overturn official-evaluator runtime evidence. The strongest available outcome
    is a recommendation to draft a separately authorized preregistration.

Usage
-----
    python -m tools.diagnostics.d012_paraphrase_stress --limit 20        # smoke
    python -m tools.diagnostics.d012_paraphrase_stress \
        --json docs/diagnostics/D012_PARAPHRASE_STRESS.json
"""
from __future__ import annotations

import argparse
import json
import time

from starter.agent import _terms
from tools.diagnostics._paraphrase import ALL_FAMILIES, CONTENT_FAMILIES, Rewriter
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
from tools.diagnostics.d3_counterfactual_bench import SCORERS, _negate, normalized_text

# The control arms. Every one is already in D-3's CLOSED registry; nothing is
# added here. `bm25` is pool-order-as-is and isolates how much degradation comes
# from the query changing rather than from either ranking rule.
ARMS: tuple[str, ...] = ("bm25", "cov", "phrase_n4")
_unregistered = [arm for arm in ARMS if arm not in SCORERS]
if _unregistered:
    raise SystemExit(f"arms {_unregistered} are not in the closed D-3 registry")

# Headline depth is 10: that is E010's actual operating regime, where
# _coverage_rerank() reorders exactly the ids that are returned, so only MRR can
# move and TS delta = 0.30 * MRR delta.
HEADLINE_POOL = 10
PRIMARY_SEED = 20260831
ALT_SEEDS = (11, 12)
RATES = (0.0, 0.25, 0.5, 1.0)
MIX = CONTENT_FAMILIES


def run_config(
    samples, catalog_ids, categories, products, agent, depths, rewriter, text_cache
):
    """One full replay under `rewriter`, scoring every arm at every pool depth."""
    max_depth = max(depths)

    def probe(ctx):
        deep = ctx.pool(max_depth)
        result: dict = {}
        state = None
        for depth in depths:
            pool = deep[:depth]
            if ctx.target not in pool:
                for arm in ARMS:
                    result[f"r{depth}_{arm}"] = None
                continue
            if state is None:
                units = ctx.evidence_units()
                state = {
                    "units": units,
                    "unit_tokens": [_terms(m) for m in ctx.messages if _terms(m)],
                    "ev": frozenset().union(*units) if units else frozenset(),
                    # Built over the DEEPEST pool once; every shallower slice is a
                    # subset, and each scorer only ever reads state["pt"][p] for the
                    # p it is handed, so this is bit-identical to D-3's own state.
                    "pt": {p: ctx.product_terms(p) for p in deep},
                    "idf": {},
                    "idf_default": 0.0,
                    "text": lambda p: normalized_text(ctx.agent, p, text_cache),
                }
            for arm in ARMS:
                if arm == "bm25":
                    result[f"r{depth}_bm25"] = pool.index(ctx.target) + 1
                    continue
                score = SCORERS[arm](state)
                order = sorted(range(len(pool)), key=lambda i: _negate(score(pool[i])))
                result[f"r{depth}_{arm}"] = [pool[i] for i in order].index(ctx.target) + 1
        return result

    traces = list(
        replay(
            samples,
            catalog_ids,
            categories,
            products,
            agent,
            probe,
            progress=False,
            message_transform=rewriter,
        )
    )

    observed = {t.sample_id: (t.hit_turn, t.best_rank) for t in traces}
    out: dict = {
        "observed": {
            "overall": summarize(list(observed.values())),
            "scenario": scenario_split(traces, observed),
        },
        "arms": {},
        "turns_played": sum(len(t.turns) for t in traces),
    }
    for depth in depths:
        for arm in ARMS:
            key = f"r{depth}_{arm}"
            outcomes = {}
            for trace in traces:
                turn, rank = first_gated_turn(
                    trace,
                    lambda rec, k=key: rec.probe[k]
                    if (rec.probe.get(k) is not None and rec.probe[k] <= 10)
                    else None,
                )
                outcomes[trace.sample_id] = (turn, rank)
            out["arms"][key] = {
                "overall": summarize(list(outcomes.values())),
                "scenario": scenario_split(traces, outcomes),
            }
    return out


def advantage(result: dict, depth: int) -> float:
    return (
        result["arms"][f"r{depth}_phrase_n4"]["overall"]["technical_score"]
        - result["arms"][f"r{depth}_cov"]["overall"]["technical_score"]
    )


def _row(label: str, stats: dict, reference: dict | None) -> str:
    delta = (
        f"{stats['technical_score'] - reference['technical_score']:>+10.4f}"
        if reference
        else f"{'':>10}"
    )
    return (
        f"{label:<22}{stats['hit_rate_at_10']:>8.4f}{stats['mrr']:>10.6f}"
        f"{stats['mttc']:>8.3f}{stats['efficiency']:>8.4f}"
        f"{stats['technical_score']:>10.6f}{delta}"
    )


def print_block(title: str, result: dict, depth: int, baseline: dict | None) -> None:
    print(f"\n--- {title} (pool {depth}) ---")
    header = (
        f"{'arm':<22}{'HR@10':>8}{'MRR':>10}{'MTTC':>8}{'Eff':>8}{'TS':>10}{'vs r=0':>10}"
    )
    print(header)
    print("-" * len(header))
    print(_row("[observed E010 agent]", result["observed"]["overall"],
               baseline["observed"]["overall"] if baseline else None))
    for arm in ARMS:
        key = f"r{depth}_{arm}"
        print(_row(arm, result["arms"][key]["overall"],
                   baseline["arms"][key]["overall"] if baseline else None))
    print(f"{'A = TS(phrase_n4) - TS(cov)':<32}{advantage(result, depth):>+.6f}")


def main() -> None:
    parser = argparse.ArgumentParser(description="D012 Paraphrase Stress")
    parser.add_argument("--catalog", default=str(DEFAULT_CATALOG))
    parser.add_argument("--dataset", default=str(DEFAULT_DATASET))
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--pools", default="10,100")
    parser.add_argument("--seed", type=int, default=PRIMARY_SEED)
    parser.add_argument("--json", dest="json_out", default=None)
    parser.add_argument(
        "--skip-families", action="store_true", help="mixed-ensemble curve only"
    )
    parser.add_argument(
        "--skip-seeds", action="store_true", help="skip the alternate-seed check"
    )
    args = parser.parse_args()

    depths = tuple(sorted(int(value) for value in args.pools.split(",") if value.strip()))
    if HEADLINE_POOL not in depths:
        raise SystemExit(f"pool {HEADLINE_POOL} is the headline depth and is required")

    samples, catalog_ids, categories, products = load_fixtures(
        args.catalog, args.dataset, args.limit
    )
    # One Agent for every configuration: its two caches are pure memoizations of
    # catalog-static functions, so sharing is bit-identical to separate processes
    # and avoids a dozen index builds.
    agent = build_agent(args.catalog)
    text_cache: dict[str, str] = {}

    configs: list[tuple[str, tuple[str, ...], float, int]] = [
        (f"mix @ rate {rate:.2f}", MIX, rate, args.seed) for rate in RATES
    ]
    if not args.skip_families:
        configs += [
            (f"{family} @ rate 1.00", (family,), 1.0, args.seed)
            for family in ALL_FAMILIES
        ]
    if not args.skip_seeds:
        configs += [
            (f"mix @ rate 1.00 (seed {seed})", MIX, 1.0, seed) for seed in ALT_SEEDS
        ]

    results: dict[str, dict] = {}
    rewriters: dict[str, dict] = {}
    started = time.time()
    for index, (name, families, rate, seed) in enumerate(configs, start=1):
        rewriter = Rewriter(families, rate, seed)
        mark = time.time()
        results[name] = run_config(
            samples, catalog_ids, categories, products, agent, depths, rewriter, text_cache
        )
        rewriters[name] = rewriter.stats()
        results[name]["rewriter"] = rewriters[name]
        print(
            f"  [{index}/{len(configs)}] {name:<34} "
            f"{time.time() - mark:6.1f}s  "
            f"changed {rewriter.changed}/{rewriter.eligible} eligible",
            flush=True,
        )

    baseline = results["mix @ rate 0.00"]

    print(f"\n=== D012 Paraphrase Stress (n={len(samples)}, seed {args.seed}) ===")
    print("Offline replay; runtime agent and evaluator unmodified. Same pool and")
    print("same evidence stream for every arm within a configuration.")
    for depth in depths:
        print(f"\n########## POOL DEPTH {depth} ##########")
        for name in results:
            print_block(name, results[name], depth, baseline if name != "mix @ rate 0.00" else None)

    # ---------------------------------------------------------- the headline
    print(f"\n\n=== HEADLINE: advantage curve at pool {HEADLINE_POOL} (mixed ensemble) ===")
    print(f"{'rate':>6}{'TS cov':>12}{'TS phrase_n4':>14}{'d cov':>10}{'d phrase':>10}{'A':>11}{'A/A(0)':>9}")
    a0 = advantage(baseline, HEADLINE_POOL)
    for rate in RATES:
        name = f"mix @ rate {rate:.2f}"
        res = results[name]
        cov = res["arms"][f"r{HEADLINE_POOL}_cov"]["overall"]["technical_score"]
        phr = res["arms"][f"r{HEADLINE_POOL}_phrase_n4"]["overall"]["technical_score"]
        base_cov = baseline["arms"][f"r{HEADLINE_POOL}_cov"]["overall"]["technical_score"]
        base_phr = baseline["arms"][f"r{HEADLINE_POOL}_phrase_n4"]["overall"]["technical_score"]
        a = phr - cov
        print(
            f"{rate:>6.2f}{cov:>12.6f}{phr:>14.6f}{cov - base_cov:>+10.4f}"
            f"{phr - base_phr:>+10.4f}{a:>+11.6f}{(a / a0 if a0 else float('nan')):>9.3f}"
        )
    print("\n  d cov / d phrase are absolute degradations; A is the surviving")
    print("  advantage, and A(r) - A(0) is exactly the degradation DIFFERENCE.")

    # ------------------------------------------------------- validity gates
    a1 = advantage(results["mix @ rate 1.00"], HEADLINE_POOL)
    gates: list[tuple[str, bool, str]] = []
    placebo = results.get("punct @ rate 1.00")
    if placebo is not None:
        identical = all(
            placebo["arms"][f"r{d}_{arm}"]["overall"]
            == baseline["arms"][f"r{d}_{arm}"]["overall"]
            for d in depths
            for arm in ARMS
        ) and placebo["observed"]["overall"] == baseline["observed"]["overall"]
        gates.append(("G2 punct placebo identical to rate 0.00", identical, ""))
    changed_fraction = rewriters["mix @ rate 1.00"]["changed_fraction_of_eligible"]
    gates.append((
        "G3 >=80% of eligible messages actually changed at rate 1.00",
        changed_fraction >= 0.80,
        f"{changed_fraction:.3f}",
    ))
    total_violations = sum(stats["closure_violations"] for stats in rewriters.values())
    gates.append((
        "G4 vocabulary-closure invariant held everywhere",
        total_violations == 0,
        f"{total_violations} violation(s)",
    ))

    print("\n=== VALIDITY GATES ===")
    print("  G1 (rate 0.00 reproduces D-3) is verified against d3_counterfactual_bench")
    print("     separately; the rate 0.00 rows above are its input.")
    for label, passed, detail in gates:
        print(f"  [{'PASS' if passed else 'FAIL'}] {label}  {detail}")

    # -------------------------------------------------------------- verdict
    seed_spread = None
    if not args.skip_seeds:
        values = [a1] + [
            advantage(results[f"mix @ rate 1.00 (seed {seed})"], HEADLINE_POOL)
            for seed in ALT_SEEDS
        ]
        seed_spread = max(values) - min(values)

    if a1 <= 0:
        verdict, boundary = "SPECIALLY FRAGILE", abs(a1 - 0.0)
    elif a1 >= 0.5 * a0:
        verdict, boundary = "NOT SPECIALLY FRAGILE", abs(a1 - 0.5 * a0)
    else:
        verdict = "PARTIAL EROSION"
        boundary = min(abs(a1 - 0.0), abs(a1 - 0.5 * a0))
    if seed_spread is not None and seed_spread >= boundary:
        verdict = f"INCONCLUSIVE (was {verdict}; seed spread {seed_spread:.6f} >= {boundary:.6f})"

    print("\n=== VERDICT (preregistered decision rule) ===")
    print(f"  A(0.00) = {a0:+.6f}   A(1.00) = {a1:+.6f}   0.50*A(0) = {0.5 * a0:+.6f}")
    if seed_spread is not None:
        print(f"  seed spread of A(1.00) over {1 + len(ALT_SEEDS)} seeds = {seed_spread:.6f}")
    print(f"  --> {verdict}")
    print("\n  This verdict CANNOT revert E010. Offline diagnostic evidence does not")
    print("  overturn official-evaluator runtime evidence; at most it justifies")
    print("  drafting a new, separately authorized preregistration.")
    print(f"\n  total wall clock {time.time() - started:.1f}s")

    if args.json_out:
        payload = {
            "tool": "D012 paraphrase stress",
            "sample_count": len(samples),
            "pool_depths": list(depths),
            "headline_pool": HEADLINE_POOL,
            "arms": list(ARMS),
            "primary_seed": args.seed,
            "alt_seeds": list(ALT_SEEDS) if not args.skip_seeds else [],
            "rates": list(RATES),
            "mixed_ensemble": list(MIX),
            "configurations": results,
            "advantage": {
                name: {str(d): advantage(res, d) for d in depths}
                for name, res in results.items()
            },
            "gates": {label: passed for label, passed, _ in gates},
            "seed_spread_A1": seed_spread,
            "verdict": verdict,
        }
        with open(args.json_out, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=1)
        print(f"\n  wrote {args.json_out}")


if __name__ == "__main__":
    main()
