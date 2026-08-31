"""Frozen-property tests for the D012 paraphrase rewriter.

These assert the guarantees the D012 preregistration makes about
`tools/diagnostics/_paraphrase.py`. They are the reason a later reader can trust
that the rewriter did not decide D012's answer before any session was replayed:

  * determinism and cross-rate nesting, so the degradation curve is a curve over
    one fixed message set rather than a resample per level;
  * the vocabulary-closure invariant, which is the structural reason the rewriter
    cannot become a ground-truth channel;
  * the two "bag-of-words-neutral BY CONSTRUCTION" claims (`reorder`, `shuffle`),
    which are load-bearing for how the result is read -- if they failed silently,
    the reported differential would be understated;
  * the `punct` placebo being an exact token-level no-op, which is what makes it
    a usable harness check;
  * that no family flips an eligible message into an information-free one, which
    would confound D012 with an E003 evidence-admission regression.

The messages below are SYNTHETIC. They reproduce the shapes the published
simulator emits (`evaluator/local_evaluator.py:154-185`) without embedding any
public-set or catalog content.
"""
from __future__ import annotations

import unittest
from pathlib import Path

from starter.agent import _is_information_free, _terms
from tools.diagnostics._paraphrase import (
    ALL_FAMILIES,
    CONTENT_FAMILIES,
    FILLER,
    Rewriter,
    _rng,
    closure_violation,
    f_punct,
    f_reorder,
    f_shuffle,
    selection_u,
)

SEED = 20260831

# Synthetic stand-ins for the four evidence-bearing simulator shapes plus the
# three information-free templates the agent's E003 filter recognises.
ELIGIBLE = [
    "I'm looking for Outerwear Jackets. A key requirement is: Material:alloy.",
    "I'm looking for Footwear Boots. Reinforced rubber outsole for grip",
    "I'm looking for Bags Totes, but I'm still exploring.",
    "For that, what matters is: Adjustable padded strap; 60% cotton, 40% linen.",
    "For that, what matters is: Water resistant to 30 metres; 2 Year Battery.",
    "Actually, ignore my earlier preference. What I need is: Machine wash cold.",
    "I'm looking for Hats.",
]
INFORMATION_FREE = [
    "Those options are not quite right yet. Ask me about one specific attribute.",
    "I don't have a preference for material; please use your judgment.",
    "I don't have an additional preference for color.",
]
CORPUS = [(f"synthetic_{i:04d}", 1 + i % 7, m)
          for i, m in enumerate(ELIGIBLE + INFORMATION_FREE)]


class ParaphraseInvariantTest(unittest.TestCase):
    def test_deterministic_across_instances(self) -> None:
        a = Rewriter(CONTENT_FAMILIES, 1.0, SEED)
        b = Rewriter(CONTENT_FAMILIES, 1.0, SEED)
        self.assertEqual(
            [a(m, sid, t) for sid, t, m in CORPUS],
            [b(m, sid, t) for sid, t, m in CORPUS],
        )

    def test_selection_is_nested_across_rates(self) -> None:
        def selected(rate: float) -> set:
            return {
                (sid, t)
                for sid, t, m in CORPUS
                if not _is_information_free(m) and selection_u(SEED, sid, t) < rate
            }
        self.assertLessEqual(selected(0.25), selected(0.5))
        self.assertLessEqual(selected(0.5), selected(1.0))
        self.assertEqual(
            selected(1.0),
            {(sid, t) for sid, t, m in CORPUS if not _is_information_free(m)},
        )

    def test_vocabulary_closure_invariant(self) -> None:
        """No family may introduce a token the user's own message did not carry
        (bar the six frozen hedges). This is what keeps the rewriter from being a
        ground-truth channel."""
        for families in [CONTENT_FAMILIES, *[(f,) for f in ALL_FAMILIES]]:
            rewriter = Rewriter(families, 1.0, SEED)
            for sid, turn, message in CORPUS:
                leaked = closure_violation(message, rewriter(message, sid, turn))
                self.assertEqual(leaked, set(), f"{families} leaked {leaked}")

    def test_reorder_and_shuffle_preserve_the_token_set_exactly(self) -> None:
        """The preregistration calls these two families bag-of-words-neutral BY
        CONSTRUCTION and reads the D012 result in that light. Verify it."""
        for name, family in (("reorder", f_reorder), ("shuffle", f_shuffle)):
            for sid, turn, message in CORPUS:
                rewritten = family(message, _rng(SEED, sid, turn))
                self.assertEqual(
                    frozenset(_terms(rewritten)),
                    frozenset(_terms(message)),
                    f"{name} changed the token set of {message!r}",
                )

    def test_punct_placebo_is_an_exact_token_level_noop(self) -> None:
        for _, _, message in CORPUS:
            self.assertEqual(_terms(f_punct(message, None)), _terms(message))

    def test_information_free_messages_are_never_rewritten(self) -> None:
        for families in [CONTENT_FAMILIES, *[(f,) for f in ALL_FAMILIES]]:
            rewriter = Rewriter(families, 1.0, SEED)
            for message in INFORMATION_FREE:
                self.assertEqual(rewriter(message, "synthetic", 2), message)

    def test_no_family_flips_an_eligible_message_to_information_free(self) -> None:
        """Such a flip would demote real evidence and confound D012 with an E003
        evidence-admission regression that has nothing to do with word order."""
        for family in ALL_FAMILIES:
            rewriter = Rewriter((family,), 1.0, SEED)
            for message in ELIGIBLE:
                self.assertFalse(_is_information_free(rewriter(message, "synthetic", 1)))

    def test_placebo_is_never_composed_with_a_content_family(self) -> None:
        with self.assertRaises(ValueError):
            Rewriter(("punct", "shuffle"), 1.0, SEED)
        with self.assertRaises(ValueError):
            Rewriter(("no_such_family",), 1.0, SEED)

    def test_rate_zero_and_no_families_are_pass_through(self) -> None:
        for rewriter in (Rewriter(CONTENT_FAMILIES, 0.0, SEED), Rewriter((), 1.0, SEED)):
            for sid, turn, message in CORPUS:
                self.assertEqual(rewriter(message, sid, turn), message)

    def test_filler_words_all_survive_tokenization(self) -> None:
        """A hedge the agent's tokenizer drops would make `filler` a silent no-op."""
        for word in FILLER:
            self.assertEqual(_terms(word), [word])


class ParaphraseCorpusTest(unittest.TestCase):
    """Same invariants over every message the real simulator emits. Skipped when
    the participant data files are not present."""

    @classmethod
    def setUpClass(cls) -> None:
        root = Path(__file__).resolve().parents[1]
        catalog = root / "data" / "catalog.jsonl"
        dataset = root / "data" / "public_set.jsonl"
        if not (catalog.exists() and dataset.exists()):
            raise unittest.SkipTest("data/catalog.jsonl or data/public_set.jsonl absent")
        from evaluator.local_evaluator import (
            ALLOWED_ATTRIBUTES,
            catalog_index,
            coarse_category,
            customer_reply,
            initial_message,
            load_jsonl,
            materialize_hidden_fields,
        )
        samples = load_jsonl(dataset)
        _, categories, products = catalog_index(catalog)
        corpus = []
        for sample in samples:
            target = str(sample["ground_truth"]["parent_asin"])
            card, behavior = materialize_hidden_fields(sample, products)
            effective = {**sample, "intent_card": card, "behavior": behavior}
            disclosed: set[str] = set()
            corpus.append((
                sample["sample_id"], 1,
                initial_message(effective, coarse_category(categories.get(target, [])), disclosed),
            ))
            used = False
            for turn, attribute in enumerate(sorted(ALLOWED_ATTRIBUTES), start=2):
                reply, used = customer_reply(effective, attribute, disclosed, used)
                corpus.append((sample["sample_id"], turn, reply))
        cls.corpus = corpus

    def test_closure_invariant_over_the_real_message_stream(self) -> None:
        rewriter = Rewriter(CONTENT_FAMILIES, 1.0, SEED)
        for sid, turn, message in self.corpus:
            self.assertEqual(closure_violation(message, rewriter(message, sid, turn)), set())

    def test_stress_is_real_over_the_real_message_stream(self) -> None:
        """G3: an inert rewriter would make a null D012 result worthless."""
        rewriter = Rewriter(CONTENT_FAMILIES, 1.0, SEED)
        for sid, turn, message in self.corpus:
            rewriter(message, sid, turn)
        self.assertGreaterEqual(rewriter.changed / rewriter.eligible, 0.80)


if __name__ == "__main__":
    unittest.main()
