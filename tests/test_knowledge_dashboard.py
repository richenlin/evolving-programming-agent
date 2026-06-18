#!/usr/bin/env python3
"""Tests for knowledge dashboard (CodeGraph SQLite)."""

import json
from pathlib import Path

import pytest

import sys
sys.path.insert(0, str(Path(__file__).parent.parent / 'evolving-agent' / 'scripts' / 'knowledge'))

from dashboard import generate_stats, format_dashboard
from kb_helpers import seed_entry


class TestKnowledgeDashboard:
    def test_dashboard_empty_kb(self, kb_db):
        stats = generate_stats()
        assert stats["total_entries"] == 0
        assert stats["stale_count"] == 0

        text = format_dashboard(stats)
        assert text == "Knowledge base is empty"

    def test_dashboard_with_entries(self, kb_db):
        seed_entry(
            kb_db, id="exp-1", name="Exp 1", effectiveness=0.9,
            usage_count=10, created_at="2026-03-01T00:00:00",
        )
        seed_entry(
            kb_db, id="exp-2", name="Exp 2", effectiveness=0.1,
            usage_count=0, created_at="2026-02-01T00:00:00",
        )
        seed_entry(
            kb_db, id="prob-1", name="Problem 1", category="problem",
            content={"problem_name": "P", "symptoms": [], "root_causes": [], "solutions": []},
            effectiveness=0.5, usage_count=5, created_at="2026-03-02T00:00:00",
        )

        stats = generate_stats()

        assert stats["total_entries"] == 3
        assert stats["by_category"]["experience"] == 2
        assert stats["by_category"]["problem"] == 1
        assert stats["stale_count"] == 1
        assert stats["top_used"][0]["name"] == "Exp 1"
        assert stats["top_used"][0]["usage_count"] == 10
        assert stats["recently_added"][0]["name"] == "Problem 1"

        text = format_dashboard(stats)
        assert "Knowledge base is empty" not in text
        assert "Total entries: 3" in text

    def test_dashboard_json_format(self, kb_db):
        seed_entry(
            kb_db, id="exp-json", name="JSON Test", effectiveness=0.7,
            usage_count=3, created_at="2026-03-01T00:00:00",
        )

        stats = generate_stats()
        parsed = json.loads(json.dumps(stats, ensure_ascii=False))
        assert parsed["total_entries"] == 1
        assert "by_category" in parsed
        assert "top_used" in parsed
