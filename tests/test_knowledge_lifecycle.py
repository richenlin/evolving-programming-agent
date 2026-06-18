#!/usr/bin/env python3
"""Tests for knowledge lifecycle management (CodeGraph SQLite)."""

from datetime import datetime, timedelta
from pathlib import Path

import pytest

import sys
sys.path.insert(0, str(Path(__file__).parent.parent / 'evolving-agent' / 'scripts' / 'knowledge'))

from lifecycle import decay_unused, get_stale_entries, gc
from kb_helpers import seed_entry


class TestDecayUnused:
    def test_decay_reduces_effectiveness(self, kb_db):
        old_date = (datetime.now() - timedelta(days=100)).isoformat()
        seed_entry(
            kb_db,
            id="experience-old-001",
            name="Old Entry",
            effectiveness=0.8,
            last_used_at=old_date,
        )

        affected = decay_unused(days_threshold=90, decay_rate=0.1)

        assert len(affected) == 1
        assert affected[0]['old_effectiveness'] == 0.8
        assert abs(affected[0]['new_effectiveness'] - 0.7) < 0.01

        updated = kb_db.get_entry("experience-old-001")
        assert abs(updated['effectiveness'] - 0.7) < 0.01

    def test_decay_skips_recently_used(self, kb_db):
        recent_date = (datetime.now() - timedelta(days=30)).isoformat()
        seed_entry(
            kb_db,
            id="experience-recent-001",
            name="Recent Entry",
            effectiveness=0.8,
            last_used_at=recent_date,
        )

        affected = decay_unused(days_threshold=90, decay_rate=0.1)

        assert len(affected) == 0
        unchanged = kb_db.get_entry("experience-recent-001")
        assert unchanged['effectiveness'] == 0.8

    def test_effectiveness_floor_at_zero(self, kb_db):
        old_date = (datetime.now() - timedelta(days=100)).isoformat()
        seed_entry(
            kb_db,
            id="experience-low-001",
            name="Low Effectiveness Entry",
            effectiveness=0.05,
            last_used_at=old_date,
        )

        affected = decay_unused(days_threshold=90, decay_rate=0.1)

        assert len(affected) == 1
        assert affected[0]['new_effectiveness'] >= 0.0
        updated = kb_db.get_entry("experience-low-001")
        assert updated['effectiveness'] >= 0.0


class TestGetStaleEntries:
    def test_get_stale_entries(self, kb_db):
        seed_entry(kb_db, id="experience-stale-001", name="Stale Entry", effectiveness=0.05)
        seed_entry(kb_db, id="experience-good-001", name="Good Entry", effectiveness=0.8)

        stale = get_stale_entries(effectiveness_threshold=0.1)

        assert len(stale) == 1
        assert stale[0]['id'] == "experience-stale-001"


class TestGC:
    def test_gc_removes_stale(self, kb_db):
        seed_entry(kb_db, id="experience-gc-001", name="Stale Entry for GC", effectiveness=0.05)

        removed = gc(threshold=0.1, dry_run=False)

        assert len(removed) == 1
        assert kb_db.get_entry("experience-gc-001") is None

    def test_gc_dry_run(self, kb_db):
        seed_entry(kb_db, id="experience-dry-001", name="Stale Entry for Dry Run", effectiveness=0.05)

        would_remove = gc(threshold=0.1, dry_run=True)

        assert len(would_remove) == 1
        assert kb_db.get_entry("experience-dry-001") is not None
