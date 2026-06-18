#!/usr/bin/env python3
"""Tests for knowledge fuzzy matching (CodeGraph SQLite)."""

from pathlib import Path

import pytest

import sys
sys.path.insert(0, str(Path(__file__).parent.parent / 'evolving-agent' / 'scripts' / 'knowledge'))

from query import fuzzy_match, query_by_triggers, get_global_index, compute_relevance, tokenize, HAS_JIEBA
from kb_helpers import seed_entry


class TestComputeRelevance:
    def test_relevance_components(self):
        entry = {
            "id": "test-001",
            "name": "Test Entry",
            "effectiveness": 0.8,
            "usage_count": 50,
            "last_used_at": "2026-03-01T00:00:00",
            "_match_score": 3,
        }
        score = compute_relevance(entry, ["test"])
        assert 0 <= score <= 1
        assert score >= 0.5

    def test_relevance_ranking(self, kb_db):
        seed_entry(
            kb_db, id="experience-high-001", name="High Relevance",
            triggers=["test"], effectiveness=0.9, usage_count=100,
            last_used_at="2026-03-01T00:00:00",
        )
        seed_entry(
            kb_db, id="experience-low-001", name="Low Relevance",
            triggers=["test"], effectiveness=0.1,
            created_at="2020-01-01T00:00:00",
        )

        results = query_by_triggers(["test"], limit=10)
        assert len(results) >= 1
        assert results[0]["id"] == "experience-high-001"
        for r in results:
            assert "_relevance_score" in r

    def test_top_k_limit(self, kb_db):
        for i in range(20):
            seed_entry(
                kb_db,
                id=f"experience-test-{i:03d}",
                name=f"Test Entry {i}",
                triggers=["test"],
                effectiveness=0.5,
            )

        results = query_by_triggers(["test"], limit=10)
        assert len(results) == 10


class TestFuzzyMatch:
    def test_exact_match_still_works(self):
        assert fuzzy_match(["react"], ["react"]) == 1.0

    def test_fuzzy_match_similar_terms(self):
        score = fuzzy_match(["React hook"], ["react-hooks"])
        assert score >= 0.6

    def test_fuzzy_no_false_positives(self):
        assert fuzzy_match(["python"], ["javascript"], threshold=0.6) == 0.0
        assert fuzzy_match(["database"], ["frontend"], threshold=0.6) == 0.0

    def test_fuzzy_match_case_insensitive(self):
        assert fuzzy_match(["REACT"], ["react"]) == 1.0
        assert fuzzy_match(["React"], ["REACT"]) == 1.0

    def test_fuzzy_match_threshold(self):
        assert fuzzy_match(["abc"], ["xyz"], threshold=0.8) == 0.0
        assert fuzzy_match(["abc"], ["abd"], threshold=0.5) > 0.0


class TestQueryByTriggersWithFuzzy:
    def test_exact_trigger_match(self, kb_db):
        seed_entry(kb_db, id="experience-react-001", name="React Basics", triggers=["react"])
        seed_entry(kb_db, id="experience-hooks-001", name="React Hooks", triggers=["react-hooks"])

        results = query_by_triggers(["react"], limit=10)
        assert len(results) > 0
        assert results[0]["id"] == "experience-react-001"

    def test_fuzzy_match_integration(self, kb_db):
        seed_entry(
            kb_db,
            id="experience-hooks-001",
            name="React Hooks Guide",
            triggers=["react-hooks"],
        )

        results = query_by_triggers(["React hook"], limit=10)
        assert isinstance(results, list)


class TestGlobalIndex:
    def test_get_global_index_sqlite(self, kb_db):
        seed_entry(kb_db, id="exp-1", name="One", triggers=["a"])
        index = get_global_index()
        assert index["version"] == "codegraph-2"
        assert index["stats"]["total_entries"] >= 1


class TestTokenize:
    def test_tokenize_english(self):
        tokens = tokenize("react hooks state")
        assert "react" in tokens
        assert "hooks" in tokens
        assert "state" in tokens

    def test_tokenize_chinese_fallback(self):
        tokens = tokenize("修复CORS跨域问题")
        assert len(tokens) > 0
        token_str = " ".join(tokens)
        assert "CORS" in token_str or "cors" in token_str

    @pytest.mark.skipif(not HAS_JIEBA, reason="requires jieba")
    def test_tokenize_chinese_with_jieba(self):
        tokens = tokenize("修复CORS跨域问题")
        assert "跨域" in tokens or "跨" in tokens

    def test_tokenize_empty_string(self):
        assert tokenize("") == []

    def test_tokenize_mixed_content(self):
        tokens = tokenize("React 渲染 hooks")
        assert len(tokens) >= 2
