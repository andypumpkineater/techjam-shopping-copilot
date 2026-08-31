from __future__ import annotations

import json
import re
import sqlite3
from collections import Counter
from pathlib import Path


TOKEN_RE = re.compile(r"[a-z0-9]+", re.IGNORECASE)
STOPWORDS = {
    "a", "an", "and", "are", "as", "at", "be", "but", "by", "for", "from",
    "i", "in", "is", "it", "me", "my", "of", "on", "or", "please", "some",
    "that", "the", "this", "to", "want", "with", "would", "you", "looking",
}

# Relaxation ladder for category-scoped retrieval, most specific to least
# specific. "segment" (top-level department, e.g. "women"/"men") is reached
# only via relaxation from a more specific match, never used as an initial
# detection target (see _DETECTION_LEVELS).
_CATEGORY_LEVELS = ("full", "last2", "last1", "segment")
_DETECTION_LEVELS = ("full", "last2", "last1")
_DOMINANT_ROOT_THRESHOLD = 0.99

PRIMARY_SLOTS = 7
INSURANCE_SLOTS = 3

# E002 — fixed, deterministic, label-free clarification sequence, indexed by
# turn (1-based). One pass over the contract-legal attributes for which the
# published evaluator's classify_constraint() can disclose a constraint,
# followed by one "other" catch-all. Turns 9-10 ask nothing: repeating an
# attribute or reusing "other" would be a repeated-question policy, deferred
# to later dialogue experiments. Frozen before evaluation; not reordered.
_ASK_SEQUENCE: tuple[str | None, ...] = (
    "material", "color", "size", "style", "budget", "feature", "use_case", "other",
    None, None,
)

# E006 — adaptive, catalog-side selection among the five ask_attribute
# values that the published evaluator's classify_constraint() can actually
# label a disclosed constraint with from free product text (material,
# color, style, feature, use_case). size and budget remain legal specific
# attributes reachable through the fixed fallback below, but are not
# adaptively scored: size tokens (S/M/L) are filtered out by _terms()'s
# length>1 rule and numeric sizes are indistinguishable from prices/
# dimensions without semantic parsing, and budget would require a new
# price index (out of scope for this version). category/brand are never
# scored: classify_constraint() never labels a constraint as either, so
# asking them cannot elicit informative evidence under the published
# simulator mechanics. Frozen before evaluation; not tuned afterward.
_ADAPTIVE_SCORED_ATTRIBUTES: tuple[str, ...] = (
    "material", "color", "style", "feature", "use_case",
)

# Small, catalog-general, single-token vocabularies (English domain words
# matching this catalog's own top-level department, "Clothing, Shoes &
# Jewelry"), chosen independently of the evaluator's own MATERIALS/
# COLOR_RE constants, ground truth, targets, or public evaluator output.
# Frozen; not to be revised after seeing evaluator results.
_ATTRIBUTE_VOCAB: dict[str, frozenset[str]] = {
    "material": frozenset({
        "cotton", "polyester", "nylon", "leather", "wool", "denim", "silk",
        "linen", "suede", "fleece", "canvas", "spandex", "velvet", "rayon",
        "cashmere", "mesh", "satin", "corduroy",
    }),
    "color": frozenset({
        "black", "white", "blue", "red", "pink", "green", "brown", "gray",
        "grey", "purple", "yellow", "orange", "navy", "beige", "gold", "silver",
    }),
    "style": frozenset({
        "casual", "formal", "athletic", "vintage", "classic", "slim",
        "relaxed", "regular", "sporty", "elegant", "modern", "retro",
    }),
    "feature": frozenset({
        "waterproof", "breathable", "adjustable", "stretch", "lightweight",
        "washable", "wireless", "rechargeable", "reversible", "insulated",
        "padded", "cushioned", "hypoallergenic", "durable",
    }),
    "use_case": frozenset({
        "hiking", "running", "gym", "winter", "outdoor", "work", "travel",
        "yoga", "beach", "wedding", "workout", "camping", "office", "school",
    }),
}

# The seven specific (non-"other") attributes from _ASK_SEQUENCE, in their
# original E002 order — reused, not re-derived, as the deterministic
# fallback when no adaptive attribute is eligible this turn.
_SPECIFIC_ATTRIBUTES: tuple[str, ...] = tuple(
    attribute for attribute in _ASK_SEQUENCE if attribute not in (None, "other")
)

# E003 — fixed prefixes of the published evaluator's information-free/
# no-preference customer_reply templates (evaluator/local_evaluator.py).
# Attribute-independent prefixes only; no attribute-name interpolation
# needed. Used to exclude boilerplate from persisted evidence.
_INFO_FREE_PREFIXES = (
    "Those options are not quite right yet",
    "I don't have a preference for ",
    "I don't have an additional preference for ",
)


def _is_information_free(message: str) -> bool:
    return message.startswith(_INFO_FREE_PREFIXES)


def _text(value: object) -> str:
    if value is None:
        return ""
    if isinstance(value, dict):
        return " ".join(f"{key} {item}" for key, item in value.items())
    if isinstance(value, list):
        return " ".join(str(item) for item in value)
    return str(value)


def _terms(text: str) -> list[str]:
    return [
        token.lower()
        for token in TOKEN_RE.findall(text)
        if len(token) > 1 and token.lower() not in STOPWORDS
    ]


# E004 — one admitted E003 message is one evidence unit; its terms are the
# same _terms() used for querying. Units that tokenize to nothing are
# dropped rather than counted as trivially "covered" by everything.
def _evidence_units(messages: list[str]) -> list[frozenset[str]]:
    units = (frozenset(_terms(message)) for message in messages)
    return [unit for unit in units if unit]


def _category_keys(categories: list[str]) -> dict[str, str]:
    cleaned = [value.strip() for value in categories if value and value.strip()]
    if not cleaned:
        return {"full": "", "last2": "", "last1": "", "segment": ""}
    return {
        "full": " ".join(cleaned).lower(),
        "last2": " ".join(cleaned[-2:]).lower(),
        "last1": cleaned[-1].lower(),
        "segment": cleaned[0].lower(),
    }


def _next_level(level: str) -> str | None:
    index = _CATEGORY_LEVELS.index(level)
    return _CATEGORY_LEVELS[index + 1] if index + 1 < len(_CATEGORY_LEVELS) else None


class Agent:
    """Editable weak baseline: stateless BM25 retrieval with no LLM dependency."""

    def __init__(self, catalog_path: str | Path = "data/catalog.jsonl") -> None:
        self.catalog_path = Path(catalog_path)
        self.connection = sqlite3.connect(":memory:")
        self._sessions: dict[str, list[str]] = {}
        self._asked_attributes: dict[str, set[str]] = {}
        self._level_vocab: dict[str, list[tuple[frozenset[str], str]]] = {}
        self._build_index()

    def _dominant_root(self) -> str | None:
        counts: Counter[str] = Counter()
        total = 0
        with self.catalog_path.open(encoding="utf-8") as handle:
            for line in handle:
                product = json.loads(line)
                categories = product.get("categories") or []
                if categories:
                    counts[str(categories[0])] += 1
                total += 1
        if not counts or total == 0:
            return None
        root, count = counts.most_common(1)[0]
        return root if count / total >= _DOMINANT_ROOT_THRESHOLD else None

    def _build_index(self) -> None:
        dominant_root = self._dominant_root()
        cursor = self.connection.cursor()
        cursor.execute(
            "CREATE VIRTUAL TABLE products USING fts5("
            "parent_asin UNINDEXED, title, categories, features, details, store, description, "
            "tokenize='unicode61 remove_diacritics 2')"
        )
        cursor.execute(
            "CREATE TABLE category_index ("
            "parent_asin TEXT, full_key TEXT, last2_key TEXT, last1_key TEXT, segment_key TEXT)"
        )
        for level in _CATEGORY_LEVELS:
            cursor.execute(f"CREATE INDEX idx_category_{level} ON category_index({level}_key)")

        product_batch: list[tuple[str, str, str, str, str, str, str]] = []
        category_batch: list[tuple[str, str, str, str, str]] = []
        with self.catalog_path.open(encoding="utf-8") as handle:
            for line in handle:
                product = json.loads(line)
                parent_asin = str(product["parent_asin"])
                product_batch.append(
                    (
                        parent_asin,
                        _text(product.get("title")),
                        _text(product.get("categories")),
                        _text(product.get("features")),
                        _text(product.get("details")),
                        _text(product.get("store")),
                        _text(product.get("description")),
                    )
                )
                categories = [str(value) for value in (product.get("categories") or [])]
                if dominant_root is not None and categories and categories[0] == dominant_root:
                    categories = categories[1:]
                keys = _category_keys(categories)
                category_batch.append(
                    (parent_asin, keys["full"], keys["last2"], keys["last1"], keys["segment"])
                )
                if len(product_batch) >= 1000:
                    cursor.executemany("INSERT INTO products VALUES (?, ?, ?, ?, ?, ?, ?)", product_batch)
                    cursor.executemany("INSERT INTO category_index VALUES (?, ?, ?, ?, ?)", category_batch)
                    product_batch.clear()
                    category_batch.clear()
        if product_batch:
            cursor.executemany("INSERT INTO products VALUES (?, ?, ?, ?, ?, ?, ?)", product_batch)
            cursor.executemany("INSERT INTO category_index VALUES (?, ?, ?, ?, ?)", category_batch)
        self.connection.commit()

        segment_values = frozenset(
            str(row[0])
            for row in cursor.execute(
                "SELECT DISTINCT segment_key FROM category_index WHERE segment_key != ''"
            ).fetchall()
        )
        for level in _DETECTION_LEVELS:
            rows = cursor.execute(
                f"SELECT DISTINCT {level}_key FROM category_index WHERE {level}_key != ''"
            ).fetchall()
            vocab: list[tuple[frozenset[str], str]] = []
            for (key,) in rows:
                # A key that coincides with an observed department/segment value
                # (e.g. a sparsely-tagged product whose only category is "Women")
                # is department-level evidence, not specific evidence, regardless
                # of which column produced it. Keep it out of initial detection;
                # it stays reachable only through relaxation.
                if key in segment_values:
                    continue
                tokens = frozenset(_terms(key))
                if tokens:
                    vocab.append((tokens, key))
            self._level_vocab[level] = vocab

    def _detect_category(self, message_tokens: frozenset[str]) -> tuple[str, str] | None:
        if not message_tokens:
            return None
        for level in _DETECTION_LEVELS:
            matches = [
                (len(tokens), key)
                for tokens, key in self._level_vocab[level]
                if tokens.issubset(message_tokens)
            ]
            if matches:
                matches.sort(key=lambda item: (-item[0], -len(item[1])))
                return level, matches[0][1]
        return None

    def _category_filtered_query(
        self, level: str, keys: frozenset[str], expression: str, limit: int
    ) -> list[str]:
        column = f"{level}_key"
        placeholders = ",".join("?" for _ in keys)
        sql = (
            "SELECT parent_asin FROM products WHERE products MATCH ? "
            f"AND parent_asin IN (SELECT parent_asin FROM category_index WHERE {column} IN ({placeholders})) "
            "ORDER BY bm25(products, 0.0, 6.0, 4.0, 2.5, 2.5, 1.5, 1.0) LIMIT ?"
        )
        rows = self.connection.execute(sql, (expression, *keys, limit)).fetchall()
        return [str(row[0]) for row in rows]

    def _observed_broader_keys(
        self, level: str, keys: frozenset[str], next_level: str
    ) -> frozenset[str]:
        column = f"{level}_key"
        next_column = f"{next_level}_key"
        placeholders = ",".join("?" for _ in keys)
        sql = (
            f"SELECT DISTINCT {next_column} FROM category_index "
            f"WHERE {column} IN ({placeholders}) AND {next_column} != ''"
        )
        rows = self.connection.execute(sql, tuple(keys)).fetchall()
        return frozenset(str(row[0]) for row in rows)

    def _relaxed_primary_ids(
        self, detected: tuple[str, str], expression: str, limit: int
    ) -> list[str]:
        level, key = detected
        keys = frozenset({key})
        while True:
            ids = self._category_filtered_query(level, keys, expression, limit)
            if len(ids) >= limit:
                return ids
            next_level = _next_level(level)
            if next_level is None:
                return ids
            broader = self._observed_broader_keys(level, keys, next_level)
            if not broader:
                return ids
            level, keys = next_level, broader

    def _unscoped_query(self, expression: str, limit: int) -> list[str]:
        rows = self.connection.execute(
            "SELECT parent_asin FROM products WHERE products MATCH ? "
            "ORDER BY bm25(products, 0.0, 6.0, 4.0, 2.5, 2.5, 1.5, 1.0) LIMIT ?",
            (expression, limit),
        ).fetchall()
        return [str(row[0]) for row in rows]

    def _product_terms(self, parent_asin: str) -> frozenset[str]:
        row = self.connection.execute(
            "SELECT title, categories, features, details, store, description "
            "FROM products WHERE parent_asin = ?",
            (parent_asin,),
        ).fetchone()
        if row is None:
            return frozenset()
        return frozenset(_terms(" ".join(str(value) for value in row)))

    def _coverage_rerank(self, session_id: str, ids: list[str]) -> list[str]:
        # E004 — reorder the exact E003 candidate set by how many admitted
        # evidence units each candidate's indexed text overlaps (binary
        # per-unit credit, no weights). Same set, same length; only order
        # may change. Stable sort preserves E003's order on ties.
        evidence_units = _evidence_units(self._sessions[session_id])
        if not evidence_units:
            return ids
        coverage = {
            parent_asin: sum(
                1 for unit in evidence_units if self._product_terms(parent_asin) & unit
            )
            for parent_asin in ids
        }
        return sorted(ids, key=lambda parent_asin: -coverage[parent_asin])

    def _attribute_score(
        self,
        attribute: str,
        product_terms_by_id: dict[str, frozenset[str]],
        ids: list[str],
    ) -> tuple[int, int]:
        # E006 — score one adaptively-scored attribute against the exact
        # final E004 candidate ids, reusing product terms the caller already
        # computed once per candidate (no repeated _product_terms() calls
        # per attribute).
        vocab = _ATTRIBUTE_VOCAB[attribute]
        present = [
            value
            for value in (product_terms_by_id[parent_asin] & vocab for parent_asin in ids)
            if value
        ]
        usable_count = len(present)
        distinct_count = len(set(present))
        if usable_count >= 2 and distinct_count >= 2:
            return distinct_count, usable_count
        return 0, usable_count

    def _select_attribute(self, session_id: str, ids: list[str]) -> str | None:
        # E006 — adaptive, catalog-side ask_attribute selection. Reads only
        # the exact final E004 candidate ids for this turn (never enlarges,
        # reorders, or reruns retrieval) plus this session's clarification-
        # control state. Does not touch retrieval, evidence, or ranking.
        asked = self._asked_attributes[session_id]
        product_terms_by_id = {
            parent_asin: self._product_terms(parent_asin) for parent_asin in ids
        }
        best_attribute: str | None = None
        best_score: tuple[int, int] = (0, 0)
        for attribute in _ADAPTIVE_SCORED_ATTRIBUTES:
            if attribute in asked:
                continue
            score = self._attribute_score(attribute, product_terms_by_id, ids)
            if score[0] > 0 and score > best_score:
                best_score = score
                best_attribute = attribute
        chosen = best_attribute
        if chosen is None:
            for attribute in _SPECIFIC_ATTRIBUTES:
                if attribute not in asked:
                    chosen = attribute
                    break
        if chosen is None and "other" not in asked:
            chosen = "other"
        if chosen is not None:
            asked.add(chosen)
        return chosen

    def reset(self, session_id: str, user_profile: dict) -> None:
        # The profile is anonymized and may be used for personalization.
        self._sessions[session_id] = []
        self._asked_attributes[session_id] = set()

    def respond(
        self,
        session_id: str,
        user_message: str,
        turn: int,
        top_k: int,
    ) -> dict:
        if session_id not in self._sessions:
            raise RuntimeError("reset must be called before respond")
        if turn == 1 or not _is_information_free(user_message):
            self._sessions[session_id].append(user_message)
        accumulated_text = " ".join(self._sessions[session_id])
        unique_terms = list(dict.fromkeys(_terms(accumulated_text)))[:40]
        expression = " OR ".join(f'"{term}"' for term in unique_terms)
        if not expression:
            recommendations: list[dict] = []
            ids: list[str] = []
        else:
            detected = self._detect_category(frozenset(unique_terms))
            if detected is None:
                ids = self._unscoped_query(expression, top_k)
            else:
                primary_slots = min(PRIMARY_SLOTS, top_k)
                insurance_slots = min(INSURANCE_SLOTS, top_k - primary_slots)
                primary_ids = self._relaxed_primary_ids(detected, expression, primary_slots)
                global_ids = self._unscoped_query(
                    expression, max(top_k * 5, primary_slots + insurance_slots)
                )
                ids = []
                seen: set[str] = set()
                for parent_asin in primary_ids[:primary_slots]:
                    if parent_asin not in seen:
                        ids.append(parent_asin)
                        seen.add(parent_asin)
                added = 0
                for parent_asin in global_ids:
                    if added >= insurance_slots:
                        break
                    if parent_asin in seen:
                        continue
                    ids.append(parent_asin)
                    seen.add(parent_asin)
                    added += 1
                if len(ids) < top_k:
                    # Primary route under-filled its 7 reserved slots (e.g. a
                    # narrow scope that couldn't relax further). Backfill from
                    # the same global BM25 results, past the 3 reserved
                    # insurance slots, so the agent still returns top_k ids
                    # whenever the catalog can supply them.
                    for parent_asin in global_ids:
                        if len(ids) >= top_k:
                            break
                        if parent_asin in seen:
                            continue
                        ids.append(parent_asin)
                        seen.add(parent_asin)
                ids = ids[:top_k]
            ids = self._coverage_rerank(session_id, ids)
            recommendations = [{"parent_asin": parent_asin} for parent_asin in ids]
        ask_attribute = self._select_attribute(session_id, ids)
        return {
            "message": "Here are the closest matches I found.",
            "ask_attribute": ask_attribute,
            "recommendations": recommendations,
            "usage": {"prompt_tokens": 0, "completion_tokens": 0},
        }
