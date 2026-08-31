"""Render a real, reproducible multi-turn session as a transcript.

This satisfies the demonstration requirement in
`docs/competition_specification.md` ("One demonstrated multi-turn session") and
`docs/final_evaluation_faq.md` section 7 ("The demonstration should show at least
one complete multi-turn session").

WHAT THIS IS
    A transcript recorder. It drives the frozen Agent through its published
    contract only -- `reset()` and `respond()` -- and prints what actually
    happened, turn by turn.

WHAT THIS IS NOT
    A second evaluator. It computes no metrics. Every piece of customer-side
    semantics is IMPORTED from the unmodified official evaluator rather than
    reimplemented here:

        initial_message, customer_reply, coarse_category,
        materialize_hidden_fields, normalize_recommendations,
        catalog_index, load_jsonl, MAX_TURNS, TOP_K

    The only thing this module owns is the turn loop that calls them, plus
    formatting. The loop mirrors `evaluator.local_evaluator.evaluate()`,
    including the intent_override gate and the stop-on-first-hit rule.

    `--verify` checks that mirroring mechanically: it re-derives the outcome
    (hit / first_hit_turn / best_rank) and compares it against the tracked
    per-session snapshot named by SNAPSHOT below -- currently
    `docs/diagnostics/E014_SESSIONS.json`, the current submission baseline -- which was
    produced by the official evaluator. If this driver drifted from evaluator
    semantics, that comparison fails.

GROUND TRUTH
    The target `parent_asin` is used exactly the way the evaluator uses it: to
    locate the target in a result list AFTER the agent has already answered, and
    to stop the session. It never reaches the Agent. The Agent receives only
    `reset(session_id, user_profile)` and `respond(session_id, user_message,
    turn, top_k)`, with messages produced by the published simulator.

DETERMINISM
    The evaluator assigns each session a random `session_id`
    (`public_{uuid4().hex}`); this tool uses `demo_{sample_id}` so runs are
    reproducible. The Agent uses `session_id` only as a dictionary key for
    per-session state, so this cannot affect any output. Everything else --
    message templates, disclosure policy, override turn -- is derived
    deterministically by the evaluator's own helpers.

USAGE
    python3 -m tools.demo_session --sample-id public_0001
    python3 -m tools.demo_session --sample-id public_0001 --verify
    python3 -m tools.demo_session --sample-id public_0001 --markdown
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path

from evaluator.local_evaluator import (
    MAX_TURNS,
    TOP_K,
    catalog_index,
    coarse_category,
    customer_reply,
    initial_message,
    load_jsonl,
    materialize_hidden_fields,
    normalize_recommendations,
)
from starter.agent import Agent


REPO = Path(__file__).resolve().parent.parent
# The per-session record of the official evaluator run behind the reported
# TechnicalScore. Repoint this at the new snapshot whenever the submission
# baseline advances; the generated Markdown reads the name from here, so the
# doc cannot drift away from what --verify actually checks.
SNAPSHOT = REPO / "docs" / "diagnostics" / "E014_SESSIONS.json"
SHOW_RECOMMENDATIONS = 5


def run_session(agent: Agent, sample: dict, catalog_ids, categories, products) -> dict:
    """Drive one session. Mirrors evaluator.local_evaluator.evaluate()'s loop."""
    session_id = f"demo_{sample['sample_id']}"
    agent.reset(session_id, sample["user_profile"])
    target = str(sample["ground_truth"]["parent_asin"])
    card, behavior = materialize_hidden_fields(sample, products)
    effective = {**sample, "intent_card": card, "behavior": behavior}

    disclosed: set[str] = set()
    boundary_used = False
    override_applied = sample["scenario_type"] != "intent_override"
    user_message = initial_message(effective, coarse_category(categories.get(target, [])), disclosed)

    turns: list[dict] = []
    hit_turn: int | None = None
    best_rank: int | None = None
    for turn in range(1, MAX_TURNS + 1):
        response = agent.respond(session_id, user_message, turn, TOP_K)
        ranked = normalize_recommendations(response.get("recommendations"), catalog_ids)
        record = {
            "turn": turn,
            "customer": user_message,
            "agent_message": response.get("message"),
            "ask_attribute": response.get("ask_attribute"),
            "ranked": ranked,
            "usage": response.get("usage"),
            "target_rank": ranked.index(target) + 1 if target in ranked else None,
            "gated": not override_applied,
        }
        turns.append(record)

        if override_applied and target in ranked:
            best_rank = ranked.index(target) + 1
            hit_turn = turn
            break
        if turn == MAX_TURNS:
            break

        override = effective.get("behavior", {}).get("override") or {}
        if not override_applied and turn + 1 == int(override.get("turn", 3)):
            override_applied = True
            new_value = str(override.get("new_value", ""))
            if new_value:
                disclosed.add(new_value)
            user_message = str(override.get("message", "Actually, please ignore my earlier preference."))
        else:
            user_message, boundary_used = customer_reply(
                effective, response.get("ask_attribute"), disclosed, boundary_used
            )

    return {
        "sample_id": sample["sample_id"],
        "scenario_type": sample["scenario_type"],
        "user_profile": sample["user_profile"],
        "target": target,
        "turns": turns,
        "hit": hit_turn is not None,
        "first_hit_turn": hit_turn,
        "best_rank": best_rank,
    }


def verify(result: dict) -> tuple[bool, str]:
    """Compare the outcome against the official evaluator's tracked snapshot."""
    if not SNAPSHOT.exists():
        return False, f"snapshot not found: {SNAPSHOT}"
    sessions = json.loads(SNAPSHOT.read_text(encoding="utf-8"))["sessions"]
    match = next((s for s in sessions if s["sample_id"] == result["sample_id"]), None)
    if match is None:
        return False, f"{result['sample_id']} absent from the snapshot"
    fields = ("hit", "first_hit_turn", "best_rank")
    diffs = [f"{f}: driver={result[f]!r} evaluator={match[f]!r}" for f in fields if result[f] != match[f]]
    if diffs:
        return False, "; ".join(diffs)
    return True, f"hit={match['hit']} first_hit_turn={match['first_hit_turn']} best_rank={match['best_rank']}"


def provenance() -> dict:
    def git(*args: str) -> str:
        try:
            return subprocess.run(["git", *args], cwd=REPO, capture_output=True, text=True, check=True).stdout.strip()
        except Exception:
            return "unavailable"
    agent_source = (REPO / "starter" / "agent.py").read_bytes()
    return {
        # The commit that last CHANGED the agent, not repository HEAD. HEAD moves
        # on every docs commit, which would churn this transcript and point a
        # reader at a commit where nothing about the agent happened. This is the
        # commit whose starter/agent.py hash is bound to the reported result in
        # docs/PROVENANCE.json.
        "agent_commit": git("log", "-1", "--format=%H", "--", "starter/agent.py"),
        "head_commit": git("rev-parse", "HEAD"),
        "agent_sha256": hashlib.sha256(agent_source).hexdigest(),
        "agent_matches_head": git("status", "--porcelain", "--", "starter/agent.py") == "",
    }


def title_of(products: dict, parent_asin: str) -> str:
    title = str(products.get(parent_asin, {}).get("title") or "")
    return (title[:70] + "…") if len(title) > 70 else title


def render_markdown(result: dict, products: dict, meta: dict, verified: str | None) -> str:
    out: list[str] = []
    w = out.append
    w("# Demo — One Complete Multi-Turn Session")
    w("")
    w("Generated by `tools/demo_session.py`. Not hand-edited. See "
      "[Reproducibility](#reproducibility) for how to regenerate it.")
    w("")
    w("## What this demonstrates")
    w("")
    w("One real session, start to finish, against the frozen Agent that produced our")
    w("reported TechnicalScore. It shows the three mechanisms the system runs on:")
    w("")
    w("- **evidence accumulates** — each customer reply joins the lexical query and stays,")
    w("  split at clause boundaries so each stated constraint scores on its own (E013);")
    w("- **clarification opens wide, then narrows** — the first two turns ask the")
    w("  open-ended `other`, then the attribute is chosen from the candidates themselves;")
    w("- **the ranking moves** as evidence arrives, until the target reaches the Top 10.")
    w("")
    w("The Agent never receives the target. Customer messages come from the published")
    w("simulator in `evaluator/local_evaluator.py`; the Agent is driven only through")
    w("`reset()` and `respond()`.")
    w("")
    w("## Session")
    w("")
    w(f"| | |")
    w(f"|---|---|")
    w(f"| Sample | `{result['sample_id']}` (public set) |")
    w(f"| Scenario | {result['scenario_type']} |")
    w(f"| Hidden target | `{result['target']}` — {title_of(products, result['target'])} |")
    w(f"| Outcome | {'hit' if result['hit'] else 'no hit'}"
      + (f" at turn {result['first_hit_turn']}, rank {result['best_rank']}" if result['hit'] else "")
      + " |")
    w("")
    w("Anonymized profile the Agent received:")
    w("")
    w("```json")
    w(json.dumps(result["user_profile"], indent=2, sort_keys=True))
    w("```")
    w("")
    w("## Transcript")
    w("")
    for record in result["turns"]:
        w(f"### Turn {record['turn']}")
        w("")
        w(f"**Customer** — {record['customer']}")
        w("")
        w(f"**Agent** — {record['agent_message']}")
        w("")
        attribute = record["ask_attribute"]
        w(f"**`ask_attribute`** — `{attribute}`" if attribute else "**`ask_attribute`** — `null`")
        w("")
        if not record["ranked"]:
            w("_No recommendations this turn._")
            w("")
            continue
        shown = record["ranked"][:SHOW_RECOMMENDATIONS]
        w(f"**Top {len(shown)} of {len(record['ranked'])} recommendations**")
        w("")
        w("| Rank | `parent_asin` | Title |")
        w("|---:|---|---|")
        for rank, parent_asin in enumerate(shown, start=1):
            marker = " **← target**" if parent_asin == result["target"] else ""
            w(f"| {rank} | `{parent_asin}` | {title_of(products, parent_asin)}{marker} |")
        w("")
        if record["target_rank"] is not None and record["target_rank"] > len(shown):
            w(f"_Target is at rank {record['target_rank']} of this turn's Top 10._")
            w("")
        if record["gated"]:
            w("_Intent-override gate: a hit cannot be recorded before the changed intent is revealed._")
            w("")
    w("## What to notice")
    w("")
    attributes = [t["ask_attribute"] for t in result["turns"] if t["ask_attribute"]]
    w(f"- The clarification attribute changes across turns: "
      + ", ".join(f"`{a}`" for a in attributes) + ".")
    w("  Turns 1-2 ask the open-ended `other` unconditionally: most of a shopper's")
    w("  constraints do not fall into any one attribute category, so an open question")
    w("  elicits more per turn than a well-chosen narrow one. From turn 3 the attribute")
    w("  is scored against that turn's own Top 10, so the Agent asks about what its")
    w("  current candidates disagree on. Both halves are E013; neither works alone.")
    first, last = result["turns"][0], result["turns"][-1]
    w(f"- The recommendation list is not static: turn 1 opens with "
      f"`{first['ranked'][0] if first['ranked'] else '—'}` at rank 1 and the final turn opens with "
      f"`{last['ranked'][0] if last['ranked'] else '—'}`.")
    if result["hit"]:
        w(f"- The target reaches rank {result['best_rank']} at turn {result['first_hit_turn']}, and the")
        w("  session stops there — the evaluator's stop-on-first-hit rule.")
    if result["scenario_type"] == "intent_override":
        w("- **A visible limitation.** Evidence is append-only: after the customer says")
        w('  "ignore my earlier preference", the earlier wording still remains in the')
        w("  accumulated query. The system has no semantic supersession, so the override")
        w("  is absorbed as additional evidence rather than as a replacement. An")
        w("  erase-everything reset was tested and made results worse (E005, reverted);")
        w("  a finer-grained policy was never tested. See the README's Limitations.")
    w("- Every turn reports `usage` of 0 prompt / 0 completion tokens. No model is")
    w("  called at any point.")
    w("")
    w("## Reproducibility")
    w("")
    w("```bash")
    w(f"python3 -m tools.demo_session --sample-id {result['sample_id']} --markdown")
    w("```")
    w("")
    w("Prerequisites — Python, catalog placement, FTS5 check: "
      "[`docs/REPRODUCIBILITY.md`](REPRODUCIBILITY.md) §§1–3.")
    w("")
    w("| | |")
    w("|---|---|")
    w(f"| `starter/agent.py` last changed in commit | `{meta['agent_commit']}` |")
    w(f"| `starter/agent.py` SHA-256 | `{meta['agent_sha256']}` |")
    w(f"| `starter/agent.py` uncommitted changes at generation | "
      f"{'none' if meta['agent_matches_head'] else 'PRESENT -- transcript is not from the committed agent'} |")
    w("| Transcript source | generated directly by `tools/demo_session.py`; not hand-edited |")
    w("| Customer messages | produced by the unmodified published simulator |")
    if verified:
        w(f"| Outcome verified against official evaluator snapshot | {verified} |")
    w("")
    w("The outcome above is cross-checked against")
    w(f"[`docs/diagnostics/{SNAPSHOT.name}`](diagnostics/{SNAPSHOT.name}), the")
    w("per-session record of the official evaluator run that produced our reported")
    w("TechnicalScore:")
    w("")
    w("```bash")
    w(f"python3 -m tools.demo_session --sample-id {result['sample_id']} --verify")
    w("```")
    w("")
    return "\n".join(out)


def render_text(result: dict, products: dict) -> str:
    out: list[str] = []
    w = out.append
    w(f"session {result['sample_id']}  scenario={result['scenario_type']}")
    w(f"target  {result['target']}  {title_of(products, result['target'])}")
    w("")
    for record in result["turns"]:
        w(f"--- turn {record['turn']} ---")
        w(f"  customer : {record['customer']}")
        w(f"  agent    : {record['agent_message']}")
        w(f"  ask      : {record['ask_attribute']}")
        for rank, parent_asin in enumerate(record["ranked"][:SHOW_RECOMMENDATIONS], start=1):
            marker = "  <-- target" if parent_asin == result["target"] else ""
            w(f"    {rank:>2}. {parent_asin}  {title_of(products, parent_asin)}{marker}")
        if record["gated"]:
            w("  (intent-override gate active: no hit may be recorded yet)")
        w("")
    w(f"outcome: hit={result['hit']} first_hit_turn={result['first_hit_turn']} best_rank={result['best_rank']}")
    return "\n".join(out)


def main() -> None:
    parser = argparse.ArgumentParser(description="Render one multi-turn session transcript")
    parser.add_argument("--catalog", default="data/catalog.jsonl")
    parser.add_argument("--dataset", default="data/public_set.jsonl")
    parser.add_argument("--sample-id", default="public_0001")
    parser.add_argument("--markdown", action="store_true", help="emit Markdown instead of plain text")
    parser.add_argument("--verify", action="store_true",
                        help="compare the outcome against the official evaluator snapshot and exit")
    args = parser.parse_args()

    samples = load_jsonl(args.dataset)
    sample = next((s for s in samples if s["sample_id"] == args.sample_id), None)
    if sample is None:
        raise SystemExit(f"sample id not found in {args.dataset}: {args.sample_id}")

    catalog_ids, categories, products = catalog_index(args.catalog)
    result = run_session(Agent(args.catalog), sample, catalog_ids, categories, products)

    ok, detail = verify(result)
    if args.verify:
        print(("VERIFIED   " if ok else "MISMATCH   ") + f"{result['sample_id']}: {detail}")
        raise SystemExit(0 if ok else 1)

    if args.markdown:
        print(render_markdown(result, products, provenance(), detail if ok else None))
    else:
        print(render_text(result, products))


if __name__ == "__main__":
    main()
