# Reproducibility

How to reproduce the reported result from a clean checkout, what was actually
measured, and how results are bound to code.

This document states measurements, not claims. Every number here is either
computed from a tracked artifact in this repository or was produced by a run
recorded in `docs/PROVENANCE.json`. Where a figure is
environment-specific, it says so.

---

## 1. Environment

Verified environment for the reported result:

| Item | Value |
|---|---|
| Python | CPython 3.11.15 |
| OS / arch | macOS, Darwin 25.5.0, arm64 |
| SQLite library | 3.53.4 (CPython-bundled), FTS5 extension available |
| Third-party packages | none |
| Network | not used on the scored path |

The scored path (`starter/agent.py`) imports only `json`, `re`, `sqlite3`,
`collections`, and `pathlib` — all Python standard library. See
`requirements.txt`, which is a deliberate no-dependency manifest.

The organizer README recommends "Python 3.10 or later". We report only the
version we actually tested (3.11.15) and do not claim a wider supported range.

The agent requires SQLite built with FTS5. Verify before running:

```bash
python3 -c "import sqlite3; sqlite3.connect(':memory:').execute('CREATE VIRTUAL TABLE t USING fts5(a)'); print('FTS5 OK')"
```

## 2. Catalog prerequisite

`data/catalog.jsonl` is **not committed**. It is a 60 MB frozen artifact
published by the organizer and is excluded by `.gitignore`, consistent with
`docs/final_evaluation_faq.md` section 4 ("Large assets should be supplied
through documented and reproducible download instructions rather than committed
directly to the repository"). Nothing in this repository runs without it.

Obtain it from the **organizer's upstream repository**, not from this fork:

```
https://github.com/TechJam2026/techjam-conversational-search
```

Follow the organizer's own instructions in `README.md` ("Download the Catalog")
and `data/README.md`: download `catalog.jsonl.gz` from the published GitHub
Release, verify it against the organizer's published `SHA256SUMS`, then

```bash
gzip -dk catalog.jsonl.gz
mv catalog.jsonl data/catalog.jsonl
wc -l data/catalog.jsonl        # must print 50000
```

> **HUMAN CHECK REQUIRED.** The exact Release asset URL has not been verified
> from this environment (no network access during preparation). What is
> verified from git: the upstream remote carries the tag `participant-kit` at
> commit `2a6cc8e`, and our fork `origin` carries **no tags at all** — so the
> catalog must be taken from upstream. Do not direct judges at a Release on our
> fork.

### Checksums — two different files, two different hashes

These are distinct artifacts and must not be conflated:

| File | SHA-256 | Source of the value |
|---|---|---|
| `catalog.jsonl.gz` (organizer's compressed artifact) | `07fd142631fd6b03e2b4d09988c3eb7d53720e9d57010c79db48eeaada50a8f8` | organizer's published `SHA256SUMS`, verified at download |
| `data/catalog.jsonl` (our local decompressed file) | `da979b05a68af864cb0dcf9ee6a81c010c7e66a57978ad286c7a2e005fc69a67` | computed locally |

The organizer checksum verified the **compressed** download. The decompressed
JSONL is a different byte representation and therefore has a different hash. We
record our local decompressed hash for our own run-to-run binding only; **no
organizer-endorsed cryptographic verification of the decompressed file is
claimed.**

We neither re-host nor redistribute the catalog.

## 3. Setup

```bash
git clone <this repository>
cd techjam-conversational-search

# optional; nothing needs installing
python3 -m venv .venv

# place the catalog as described in section 2, then confirm:
wc -l data/catalog.jsonl        # 50000
wc -l data/public_set.jsonl     # 200
```

Run the test suite (standard library only, a few seconds):

```bash
python3 -m unittest discover -s tests
```

## 4. Exact evaluator command

```bash
python3 -m evaluator.local_evaluator
```

This runs the **unmodified** official evaluator over the 200 public sessions and
writes `results.json`. To keep a run instead of overwriting the working file:

```bash
python3 -m evaluator.local_evaluator --output results_myrun.json
```

`evaluator/` is untouched in this repository and must stay that way
(`docs/submission_rules.md`, "Disallowed Submission Contents").

## 5. Final measured metrics

Official evaluator, 200 public sessions, current system (E014):

| Metric | Value |
|---|---|
| HitRate@10 | **0.990** |
| MRR | **0.649123** |
| MTTC | **2.400** |
| Efficiency | **0.860** |
| **TechnicalScore** | **0.861737** |

By scenario:

| Scenario | n | HitRate@10 | MRR | MTTC |
|---|---|---|---|---|
| buying | 80 | 0.9875 | 0.598135 | 1.9375 |
| browsing | 80 | 1.000 | 0.637574 | 2.2125 |
| intent_override | 30 | 0.966667 | 0.820833 | 3.933333 |
| boundary | 10 | 1.000 | 0.634286 | 3.000 |

Per-session outcomes for this exact run are tracked verbatim as
`docs/diagnostics/E014_SESSIONS.json`. The five prior KEEP runs are tracked the
same way (`E006_M6_SESSIONS.json`, `E010_SESSIONS.json`, `E011_SESSIONS.json`,
`E012_SESSIONS.json`, `E013_SESSIONS.json`) and all six are bound to their code
in `docs/PROVENANCE.json`.

These are **official evaluator results**. Oracle bounds and counterfactual
figures appearing elsewhere in this repository (`docs/diagnostics/E006_M6_BASELINE.json`,
D-1 / D-2 / D-3) are **diagnostic**, are upper bounds or offline replays, and
are not comparable to the table above. `docs/PROVENANCE.json` labels
every artifact with its evidence class.

## 6. Runtime

| Measurement | Value |
|---|---|
| 200-session evaluator run, wall clock | **415.83 s** |
| Measured on | CPython 3.11.15, macOS Darwin 25.5.0, arm64 |
| Per session, derived | ~2.1 s |

This is a **single measurement on one machine**, not a latency guarantee. It
includes one full index build (the 50,000-product in-memory SQLite FTS5 index is
constructed once per `Agent` instantiation) plus all 200 sessions. Different
hardware will differ. `docs/final_evaluation_faq.md` section 3 confirms there is
no standardized organizer hardware and no separate per-response timeout.

Wall clocks for every accepted system, as recorded in `EXPERIMENTS.md`:
E006+M6 73.4 s, E010 101.4 s, E011 282.9 s, E012 444.30 s, E013 411.19 s,
E014 415.83 s. The step change is E011/E012 — reranking a 100-deep pool instead
of a 10-deep one — and E013 and E014 are flat against E012 (E014's rotation adds
one list slice and no retrieval or ranking work). The cost was disclosed and
accepted rather than optimized, because the E011 preregistration forbade bundling
a performance experiment into a capability experiment.

## 7. Model, tokens, and cost

| Item | Value |
|---|---|
| Model calls on the scored path | **0** |
| External API calls | **0** |
| Network access required | **none** |
| Reported `usage` tokens (prompt / completion / total) | **0 / 0 / 0** |
| Model / API cost | **$0.00** |

`starter/agent.py` returns `{"prompt_tokens": 0, "completion_tokens": 0}` because
no model is invoked. This is an honest zero, not an omission —
`docs/final_evaluation_faq.md` section 7 permits non-LLM systems to report zero
usage.

Per `docs/final_evaluation_faq.md` section 2, network access and external APIs
*are* permitted in final evaluation. Our scored path remains offline by design
choice, not because of an organizer restriction.

No credentials, API keys, or environment variables are required to run anything
in this repository. There is therefore no environment-variable manifest.

## 8. Determinism and reproducibility notes

**Reproduced at the current baseline.** On 2026-09-01, during the final
submission audit, the official evaluator was re-run at the submitted commit
`769bd5f` (`starter/agent.py` SHA-256
`1bde5aa6bdd5a52c0eb88d744c394263a64fbb0ab3606bb8a157b3b095274643`) and produced
output **byte-identical** to the tracked snapshot
`docs/diagnostics/E014_SESSIONS.json` (SHA-256
`e69e83c693ecd7992ad6119202425ff82ac458b2e552c35d78437c6b6e05843a`) — same
TechnicalScore 0.861737, same 200 per-session records, same bytes. Wall clock
425.14 s.

Read that for exactly what it is:

- It **is** evidence that this pipeline is deterministic on this machine, and
  that the reported score is not a one-off draw.
- It is **not** a second independent measurement used to justify anything. It ran
  *after* the E014 KEEP decision was already recorded, no algorithm or threshold
  was revisited on the basis of it, and the KEEP still rests on the single
  preregistered run. Project policy remains **one official run per experiment**;
  a post-freeze determinism check on a frozen baseline is not an experiment.
- It is **not** evidence about a different machine, a different Python, a
  different SQLite, or the unreleased final sessions.

**Reproduced again from a clean clone.** The same day, the repository was cloned
fresh into an empty directory, the catalog placed exactly as section 2 above
describes, and the documented commands run in order: the FTS5 check, the test
suite (41 tests, all passing), the source-integrity one-liner in section 10, the
demo verification, and finally the bare `python3 -m evaluator.local_evaluator`.
The resulting `results.json` was again **byte-identical** to
`docs/diagnostics/E014_SESSIONS.json` (SHA-256 `e69e83c6…`), in 422.62 s. Nothing
outside this repository and the organizer's catalog was needed, and no step in
sections 1–4 had to be improvised. That is the cold-start check these
instructions exist to pass.

The re-run outputs were written outside the repository and are not tracked: their
SHA-256 equals the tracked snapshot's, so a second copy would carry no
information.

**Also reproduced earlier, at E011.** On 2026-08-31 the same check at commit
`093078d` returned output byte-identical to
`docs/diagnostics/E011_SESSIONS.json` (SHA-256
`b78820ce3bcd1045196112eed8c4cfda263b40d4844b4051671733b06a2519e3`) in 283.32 s.
E012 and E013 were never re-run and are still single-run results.

The agent contains no randomness: no `random`, no `time`, no hashing of
unordered structures into output order, no concurrency. Ordering is decided by
SQLite BM25 plus an explicit stable sort.

**Known limits, stated rather than smoothed over** (from `EXPERIMENTS.md`, M6):

- Empirical determinism passed in the verified environment. Some SQLite ordering
  paths carry no explicit deterministic secondary tie-breaker, so ordering of
  **exact ties** is not formally guaranteed across SQLite versions. No ordering
  semantics were changed after this was recorded.
- An empty or punctuation-only initial user message yields zero recommendations,
  because no lexical expression is produced. This is unfixed and is classified as
  a defensive robustness gap, not an observed evaluator blocker.
- No run-to-run variance estimate exists (the planned D-6 was never built), so
  small deltas between experiments cannot be separated from noise. At n=200 a
  TechnicalScore move of 0.021 is roughly 7 sessions, and E014's margin over its
  predecessor E013 (+0.021817) sits just above that scale rather than far above
  it. The cumulative margin over the E010 baseline (+0.118592) is not at risk
  from this.

## 9. Final results retention procedure

`docs/final_evaluation_faq.md` section 1 and `docs/submission_rules.md`
("Final Evaluation and Code Freeze") require retaining the generated
`results.json` including per-session results, together with the submitted commit
hash and environment details.

`.gitignore` excludes `results*.json` deliberately: a bare `results.json` in the
repository root is scratch output that is silently stale
(`tools/diagnostics/README.md`, "Result snapshots"). Rather than lift that
ignore, we retain results under an explicit, named, tracked convention.

**When the 800-session final package is released, run exactly this:**

```bash
# 1. Confirm the working tree is the frozen submitted commit.
git status --porcelain          # must be empty
git rev-parse HEAD              # record this hash
shasum -a 256 starter/agent.py  # record this hash

# 2. Run the UNMODIFIED official evaluator on the released package.
python3 -m evaluator.local_evaluator \
    --dataset <released final dataset path> \
    --output docs/diagnostics/FINAL_EVALUATION_SESSIONS.json

# 3. Bind the artifact to the code.
shasum -a 256 docs/diagnostics/FINAL_EVALUATION_SESSIONS.json
```

Then append a `final_run` entry to `docs/PROVENANCE.json` recording:
commit hash, `starter/agent.py` SHA-256, evaluator command, artifact path and
SHA-256, headline metrics, wall clock, Python version, OS/arch, and timestamp.
Commit the artifact and the manifest entry together.

Do not modify the Agent, indexes, or configuration after the final package is
released — that is an explicit code-freeze requirement, not a preference.

## 10. Commit and SHA provenance procedure

`docs/PROVENANCE.json` is the single manifest binding
result -> commit -> agent SHA-256 -> evaluator command -> artifact SHA-256 ->
headline metrics, for every retained run. Each entry is independently
verifiable:

```bash
# artifact integrity
shasum -a 256 docs/diagnostics/E014_SESSIONS.json

# the code that produced it
git show 769bd5f:starter/agent.py | shasum -a 256
```

### Submitted source is the evaluated source

| | SHA-256 |
|---|---|
| `starter/agent.py` as evaluated for the E014 result (commit `769bd5f`) | `1bde5aa6bdd5a52c0eb88d744c394263a64fbb0ab3606bb8a157b3b095274643` |
| `starter/agent.py` as submitted | `1bde5aa6bdd5a52c0eb88d744c394263a64fbb0ab3606bb8a157b3b095274643` |

**These are the same file.** The submitted `starter/agent.py` is byte-identical
to the agent that produced TechnicalScore 0.861737 under the official evaluator.
There is no divergence to explain, and no "equivalent but modified" claim to
audit. Verify it in one line:

```bash
diff <(git show 769bd5f:starter/agent.py) starter/agent.py && echo "byte-identical"
```

**Reproduction status, stated plainly.** Each experiment is *decided* on a
single official-evaluator run, by project policy. Two determinism reproductions
have been performed in this project's history, both after the decision they
follow, and neither used to revisit one:

| At | Date | Commit | How | Result |
|---|---|---|---|---|
| **E014 — the submitted baseline** | 2026-09-01 | `769bd5f` | in place | byte-identical to `E014_SESSIONS.json`, 425.14 s |
| **E014 — the submitted baseline** | 2026-09-01 | `769bd5f` | **clean clone**, catalog placed per section 2 | byte-identical to `E014_SESSIONS.json`, 422.62 s |
| E011 | 2026-08-31 | `093078d` | in place | byte-identical to `E011_SESSIONS.json`, 283.32 s |

E012 and E013 were never re-run. Both reproductions are recorded in
`docs/PROVENANCE.json` as determinism evidence, explicitly not as second
measurements. See section 8 for what they do and do not establish.

---

## Open human checks

- **Catalog Release URL** — see section 2. Must be confirmed to point at the
  organizer's upstream repository.
- **Repository visibility** — whether this repository is reachable by judges has
  not been verified from this environment. No document in this repository claims
  it is publicly accessible until that is confirmed.
