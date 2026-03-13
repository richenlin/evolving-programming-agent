#!/usr/bin/env python3
"""
Tests for knowledge isolation.

Project-level knowledge is now stored in $PROJECT_ROOT/.opencode/.knowledge-context.md
(a persistent Markdown file) rather than a separate $PROJECT_ROOT/.opencode/knowledge/
directory.  These tests verify global KB store/query and the trigger merge logic.
"""

import json
from pathlib import Path

import pytest

import sys
sys.path.insert(0, str(Path(__file__).parent.parent / 'evolving-agent' / 'scripts' / 'knowledge'))

from store import store_experience
from query import query_by_triggers
from trigger import _extract_project_experience, format_for_context_with_merge, PROJECT_EXPERIENCE_HEADER
import query as _query_module


class TestKnowledgeIsolation:
    """Tests for global KB and project knowledge context."""

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

    def test_project_experience_extraction(self, tmp_path):
        """从 .knowledge-context.md 中提取项目经验部分"""
        ctx_file = tmp_path / '.knowledge-context.md'
        ctx_file.write_text(
            "## 相关知识\n### [problem] CORS\n**解决方案**: proxy\n\n"
            "## 项目经验\n### 2026-03-13 问题：签名过期 → 解决：设置有效期\n"
            "### 2026-03-12 决策：选择 Gin → 原因：团队熟悉\n",
            encoding='utf-8'
        )

        extracted = _extract_project_experience(str(ctx_file))
        assert "## 项目经验" in extracted
        assert "签名过期" in extracted
        assert "选择 Gin" in extracted
        assert "CORS" not in extracted

    def test_project_experience_missing_file(self, tmp_path):
        """文件不存在时返回空"""
        extracted = _extract_project_experience(str(tmp_path / 'nonexistent.md'))
        assert extracted == ''

    def test_project_experience_no_section(self, tmp_path):
        """文件中没有项目经验部分时返回空"""
        ctx_file = tmp_path / '.knowledge-context.md'
        ctx_file.write_text("## 相关知识\nsome content\n", encoding='utf-8')

        extracted = _extract_project_experience(str(ctx_file))
        assert extracted == ''

    def test_merge_preserves_project_experience(self, tmp_path):
        """format_for_context_with_merge 保留已有项目经验"""
        ctx_file = tmp_path / '.knowledge-context.md'
        ctx_file.write_text(
            "## 相关知识\nold content\n\n"
            "## 项目经验\n### 2026-03-13 决策：选择 Redis\n",
            encoding='utf-8'
        )

        empty_result = {'knowledge': {'high_relevance': [], 'medium_relevance': []}}
        output = format_for_context_with_merge(empty_result, str(ctx_file))
        assert "## 项目经验" in output
        assert "选择 Redis" in output

    def test_global_query_no_project_root(self, tmp_path):
        """query_by_triggers 只查全局知识库"""
        global_kb = self._setup_global_kb(tmp_path)
        original = _query_module.get_kb_root
        _query_module.get_kb_root = lambda: global_kb

        try:
            results = query_by_triggers(["react"])
            names = [r.get('name') for r in results]
            assert "Global Experience" in names
        finally:
            _query_module.get_kb_root = original
