#!/usr/bin/env python3
"""Tests for knowledge query usage tracking (CodeGraph SQLite)."""

from datetime import datetime
from pathlib import Path

import pytest

import sys
sys.path.insert(0, str(Path(__file__).parent.parent / 'evolving-agent' / 'scripts' / 'knowledge'))

from query import batch_update_usage, query_by_triggers, get_entry
from kb_helpers import seed_entry


class TestUpdateUsage:
    def test_batch_update_increments_count(self, kb_db):
        seed_entry(kb_db, id="test-001", name="Test Entry", usage_count=5)

        entry = kb_db.get_entry("test-001")
        batch_update_usage([(None, entry)])

        updated = kb_db.get_entry("test-001")
        assert updated["usage_count"] == 6

    def test_batch_update_sets_timestamp(self, kb_db):
        old_time = "2026-01-01T00:00:00"
        seed_entry(kb_db, id="test-002", name="Test Entry", usage_count=0, last_used_at=old_time)

        entry = kb_db.get_entry("test-002")
        batch_update_usage([(None, entry)])

        updated = kb_db.get_entry("test-002")
        assert updated["last_used_at"] != old_time
        datetime.fromisoformat(updated["last_used_at"])

    def test_query_increments_usage(self, kb_db):
        seed_entry(
            kb_db,
            id="test-003",
            name="React Hooks",
            triggers=["react", "hooks"],
            usage_count=0,
        )

        query_by_triggers(["react"], limit=5)

        updated = kb_db.get_entry("test-003")
        assert updated["usage_count"] >= 1

    def test_batch_update_deduplicates(self, kb_db):
        seed_entry(kb_db, id="test-004", name="Test", usage_count=3)
        entry = kb_db.get_entry("test-004")

        batch_update_usage([(None, entry), (None, entry), (None, entry)])

        updated = kb_db.get_entry("test-004")
        assert updated["usage_count"] == 4

    def test_get_entry_returns_stored(self, kb_db):
        seed_entry(kb_db, id="test-005", name="Test Entry", category="problem",
                   content={"problem_name": "P", "symptoms": [], "root_causes": [], "solutions": []},
                   tags=["python", "testing"], effectiveness=0.85, usage_count=10)

        entry = get_entry("test-005")
        assert entry["name"] == "Test Entry"
        assert entry["category"] == "problem"
        assert entry["tags"] == ["python", "testing"]
        assert entry["effectiveness"] == 0.85
