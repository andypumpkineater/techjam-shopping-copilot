# E006 + M6 — Baseline Diagnostic Snapshot

Captured **2026-08-31** during **R009 — Diagnostic / Research Infrastructure**.

| | |
|---|---|
| Runtime agent | E006 (adaptive catalog-side clarification) + M6 (`_product_terms` memoization) |
| `starter/agent.py` commit | `c8cc1e2` |
| `starter/agent.py` SHA-256 | `8615fd2164bf5dbfa46b2baf802b6a6ebeb70503aa692d0d2e1f77a145e3a67a` |
| Runtime change in R009 | **None** |
| Machine-readable copy | [`E006_M6_BASELINE.json`](E006_M6_BASELINE.json) |

Every number below was produced by an actual run recorded in this session — none
is transcribed from memory. Reproduction commands are given for each block.

> **Evidence class matters.** This document mixes two kinds of evidence and never
> conflates them:
>
> - **Runtime-experiment evidence** — the official evaluator's verdict on the
>   real agent. Only this can support a KEEP.
> - **Diagnostic evidence** — offline analysis over the agent's own query stream.
>   It can *reject* a hypothesis or *bound* what is achievable. It can never
>   establish that a change works.

---

## 1. Official baseline (runtime-experiment evidence)

```bash
python3 -m evaluator.local_evaluator
```

| Metric | Value |
|---|---|
| sample_count | 200 |
| HitRate@10 | **0.835** |
| MRR | **0.522579** |
| MTTC | **4.515** |
| Efficiency | **0.6485** |
| **TechnicalScore** | **0.703974** |

Scenario metrics:

| Scenario | n | HR@10 | MRR | MTTC |
|---|---|---|---|---|
| buying | 80 | 0.8625 | 0.502108 | 3.900 |
| browsing | 80 | 0.825 | 0.479415 | 4.675 |
| intent_override | 30 | 0.800 | 0.658135 | 5.333333 |
| boundary | 10 | 0.800 | 0.625 | 5.700 |

Reported token usage: 0 prompt / 0 completion (no model on the scored path).

R009 regression: identical to the previously recorded E006 + M6 baseline in
every overall field, every scenario field, and all 200 per-session outcomes
(0 mismatches). Wall clock 73.4 s.

---

## 2. Candidate oracle — D-1 (diagnostic evidence)

```bash
python3 -m tools.diagnostics.d1_candidate_oracle
```

Best (smallest) deep BM25 rank the target attains at any turn, under the agent's
**own** accumulated query. Probe depth 1000.

| Depth N | Recall@N |
|---|---|
| 10 | 0.805 |
| 20 | 0.875 |
| 50 | 0.935 |
| 100 | **0.990** |
| 200 | 0.995 |
| 500 | 1.000 |

Distribution of best deep rank: rank 1 → 85 sessions; 2–3 → 33; 4–10 → 43;
11–20 → 14; 21–50 → 12; 51–100 → 11; 101–1000 → 2; unreachable → 0.

Of the 33 sessions the agent misses, **none** is unreachable: 5 had the target
inside deep top-10 at some turn, 19 in 11–50, 9 in 51–200. Of the 167 hits, 24
had a better deep rank available at some turn than the rank actually scored.

**Reading.** HR@10 is 0.835 while Recall@100 is 0.990. The target is nearly
always reachable; the loss is in **ranking**, not in candidate generation. This
bounds the value of any recall-oriented work (extra retrieval routes, synonym
expansion, dense retrieval) at roughly one point.

---

## 3. Perfect-reranker upper bounds — D-2 (diagnostic evidence)

```bash
python3 -m tools.diagnostics.d2_reranker_bounds
```

Oracle places the target at rank 1 whenever it is inside a depth-P pool. Hits are
taken at the first turn permitted by the intent_override gate. **These are upper
bounds, not predictions** — no real reranker reaches them.

| Bound | HR@10 | MRR | MTTC | Eff | TS | vs baseline |
|---|---|---|---|---|---|---|
| observed agent | 0.8350 | 0.522579 | 4.515 | 0.6485 | 0.703974 | — |
| perfect order, **current top-10** | 0.8350 | 0.835000 | 4.515 | 0.6485 | **0.797700** | +0.0937 |
| perfect reranker, pool 10 | 0.8050 | 0.805000 | 4.840 | 0.6160 | 0.767200 | +0.0632 |
| perfect reranker, pool 20 | 0.8750 | 0.875000 | 4.030 | 0.6970 | 0.839400 | +0.1354 |
| perfect reranker, pool 30 | 0.9150 | 0.915000 | 3.515 | 0.7485 | 0.881700 | +0.1777 |
| perfect reranker, pool 50 | 0.9350 | 0.935000 | 3.240 | 0.7760 | 0.903200 | +0.1992 |
| perfect reranker, pool 100 | 0.9900 | 0.990000 | 2.555 | 0.8445 | **0.960900** | +0.2569 |
| perfect reranker, pool 200 | 0.9950 | 0.995000 | 2.055 | 0.8945 | 0.974900 | +0.2709 |

**Reading.** Reordering only the ten ids the agent already returns is worth
+0.094 — more than every experiment since E003 combined. Pool depth prices the
second stage: 10 → 100 moves the ceiling from 0.767 to 0.961.

> ### Correction to the 2026-08-31 audit
>
> The audit's pool-depth oracle table reported TS 0.7722 / 0.8447 / 0.8872 /
> 0.9089 / 0.9677 / 0.9822 for P = 10/20/30/50/100/200. Those values were
> computed **without** the intent_override gate, while the audit's other two
> tables were gated. R009 applies the gate consistently, which matches
> `evaluator/local_evaluator.py:234, :252, :259`.
>
> Both figures were reproduced from the same source data during R009: the ungated
> path returns the audit's numbers exactly, and the gated path returns the values
> in the table above exactly. Root cause is the gate alone — query
> reconstruction, session simulation, candidate depth, and target-rank definition
> are identical. **The gated values above supersede the audit's table.** The
> audit's qualitative conclusion is unaffected.

---

## 4. Counterfactual reranker bench — D-3 (diagnostic evidence)

Same agent, same evidence stream, same dialogue, same candidate pool; only the
final top-10 selection rule differs. Override-gated. These are **real rules**,
not oracles.

### Pool depth 100

```bash
python3 -m tools.diagnostics.d3_counterfactual_bench --pool 100
```

| Scorer | HR@10 | MRR | MTTC | TS | vs baseline |
|---|---|---|---|---|---|
| *(observed agent)* | 0.8350 | 0.522579 | 4.515 | 0.703974 | — |
| `bm25` | 0.8050 | 0.521002 | 4.840 | 0.682001 | −0.0220 |
| `cov` (E004, current) | 0.8200 | 0.519141 | 4.745 | 0.690842 | −0.0131 |
| `frac` | 0.8400 | 0.501833 | 4.545 | 0.699650 | −0.0043 |
| `gidf` (global catalog IDF) | 0.8150 | 0.507294 | 4.795 | 0.683788 | −0.0202 |
| `full` | 0.8000 | 0.522875 | 4.880 | 0.679263 | −0.0247 |
| `cov+gidf` | 0.8200 | 0.512488 | 4.750 | 0.688746 | −0.0152 |
| `full+frac` | 0.8500 | 0.511262 | 4.485 | 0.708679 | +0.0047 |
| `phrase_n2` | 0.9000 | 0.547319 | 4.005 | 0.754096 | +0.0501 |
| `phrase_n3` | 0.9500 | 0.591353 | 3.690 | 0.798606 | +0.0946 |
| `phrase_n4` | 0.9600 | 0.617048 | 3.575 | 0.813614 | +0.1096 |
| `phrase_n8` | 0.9600 | 0.633387 | 3.545 | 0.819116 | +0.1151 |

### Pool depth 60

```bash
python3 -m tools.diagnostics.d3_counterfactual_bench --pool 60 \
    --scorers bm25,phrase_n2,phrase_n3,phrase_n4,phrase_n8
```

| Scorer | HR@10 | MRR | MTTC | TS | vs baseline |
|---|---|---|---|---|---|
| `bm25` | 0.8050 | 0.521002 | 4.840 | 0.682001 | −0.0220 |
| `phrase_n2` | 0.8900 | 0.547869 | 4.055 | 0.748261 | +0.0443 |
| `phrase_n3` | 0.9300 | 0.591250 | 3.805 | 0.786275 | +0.0823 |
| `phrase_n4` | 0.9350 | 0.612403 | 3.740 | 0.796421 | +0.0924 |
| `phrase_n8` | 0.9350 | 0.628575 | 3.710 | 0.801873 | +0.0979 |

All pool-100 bag-of-words values and all pool-60 phrase values reproduce the
2026-08-31 audit **exactly**.

### What this establishes, and what it does not

**Established (diagnostic):** every bag-of-words re-weighting tested — binary
coverage, per-unit term recall, global catalog IDF, full-unit containment, and
two pairwise combinations — lands within roughly ±0.02 of the current system,
with the best at +0.005. The bag-of-words overlap signal is substantially
exhausted. This is consistent with E007 and E008 both failing: each re-weighted
that same exhausted dimension.

**Not established:** that word-order / proximity ranking improves the agent.
`phrase_*` is a **counterfactual measurement on a fixed dialogue trajectory**. A
real implementation changes the candidate set, which changes `_select_attribute`,
which changes what the simulator discloses, which changes every later turn. The
counterfactual cannot model that feedback.

**Status of E010 (proximity-aware reranking): PREREGISTERED HYPOTHESIS, NOT RUN.**
No official evaluator run has been performed for any proximity ranking rule. It
must not be described as validated, promising-and-therefore-adopted, or as having
a known effect size.

Note also that `phrase_n3` already captures roughly 84 % of `phrase_n8`'s
counterfactual delta, and 4 → 8 is worth about +0.005. Short-range adjacency, not
long verbatim quotation, carries the signal — relevant to paraphrase robustness,
which is **untested** and is the subject of the planned D012 stress test.

---

## 5. Known limitations of this snapshot

1. **Conservative replay bias.** The replay stops when the real agent hits, as
   the evaluator does. A counterfactual rule is never credited for turns the real
   agent did not reach, biasing counterfactual scores downward.
2. **Fixed trajectory.** All D-2/D-3 numbers hold the dialogue constant. Any real
   ranking change perturbs the trajectory; the counterfactual cannot model that.
3. **Public set only.** n = 200, and `difficulty_bucket` is perfectly collinear
   with `scenario_type`, so it adds no independent diagnostic axis. The
   `boundary` bucket (n = 10) cannot support any conclusion.
4. **No run-to-run variance estimate.** The evaluator is deterministic, but no
   bootstrap confidence interval exists yet (planned as D-6), so small deltas
   such as E004's +0.0058 and E006's +0.0112 have never been separated from
   noise.
5. **Private-set generalization is unmeasured.** No paraphrase stress test exists
   yet (planned as D012).
