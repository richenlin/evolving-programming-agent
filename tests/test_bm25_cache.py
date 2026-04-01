#!/usr/bin/env python3
"""
Tests for BM25 persistent cache functionality.
"""

import json
import os
import tempfile
import time
from pathlib import Path

import pytest

import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "evolving-agent" / "scripts"))

from knowledge.embedding import (
    _load_cache,
    _save_cache,
    _get_file_stats,
    build_index,
    search,
    invalidate_cache,
    rebuild_cache,
)


@pytest.fixture
def temp_kb():
    """Create a temporary knowledge base with test data."""
    with tempfile.TemporaryDirectory() as tmpdir:
        kb_root = Path(tmpdir)

        exp_dir = kb_root / "experiences"
        exp_dir.mkdir()

        entry1 = {
            "id": "exp-001",
            "name": "Test Experience 1",
            "content": {"description": "This is a test experience about Python"},
            "triggers": ["python", "test"],
        }
        with open(exp_dir / "exp-001.json", "w", encoding="utf-8") as f:
            json.dump(entry1, f)
        time.sleep(0.01)

        entry2 = {
            "id": "exp-002",
            "name": "Test Experience 2",
            "content": {"description": "Another experience about JavaScript"},
            "triggers": ["javascript", "web"],
        }
        with open(exp_dir / "exp-002.json", "w", encoding="utf-8") as f:
            json.dump(entry2, f)

        yield kb_root


def test_cache_created_on_first_build(temp_kb):
    """Test that cache file is created after first build."""
    cache_file = temp_kb / ".bm25_cache.json"
    assert not cache_file.exists()

    index, entry_ids, entries = build_index(temp_kb)

    assert cache_file.exists()

    cache = _load_cache(temp_kb)
    assert cache["version"] == 2
    assert cache["file_count"] == 2
    assert len(cache["doc_ids"]) == 2
    assert len(cache["doc_texts"]) == 2
    assert "built_at" in cache


def test_cache_reused_on_second_build(temp_kb):
    """Test that cache is reused on second build."""
    cache_file = temp_kb / ".bm25_cache.json"

    index1, entry_ids1, entries1 = build_index(temp_kb)
    first_build_time = cache_file.stat().st_mtime

    time.sleep(0.1)

    index2, entry_ids2, entries2 = build_index(temp_kb)
    second_build_time = cache_file.stat().st_mtime

    assert first_build_time == second_build_time

    assert entry_ids1 == entry_ids2


def test_cache_invalidated_on_new_file(temp_kb):
    """Test that cache is invalidated when a new file is added."""
    index1, entry_ids1, entries1 = build_index(temp_kb)
    cache1 = _load_cache(temp_kb)
    original_file_count = cache1["file_count"]

    exp_dir = temp_kb / "experiences"
    entry3 = {
        "id": "exp-003",
        "name": "Test Experience 3",
        "content": {"description": "A new experience about Rust"},
        "triggers": ["rust", "systems"],
    }
    with open(exp_dir / "exp-003.json", "w", encoding="utf-8") as f:
        json.dump(entry3, f)

    invalidate_cache(temp_kb)

    index2, entry_ids2, entries2 = build_index(temp_kb)
    cache2 = _load_cache(temp_kb)

    assert cache2["file_count"] == original_file_count + 1
    assert len(entry_ids2) == 3


def test_cache_invalidated_on_modified_file(temp_kb):
    """Test that cache is invalidated when a file is modified."""
    index1, entry_ids1, entries1 = build_index(temp_kb)
    cache1 = _load_cache(temp_kb)
    original_mtime = cache1["newest_mtime"]

    time.sleep(0.1)

    exp_dir = temp_kb / "experiences"
    entry1 = {
        "id": "exp-001",
        "name": "Modified Test Experience 1",
        "content": {"description": "This is a MODIFIED test experience about Python"},
        "triggers": ["python", "test", "modified"],
    }
    with open(exp_dir / "exp-001.json", "w", encoding="utf-8") as f:
        json.dump(entry1, f)

    invalidate_cache(temp_kb)

    index2, entry_ids2, entries2 = build_index(temp_kb)
    cache2 = _load_cache(temp_kb)

    assert cache2["newest_mtime"] > original_mtime


def test_rebuild_cache_function(temp_kb):
    """Test that rebuild_cache forces cache rebuild."""
    cache_file = temp_kb / ".bm25_cache.json"

    index1, entry_ids1, entries1 = build_index(temp_kb)
    first_build_time = cache_file.stat().st_mtime

    time.sleep(0.1)

    rebuild_cache(temp_kb)
    second_build_time = cache_file.stat().st_mtime

    assert second_build_time > first_build_time

    cache = _load_cache(temp_kb)
    assert cache["version"] == 2
    assert cache["file_count"] == 2


def test_search_with_cache(temp_kb):
    """Test that search works correctly with cached index."""
    results1 = search("Python", temp_kb, top_k=5)
    assert len(results1) > 0

    results2 = search("Python", temp_kb, top_k=5)
    assert len(results2) > 0
    assert results1 == results2


def test_cache_file_stats(temp_kb):
    """Test _get_file_stats function."""
    file_count, newest_mtime = _get_file_stats(temp_kb)

    assert file_count == 2
    assert newest_mtime > 0

    exp_dir = temp_kb / "experiences"
    entry3 = {
        "id": "exp-003",
        "name": "Test Experience 3",
        "content": {"description": "Another test"},
        "triggers": ["test"],
    }
    with open(exp_dir / "exp-003.json", "w", encoding="utf-8") as f:
        json.dump(entry3, f)

    new_file_count, new_newest_mtime = _get_file_stats(temp_kb)
    assert new_file_count == 3
    assert new_newest_mtime >= newest_mtime


def test_empty_kb(temp_kb):
    """Test behavior with empty knowledge base."""
    exp_dir = temp_kb / "experiences"
    for f in exp_dir.glob("*.json"):
        f.unlink()

    index, entry_ids, entries = build_index(temp_kb)
    assert index is None
    assert entry_ids == []
    assert entries == []


def test_cache_with_multiple_categories(temp_kb):
    """Test cache with multiple category directories."""
    prob_dir = temp_kb / "problems"
    prob_dir.mkdir()

    prob1 = {
        "id": "prob-001",
        "name": "Test Problem",
        "content": {"description": "A problem description"},
        "triggers": ["problem", "bug"],
    }
    with open(prob_dir / "prob-001.json", "w", encoding="utf-8") as f:
        json.dump(prob1, f)

    index, entry_ids, entries = build_index(temp_kb)

    cache = _load_cache(temp_kb)
    assert cache["file_count"] == 3
    assert len(entry_ids) == 3
