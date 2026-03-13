#!/usr/bin/env python3
"""Tests for BM25-based search (replacement for embedding-based semantic search)."""

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(
    0, str(Path(__file__).parent.parent / "evolving-agent" / "scripts" / "knowledge")
)

from embedding import HAS_EMBEDDING, BM25Index, search, build_index, invalidate_cache, _bm25_tokenize


def _make_kb(tmp_path, entries):
    """Helper: create a mini knowledge base with given entries."""
    kb_root = tmp_path / "knowledge"
    exp_dir = kb_root / "experiences"
    exp_dir.mkdir(parents=True)

    index_triggers = {}
    for entry in entries:
        entry_id = entry["id"]
        with open(exp_dir / f"{entry_id}.json", "w") as f:
            json.dump(entry, f)
        for trigger in entry.get("triggers", []):
            index_triggers.setdefault(trigger, []).append(entry_id)

    with open(kb_root / "index.json", "w") as f:
        json.dump({"trigger_index": index_triggers}, f)

    return kb_root


class TestHasEmbedding:
    """BM25 is always available."""

    def test_has_embedding_always_true(self):
        assert HAS_EMBEDDING is True


class TestBM25Index:
    """Unit tests for the BM25Index class."""

    def test_empty_corpus(self):
        index = BM25Index([], [])
        assert index.doc_count == 0
        results = index.search(["test"], top_k=5)
        assert results == []

    def test_single_document(self):
        index = BM25Index(["hello world"], ["doc-1"])
        results = index.search(["hello"], top_k=5)
        assert len(results) == 1
        assert results[0][0] == "doc-1"
        assert results[0][1] > 0

    def test_multiple_documents_ranking(self):
        docs = [
            "react hooks state management guide",
            "python flask web framework tutorial",
            "react component lifecycle hooks performance",
        ]
        ids = ["doc-react-1", "doc-python", "doc-react-2"]
        index = BM25Index(docs, ids)

        results = index.search(["react", "hooks"], top_k=3)
        assert len(results) >= 2
        result_ids = [r[0] for r in results]
        # Both react docs should rank above python doc
        assert "doc-react-1" in result_ids[:2]
        assert "doc-react-2" in result_ids[:2]

    def test_no_match_returns_empty(self):
        index = BM25Index(["hello world"], ["doc-1"])
        results = index.search(["nonexistent"], top_k=5)
        assert results == []

    def test_chinese_tokenization(self):
        docs = ["修复跨域请求问题", "优化数据库查询性能"]
        ids = ["doc-cors", "doc-db"]
        index = BM25Index(docs, ids)
        query_tokens = _bm25_tokenize("跨域")
        results = index.search(query_tokens, top_k=5)
        assert len(results) >= 1
        assert results[0][0] == "doc-cors"

    def test_score_is_positive(self):
        index = BM25Index(["test document"], ["doc-1"])
        results = index.search(["test"], top_k=1)
        assert results[0][1] > 0


class TestSearch:
    """Integration tests for the search() function."""

    def test_search_basic(self, tmp_path):
        invalidate_cache()
        kb_root = _make_kb(
            tmp_path,
            [
                {
                    "id": "experience-cors-001",
                    "name": "CORS proxy solution",
                    "triggers": ["cors", "proxy"],
                    "content": {
                        "description": "Fix cross-origin resource sharing issues"
                    },
                    "effectiveness": 0.8,
                }
            ],
        )
        results = search("cors proxy cross origin", kb_root, top_k=5)
        assert isinstance(results, list)
        assert len(results) >= 1
        assert results[0][0] == "experience-cors-001"
        assert isinstance(results[0][1], float)
        assert results[0][1] > 0

    def test_search_empty_kb(self, tmp_path):
        invalidate_cache()
        kb_root = tmp_path / "knowledge"
        kb_root.mkdir(parents=True)
        results = search("anything", kb_root, top_k=5)
        assert results == []

    def test_search_multiple_entries(self, tmp_path):
        invalidate_cache()
        kb_root = _make_kb(
            tmp_path,
            [
                {
                    "id": "experience-react-001",
                    "name": "React Hooks Guide",
                    "triggers": ["react", "hooks"],
                    "content": {
                        "description": "Guide to React hooks and state management"
                    },
                },
                {
                    "id": "experience-vue-001",
                    "name": "Vue Composition API",
                    "triggers": ["vue", "composition"],
                    "content": {"description": "Vue 3 composition API patterns"},
                },
            ],
        )

        results = search("react hooks state", kb_root, top_k=5)
        assert len(results) >= 1
        assert results[0][0] == "experience-react-001"

    def test_search_synonym_expansion(self, tmp_path):
        """Synonym expansion should help match related terms."""
        invalidate_cache()
        kb_root = _make_kb(
            tmp_path,
            [
                {
                    "id": "experience-perf-001",
                    "name": "Performance optimization",
                    "triggers": ["optimize", "performance"],
                    "content": {
                        "description": "Web app performance optimization techniques"
                    },
                },
            ],
        )
        # Use English keyword that has synonym mapping
        # 'optimize' expands to '优化', 'optimization', 'performance', '性能'
        results = search("optimize", kb_root, top_k=5)
        assert len(results) >= 1


class TestBuildIndex:
    """Tests for build_index()."""

    def test_build_index_returns_tuple(self, tmp_path):
        invalidate_cache()
        kb_root = _make_kb(
            tmp_path,
            [
                {
                    "id": "experience-test-001",
                    "name": "Test entry",
                    "triggers": ["test"],
                    "content": {"description": "A test entry"},
                },
            ],
        )
        index, ids, entries = build_index(kb_root)
        assert index is not None
        assert isinstance(index, BM25Index)
        assert len(ids) == 1
        assert ids[0] == "experience-test-001"
        assert len(entries) == 1

    def test_build_index_empty(self, tmp_path):
        invalidate_cache()
        kb_root = tmp_path / "knowledge"
        kb_root.mkdir()
        index, ids, entries = build_index(kb_root)
        assert index is None
        assert ids == []
        assert entries == []


class TestCache:
    """Tests for index cache behavior."""

    def test_cache_invalidation(self, tmp_path):
        invalidate_cache()
        kb_root = _make_kb(
            tmp_path,
            [
                {
                    "id": "exp-1",
                    "name": "Entry 1",
                    "triggers": ["a"],
                    "content": {"description": "First"},
                },
            ],
        )
        r1 = search("a", kb_root, top_k=5)
        assert len(r1) == 1

        invalidate_cache(kb_root)

        # After invalidation, should rebuild
        r2 = search("a", kb_root, top_k=5)
        assert len(r2) == 1
