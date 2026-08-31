"""Direct contract, isolation, determinism, and stability tests for the shipped Agent.

These tests pin the behavior of the FROZEN agent in `starter/agent.py`. They are
deliberately *not* quality tests:

- No test reads `ground_truth` or any target label.
- No test asserts a ranking is "good", or checks a metric threshold.
  Ranking quality is measured only by the official evaluator
  (`evaluator/local_evaluator.py`), never here.
- Tests that describe a known limitation (empty / punctuation-only input) pin the
  CURRENT behavior so that a future change cannot alter it silently. They are not
  assertions that the behavior is desirable.

If one of these fails, that is a finding to report — not a licence to edit
`starter/agent.py`, which is under an algorithm freeze and whose SHA-256 is bound
to the reported result in `docs/PROVENANCE.json`.

The suite runs against a small synthetic catalog written to a temp directory, so
it needs neither the 60 MB frozen catalog nor the public session labels. It is
fast (the FTS5 index is built over a few dozen rows) and reproducible on a clean
checkout.
"""

from __future__ import annotations

import json
import re
import tempfile
import unittest
from pathlib import Path

from evaluator.local_evaluator import ALLOWED_ATTRIBUTES, TOP_K
from starter.agent import Agent


ROOT = "Clothing, Shoes & Jewelry"

# A small synthetic catalog. Values are invented; they are shaped like the frozen
# catalog (same field names, same nested types) so that the agent's own text
# extraction, category ladder, and attribute vocabularies all have something real
# to work on. Materials, colors, styles, features, and use cases are varied on
# purpose: the adaptive clarification policy only proposes an attribute when the
# current candidates carry at least two DISTINCT values for it.
_SPECS = [
    ("running shoes", "Mesh Trail Running Shoe", ["Men", "Shoes", "Athletic", "Running Shoes"],
     "breathable mesh upper", "black", "athletic", "lightweight", "running", 64.99),
    ("running shoes", "Cushioned Road Running Sneaker", ["Men", "Shoes", "Athletic", "Running Shoes"],
     "nylon and spandex knit", "blue", "sporty", "cushioned", "running", 89.50),
    ("running shoes", "Waterproof Trail Runner", ["Men", "Shoes", "Athletic", "Running Shoes"],
     "leather and mesh", "brown", "modern", "waterproof", "hiking", 112.00),
    ("running shoes", "Minimal Canvas Running Shoe", ["Men", "Shoes", "Athletic", "Running Shoes"],
     "canvas upper", "white", "classic", "lightweight", "gym", 45.00),
    ("hiking boots", "Insulated Winter Hiking Boot", ["Men", "Shoes", "Outdoor", "Hiking Boots"],
     "suede and wool lining", "brown", "relaxed", "insulated", "winter", 145.00),
    ("hiking boots", "Lightweight Hiking Boot", ["Men", "Shoes", "Outdoor", "Hiking Boots"],
     "nylon mesh", "gray", "modern", "breathable", "hiking", 98.00),
    ("hiking boots", "Waterproof Leather Hiking Boot", ["Men", "Shoes", "Outdoor", "Hiking Boots"],
     "full grain leather", "black", "classic", "waterproof", "outdoor", 175.00),
    ("t shirt", "Organic Cotton Crew Tee", ["Men", "Clothing", "Shirts", "T-Shirts"],
     "organic cotton jersey", "white", "casual", "washable", "work", 22.00),
    ("t shirt", "Performance Polyester Tee", ["Men", "Clothing", "Shirts", "T-Shirts"],
     "polyester blend", "navy", "athletic", "breathable", "gym", 28.00),
    ("t shirt", "Relaxed Linen Tee", ["Men", "Clothing", "Shirts", "T-Shirts"],
     "washed linen", "beige", "relaxed", "lightweight", "travel", 39.00),
    ("t shirt", "Vintage Wash Cotton Tee", ["Men", "Clothing", "Shirts", "T-Shirts"],
     "cotton slub", "green", "vintage", "durable", "casual wear", 26.50),
    ("winter jacket", "Insulated Down Parka", ["Women", "Clothing", "Coats", "Jackets"],
     "nylon shell with down fill", "black", "classic", "insulated", "winter", 249.00),
    ("winter jacket", "Fleece Lined Softshell", ["Women", "Clothing", "Coats", "Jackets"],
     "fleece and polyester", "purple", "sporty", "windproof", "hiking", 132.00),
    ("winter jacket", "Waterproof Rain Shell", ["Women", "Clothing", "Coats", "Jackets"],
     "ripstop nylon", "yellow", "modern", "waterproof", "travel", 158.00),
    ("winter jacket", "Wool Overcoat", ["Women", "Clothing", "Coats", "Jackets"],
     "wool blend", "gray", "formal", "durable", "office", 289.00),
    ("yoga pants", "High Waist Yoga Legging", ["Women", "Clothing", "Activewear", "Leggings"],
     "spandex and nylon", "black", "athletic", "stretch", "yoga", 58.00),
    ("yoga pants", "Cotton Lounge Legging", ["Women", "Clothing", "Activewear", "Leggings"],
     "cotton spandex", "gray", "relaxed", "breathable", "yoga", 42.00),
    ("yoga pants", "Compression Training Tight", ["Women", "Clothing", "Activewear", "Leggings"],
     "polyester spandex", "navy", "sporty", "stretch", "workout", 65.00),
    ("leather belt", "Full Grain Leather Belt", ["Men", "Accessories", "Belts"],
     "full grain leather", "brown", "classic", "adjustable", "office", 48.00),
    ("leather belt", "Reversible Dress Belt", ["Men", "Accessories", "Belts"],
     "leather", "black", "formal", "reversible", "wedding", 55.00),
    ("silk scarf", "Printed Silk Scarf", ["Women", "Accessories", "Scarves"],
     "mulberry silk", "red", "elegant", "lightweight", "wedding", 78.00),
    ("silk scarf", "Satin Twill Scarf", ["Women", "Accessories", "Scarves"],
     "satin twill", "pink", "vintage", "washable", "travel", 62.00),
    ("wool sweater", "Merino Wool Crew Sweater", ["Men", "Clothing", "Sweaters"],
     "merino wool", "navy", "classic", "durable", "winter", 118.00),
    ("wool sweater", "Cashmere Blend Pullover", ["Men", "Clothing", "Sweaters"],
     "cashmere blend", "beige", "elegant", "lightweight", "office", 165.00),
]


def _build_catalog(path: Path) -> list[str]:
    """Write the synthetic catalog and return its parent_asin values in file order."""
    identifiers: list[str] = []
    with path.open("w", encoding="utf-8") as handle:
        for index, (kind, title, tail, material, color, style, feature, use_case, price) in enumerate(_SPECS):
            parent_asin = f"B{index:09d}"
            identifiers.append(parent_asin)
            handle.write(json.dumps({
                "parent_asin": parent_asin,
                "title": f"{title} for {use_case}",
                "categories": [ROOT, *tail],
                "features": [
                    f"{material} construction",
                    f"{style} fit",
                    f"{feature} design",
                    f"ideal for {use_case}",
                ],
                "details": {"Material": material, "Color": color, "Style": style},
                "description": [f"A {style} {kind} in {color}. {feature.capitalize()} and made from {material}."],
                "store": f"{title.split()[0]} Supply",
                "price": price,
                "average_rating": 4.0 + (index % 10) / 10.0,
                "rating_number": 100 + index,
            }) + "\n")
    return identifiers


class AgentTestBase(unittest.TestCase):
    """One synthetic catalog and one Agent per test class.

    The agent's index is immutable after construction and `reset()` clears only
    per-session state, so a shared instance is safe for every test that does not
    specifically exercise construction.
    """

    @classmethod
    def setUpClass(cls) -> None:
        cls._tmp = tempfile.TemporaryDirectory()
        cls.catalog_path = Path(cls._tmp.name) / "catalog.jsonl"
        cls.catalog_ids = _build_catalog(cls.catalog_path)
        cls.agent = Agent(cls.catalog_path)

    @classmethod
    def tearDownClass(cls) -> None:
        cls._tmp.cleanup()

    def drive(self, agent: Agent, session_id: str, messages: list[str], top_k: int = TOP_K) -> list[dict]:
        """Run a message trajectory through the public contract only."""
        agent.reset(session_id, {"preference_tags": ["comfort"], "average_prior_rating": 4.5})
        return [
            agent.respond(session_id, message, turn, top_k)
            for turn, message in enumerate(messages, start=1)
        ]

    @staticmethod
    def ids(response: dict) -> list[str]:
        return [item["parent_asin"] for item in response["recommendations"]]


class ContractTest(AgentTestBase):
    """A. The published Agent interface (docs/agent_api_contract.json, spec
    'Required Agent Interface', docs/submission_rules.md 'Output Rules')."""

    def test_reset_and_respond_are_callable(self) -> None:
        self.agent.reset("s-callable", {"preference_tags": ["fit"]})
        response = self.agent.respond("s-callable", "I'm looking for running shoes.", 1, TOP_K)
        self.assertIsInstance(response, dict)

    def test_response_carries_the_contract_fields(self) -> None:
        response = self.drive(self.agent, "s-fields", ["I'm looking for a wool sweater."])[0]
        for field in ("message", "ask_attribute", "recommendations", "usage"):
            self.assertIn(field, response)

    def test_message_is_a_string(self) -> None:
        # The evaluator discards a whole response whose `message` is not a str.
        for response in self.drive(self.agent, "s-message", [
            "I'm looking for hiking boots.",
            "For that, what matters is: waterproof design.",
        ]):
            self.assertIsInstance(response["message"], str)

    def test_ask_attribute_is_legal_or_none(self) -> None:
        responses = self.drive(self.agent, "s-attr", [
            "I'm looking for running shoes.",
            "For that, what matters is: mesh.",
            "For that, what matters is: color: black.",
            "I don't have an additional preference for style.",
        ])
        for response in responses:
            attribute = response["ask_attribute"]
            if attribute is not None:
                self.assertIn(attribute, ALLOWED_ATTRIBUTES)

    def test_ask_attribute_vocabulary_matches_the_published_contract(self) -> None:
        # Guards against the evaluator constant and the shipped contract drifting.
        contract_path = Path(__file__).resolve().parent.parent / "docs" / "agent_api_contract.json"
        contract = json.loads(contract_path.read_text(encoding="utf-8"))
        published = set(re.findall(r'"([a-z_]+)"', json.dumps(contract))) & ALLOWED_ATTRIBUTES
        self.assertEqual(published, set(ALLOWED_ATTRIBUTES))

    def test_recommendations_are_an_ordered_list_of_asin_records(self) -> None:
        response = self.drive(self.agent, "s-order", ["I'm looking for a winter jacket."])[0]
        self.assertIsInstance(response["recommendations"], list)
        for item in response["recommendations"]:
            self.assertIsInstance(item, dict)
            self.assertIsInstance(item["parent_asin"], str)
            self.assertTrue(item["parent_asin"])

    def test_recommendations_contain_no_duplicates(self) -> None:
        # The evaluator silently drops duplicates, so a duplicate costs a slot.
        for response in self.drive(self.agent, "s-dupes", [
            "I'm looking for yoga pants.",
            "For that, what matters is: spandex.",
            "For that, what matters is: color: black.",
        ]):
            recommended = self.ids(response)
            self.assertEqual(len(recommended), len(set(recommended)))

    def test_recommendation_count_never_exceeds_top_k(self) -> None:
        # top_k is a contract parameter, not a constant: honor whatever is passed.
        for top_k in (1, 3, 10):
            with self.subTest(top_k=top_k):
                response = self.drive(self.agent, f"s-topk-{top_k}", ["I'm looking for a t shirt."], top_k)[0]
                self.assertLessEqual(len(response["recommendations"]), top_k)

    def test_every_recommended_asin_exists_in_the_catalog(self) -> None:
        # Recommending an id outside the frozen catalog is a hard rule violation
        # (docs/final_evaluation_faq.md section 4); the evaluator drops it silently.
        known = set(self.catalog_ids)
        for response in self.drive(self.agent, "s-valid", [
            "I'm looking for leather belts.",
            "For that, what matters is: leather.",
        ]):
            for parent_asin in self.ids(response):
                self.assertIn(parent_asin, known)

    def test_usage_reports_non_negative_integer_tokens(self) -> None:
        usage = self.drive(self.agent, "s-usage", ["I'm looking for a silk scarf."])[0]["usage"]
        self.assertIsInstance(usage, dict)
        for field in ("prompt_tokens", "completion_tokens"):
            self.assertIsInstance(usage[field], int)
            self.assertGreaterEqual(usage[field], 0)

    def test_respond_before_reset_raises(self) -> None:
        # Pins current behavior. The evaluator catches exceptions and scores the
        # turn as a miss, so this can never crash a run; it is a programming guard.
        with self.assertRaises(RuntimeError):
            self.agent.respond("s-never-reset", "I'm looking for shoes.", 1, TOP_K)


class SessionIsolationTest(AgentTestBase):
    """B. `docs/final_evaluation_faq.md` section 5: "Teams may share immutable
    indexes, but conversational state must remain isolated between sessions."."""

    def test_reset_clears_only_the_named_session(self) -> None:
        """Resetting an unrelated session id must leave this session untouched.

        Both runs send the identical trajectory to "keep"; the only difference is
        that one has unrelated `reset()` + `respond()` calls woven between the
        turns. Any divergence would mean a reset reached the wrong session.
        """
        trajectory = [
            "I'm looking for hiking boots.",
            "For that, what matters is: full grain leather.",
            "For that, what matters is: waterproof design.",
        ]
        undisturbed = self.drive(Agent(self.catalog_path), "keep", trajectory)

        agent = Agent(self.catalog_path)
        agent.reset("keep", {})
        disturbed = []
        for turn, message in enumerate(trajectory, start=1):
            disturbed.append(agent.respond("keep", message, turn, TOP_K))
            agent.reset(f"other-{turn}", {})
            agent.respond(f"other-{turn}", "I'm looking for a silk scarf.", 1, TOP_K)

        self.assertEqual(
            [(self.ids(r), r["ask_attribute"]) for r in disturbed],
            [(self.ids(r), r["ask_attribute"]) for r in undisturbed],
        )

    def test_reset_wipes_accumulated_evidence_for_that_session(self) -> None:
        agent = Agent(self.catalog_path)
        self.drive(agent, "reuse", [
            "I'm looking for a winter jacket.",
            "For that, what matters is: wool blend.",
        ])
        fresh = self.drive(agent, "reuse", ["I'm looking for a winter jacket."])[0]
        baseline = self.drive(agent, "baseline", ["I'm looking for a winter jacket."])[0]
        # After reset the reused id must behave like a brand-new session.
        self.assertEqual(self.ids(fresh), self.ids(baseline))
        self.assertEqual(fresh["ask_attribute"], baseline["ask_attribute"])

    def test_two_sessions_do_not_share_evidence(self) -> None:
        agent = Agent(self.catalog_path)
        agent.reset("a", {})
        agent.reset("b", {})
        agent.respond("a", "I'm looking for running shoes.", 1, TOP_K)
        agent.respond("a", "For that, what matters is: waterproof design.", 2, TOP_K)
        solo = self.drive(Agent(self.catalog_path), "b", ["I'm looking for a silk scarf."])[0]
        shared = agent.respond("b", "I'm looking for a silk scarf.", 1, TOP_K)
        self.assertEqual(self.ids(shared), self.ids(solo))

    def test_interleaved_sessions_are_isolated(self) -> None:
        """The FAQ section 5 requirement, exercised the way the risk actually
        arises: two conversations advancing turn by turn against one Agent.

        Each interleaved session must produce exactly what it produces when run
        alone -- recommendations AND clarification attribute, since the asked-set
        is per-session state too.
        """
        left = [
            "I'm looking for running shoes, but I'm still exploring.",
            "For that, what matters is: mesh; breathable design.",
            "For that, what matters is: color: black.",
            "I don't have an additional preference for style.",
        ]
        right = [
            "I'm looking for a wool sweater. A key requirement is: merino wool.",
            "For that, what matters is: color: navy.",
            "For that, what matters is: classic fit.",
            "I don't have an additional preference for feature.",
        ]
        alone_left = self.drive(Agent(self.catalog_path), "L", left)
        alone_right = self.drive(Agent(self.catalog_path), "R", right)

        agent = Agent(self.catalog_path)
        agent.reset("L", {})
        agent.reset("R", {})
        woven_left: list[dict] = []
        woven_right: list[dict] = []
        for turn in range(1, len(left) + 1):
            woven_left.append(agent.respond("L", left[turn - 1], turn, TOP_K))
            woven_right.append(agent.respond("R", right[turn - 1], turn, TOP_K))

        for turn, (woven, alone) in enumerate(zip(woven_left, alone_left), start=1):
            with self.subTest(session="L", turn=turn):
                self.assertEqual(self.ids(woven), self.ids(alone))
                self.assertEqual(woven["ask_attribute"], alone["ask_attribute"])
        for turn, (woven, alone) in enumerate(zip(woven_right, alone_right), start=1):
            with self.subTest(session="R", turn=turn):
                self.assertEqual(self.ids(woven), self.ids(alone))
                self.assertEqual(woven["ask_attribute"], alone["ask_attribute"])


class DeterminismTest(AgentTestBase):
    """C. Empirical determinism in the tested environment.

    This does NOT establish determinism across SQLite versions. Exact-tie
    ordering has no explicit secondary tie-breaker (docs/REPRODUCIBILITY.md
    section 8); these tests pin behavior here, on this build.
    """

    TRAJECTORY = [
        "I'm looking for hiking boots. A key requirement is: waterproof design.",
        "For that, what matters is: full grain leather.",
        "For that, what matters is: color: black.",
        "I don't have an additional preference for use_case.",
        "Those options are not quite right yet. Ask me about one specific attribute.",
    ]

    def test_two_sessions_on_one_agent_agree(self) -> None:
        first = self.drive(self.agent, "d-1", self.TRAJECTORY)
        second = self.drive(self.agent, "d-2", self.TRAJECTORY)
        # Also proves the catalog-static memoization caches (M6, E010) are pure:
        # the second run is served from warm caches and must not differ.
        self.assertEqual(
            [(self.ids(r), r["ask_attribute"]) for r in first],
            [(self.ids(r), r["ask_attribute"]) for r in second],
        )

    def test_independent_agent_instances_agree(self) -> None:
        first = self.drive(Agent(self.catalog_path), "d-a", self.TRAJECTORY)
        second = self.drive(Agent(self.catalog_path), "d-b", self.TRAJECTORY)
        self.assertEqual(
            [(self.ids(r), r["message"], r["ask_attribute"]) for r in first],
            [(self.ids(r), r["message"], r["ask_attribute"]) for r in second],
        )


class StabilityAndEdgeCaseTest(AgentTestBase):
    """D. Protocol stability, plus two KNOWN limitations pinned as current
    behavior (docs/REPRODUCIBILITY.md section 8). Pinning is not endorsement."""

    def test_a_full_ten_turn_session_never_raises(self) -> None:
        agent = Agent(self.catalog_path)
        agent.reset("ten", {})
        messages = [
            "I'm looking for a winter jacket, but I'm still exploring.",
            "For that, what matters is: nylon shell with down fill.",
            "For that, what matters is: color: black.",
            "I don't have an additional preference for style.",
            "Those options are not quite right yet. Ask me about one specific attribute.",
            "For that, what matters is: insulated design.",
            "I don't have a preference for feature; please use your judgment.",
            "For that, what matters is: ideal for winter.",
            "I don't have an additional preference for use_case.",
            "Those options are not quite right yet. Ask me about one specific attribute.",
        ]
        for turn, message in enumerate(messages, start=1):
            response = agent.respond("ten", message, turn, TOP_K)
            self.assertIsInstance(response["message"], str)
            self.assertLessEqual(len(response["recommendations"]), TOP_K)
            if response["ask_attribute"] is not None:
                self.assertIn(response["ask_attribute"], ALLOWED_ATTRIBUTES)

    def test_an_attribute_is_never_asked_twice_in_one_session(self) -> None:
        agent = Agent(self.catalog_path)
        agent.reset("no-repeat", {})
        asked: list[str] = []
        message = "I'm looking for running shoes, but I'm still exploring."
        for turn in range(1, 11):
            response = agent.respond("no-repeat", message, turn, TOP_K)
            if response["ask_attribute"] is not None:
                asked.append(response["ask_attribute"])
            message = "Those options are not quite right yet. Ask me about one specific attribute."
        self.assertEqual(len(asked), len(set(asked)))

    def test_empty_initial_message_returns_no_recommendations_without_raising(self) -> None:
        """KNOWN LIMITATION, pinned. An empty message produces no lexical
        expression, so no candidates are retrieved. Unfixed by decision; see
        docs/REPRODUCIBILITY.md section 8. This test records the behavior, it does
        not endorse it."""
        response = self.drive(self.agent, "empty", [""])[0]
        self.assertEqual(response["recommendations"], [])
        self.assertIsInstance(response["message"], str)

    def test_punctuation_only_initial_message_behaves_the_same(self) -> None:
        """KNOWN LIMITATION, pinned -- see the test above."""
        response = self.drive(self.agent, "punct", ["!!! ... ???"])[0]
        self.assertEqual(response["recommendations"], [])
        self.assertIsInstance(response["message"], str)

    def test_a_session_recovers_once_real_text_arrives(self) -> None:
        # The empty-input gap is first-turn only: later content still retrieves.
        responses = self.drive(self.agent, "recover", ["", "I'm looking for a silk scarf."])
        self.assertEqual(responses[0]["recommendations"], [])
        self.assertTrue(responses[1]["recommendations"])


if __name__ == "__main__":
    unittest.main()
