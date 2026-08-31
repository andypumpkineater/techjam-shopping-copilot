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

D012 paraphrase rewriter -- FROZEN by the preregistration in EXPERIMENTS.md.

=============================================================================
THIS FILE IS THE ONE PART OF D012 THAT COULD FABRICATE ITS OWN CONCLUSION
=============================================================================
Every constant, family, and intensity below was written into EXPERIMENTS.md
("D012 -- Paraphrase Stress", section "The rewriter -- frozen specification")
and committed BEFORE this file existed. None of it may be retuned after seeing a
result. If a family produces an uninteresting curve, that is a reported result.

Ground-truth boundary: the rewriter receives `(message, sample_id, turn)` and
NOTHING else -- no sample, no product, no target, no catalog handle. `sample_id`
and `turn` are used solely as hash salt. It is a pure function of the user's own
message text.

Vocabulary-closure invariant, checked at runtime when `verify=True`:

    _terms(out) subset-of  _terms(in) | FILLER | {t+"s", t[:-1] for t in _terms(in)}

so the rewriter can introduce no information that was not already in the user's
own message, plus six fixed English hedge words. That is the structural reason no
`ground_truth`, catalog text, or target-derived string can enter through here.

A priori bias, stated in the preregistration before any run: every content family
is structurally more damaging to a contiguous-n-gram rule than to a binary
per-unit bag-of-words rule, and `shuffle` and `filler` are bag-of-words-neutral by
construction. D012 is deliberately biased against E010; that is why its decision
rule reads the surviving advantage, not the raw degradation.
"""
from __future__ import annotations

import hashlib
import math
import random
import re

from starter.agent import _is_information_free, _terms

# Frozen. Generic English hedges, chosen without reference to the catalog, to any
# scorer, or to any result. All six survive _terms() (length > 1, not STOPWORDS).
FILLER: tuple[str, ...] = ("really", "kind", "sort", "general", "overall", "honestly")

CLAUSE_SPLIT = re.compile(r"(?<=[.;:,])\s+")
NON_ALNUM = re.compile(r"[^A-Za-z0-9]")
PUNCT_SPACE = re.compile(r"([.,;:!?])")
# A word eligible for morphological toggling: optional surrounding punctuation
# around exactly ONE alphabetic run. Excludes digits ("8.37", "96%") and interior
# punctuation ("don't"), so the toggle can never split or merge a token.
SIMPLE_WORD = re.compile(r"([^A-Za-z0-9]*)([A-Za-z]+)([^A-Za-z0-9]*)")

# Canonical application order when families are composed. `punct` is the placebo
# and is never part of the mixed ensemble.
CONTENT_FAMILIES: tuple[str, ...] = ("reorder", "shuffle", "morph", "drop", "filler")
PLACEBO_FAMILY = "punct"
ALL_FAMILIES: tuple[str, ...] = CONTENT_FAMILIES + (PLACEBO_FAMILY,)


# ------------------------------------------------------------------ seeding
def _digest(seed: object, sample_id: str, turn: int, tag: str) -> bytes:
    return hashlib.sha256(f"{seed}|{sample_id}|{turn}|{tag}".encode("utf-8")).digest()


def selection_u(seed: object, sample_id: str, turn: int) -> float:
    """Uniform in [0, 1) per message. A message is rewritten iff `u < rate`, which
    makes the selected sets NESTED across rates: what is rewritten at 0.25 is a
    subset of 0.50, a subset of 1.00. The degradation curve therefore varies
    coverage of one fixed message set instead of resampling per level."""
    return int.from_bytes(_digest(seed, sample_id, turn, "select")[:8], "big") / 2.0**64


def _rng(seed: object, sample_id: str, turn: int) -> random.Random:
    return random.Random(
        hashlib.sha256(f"{seed}|{sample_id}|{turn}|apply".encode("utf-8")).hexdigest()
    )


# ------------------------------------------------------------- word helpers
def _alnum(word: str) -> str:
    return NON_ALNUM.sub("", word)


def _is_content(word: str) -> bool:
    """A word carrying at least one token that survives _terms() -- i.e. one the
    agent's retrieval and both ranking rules can actually see."""
    return bool(_terms(word))


def _split_clauses(text: str) -> list[str]:
    return CLAUSE_SPLIT.split(text)


def _join_clauses(clauses: list[str]) -> str:
    return " ".join(clauses)


# ---------------------------------------------------------------- families
def f_reorder(text: str, rng: random.Random) -> str:
    """Clause permutation; within-clause word order preserved.

    Bag-of-words coverage is EXACTLY invariant here (the per-unit token set does
    not change). Only n-grams that straddled a clause boundary are affected."""
    clauses = _split_clauses(text)
    if len(clauses) < 2:
        return text
    shift = 1 + rng.randrange(len(clauses) - 1)
    return _join_clauses(clauses[shift:] + clauses[:shift])


def f_shuffle(text: str, rng: random.Random) -> str:
    """ceil(L/4) adjacent transpositions inside each clause of L >= 4 words.

    A permutation preserves the token set exactly, so this family is
    bag-of-words-neutral BY CONSTRUCTION and is the upper bound on the
    differential, not a realistic estimate of it."""
    out: list[str] = []
    for clause in _split_clauses(text):
        words = clause.split()
        length = len(words)
        if length >= 4:
            k = min(math.ceil(length / 4), length - 1)
            for position in sorted(rng.sample(range(length - 1), k)):
                words[position], words[position + 1] = words[position + 1], words[position]
        out.append(" ".join(words))
    return _join_clauses(out)


def _toggle_plural(core: str) -> str | None:
    lowered = core.lower()
    if lowered.endswith("s"):
        if len(core) >= 5 and not lowered.endswith(("ss", "us", "is")):
            return core[:-1]
        return None
    if lowered.endswith(("x", "z", "h")):
        return None
    return core + "s"


def f_morph(text: str, rng: random.Random) -> str:
    """Plural toggle on ceil(n/3) eligible content words. Rule-based English
    morphology, so no vocabulary list is consulted and nothing is catalog-specific."""
    words = text.split()
    eligible = [
        index
        for index, word in enumerate(words)
        if _is_content(word)
        and SIMPLE_WORD.fullmatch(word)
        and len(_alnum(word)) >= 4
    ]
    if not eligible:
        return text
    k = min(math.ceil(len(eligible) / 3), len(eligible))
    for index in rng.sample(eligible, k):
        prefix, core, suffix = SIMPLE_WORD.fullmatch(words[index]).groups()
        toggled = _toggle_plural(core)
        if toggled:
            words[index] = prefix + toggled + suffix
    return " ".join(words)


def f_drop(text: str, rng: random.Random) -> str:
    """Delete C // 8 content words -- deliberately the mildest setting of the most
    destructive family, since paraphrase usually preserves content."""
    words = text.split()
    eligible = [index for index, word in enumerate(words) if _is_content(word)]
    k = len(eligible) // 8
    if k <= 0:
        return text
    removed = set(rng.sample(eligible, k))
    return " ".join(word for index, word in enumerate(words) if index not in removed)


def f_filler(text: str, rng: random.Random) -> str:
    """One hedge word into each clause of >= 6 words. A unit can only GAIN a token,
    so binary per-unit coverage is ~unaffected; contiguous n-grams spanning the
    insertion point are broken."""
    out: list[str] = []
    for clause in _split_clauses(text):
        words = clause.split()
        if len(words) >= 6:
            # randrange(len) never appends past the final word, so the hedge is
            # never placed after the clause's trailing punctuation.
            words.insert(rng.randrange(len(words)), rng.choice(FILLER))
        out.append(" ".join(words))
    return _join_clauses(out)


def f_punct(text: str, rng: random.Random) -> str:
    """PLACEBO. Provably token-neutral under _terms(): inserting whitespace before a
    non-alphanumeric character cannot split an [a-z0-9]+ run (punctuation is never
    inside one), and adding whitespace can never merge two. Every arm must return
    metrics identical to rate 0.00; if one moves, the harness is broken."""
    return PUNCT_SPACE.sub(r" \1", text).replace(" ", "  ")


_FAMILY = {
    "reorder": f_reorder,
    "shuffle": f_shuffle,
    "morph": f_morph,
    "drop": f_drop,
    "filler": f_filler,
    PLACEBO_FAMILY: f_punct,
}


# ------------------------------------------------------- closure invariant
def closure_violation(source: str, output: str) -> set[str]:
    """Tokens the rewriter introduced that were not derivable from the user's own
    message. Must always be empty -- see the module docstring."""
    source_terms = set(_terms(source))
    allowed = set(source_terms) | set(FILLER)
    for term in source_terms:
        allowed.add(term + "s")
        allowed.add(term[:-1])
    return set(_terms(output)) - allowed


# ------------------------------------------------------------- the rewriter
class Rewriter:
    """Callable `(message, sample_id, turn) -> str` for `_replay.replay()`.

    Applies the requested families, in canonical order, to the selected fraction
    of EVIDENCE-BEARING messages. Information-free messages are passed through
    untouched: E003 drops them from evidence after turn 1 anyway, and perturbing
    their prefixes would silently flip `_is_information_free()` and promote
    boilerplate into evidence -- confounding D012 with an E003 regression that has
    nothing to do with word order.
    """

    def __init__(
        self,
        families: tuple[str, ...],
        rate: float,
        seed: object,
        verify: bool = True,
        keep_examples: int = 12,
    ) -> None:
        unknown = [name for name in families if name not in _FAMILY]
        if unknown:
            raise ValueError(f"unknown paraphrase family/families {unknown}")
        if PLACEBO_FAMILY in families and len(families) > 1:
            raise ValueError(
                f"{PLACEBO_FAMILY!r} is the placebo and is never composed with a "
                "content family (preregistered)"
            )
        # Canonical order, independent of how the caller listed them.
        self.families = tuple(name for name in ALL_FAMILIES if name in families)
        self.rate = rate
        self.seed = seed
        self.verify = verify
        self.keep_examples = keep_examples
        self.eligible = 0
        self.selected = 0
        self.changed = 0
        self.violations = 0
        self.violating_tokens: set[str] = set()
        self.examples: list[tuple[str, str]] = []

    def __call__(self, message: str, sample_id: str, turn: int) -> str:
        if not self.families or self.rate <= 0.0:
            return message
        if _is_information_free(message):
            return message
        self.eligible += 1
        if selection_u(self.seed, sample_id, turn) >= self.rate:
            return message
        self.selected += 1
        rng = _rng(self.seed, sample_id, turn)
        output = message
        for name in self.families:
            output = _FAMILY[name](output, rng)
        if output != message:
            self.changed += 1
        if self.verify:
            leaked = closure_violation(message, output)
            if leaked:
                self.violations += 1
                self.violating_tokens |= leaked
        if len(self.examples) < self.keep_examples:
            self.examples.append((message, output))
        return output

    def stats(self) -> dict:
        return {
            "families": list(self.families),
            "rate": self.rate,
            "seed": self.seed,
            "eligible_messages": self.eligible,
            "selected_messages": self.selected,
            "changed_messages": self.changed,
            "changed_fraction_of_selected": (
                round(self.changed / self.selected, 6) if self.selected else 0.0
            ),
            "changed_fraction_of_eligible": (
                round(self.changed / self.eligible, 6) if self.eligible else 0.0
            ),
            "closure_violations": self.violations,
            "closure_violating_tokens": sorted(self.violating_tokens)[:20],
        }
