# Shopping Copilot

**TikTok TechJam 2026 — Track 4: Conversational E-Commerce Search**

A deterministic conversational shopping agent that opens with wide, open-ended
questions, splits every reply into its individual constraints, retrieves broadly
and reranks by word-order proximity, and — when a turn brings no new evidence —
advances to the next window of the ranked pool instead of repeating the same
Top 10 — reaching **0.990 HitRate@10** and **0.861737 TechnicalScore** with no
LLM calls, no network on the scored path, and no third-party runtime
dependencies.

```text
HitRate@10      0.990       MRR             0.649123
MTTC            2.400       Efficiency      0.860
TechnicalScore  0.861737    Tokens          0
Model cost      $0.00       Deps            0
```

Official evaluator · 200 public sessions · unmodified `evaluator/local_evaluator.py`

---

## Results

Official evaluator, 200 public sessions, unmodified `evaluator/local_evaluator.py`.

| Metric | Our final system (E014) | Official starter (E000) |
|---|---:|---:|
| HitRate@10 | **0.990** | 0.125 |
| MRR | **0.649123** | 0.068034 |
| MTTC | **2.400** | 9.81 |
| Efficiency | **0.860** | 0.119 |
| **TechnicalScore** | **0.861737** | 0.106710 |

By scenario:

| Scenario | n | HR@10 | MRR | MTTC |
|---|---:|---:|---:|---:|
| buying | 80 | 0.9875 | 0.598135 | 1.9375 |
| browsing | 80 | 1.000 | 0.637574 | 2.2125 |
| intent_override | 30 | 0.966667 | 0.820833 | 3.933333 |
| boundary | 10 | 1.000 | 0.634286 | 3.000 |

> Scenario metrics are descriptive; `boundary` has only 10 public sessions.

Every number is bound to the exact code that produced it in
[`docs/PROVENANCE.json`](docs/PROVENANCE.json) (commit → agent SHA-256 →
evaluator command → artifact SHA-256 → metrics), with the per-session record in
[`docs/diagnostics/E014_SESSIONS.json`](docs/diagnostics/E014_SESSIONS.json).
Re-run at the submitted commit on 2026-09-01, including from a clean clone, it
reproduced **byte-identical** — [`docs/REPRODUCIBILITY.md`](docs/REPRODUCIBILITY.md)
§8 states what that does and does not establish.

**Feasibility**

| Model calls | External APIs | Network (scored path) | Tokens (p/c/t) | Cost | Third-party deps | 200-session wall clock |
|---:|---:|---:|---:|---:|---:|---:|
| 0 | 0 | none | 0 / 0 / 0 | $0.00 | none (stdlib only) | 415.83 s |

Network and external APIs *are* permitted in final evaluation
([`docs/final_evaluation_faq.md`](docs/final_evaluation_faq.md) §2); staying
offline was our design choice, not a rule. Full detail, including the
determinism checks behind these numbers:
[`docs/REPRODUCIBILITY.md`](docs/REPRODUCIBILITY.md).

## Highlights

- **Retrieval, not generation.** No LLM, no embeddings, no network on the scored
  path — the whole system is Python stdlib (`json`, `re`, `sqlite3`,
  `collections`, `pathlib`) plus SQLite's built-in FTS5/BM25.
- **Clarification is a retrieval instrument.** The agent asks wide first (an
  open-ended question for the first two turns), then picks the single catalog
  attribute its current Top 10 disagrees on most — not a scripted question tree.
- **Advances the page instead of repeating it.** When a turn adds no new
  constraint, the agent shows the next window of the ranked pool rather than
  the same ten products again — the one change in this project with a
  *provable*, not just measured, benefit.
- **Retrieve wide → rerank → truncate.** 100 candidates are reranked by
  longest-common-word-order before the Top 10 is cut, so a candidate at pool
  rank 80 can still surface.
- **Thirteen preregistered experiments, each decided on a single
  official-evaluator run** — hypothesis and decision rule fixed before
  evaluation, failures recorded at the same weight as successes
  ([`EXPERIMENTS.md`](EXPERIMENTS.md)).

## How It Works

A simulated customer opens with a short, often vague message. A hidden target
product sits in a frozen 50,000-product catalog; within 10 turns the agent must
place its exact `parent_asin` inside its Top 10. Every turn:

```text
  turn t: user message
        │  ▼
  ┌─────────────────────────────────────────────────┐
  │ EVIDENCE   append non-template replies, split    │
  │            into clauses → one lexical query      │
  └─────────────────────────────────────────────────┘
        │  accumulated query (deduped, capped at 40)
  ┌─────────────────────────────────────────────────┐
  │ RETRIEVE   FTS5/BM25 over 50,000 items; 70       │
  │            category-scoped + 30 global → 100     │
  └─────────────────────────────────────────────────┘
        │  100 candidates
  ┌─────────────────────────────────────────────────┐
  │ RERANK     word-order proximity (n-grams 2..4),  │
  │            coverage as tiebreak; stable sort     │
  └─────────────────────────────────────────────────┘
        │  100 candidates, reordered
  ┌─────────────────────────────────────────────────┐
  │ TRUNCATE   head = ranked[:top_k]  ← only now     │
  └─────────────────────────────────────────────────┘
        │ pre-rotation head        │ full ranked pool
        │                          ▼
        │      ┌───────────────────────────────────┐
        │      │ ROTATE  idle turn → next window;   │──► recommendations
        │      │         new evidence → back to head│
        │      └───────────────────────────────────┘
        ▼
  ┌─────────────────────────────────────────────────┐
  │ ASK   turns 1-2: open-ended; turn 3+: attribute  │
  │       the head disagrees on most ──► ask_attribute
  └─────────────────────────────────────────────────┘
        │
        ▼
  simulator discloses a constraint → evidence at turn t+1
```

The loop closes: what the agent retrieves determines what it asks, and what it
asks determines what it can retrieve next. Rotation is deliberately kept outside
that loop — the question is always chosen from the pre-rotation head, so which
page is showing never changes what the agent asks or what the customer
discloses. That's what makes rotation's effect predictable offline *exactly*,
not just approximately.

**Design rationale, briefly.** Reranking *before* truncating — not after — is
what lets a candidate at pool rank 80 reach the returned ten: a pool already cut
to 10 can only be reordered, which moves MRR alone. Within that reranking, the
longest contiguous run of the user's own words is a stronger match signal than
plain word overlap, since two candidates can share every word and still be
different products; overlap is used only to break ties. The clarification and
page-rotation mechanics that close the loop above are covered in Highlights.

Implementation: [`starter/agent.py`](starter/agent.py), 663 lines, standard
library only.

## Demo

[**One complete multi-turn session**](docs/DEMO_SESSION.md) — a real
`intent_override` session: two open-ended questions, a reply carrying two
constraints at once (`Water Resistant; 3 Year Battery`) that the clause splitter
separates, and the target reaching rank 1 at turn 3. Generated by
`tools/demo_session.py`, never hand-edited, cross-checked against the tracked
per-session record:

```bash
python3 -m tools.demo_session --sample-id public_0003 --verify
```

This session finds its target before any idle turn occurs, so it doesn't
demonstrate page rotation; see [`EXPERIMENTS.md`](EXPERIMENTS.md) for sessions
where rotation changed the outcome.

## Quickstart

Python 3.11.15 verified; needs SQLite with FTS5 (bundled with CPython).

```bash
# 0. Nothing to install.
python3 -c "import sqlite3; sqlite3.connect(':memory:').execute('CREATE VIRTUAL TABLE t USING fts5(a)'); print('FTS5 OK')"
```

```bash
# 1. Get the catalog — a 60 MB organizer artifact, NOT committed here.
#    Download catalog.jsonl.gz from the official TechJam 2026 release,
#    verify it against the organizer's SHA256SUMS, then:
gzip -dk catalog.jsonl.gz
mv catalog.jsonl data/catalog.jsonl
wc -l data/catalog.jsonl        # must print 50000
```

```bash
# 2. Run the tests (stdlib only, a few seconds).
python3 -m unittest discover -s tests
```

```bash
# 3. Run the unmodified official evaluator over the 200 public sessions.
python3 -m evaluator.local_evaluator
```

No API keys or environment variables required. Full runbook — checksums (the
organizer's covers the compressed download, not the decompressed JSONL),
determinism checks, results-retention procedure:
[`docs/REPRODUCIBILITY.md`](docs/REPRODUCIBILITY.md).

## Experiment Log

Every change was preregistered with a hypothesis and a decision rule, run once
on the official evaluator, then kept or reverted — failures recorded at the
same weight as successes. Three experiments (E005, E007, E008) regressed and
were reverted rather than kept for effort spent. Major milestones:

| ID | Change | TechnicalScore |
|---|---|---:|
| E000 | official starter (weak BM25) | 0.106710 |
| E002 | clarification channel opened | 0.427649 |
| E003 | multi-turn evidence accumulation | 0.686904 |
| E011 | word-order reranker + deeper candidate pool | 0.796939 |
| E013 | clause-level evidence + early open questions | 0.839920 |
| **E014** | **idle-turn slate rotation** | **0.861737** |

<details>
<summary>Full experiment table, E000–E014 (all metrics, all decisions)</summary>

| ID | Change | HR@10 | MRR | MTTC | Efficiency | TechnicalScore | |
|---|---|---:|---:|---:|---:|---:|---|
| E000 | official starter (weak BM25) | 0.125 | 0.068034 | 9.81 | 0.119 | 0.106710 | — |
| E001 | category-aware lexical retrieval | 0.160 | 0.066704 | 9.46 | 0.154 | 0.130811 | KEEP |
| E002 | clarification channel | 0.555 | 0.244496 | 7.16 | 0.384 | 0.427649 | KEEP |
| E003 | multi-turn evidence accumulation | 0.835 | 0.498681 | 5.01 | 0.599 | 0.686904 | KEEP |
| E004 | coverage-aware reranking | 0.835 | 0.518149 | 5.01 | 0.599 | 0.692745 | KEEP |
| E005 | explicit intent-override reset | 0.795 | 0.455204 | 5.50 | 0.550 | 0.644061 | REVERT |
| E006 | adaptive catalog-side clarification | 0.835 | 0.522579 | 4.515 | 0.6485 | 0.703974 | KEEP |
| E007 | pool expansion before coverage rerank | 0.805 | 0.497075 | 4.94 | 0.606 | 0.672822 | REVERT |
| E008 | candidate-local IDF reranking | 0.835 | 0.424498 | 4.515 | 0.6485 | 0.674549 | REVERT |
| E010 | word-order proximity reranking | 0.835 | 0.653149 | 4.515 | 0.6485 | 0.743145 | KEEP |
| E011 | pool 50, truncate after rerank | 0.930 | 0.625462 | 3.785 | 0.7215 | 0.796939 | KEEP |
| E012 | pool 50 → 100 | 0.965 | 0.623520 | 3.575 | 0.7425 | 0.818056 | KEEP |
| E013 | clause-level evidence + early open questions | 0.960 | 0.641067 | 2.620 | 0.838 | 0.839920 | KEEP |
| **E014** | **idle-turn slate rotation** | **0.990** | **0.649123** | **2.400** | **0.860** | **0.861737** | **KEEP** |

</details>

Full preregistrations, negative results, and the offline diagnostics that
motivated each step (candidate-recall ceilings, tie analysis):
[`EXPERIMENTS.md`](EXPERIMENTS.md) · [`PROJECT_STATE.md`](PROJECT_STATE.md) ·
[`tools/diagnostics/README.md`](tools/diagnostics/README.md).

## Limitations

- **Evidence is append-only.** No semantic supersession on intent override — an
  explicit erase-on-override reset was tested (E005) and made things worse, so
  it was reverted rather than kept for tidiness. The single largest known
  defect; see "What we'd improve" below.
- **Exact-tie ordering isn't formally guaranteed** across SQLite versions —
  determinism held empirically here, but some ordering paths carry no explicit
  secondary tie-breaker.
- **Empty or punctuation-only first messages return nothing** — an unfixed
  defensive edge case, not an observed evaluator blocker.
- **The reranker depends on literal word-order/substring matching**, which our
  own earlier design record had explicitly forbidden as an overfitting risk;
  later experiments overruled that rule because 98.9% of hits have non-zero
  proximity and every rank-1 hit does. This is safe only because the organizer
  states final evaluation uses the same deterministic templates with no
  undisclosed paraphrasing ([`docs/final_evaluation_faq.md`](docs/final_evaluation_faq.md)
  §1) — a written guarantee we rely on, not a property we verified ourselves.
  Two mechanisms specifically lean on the simulator's own implementation: the
  clause splitter's `;` boundary matches `customer_reply()`'s own join
  character, and the open-ended `other` question takes that function's
  unfiltered wildcard branch — part of E013's turn-2-hit jump (38 → 94
  sessions) may reflect that structural shortcut rather than shopper behavior
  alone, and we cannot separate the two from the public set.
- **No sampling-uncertainty estimate exists.** The evaluator itself is
  deterministic on the fixed 200-session public set — re-running it reproduces
  the same result bit-for-bit. What's missing is a confidence interval for how
  much the score would vary over a *different* sample from the same
  distribution, so small deltas between experiments can't be judged against a
  known noise floor. Session-level results for every KEEP/REVERT decision,
  including where E014's gain concentrates and where E013 redistributed rank,
  are in [`EXPERIMENTS.md`](EXPERIMENTS.md).
- **These are public-set results**, which does not by itself establish relative
  ranking on the unreleased sessions beyond the evaluation mechanics the
  organizer has stated.

**What we'd improve given more time:** semantic supersession at clause
granularity instead of append-only evidence (the untested middle ground
between E005's all-or-nothing reset and today's never-erase); a measured
paraphrase-risk bound to replace the argued one (the D012 stress test was
built and then cancelled once the organizer's no-paraphrasing FAQ answer was
published); a bootstrap-based sampling-uncertainty estimate over the public
sessions, so future deltas can be judged against a confidence interval rather
than argued; and retiring the two remaining simulator-semantics couplings
above.

## Reference

**Code & artifacts**

| | |
|---|---|
| [`starter/agent.py`](starter/agent.py) | the system — 663 lines, stdlib only |
| [`evaluator/local_evaluator.py`](evaluator/local_evaluator.py) | official evaluator — unmodified |
| [`data/public_set.jsonl`](data/public_set.jsonl) | 200 labeled public sessions |
| `data/catalog.jsonl` | 50,000-product frozen catalog (not committed — see Quickstart) |
| [`tests/`](tests/) | evaluator contract + paraphrase robustness tests |
| [`tools/diagnostics/`](tools/diagnostics/) | offline analysis: recall, bounds, paired deltas |

**Documentation**

| Document | What it's for |
|---|---|
| [`docs/REPRODUCIBILITY.md`](docs/REPRODUCIBILITY.md) | environment, catalog setup, exact commands, determinism limits |
| [`docs/PROVENANCE.json`](docs/PROVENANCE.json) | result → commit → agent SHA-256 → artifact SHA-256 → metrics |
| [`EXPERIMENTS.md`](EXPERIMENTS.md) | every experiment, including preregistrations and negative results |
| [`PROJECT_STATE.md`](PROJECT_STATE.md) | current milestone, decisions, open items |
| [`docs/M2_SYSTEM_DESIGN.md`](docs/M2_SYSTEM_DESIGN.md) | pre-implementation design record (v1.1), with a banner noting where the shipped system diverges |
| [`docs/competition_specification.md`](docs/competition_specification.md) · [`docs/final_evaluation_faq.md`](docs/final_evaluation_faq.md) · [`docs/submission_rules.md`](docs/submission_rules.md) | organizer task, scoring, and submission rules |
| [`DATA_ATTRIBUTION.md`](DATA_ATTRIBUTION.md) | Amazon Reviews 2023 attribution and use terms |

**Submitted source integrity.** The submitted `starter/agent.py` is
byte-identical to the file that produced TechnicalScore 0.861737 under the
official evaluator (SHA-256 `1bde5aa6…` — full hash and commit binding in
[`docs/PROVENANCE.json`](docs/PROVENANCE.json)):

```bash
diff <(git show 769bd5f:starter/agent.py) starter/agent.py && echo "byte-identical"
```

## Team

**PumpkinEater** — one-person team, **LIU DIANDIAN** (architecture, all
experiments and KEEP/REVERT decisions, reproducibility discipline). Built with
the help of an AI coding assistant — commit trailers record where — which does
not affect the Feasibility numbers above: the shipped agent itself makes 0
model calls and reports 0 tokens at $0.00.

## Data Source

Catalog and sessions are derived from Amazon Reviews 2023 by McAuley Lab, UCSD.
See [`DATA_ATTRIBUTION.md`](DATA_ATTRIBUTION.md) before using or redistributing
the data. We neither re-host nor redistribute the catalog.
