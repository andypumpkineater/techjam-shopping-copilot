"""Shared offline session-replay core for the D-* diagnostics.

=============================================================================
GROUND TRUTH BOUNDARY -- READ BEFORE EDITING
=============================================================================
This module reads `ground_truth` from `data/public_set.jsonl` and re-derives the
evaluator's hidden intent cards. That is permitted ONLY because everything here
runs OFFLINE, for error analysis, and never on the scored path.

`ground_truth` (and anything derived from it) must NEVER reach:
  - starter/agent.py
  - runtime query construction
  - runtime ranking
  - runtime clarification
  - runtime session state
  - any runtime lookup table

The Agent instance below is driven exclusively through its public contract --
`reset(session_id, user_profile)` and `respond(session_id, user_message, turn,
top_k)` -- with messages produced by the published simulator. The target id is
used only to LOCATE the target in a result list after the Agent has answered.
=============================================================================

Why a shared module: D-1, D-2, D-3 and the invariant checker all need the exact
same session replay. Four private copies would drift, and a drifted replay
silently invalidates cross-diagnostic comparisons.
"""
from __future__ import annotations

import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Iterator

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from evaluator.local_evaluator import (  # noqa: E402
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
from starter.agent import Agent, _terms  # noqa: E402

DEFAULT_CATALOG = REPO_ROOT / "data" / "catalog.jsonl"
DEFAULT_DATASET = REPO_ROOT / "data" / "public_set.jsonl"

# Mirrors the BM25 field weights hard-coded in starter/agent.py:277 and :315
# (parent_asin, title, categories, features, details, store, description).
# `verify_agent_bm25_weights()` fails loudly if the agent ever diverges, so a
# runtime change cannot silently invalidate a diagnostic's deep ranking.
BM25_WEIGHTS = (0.0, 6.0, 4.0, 2.5, 2.5, 1.5, 1.0)
_BM25_SQL_LITERAL = "bm25(products, 0.0, 6.0, 4.0, 2.5, 2.5, 1.5, 1.0)"

# Mirrors starter/agent.py:420 -- the accumulated-evidence query term cap.
QUERY_TERM_CAP = 40


def verify_agent_bm25_weights() -> None:
    """Guard: the diagnostics reconstruct the agent's own deep ranking, so the
    BM25 weighting must still match. Raises instead of reporting wrong numbers."""
    source = (REPO_ROOT / "starter" / "agent.py").read_text(encoding="utf-8")
    if _BM25_SQL_LITERAL not in source:
        raise RuntimeError(
            "starter/agent.py no longer contains the expected BM25 weighting "
            f"{_BM25_SQL_LITERAL!r}. The diagnostics reconstruct the agent's deep "
            "ranking and would report misleading numbers. Update BM25_WEIGHTS in "
            "tools/diagnostics/_replay.py deliberately, then re-baseline."
        )


@dataclass
class TurnRecord:
    turn: int
    ask_attribute: object
    ranked: list[str]                  # agent's actual scored top-10 (post-normalize)
    target_rank_top10: int | None      # 1-based rank in `ranked`, else None
    expression: str                    # the agent's own FTS5 query this turn
    n_terms: int
    term_cap_hit: bool
    n_evidence_units: int
    user_message: str
    probe: dict = field(default_factory=dict)   # per-tool extra fields


@dataclass
class SessionTrace:
    sample_id: str
    scenario_type: str
    target: str
    override_turn: int | None          # evaluator gate: no conversion before this turn
    hit_turn: int | None               # the real agent's first-hit turn
    best_rank: int | None              # the real agent's scored rank at the hit
    turns: list[TurnRecord] = field(default_factory=list)

    def as_dict(self) -> dict:
        return {
            "sample_id": self.sample_id,
            "scenario_type": self.scenario_type,
            "target": self.target,
            "override_turn": self.override_turn,
            "hit_turn": self.hit_turn,
            "best_rank": self.best_rank,
            "turns": [
                {
                    "turn": t.turn,
                    "ask_attribute": t.ask_attribute,
                    "ranked": t.ranked,
                    "target_rank_top10": t.target_rank_top10,
                    "n_terms": t.n_terms,
                    "term_cap_hit": t.term_cap_hit,
                    "n_evidence_units": t.n_evidence_units,
                    **t.probe,
                }
                for t in self.turns
            ],
        }


class ProbeContext:
    """Everything a diagnostic needs at one turn, after the Agent has answered."""

    def __init__(self, agent, session_id, turn, target, expression, ranked, messages):
        self.agent = agent
        self.session_id = session_id
        self.turn = turn
        self.target = target
        self.expression = expression
        self.ranked = ranked
        self.messages = messages
        self._pools: dict[int, list[str]] = {}

    def pool(self, depth: int) -> list[str]:
        """Top-`depth` ids under the agent's OWN unscoped BM25 ranking for this
        turn's query. Cached per depth; a deeper pool is sliced from a wider one
        only when one was already fetched."""
        if not self.expression:
            return []
        for have in sorted(self._pools):
            if have >= depth:
                return self._pools[have][:depth]
        rows = self.agent.connection.execute(
            "SELECT parent_asin FROM products WHERE products MATCH ? "
            f"ORDER BY {_BM25_SQL_LITERAL} LIMIT ?",
            (self.expression, depth),
        ).fetchall()
        self._pools[depth] = [str(r[0]) for r in rows]
        return self._pools[depth]

    def target_rank_in_pool(self, depth: int) -> int | None:
        pool = self.pool(depth)
        return pool.index(self.target) + 1 if self.target in pool else None

    def evidence_units(self) -> list[frozenset[str]]:
        """One admitted message = one evidence unit (the E004 definition)."""
        units = (frozenset(_terms(m)) for m in self.messages)
        return [u for u in units if u]

    def product_terms(self, parent_asin: str) -> frozenset[str]:
        return self.agent._product_terms(parent_asin)


def rebuild_expression(agent, session_id: str) -> tuple[str, list[str], bool]:
    """Reconstruct the FTS5 expression the agent built this turn.

    Mirrors starter/agent.py:419-421 exactly. Reads the agent's accumulated
    evidence (a read-only peek at an internal attribute) rather than guessing.
    If that internal shape ever changes, this raises rather than silently
    reconstructing a different query."""
    try:
        messages = agent._sessions[session_id]
    except (AttributeError, KeyError) as exc:  # pragma: no cover - defensive
        raise RuntimeError(
            "Cannot read the agent's accumulated evidence "
            "(expected `Agent._sessions[session_id]`). The diagnostics "
            "reconstruct the agent's own query; update _replay.py deliberately."
        ) from exc
    all_terms = list(dict.fromkeys(_terms(" ".join(messages))))
    terms = all_terms[:QUERY_TERM_CAP]
    expression = " OR ".join(f'"{t}"' for t in terms)
    return expression, terms, len(all_terms) > QUERY_TERM_CAP


def load_fixtures(catalog: Path, dataset: Path, limit: int | None = None):
    samples = load_jsonl(dataset)
    if limit:
        samples = samples[:limit]
    catalog_ids, categories, products = catalog_index(catalog)
    return samples, catalog_ids, categories, products


def replay(
    samples: list[dict],
    catalog_ids: set[str],
    categories: dict[str, list[str]],
    products: dict[str, dict],
    agent: Agent,
    probe: Callable[[ProbeContext], dict] | None = None,
    progress: bool = True,
) -> Iterator[SessionTrace]:
    """Replay the published simulator offline against a real Agent instance.

    Faithful to evaluator/local_evaluator.py::evaluate(), including the
    intent_override gate (`override_applied`) and the same customer-reply policy.

    KNOWN AND INTENTIONAL LIMITATION -- read before interpreting counterfactuals:
    the loop stops when the REAL agent hits, exactly as the evaluator does. Turns
    after that point are never played, so a counterfactual reranker evaluated on
    this trace can only use turns the real agent actually reached. That biases
    counterfactual scores DOWNWARD (a rule that would have hit at turn 6 in a
    session the real agent won at turn 2 is recorded as a miss), which is the
    conservative direction. Do not "fix" this by playing extra turns: the
    disclosure stream depends on the agent's own ask_attribute choices, so those
    turns would not exist under the counterfactual either.
    """
    for index, sample in enumerate(samples, start=1):
        # Deterministic per-sample session id: reruns are byte-comparable.
        session_id = f"diag_{sample['sample_id']}"
        agent.reset(session_id, sample["user_profile"])
        target = str(sample["ground_truth"]["parent_asin"])
        card, behavior = materialize_hidden_fields(sample, products)
        effective = {**sample, "intent_card": card, "behavior": behavior}

        override = (behavior or {}).get("override") or {}
        override_turn = int(override["turn"]) if override else None

        disclosed: set[str] = set()
        boundary_used = False
        override_applied = sample["scenario_type"] != "intent_override"
        user_message = initial_message(
            effective, coarse_category(categories.get(target, [])), disclosed
        )

        trace = SessionTrace(
            sample_id=sample["sample_id"],
            scenario_type=sample["scenario_type"],
            target=target,
            override_turn=override_turn,
            hit_turn=None,
            best_rank=None,
        )

        for turn in range(1, MAX_TURNS + 1):
            response = agent.respond(session_id, user_message, turn, TOP_K)
            ranked = normalize_recommendations(response.get("recommendations"), catalog_ids)
            expression, terms, cap_hit = rebuild_expression(agent, session_id)
            messages = list(agent._sessions[session_id])

            record = TurnRecord(
                turn=turn,
                ask_attribute=response.get("ask_attribute"),
                ranked=ranked,
                target_rank_top10=(ranked.index(target) + 1) if target in ranked else None,
                expression=expression,
                n_terms=len(terms),
                term_cap_hit=cap_hit,
                n_evidence_units=len(messages),
                user_message=user_message,
            )
            if probe is not None:
                ctx = ProbeContext(
                    agent, session_id, turn, target, expression, ranked, messages
                )
                record.probe = probe(ctx) or {}
            trace.turns.append(record)

            if override_applied and target in ranked:
                trace.best_rank = ranked.index(target) + 1
                trace.hit_turn = turn
                break
            if turn == MAX_TURNS:
                break

            if not override_applied and turn + 1 == int(override.get("turn", 3)):
                override_applied = True
                new_value = str(override.get("new_value", ""))
                if new_value:
                    disclosed.add(new_value)
                user_message = str(
                    override.get("message", "Actually, please ignore my earlier preference.")
                )
            else:
                user_message, boundary_used = customer_reply(
                    effective, response.get("ask_attribute"), disclosed, boundary_used
                )

        yield trace
        if progress and index % 25 == 0:
            print(f"  replayed {index}/{len(samples)}", file=sys.stderr)


# --------------------------------------------------------------------------
# Metrics -- mirrors evaluator/local_evaluator.py:188-201 and :279-280
# --------------------------------------------------------------------------
MISS_TURN = MAX_TURNS + 1


def efficiency(mttc: float) -> float:
    return max(0.0, min(1.0, (11.0 - mttc) / 10.0))


def technical_score(hit_rate: float, mrr: float, mttc: float) -> float:
    return 0.50 * hit_rate + 0.30 * mrr + 0.20 * efficiency(mttc)


def summarize(outcomes: list[tuple[int | None, int | None]]) -> dict:
    """outcomes: list of (first_hit_turn, rank). Both None for a miss."""
    n = len(outcomes)
    if n == 0:
        return {"sample_count": 0}
    hits = sum(1 for turn, _ in outcomes if turn is not None)
    hit_rate = hits / n
    mrr = sum((1.0 / rank) if rank else 0.0 for _, rank in outcomes) / n
    mttc = sum(turn if turn is not None else MISS_TURN for turn, _ in outcomes) / n
    return {
        "sample_count": n,
        "hit_rate_at_10": round(hit_rate, 6),
        "mrr": round(mrr, 6),
        "mttc": round(mttc, 6),
        "efficiency": round(efficiency(mttc), 6),
        "technical_score": round(technical_score(hit_rate, mrr, mttc), 6),
    }


def scenario_split(traces, outcomes: dict[str, tuple[int | None, int | None]]) -> dict:
    buckets: dict[str, list] = {}
    for trace in traces:
        buckets.setdefault(trace.scenario_type, []).append(outcomes[trace.sample_id])
    return {name: summarize(buckets[name]) for name in sorted(buckets)}


def first_gated_turn(trace: SessionTrace, predicate) -> tuple[int | None, int | None]:
    """First turn satisfying `predicate(turn_record) -> rank|None`, honoring the
    intent_override gate: an override session cannot convert before its override
    turn (evaluator/local_evaluator.py:234, :252, :259). Returns (turn, rank)."""
    for record in trace.turns:
        if trace.override_turn is not None and record.turn < trace.override_turn:
            continue
        rank = predicate(record)
        if rank is not None:
            return record.turn, rank
    return None, None


def build_agent(catalog: Path) -> Agent:
    verify_agent_bm25_weights()
    return Agent(catalog)
