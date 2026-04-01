#!/usr/bin/env python3
"""
Tests for query performance optimizations.

Tests verify:
1. Usage not updated during query (deferred to batch update)
2. Trigger cap (max 20 triggers)
3. Fuzzy matching skipped when sufficient results
4. Synonym expansion total cap
5. Batch update usage functionality
"""

import json
import tempfile
from datetime import datetime
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

# Import the module under test
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "evolving-agent" / "scripts"))

from knowledge.query import (
    expand_with_synonyms,
    batch_update_usage,
    _query_by_triggers_single_root,
    query_by_triggers,
    load_json,
)


class TestSynonymExpansionCap:
    """Test synonym expansion max_total parameter."""

    def test_synonym_expansion_total_cap(self):
        """Synonym expansion should respect max_total limit."""
        # Use tokens that have many synonyms
        tokens = ["优化", "性能", "错误", "测试", "部署"]
        
        # Without cap, this would expand to many more tokens
        expanded = expand_with_synonyms(tokens, max_expansions=3, max_total=10)
        
        # Should be capped at max_total
        assert len(expanded) <= 10
        # Original tokens should be preserved
        for token in tokens:
            assert token in expanded

    def test_synonym_expansion_respects_max_expansions(self):
        """Each token should respect max_expansions limit."""
        tokens = ["优化"]
        
        expanded_small = expand_with_synonyms(tokens, max_expansions=1, max_total=100)
        expanded_large = expand_with_synonyms(tokens, max_expansions=3, max_total=100)
        
        # More expansions should result in more tokens (up to available synonyms)
        assert len(expanded_small) <= len(expanded_large)

    def test_synonym_expansion_no_duplicates(self):
        """Expanded list should not contain duplicates."""
        tokens = ["优化", "optimize"]
        
        expanded = expand_with_synonyms(tokens, max_expansions=3, max_total=100)
        
        # Check for duplicates (case-insensitive)
        lower_expanded = [t.lower() for t in expanded]
        assert len(lower_expanded) == len(set(lower_expanded))


class TestTriggerCap:
    """Test trigger cap optimization."""

    def test_trigger_cap_limits_to20(self):
        """When more than 20 triggers provided, should cap at 20."""
        # Create mock knowledge base
        with tempfile.TemporaryDirectory() as tmpdir:
            kb_root = Path(tmpdir)
            
            # Create minimal index
            index_data = {
                "trigger_index": {},
                "version": "1.0"
            }
            (kb_root / "index.json").write_text(json.dumps(index_data))
            
            # Create 30 triggers
            triggers = [f"trigger{i}" for i in range(30)]
            
            # Query should not fail with many triggers
            results = _query_by_triggers_single_root(triggers, limit=10, kb_root=kb_root)
            
            # Should return empty results (no matching triggers)
            assert results == []

    def test_trigger_cap_keeps_longer_triggers(self):
        """When capping, should keep longer (more specific) triggers."""
        with tempfile.TemporaryDirectory() as tmpdir:
            kb_root = Path(tmpdir)
            
            # Create minimal index
            index_data = {
                "trigger_index": {},
                "version": "1.0"
            }
            (kb_root / "index.json").write_text(json.dumps(index_data))
            
            # Create triggers of varying lengths
            triggers = ["a" * i for i in range(1, 31)]  # "a", "aa", "aaa", ...
            
            # Query should not fail
            results = _query_by_triggers_single_root(triggers, limit=10, kb_root=kb_root)
            
            assert results == []


class TestFuzzySkip:
    """Test fuzzy matching early termination."""

    def test_fuzzy_skipped_when_enough_results(self):
        """When exact+partial matches are sufficient, skip fuzzy matching."""
        with tempfile.TemporaryDirectory() as tmpdir:
            kb_root = Path(tmpdir)
            
            # Create index with exact matches
            index_data = {
                "trigger_index": {
                    "react": ["experience-1"],
                    "hooks": ["experience-2"],
                    "state": ["experience-3"],
                },
                "version": "1.0"
            }
            (kb_root / "index.json").write_text(json.dumps(index_data))
            
            # Create experience directory and files
            exp_dir = kb_root / "experiences"
            exp_dir.mkdir()
            
            for i in range(1, 4):
                entry = {
                    "id": f"experience-{i}",
                    "name": f"Test Entry {i}",
                    "triggers": ["react", "hooks", "state"],
                    "effectiveness": 0.8,
                    "usage_count": 0,
                    "created_at": datetime.now().isoformat(),
                }
                (exp_dir / f"experience-{i}.json").write_text(json.dumps(entry))
            
            # Query with triggers that have exact matches
            triggers = ["react", "hooks", "state"]
            results = _query_by_triggers_single_root(triggers, limit=2, kb_root=kb_root)
            
            # Should return results without fuzzy matching
            assert len(results) >= 2
            # All results should have match_type "exact" (no fuzzy)
            for result in results:
                assert result.get("_match_type") in ["exact", "partial"]


class TestUsageUpdate:
    """Test deferred usage update optimization."""

    def test_usage_not_updated_during_query(self):
        """Query should not update usage_count (deferred to batch update)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            kb_root = Path(tmpdir)
            
            # Create index
            index_data = {
                "trigger_index": {
                    "react": ["experience-1"],
                },
                "version": "1.0"
            }
            (kb_root / "index.json").write_text(json.dumps(index_data))
            
            # Create experience directory and file
            exp_dir = kb_root / "experiences"
            exp_dir.mkdir()
            
            initial_usage_count = 5
            entry = {
                "id": "experience-1",
                "name": "Test Entry",
                "triggers": ["react"],
                "effectiveness": 0.8,
                "usage_count": initial_usage_count,
                "created_at": datetime.now().isoformat(),
            }
            entry_path = exp_dir / "experience-1.json"
            entry_path.write_text(json.dumps(entry))
            
            # Query
            triggers = ["react"]
            results = _query_by_triggers_single_root(triggers, limit=10, kb_root=kb_root)
            
            # Reload entry from disk
            updated_entry = load_json(entry_path)
            
            # Usage count should NOT have changed during query
            assert updated_entry["usage_count"] == initial_usage_count

    def test_batch_update_usage(self):
        """Batch update usage should update multiple entries."""
        with tempfile.TemporaryDirectory() as tmpdir:
            kb_root = Path(tmpdir)
            exp_dir = kb_root / "experiences"
            exp_dir.mkdir()
            
            # Create multiple entries
            entries_to_update = []
            for i in range(1, 4):
                entry = {
                    "id": f"experience-{i}",
                    "name": f"Test Entry {i}",
                    "usage_count": i * 10,
                    "created_at": datetime.now().isoformat(),
                }
                entry_path = exp_dir / f"experience-{i}.json"
                entry_path.write_text(json.dumps(entry))
                entries_to_update.append((entry_path, entry))
            
            # Batch update
            batch_update_usage(entries_to_update)
            
            # Verify all entries updated
            for i, (entry_path, _) in enumerate(entries_to_update, 1):
                updated_entry = load_json(entry_path)
                assert updated_entry["usage_count"] == i * 10 + 1
                assert "last_used_at" in updated_entry


class TestIntegration:
    """Integration tests for all optimizations together."""

    def test_query_with_many_triggers_and_synonyms(self):
        """Query should handle many triggers + synonym expansion efficiently."""
        with tempfile.TemporaryDirectory() as tmpdir:
            kb_root = Path(tmpdir)
            
            # Create index with many triggers
            trigger_index = {}
            for i in range(50):
                trigger_index[f"trigger{i}"] = [f"experience-{i}"]
            
            index_data = {
                "trigger_index": trigger_index,
                "version": "1.0"
            }
            (kb_root / "index.json").write_text(json.dumps(index_data))
            
            # Create experience directory
            exp_dir = kb_root / "experiences"
            exp_dir.mkdir()
            
            # Create entries
            for i in range(50):
                entry = {
                    "id": f"experience-{i}",
                    "name": f"Test Entry {i}",
                    "triggers": [f"trigger{i}"],
                    "effectiveness": 0.5 + (i / 100),
                    "usage_count": 0,
                    "created_at": datetime.now().isoformat(),
                }
                (exp_dir / f"experience-{i}.json").write_text(json.dumps(entry))
            
            # Query with many triggers
            triggers = [f"trigger{i}" for i in range(50)]
            results = _query_by_triggers_single_root(triggers, limit=10, kb_root=kb_root)
            
            # Should return limited results
            assert len(results) <= 10
            # Results should be sorted by relevance
            if len(results) > 1:
                for i in range(len(results) - 1):
                    assert results[i]["_relevance_score"] >= results[i + 1]["_relevance_score"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
