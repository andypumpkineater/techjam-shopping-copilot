# Shopping Copilot

**TikTok TechJam 2026 — Track 4: Conversational E-Commerce Search**

A deterministic conversational shopping agent that opens with wide, open-ended
questions, splits every reply into its individual constraints, retrieves broadly
and reranks by word-order proximity — reaching **0.960 HitRate@10** and
**0.839920 TechnicalScore** with no LLM calls, no network on the scored path,
and no third-party runtime dependencies.

```text
HitRate@10  0.960   MRR  0.641067   MTTC  2.620   Efficiency  0.838
TechnicalScore  0.839920     tokens 0     model cost $0.00     deps 0
Official evaluator · 200 public sessions · unmodified evaluator/local_evaluator.py
```

---

## What It Is

A simulated customer opens with a short, often vague message. A hidden target
product sits in a frozen 50,000-product catalog. Within at most 10 turns, the
agent must place that exact `parent_asin` inside its Top 10.

Shopping Copilot treats this as **retrieval under uncertainty** rather than a
language problem. Every turn it does three things:

1. **Accumulates** the conversation into a single lexical query, discarding the
   simulator's information-free replies.
2. **Retrieves wide, reranks, then truncates.**
3. **Asks wide first, then narrow** — the first two turns ask an open-ended
   question; after that the Top 10 it just produced decides what it asks about.

There is no model in the loop. The whole system is Python standard library:
`json`, `re`, `sqlite3`, `collections`, `pathlib`, with SQLite's built-in FTS5
providing BM25.

## Results

Official evaluator, 200 public sessions, unmodified `evaluator/local_evaluator.py`.

| Metric | Our final system (E013) | Official starter (E000) |
|---|---:|---:|
| HitRate@10 | **0.960** | 0.125 |
| MRR | **0.641067** | 0.068034 |
| MTTC | **2.620** | 9.81 |
| Efficiency | **0.838** | 0.119 |
| **TechnicalScore** | **0.839920** | 0.106710 |

By scenario:

| Scenario | n | HR@10 | MRR | MTTC |
|---|---:|---:|---:|---:|
| buying | 80 | 0.950 | 0.577996 | 2.200 |
| browsing | 80 | 0.975 | 0.633408 | 2.375 |
| intent_override | 30 | 0.933333 | 0.809722 | 4.200 |
| boundary | 10 | 1.000 | 0.700952 | 3.200 |

> Scenario-level results are descriptive; the boundary bucket contains only 10
> public sessions.

Every number above is bound to the exact code that produced it in
[`docs/PROVENANCE.json`](docs/PROVENANCE.json) — commit → `starter/agent.py`
SHA-256 → evaluator command → artifact SHA-256 → metrics. The per-session record
is [`docs/diagnostics/E013_SESSIONS.json`](docs/diagnostics/E013_SESSIONS.json).
Each experiment is run on the official evaluator exactly once, by policy; the
E011 result was additionally reproduced independently on 2026-08-31 and came
back byte-identical, which is the evidence we have for determinism of this
pipeline. No second run of E013 has been performed.

## Why It Works

Four ideas carry almost all of the improvement.

**Clarification is a retrieval instrument, not politeness.** `ask_attribute` is
the only channel through which the simulator volunteers new constraints, and
opening it at all was the single largest jump this project measured. Choosing
*which* attribute to open it with is done from the catalog side: for each
candidate attribute the agent counts how many of its current Top 10 carry a value
for it and how many *distinct* values appear. An attribute the candidates all
agree on buys nothing; the agent asks about the one they most disagree on.

**Open-ended questions beat well-chosen narrow ones — at first.** Most of what a
shopper cares about does not fall into any single attribute category, so a narrow
question can only ever collect the fraction that happens to match its category.
The first two turns therefore ask an open-ended question and collect whatever the
customer volunteers; only from turn 3, once the obvious constraints are in hand,
does the catalog-side attribute scoring above take over. This alone cut mean
time-to-conversion by nearly a full turn: hits at turn 2 went from 38 to 94 of
200 sessions, and the tail past turn 6 disappeared.

**Evidence must survive the turn it arrived in — and stay separable.** Each
admitted user message is kept and joined into one accumulated query, with the
simulator's no-preference and not-quite-right templates deterministically
excluded so boilerplate never dilutes it. Messages are split at clause
boundaries before scoring, so a reply that states two constraints becomes two
independent pieces of evidence rather than one blurred one. That matters because
the reranker below credits each evidence unit only once: without the split, the
second constraint in a sentence is invisible to ranking.

**Order is a stronger signal than overlap.** Two candidates can match the same
bag of words and be entirely different products. The reranker scores each
candidate by the longest contiguous run of the user's own words (n-grams up to
length 4) that appears in the product's text, summed across evidence units, and
uses bag-of-words coverage only to break ties.

Ordering strength is what makes the structural choice pay off. **Retrieve wide →
rerank → truncate**: a pool already cut to 10 can only be reordered, which moves
MRR and nothing else. Reranking 100 and cutting afterwards lets a candidate at pool
rank 80 reach the returned ten — which is where HitRate@10 comes from.

## Architecture

```text
  turn t: user message
        │
        ▼
  ┌───────────────────────────────────────────────────────────┐
  │ EVIDENCE            append if not an information-free      │
  │                     simulator template; split into clause  │
  │                     units, join into one lexical query     │
  └───────────────────────────────────────────────────────────┘
        │  accumulated query (deduped terms, capped at 40)
        ▼
  ┌───────────────────────────────────────────────────────────┐
  │ RETRIEVE WIDE       SQLite FTS5 / BM25 over 50,000 items   │
  │                                                            │
  │   category-scoped primary ......... 70 pool slots          │
  │     (relaxation ladder: full → last2 → last1 → segment)    │
  │   global insurance ................ 30 pool slots          │
  │     (backfilled from global BM25 if primary under-fills)   │
  │                                    ─────────────────────   │
  │                                    POOL_DEPTH = 100        │
  └───────────────────────────────────────────────────────────┘
        │  100 candidates
        ▼
  ┌───────────────────────────────────────────────────────────┐
  │ RERANK              sort by (word-order proximity,         │
  │                     then coverage); stable, so the         │
  │                     BM25 order survives full ties          │
  │                     n-grams of length 2..N_MAX = 4         │
  └───────────────────────────────────────────────────────────┘
        │  100 candidates, reordered
        ▼
  ┌───────────────────────────────────────────────────────────┐
  │ TRUNCATE            cut to top_k = 10  ← only now          │
  └───────────────────────────────────────────────────────────┘
        │  final Top 10  ─────────────────────►  recommendations
        ▼
  ┌───────────────────────────────────────────────────────────┐
  │ ASK                 turns 1-2: open-ended "other";         │
  │                     turn 3+: score attributes against THIS │
  │                     Top 10, pick the most distinct  ────►  ask_attribute
  └───────────────────────────────────────────────────────────┘
        │
        ▼
  simulator discloses a constraint → becomes evidence at turn t+1
```

The loop closes: what the agent retrieves determines what it asks, and what it
asks determines what it can retrieve next turn.

Implementation: [`starter/agent.py`](starter/agent.py), 619 lines, standard
library only.

## Quickstart

Python 3.11.15 verified; the agent needs SQLite with FTS5 (bundled with CPython).

```bash
# 0. Nothing to install — there are no third-party dependencies.
python3 -c "import sqlite3; sqlite3.connect(':memory:').execute('CREATE VIRTUAL TABLE t USING fts5(a)'); print('FTS5 OK')"
```

```bash
# 1. Obtain the catalog. It is a 60 MB organizer artifact and is NOT committed
#    here. Get catalog.jsonl.gz from the official TechJam 2026 release,
#    following the organizer's data instructions, then:
gzip -dk catalog.jsonl.gz
mv catalog.jsonl data/catalog.jsonl
wc -l data/catalog.jsonl        # must print 50000
```

Verify the downloaded `catalog.jsonl.gz` against the organizer's published
`SHA256SUMS`. Note that the organizer checksum covers the **compressed** file;
the decompressed JSONL is a different byte representation with a different hash,
and no organizer-endorsed verification of the decompressed file is claimed.
Data instructions live in [`data/README.md`](data/README.md); full detail,
including both hashes, is in
[`docs/REPRODUCIBILITY.md`](docs/REPRODUCIBILITY.md) §2.

```bash
# 2. Run the tests (standard library, a few seconds).
python3 -m unittest discover -s tests
```

```bash
# 3. Run the unmodified official evaluator over the 200 public sessions.
python3 -m evaluator.local_evaluator
```

That writes `results.json` with per-session results and the aggregate metrics in
the table above. To keep a run under its own name:

```bash
python3 -m evaluator.local_evaluator --output results_myrun.json
```

No API keys, credentials, or environment variables are required.
Full runbook — environment, checksums, determinism, results-retention procedure:
[`docs/REPRODUCIBILITY.md`](docs/REPRODUCIBILITY.md).

## How We Got Here

Every experiment was preregistered with a hypothesis and a decision rule, run
exactly once on the official evaluator, then kept or reverted. Failures are in the
record at the same weight as successes. Six steps carry the story:

- **E002 — open the clarification channel.** The starter never asked anything.
  Adding a deterministic, label-free attribute question was the largest single
  jump of the project: TechnicalScore 0.130811 → 0.427649.
- **E003 — make evidence survive.** Persisting admitted user messages across
  turns, while deterministically excluding the simulator's information-free
  templates, produced the second large jump: 0.427649 → 0.686904.
- **E007 / E008 — two controlled failures.** E007 deepened the candidate pool
  under the then-current coverage reranker (−0.031). E008 added candidate-local
  IDF weighting to that reranker (−0.029). Both were reverted.
- **R009 — diagnostic infrastructure, no runtime change.** After two experiments
  each spent a full official-evaluator slot to return a scalar of about −0.03, we
  built offline candidate-recall, ranking-bound, counterfactual, and paired-delta
  tooling instead. This is where we stopped guessing and measured the bottleneck.
- **E010 — a signal class we did not previously have.** Word-order proximity.
  Confined to a 10-deep pool it could only move MRR: +0.130570, and nothing else.
- **E011 — the stronger ranker with a deeper pool.** HitRate@10 0.835 → 0.930,
  MTTC 4.515 → 3.785, TechnicalScore 0.743145 → **0.796939**.
- **E012 — E011's own extrapolation, falsified.** E011's record predicted that
  deepening the pool costs MRR in proportion to depth. Doubling 50 → 100 cost
  only 7% of that predicted rate: HitRate@10 0.930 → 0.965, TechnicalScore
  → **0.818056**. The correction is in the record next to the claim it replaced.
- **E013 — two changes that only work together.** Clause-level evidence units
  and front-loaded open questions each *lose* score alone (−0.0042 and −0.0017
  offline); together they gain +0.0219. Preregistered and run as one indivisible
  experiment for exactly that reason. MRR rose for the first time in the project
  (+0.017547) and MTTC fell 0.955: TechnicalScore → **0.839920**.

E007 showed that deeper retrieval was harmful under the earlier coverage
reranker. After E010 introduced a stronger word-order ranking signal, E011 showed
that deeper retrieval could become beneficial. The contrast between the two
supports the interpretation that candidate-depth expansion had been
ranker-limited. That is an interpretation of two measured results, not a formal
proof.

Full progression, official evaluator, 200 public sessions:

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
| **E013** | **clause-level evidence + early open questions** | **0.960** | **0.641067** | **2.620** | **0.838** | **0.839920** | **KEEP** |

R009 is absent from the table by design: it changed no runtime behavior, so its
expected TechnicalScore impact was exactly zero. It could not be declared complete
until it reproduced the E006 baseline bit-for-bit, and it did.

Raw records for all of the above: [`EXPERIMENTS.md`](EXPERIMENTS.md).

## How We Knew Where to Look

Two offline findings shaped the final architecture. Both are **diagnostic —
offline analysis, not official measured system results** — and are not
comparable to the Results table above.

**Deep candidate recall was already high.** With the system at HitRate@10 0.835,
offline candidate analysis found Recall@100 = 0.990 against the agent's own
accumulated query. That indicated the remaining opportunity was primarily in
converting deep candidate availability into a better final Top 10, and it bounded
how much further recall-oriented work could be worth.

**The final system is close to what its own pool depth allows.** At pool 50 the
measured HitRate@10 was 0.930 against an offline pool-50 candidate-recall ceiling
of 0.935 — which is precisely why the pool was doubled. At pool 100 the offline
ceiling rises to 0.985 and measured HitRate@10 is 0.960. These ceilings are
diagnostic figures under one specific pool depth and setting, not universal
maxima.

**The remaining ranking gap is not reachable with lexical signals.** After the
pool expansion, offline analysis found that 86% of the sessions where the target
sits below rank 1 have *no* candidate strictly outranking it — the target is tied,
in groups of typically 9. Adding true BM25 as a third sort key recovers only
+0.0029 of that, so the ties are real ambiguity rather than correctable
mis-ordering. E013 recovered part of it from the other side, by raising the
resolution of the score's *inputs* rather than adding a key. What is left would
require a new signal class (semantic / embedding / LLM); we did not add one, for
the reason given under Feasibility.

The diagnostic tooling and its ground-truth boundary — offline error analysis
only, never reachable from agent code — are documented in
[`tools/diagnostics/README.md`](tools/diagnostics/README.md), with the baseline
snapshot in
[`docs/diagnostics/E006_M6_BASELINE.md`](docs/diagnostics/E006_M6_BASELINE.md).
Every artifact in this repository carries an evidence class in
[`docs/PROVENANCE.json`](docs/PROVENANCE.json).

## Feasibility

| Item | Value |
|---|---|
| Model calls on the scored path | **0** |
| External API calls | **0** |
| Network access required on the scored path | **none** |
| Reported `usage` tokens (prompt / completion / total) | **0 / 0 / 0** |
| Model / API cost | **$0.00** |
| Third-party runtime dependencies | **none** (Python stdlib only) |
| Credentials / environment variables required | **none** |
| 200-session evaluator run, wall clock | **411.19 s** |

The runtime figure is **one measured wall-clock run in the documented
environment** (CPython 3.11.15, macOS Darwin 25.5.0, arm64), covering one full
50,000-product FTS5 index build plus all 200 sessions. It is not a latency
guarantee and different hardware will differ.

The zero token count is an honest zero, not an omission: no model is invoked, so
`usage` reports `{"prompt_tokens": 0, "completion_tokens": 0}`. Network access
and external APIs *are* permitted in final evaluation
([`docs/final_evaluation_faq.md`](docs/final_evaluation_faq.md) §2); our scored
path stays offline by design choice, not because of any restriction.

The agent is deterministic in the tested environment — no `random`, no `time`, no
concurrency, no hashing of unordered structures into output order. That was
checked directly at E011, where re-running the official evaluator at the
submitted commit reproduced the tracked per-session snapshot byte-for-byte. Later
experiments are run once each by policy, so the current commit's snapshot has not
been independently re-derived.

## Demo

[**One complete multi-turn session**](docs/DEMO_SESSION.md) — a real
`intent_override` session, turn by turn: two open-ended questions, a reply
carrying two constraints at once (`Water Resistant; 3 Year Battery`) that the
clause splitter separates, the ranking moving as evidence arrives, and the
target reaching rank 1 at turn 3.

The transcript is generated by `tools/demo_session.py`, never hand-edited, and
its outcome is cross-checked against the official evaluator's tracked
per-session record:

```bash
python3 -m tools.demo_session --sample-id public_0003 --verify
```

## Limitations

- **Evidence is append-only.** There is no semantic supersession, so in an intent
  override the replaced preference stays in the accumulated query alongside the
  new one. An explicit erase-on-override reset was tested (E005) and made things
  worse, so it was reverted rather than kept for tidiness.
- **Exact-tie ordering is not formally guaranteed.** Determinism held empirically
  in the verified environment, but some SQLite ordering paths carry no explicit
  deterministic secondary tie-breaker, so the ordering of exact ties is not
  guaranteed across all SQLite versions.
- **Empty or punctuation-only first messages return nothing.** No lexical
  expression can be built, so no recommendations are produced. This is an unfixed
  defensive edge case, not an observed evaluator blocker.
- **The system depends on exact substring matching.** The proximity reranker
  tests the user's own word n-grams literally against product text. Our own
  architecture record (`docs/M2_SYSTEM_DESIGN.md`, overfitting rule #1) forbade
  exactly this, and later experiments overruled it: 98.9% of hits have non-zero
  proximity, and every rank-1 hit does, so E010 + E011 rest on it almost
  entirely. The organizer states that the final evaluation uses the same
  deterministic templates with no undisclosed paraphrasing
  ([`docs/final_evaluation_faq.md`](docs/final_evaluation_faq.md) §1), which is
  what makes this acceptable — but it is a concentrated risk, not a diversified
  one, and it is a written guarantee we are relying on rather than a property we
  verified.
- **Two mechanisms are coupled to the published simulator's own semantics.** The
  clause splitter treats `;` as a boundary, which is also the character
  `customer_reply()` uses to join two constraints; and the open-ended `other`
  question uses that function's wildcard branch, which bypasses attribute
  classification. Both are disclosed in the E013 preregistration. The underlying
  product claim — open questions collect more than narrow ones — is real
  independently of the simulator, but the measured size of the effect is not
  established outside it.
- **No run-to-run variance estimate exists**, so small deltas between experiments
  cannot be separated from noise. At n=200 a TechnicalScore move of 0.021
  corresponds to roughly 7 sessions; the final system's margin over its
  predecessor (+0.0219) sits just above that scale, not far above it.
- **These results are public-set results.** Evidence from the 200 public sessions
  does not by itself establish relative ranking on the unreleased sessions,
  beyond the evaluation mechanics the organizer has stated.
- **The final change is not uniformly good.** E013 raised the aggregate score,
  but within it 43 sessions lost rank while 39 gained, and 4 previously-found
  targets were lost. MRR rose because the gains were larger per session, not
  because every session improved.

## Repository Map

```text
starter/agent.py                    the system (619 lines, stdlib only)
evaluator/local_evaluator.py        official evaluator — unmodified, never edited
data/public_set.jsonl               200 labeled public sessions
data/catalog.jsonl                  50,000-product frozen catalog (not committed)
requirements.txt                    explicit no-third-party-dependency manifest
tests/                              evaluator contract + paraphrase robustness tests
tools/diagnostics/                  offline analysis: recall, bounds, paired deltas
docs/diagnostics/                   tracked per-session result snapshots + baseline
EXPERIMENTS.md                      full preregistration and result record
PROJECT_STATE.md                    milestone state and decision record
```

## Documentation

| Document | What it is for |
|---|---|
| [`docs/REPRODUCIBILITY.md`](docs/REPRODUCIBILITY.md) | Environment, catalog setup, exact commands, runtime, determinism limits, results-retention procedure |
| [`docs/PROVENANCE.json`](docs/PROVENANCE.json) | Machine-checkable binding: result → commit → agent SHA-256 → artifact SHA-256 → metrics |
| [`EXPERIMENTS.md`](EXPERIMENTS.md) | Every experiment, including preregistrations, negative results, and reverted changes |
| [`PROJECT_STATE.md`](PROJECT_STATE.md) | Current milestone, decisions, and open items |
| [`docs/M2_SYSTEM_DESIGN.md`](docs/M2_SYSTEM_DESIGN.md) | Architecture design record (v1.1) |
| [`tools/diagnostics/README.md`](tools/diagnostics/README.md) | Diagnostic tooling and its ground-truth boundary |
| [`docs/competition_specification.md`](docs/competition_specification.md) | Organizer task, protocol, and scoring spec |
| [`docs/final_evaluation_faq.md`](docs/final_evaluation_faq.md) | Organizer final-evaluation, network, hardware, and judging policy |
| [`docs/submission_rules.md`](docs/submission_rules.md) | Organizer submission requirements |
| [`DATA_ATTRIBUTION.md`](DATA_ATTRIBUTION.md) | Amazon Reviews 2023 attribution and use terms |

## Submitted Source Integrity

The submitted `starter/agent.py` is byte-identical to the file that produced the
reported TechnicalScore of 0.839920 under the official evaluator.

```text
starter/agent.py SHA-256
47543f3dc10df61c02ffafb24f1ee1a9cd56c52dd83c7cb35aa29e082b9808ee
```

Verify in one line:

```bash
diff <(git show 01ea938:starter/agent.py) starter/agent.py && echo "byte-identical"
```

## Team

[HUMAN INPUT REQUIRED: team roster and contributions]

## Data Source

The catalog and sessions are derived from Amazon Reviews 2023 by McAuley Lab,
UCSD. See [`DATA_ATTRIBUTION.md`](DATA_ATTRIBUTION.md) before using or
redistributing the data. We neither re-host nor redistribute the catalog.
