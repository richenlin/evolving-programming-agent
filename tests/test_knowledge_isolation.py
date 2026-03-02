#!/usr/bin/env python3
"""
Tests for multi-project knowledge isolation.
"""

import json
from pathlib import Path

import pytest

import sys
sys.path.insert(0, str(Path(__file__).parent.parent / 'evolving-agent' / 'scripts' / 'knowledge'))

from store import store_experience
from query import query_by_triggers
import query as _query_module


class TestKnowledgeIsolation:
    """Tests for project-level vs global knowledge isolation."""

    def _setup_global_kb(self, tmp_path):
        """Create a mock global KB with one entry."""
        global_kb = tmp_path / 'global_knowledge'
        exp_dir = global_kb / 'experiences'
        exp_dir.mkdir(parents=True)

        entry = {
            "id": "experience-global-001",
            "name": "Global Experience",
            "triggers": ["react"],
            "effectiveness": 0.8,
            "created_at": "2026-03-01T00:00:00"
        }
        with open(exp_dir / "experience-global-001.json", 'w') as f:
            json.dump(entry, f)

        index = {"trigger_index": {"react": ["experience-global-001"]}}
        with open(global_kb / "index.json", 'w') as f:
            json.dump(index, f)

        return global_kb

    def test_global_store_and_query(self, tmp_path):
        """默认存储和检索走全局知识库"""
        kb_root = tmp_path / 'knowledge'
        kb_root.mkdir(parents=True)

        # Store without project_root → goes to kb_root (global)
        entry = store_experience(
            name="Global Test",
            description="Test",
            context="ctx",
            solution="sol",
            triggers=["global-test"],
            kb_root=kb_root
        )

        assert entry['id']
        assert (kb_root / 'experiences' / f"{entry['id']}.json").exists()

    def test_project_store_and_query(self, tmp_path):
        """指定 project_root 后存储到项目级目录"""
        project_root = tmp_path / 'my_project'
        project_root.mkdir()

        # Store with project_root
        entry = store_experience(
            name="Project Test",
            description="Test",
            context="ctx",
            solution="sol",
            triggers=["project-test"],
            project_root=project_root
        )

        project_kb = project_root / '.opencode' / 'knowledge'
        assert (project_kb / 'experiences' / f"{entry['id']}.json").exists()

    def test_cross_project_no_leak(self, tmp_path):
        """项目 A 的知识不出现在项目 B 的检索结果中"""
        project_a = tmp_path / 'project_a'
        project_b = tmp_path / 'project_b'
        project_a.mkdir()
        project_b.mkdir()

        # Store in project A
        store_experience(
            name="Project A Secret",
            description="Secret",
            context="ctx",
            solution="sol",
            triggers=["secret-a"],
            project_root=project_a
        )

        # Query from project B (with empty global)
        global_kb = tmp_path / 'global_kb'
        global_kb.mkdir(parents=True)
        original = _query_module.get_kb_root
        _query_module.get_kb_root = lambda: global_kb

        try:
            results = query_by_triggers(["secret-a"], project_root=project_b)
            # Should NOT find project A's entry
            assert len(results) == 0
        finally:
            _query_module.get_kb_root = original

    def test_project_plus_global_merge(self, tmp_path):
        """项目级查询合并全局结果"""
        project_root = tmp_path / 'my_project'
        project_root.mkdir()

        # Store entry in project KB
        store_experience(
            name="Project Entry",
            description="Proj desc",
            context="ctx",
            solution="sol",
            triggers=["react"],
            project_root=project_root
        )

        # Setup global KB with a different entry
        global_kb = self._setup_global_kb(tmp_path)
        original = _query_module.get_kb_root
        _query_module.get_kb_root = lambda: global_kb

        try:
            results = query_by_triggers(["react"], project_root=project_root)
            # Should have entries from both project and global
            names = [r.get('name') for r in results]
            assert "Project Entry" in names
            assert "Global Experience" in names
            # Project entries come first (higher relevance or just earlier in merge)
            assert len(results) == 2
        finally:
            _query_module.get_kb_root = original
