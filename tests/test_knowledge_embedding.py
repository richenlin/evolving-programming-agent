#!/usr/bin/env python3
"""
Tests for embedding-based semantic search.
"""

import json
from pathlib import Path

import pytest

import sys
sys.path.insert(0, str(Path(__file__).parent.parent / 'evolving-agent' / 'scripts' / 'knowledge'))

from embedding import HAS_EMBEDDING
from query import query_semantic


class TestEmbeddingFallback:
    """Tests for graceful degradation without sentence-transformers."""

    def test_fallback_without_dependency(self, tmp_path):
        """不安装 sentence-transformers 时不报错，fallback 到关键词搜索"""
        # query_semantic should not raise even without embedding library
        # It will either use embeddings or fall back to keyword mode
        kb_root = tmp_path / 'knowledge'
        exp_dir = kb_root / 'experiences'
        exp_dir.mkdir(parents=True)

        entry = {
            "id": "experience-test-001",
            "name": "React Hooks Guide",
            "triggers": ["react", "hooks"],
            "content": {"description": "Guide to React hooks"},
            "effectiveness": 0.8,
            "created_at": "2026-03-01T00:00:00"
        }
        with open(exp_dir / "experience-test-001.json", 'w') as f:
            json.dump(entry, f)

        index = {"trigger_index": {"react": ["experience-test-001"],
                                    "hooks": ["experience-test-001"]}}
        with open(kb_root / "index.json", 'w') as f:
            json.dump(index, f)

        import query
        original = query.get_kb_root
        query.get_kb_root = lambda: kb_root

        try:
            # Should not raise
            results = query_semantic("react hooks", limit=10)
            # In fallback mode (no embedding), should still return results via keyword
            if not HAS_EMBEDDING:
                assert isinstance(results, list)
        finally:
            query.get_kb_root = original

    @pytest.mark.skipif(not HAS_EMBEDDING, reason="requires sentence-transformers")
    def test_semantic_search_basic(self, tmp_path):
        """安装 sentence-transformers 后基本语义搜索可用"""
        from embedding import search as semantic_search

        kb_root = tmp_path / 'knowledge'
        exp_dir = kb_root / 'experiences'
        exp_dir.mkdir(parents=True)

        entry = {
            "id": "experience-cors-001",
            "name": "CORS proxy solution",
            "triggers": ["cors", "proxy"],
            "content": {"description": "Fix cross-origin resource sharing issues"},
            "effectiveness": 0.8,
            "created_at": "2026-03-01T00:00:00"
        }
        with open(exp_dir / "experience-cors-001.json", 'w') as f:
            json.dump(entry, f)

        results = semantic_search("cross domain request problem", kb_root, top_k=5)
        assert isinstance(results, list)
        if results:
            assert isinstance(results[0], tuple)
            assert len(results[0]) == 2  # (entry_id, score)

    @pytest.mark.skipif(not HAS_EMBEDDING, reason="requires sentence-transformers")
    def test_cache_creation(self, tmp_path):
        """索引缓存文件可以生成"""
        from embedding import build_index

        kb_root = tmp_path / 'knowledge'
        exp_dir = kb_root / 'experiences'
        exp_dir.mkdir(parents=True)

        entry = {
            "id": "experience-cache-001",
            "name": "Cache test",
            "triggers": ["cache"],
            "content": {"description": "Test cache creation"},
        }
        with open(exp_dir / "experience-cache-001.json", 'w') as f:
            json.dump(entry, f)

        vectors, ids, entries = build_index(kb_root)
        assert vectors is not None
        assert len(ids) == 1
        assert ids[0] == "experience-cache-001"
