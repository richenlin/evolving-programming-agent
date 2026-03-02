#!/usr/bin/env python3
"""
Tests for knowledge dashboard.
"""

import json
from pathlib import Path

import pytest

import sys
sys.path.insert(0, str(Path(__file__).parent.parent / 'evolving-agent' / 'scripts' / 'knowledge'))

from dashboard import generate_stats, format_dashboard


class TestKnowledgeDashboard:
    """Tests for knowledge dashboard."""

    def test_dashboard_empty_kb(self, tmp_path):
        """空知识库不报错，返回零统计"""
        kb_root = tmp_path / 'knowledge'
        kb_root.mkdir(parents=True)

        stats = generate_stats(kb_root)
        assert stats["total_entries"] == 0
        assert stats["stale_count"] == 0

        text = format_dashboard(stats)
        assert text == "Knowledge base is empty"

    def test_dashboard_with_entries(self, tmp_path):
        """有条目时统计正确"""
        kb_root = tmp_path / 'knowledge'

        # Create entries across categories
        for cat_dir, entries in [
            ('experiences', [
                {"id": "exp-1", "name": "Exp 1", "effectiveness": 0.9,
                 "usage_count": 10, "created_at": "2026-03-01T00:00:00"},
                {"id": "exp-2", "name": "Exp 2", "effectiveness": 0.1,
                 "usage_count": 0, "created_at": "2026-02-01T00:00:00"},
            ]),
            ('problems', [
                {"id": "prob-1", "name": "Problem 1", "effectiveness": 0.5,
                 "usage_count": 5, "created_at": "2026-03-02T00:00:00"},
            ]),
        ]:
            cat_path = kb_root / cat_dir
            cat_path.mkdir(parents=True)
            for entry in entries:
                with open(cat_path / f"{entry['id']}.json", 'w') as f:
                    json.dump(entry, f)

        stats = generate_stats(kb_root)

        assert stats["total_entries"] == 3
        assert stats["by_category"]["experience"] == 2
        assert stats["by_category"]["problem"] == 1
        # stale: effectiveness < 0.2 → only exp-2 (0.1)
        assert stats["stale_count"] == 1
        # top used: exp-1 (10), prob-1 (5), exp-2 (0)
        assert stats["top_used"][0]["name"] == "Exp 1"
        assert stats["top_used"][0]["usage_count"] == 10
        # recently added: prob-1 (2026-03-02), exp-1 (2026-03-01), exp-2 (2026-02-01)
        assert stats["recently_added"][0]["name"] == "Problem 1"

        # format should produce readable output, not "empty"
        text = format_dashboard(stats)
        assert "Knowledge base is empty" not in text
        assert "Total entries: 3" in text

    def test_dashboard_json_format(self, tmp_path):
        """--json 输出合法 JSON"""
        kb_root = tmp_path / 'knowledge'
        exp_dir = kb_root / 'experiences'
        exp_dir.mkdir(parents=True)

        entry = {"id": "exp-json", "name": "JSON Test", "effectiveness": 0.7,
                 "usage_count": 3, "created_at": "2026-03-01T00:00:00"}
        with open(exp_dir / "exp-json.json", 'w') as f:
            json.dump(entry, f)

        stats = generate_stats(kb_root)

        # Should be valid JSON-serializable
        json_str = json.dumps(stats, ensure_ascii=False)
        parsed = json.loads(json_str)
        assert parsed["total_entries"] == 1
        assert "by_category" in parsed
        assert "top_used" in parsed
