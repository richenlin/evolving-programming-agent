#!/usr/bin/env python3
"""Tests for query performance (CodeGraph SQLite)."""

from datetime import datetime
from pathlib import Path

import pytest

import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "evolving-agent" / "scripts"))

from knowledge.query import expand_with_synonyms, batch_update_usage, query_by_triggers
from kb_helpers import seed_entry


class TestSynonymExpansionCap:
    def test_synonym_expansion_total_cap(self):
        tokens = ["优化", "性能", "错误", "测试", "部署"]
        expanded = expand_with_synonyms(tokens, max_expansions=3, max_total=10)
        assert len(expanded) <= 10
        for token in tokens:
            assert token in expanded

    def test_synonym_expansion_respects_max_expansions(self):
        tokens = ["优化"]
        expanded_small = expand_with_synonyms(tokens, max_expansions=1, max_total=100)
        expanded_large = expand_with_synonyms(tokens, max_expansions=3, max_total=100)
        assert len(expanded_small) <= len(expanded_large)

    def test_synonym_expansion_no_duplicates(self):
        tokens = ["优化", "optimize"]
        expanded = expand_with_synonyms(tokens, max_expansions=3, max_total=100)
        lower_expanded = [t.lower() for t in expanded]
        assert len(lower_expanded) == len(set(lower_expanded))


class TestQueryPerformance:
    def test_many_triggers_do_not_fail(self, kb_db):
        triggers = [f"trigger{i}" for i in range(30)]
        results = query_by_triggers(triggers, limit=10)
        assert isinstance(results, list)

    def test_query_returns_limited_results(self, kb_db):
        for i in range(20):
            seed_entry(
                kb_db,
                id=f"experience-{i}",
                name=f"Entry {i}",
                triggers=[f"topic{i}"],
                effectiveness=0.5 + i / 100,
            )

        results = query_by_triggers(["topic0", "topic1", "topic2"], limit=5)
        assert len(results) <= 5

    def test_batch_update_usage(self, kb_db):
        entries = []
        for i in range(1, 4):
            seed_entry(kb_db, id=f"experience-{i}", name=f"Entry {i}", usage_count=i * 10)
            entries.append(kb_db.get_entry(f"experience-{i}"))

        batch_update_usage([(None, e) for e in entries])

        for i in range(1, 4):
            updated = kb_db.get_entry(f"experience-{i}")
            assert updated["usage_count"] == i * 10 + 1
            assert updated.get("last_used_at")

    def test_results_sorted_by_relevance(self, kb_db):
        seed_entry(
            kb_db, id="high", name="High perf entry", triggers=["perf"],
            effectiveness=0.95, usage_count=100,
            last_used_at=datetime.now().isoformat(),
            content={"description": "performance tuning", "solution": "perf optimize"},
        )
        seed_entry(
            kb_db, id="low", name="Low perf entry", triggers=["perf"],
            effectiveness=0.1, usage_count=0,
            created_at="2020-01-01T00:00:00",
            content={"description": "minor note", "solution": "perf baseline"},
        )

        results = query_by_triggers(["perf"], limit=10, use_synonyms=False)
        assert len(results) >= 2
        if len(results) > 1:
            assert results[0]["_relevance_score"] >= results[1]["_relevance_score"]
