#!/usr/bin/env python3
"""Tests for knowledge isolation (global SQLite)."""

from pathlib import Path

import pytest

import sys
sys.path.insert(0, str(Path(__file__).parent.parent / 'evolving-agent' / 'scripts' / 'knowledge'))

from store import store_experience
from query import query_by_triggers
from kb_helpers import seed_entry


class TestKnowledgeIsolation:
    def test_global_store_and_query(self, kb_db):
        entry = store_experience(
            name="Global JWT Session Pattern",
            description="长时间操作后 access token 过期导致 401",
            context="前端 SPA 长时间停留在编辑页",
            solution="access token 15m + refresh token 轮换",
            triggers=["global-test"],
            _db=kb_db,
        )

        assert entry["id"]
        stored = kb_db.get_entry(entry["id"])
        assert stored is not None
        assert stored["name"] == "Global JWT Session Pattern"

    def test_global_query(self, kb_db):
        seed_entry(
            kb_db,
            id="experience-global-001",
            name="Global Experience",
            triggers=["react"],
            effectiveness=0.8,
            created_at="2026-03-01T00:00:00",
        )

        results = query_by_triggers(["react"])
        names = [r.get("name") for r in results]
        assert "Global Experience" in names

    def test_project_scoped_store(self, tmp_path, kb_db):
        project = tmp_path / "proj"
        project.mkdir()

        entry = store_experience(
            name="Project Local Auth Flow",
            description="项目内 OAuth 回调路径与生产环境不一致",
            context="本地开发使用 localhost:3000",
            solution="按环境变量配置 redirect_uri",
            triggers=["local"],
            project_path=str(project),
        )

        assert entry["scope"] == "project"
        from codegraph.db import CodeGraphDB
        proj_db = CodeGraphDB(project / ".opencode" / "codegraph" / "knowledge.db")
        assert proj_db.get_entry(entry["id"]) is not None
