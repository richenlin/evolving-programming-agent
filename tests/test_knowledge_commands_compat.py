#!/usr/bin/env python3
"""
Full-scenario compatibility tests for `knowledge` CLI and CodeGraph integration.

Ensures original knowledge command usage remains valid after CodeGraph v3 / KnowledgePlane.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from conftest import patch_get_db
from kb_helpers import seed_entry


@pytest.fixture
def isolated_knowledge_env(tmp_path, monkeypatch):
    from codegraph.db import CodeGraphDB

    global_root = tmp_path / "global" / "codegraph"
    global_root.mkdir(parents=True)
    global_db = CodeGraphDB(global_root / "knowledge.db")

    def _get_db(project_path=None):
        if project_path:
            p = Path(project_path) / ".opencode" / "codegraph" / "knowledge.db"
            p.parent.mkdir(parents=True, exist_ok=True)
            return CodeGraphDB(p)
        return global_db

    patch_get_db(monkeypatch, _get_db)
    monkeypatch.setenv("CODEGRAPH_DIR", str(global_root))
    monkeypatch.setenv("KNOWLEDGE_BASE_PATH", str(global_root))

    try:
        import core.path_resolver as pr

        monkeypatch.setattr(pr, "get_knowledge_base_dir", lambda: global_root)
        monkeypatch.setattr(pr, "get_global_kb_root", lambda: global_root)
    except ImportError:
        pass

    return {"global_db": global_db, "global_root": global_root}


@pytest.fixture
def seeded_kb(isolated_knowledge_env):
    db = isolated_knowledge_env["global_db"]
    seed_entry(
        db,
        id="problem-cors-001",
        name="CORS 跨域修复",
        category="problem",
        content={
            "description": "浏览器 blocked by CORS policy",
            "solution": "开发环境配置 vite proxy 转发 /api",
            "symptoms": ["CORS", "跨域"],
        },
        triggers=["cors", "跨域", "vite"],
        tags=["cors", "vite"],
        scope="global",
    )
    seed_entry(
        db,
        id="experience-bcrypt-001",
        name="密码哈希 bcrypt",
        category="experience",
        content={
            "description": "User 密码存储",
            "solution": "使用 bcrypt cost factor 12",
            "summary": "bcrypt cost 12",
        },
        triggers=["bcrypt", "password", "hash"],
        scope="global",
    )
    return isolated_knowledge_env


@pytest.fixture
def built_project(sample_project, isolated_knowledge_env):
    from codegraph.indexer import scan_project
    from codegraph.extractor import extract_session

    scan_project(sample_project, incremental=False)
    extract_session(sample_project)
    return sample_project


def _run_cli(scripts_dir: Path, *args: str, env: dict | None = None, stdin: str | None = None):
    run_py = scripts_dir / "run.py"
    run_env = {**os.environ, "PYTHONPATH": str(scripts_dir)}
    if env:
        run_env.update(env)
    return subprocess.run(
        [sys.executable, str(run_py), *args],
        input=stdin,
        capture_output=True,
        text=True,
        cwd=str(scripts_dir),
        env=run_env,
    )


def _env_for(isolated_knowledge_env) -> dict:
    root = str(isolated_knowledge_env["global_root"])
    return {"CODEGRAPH_DIR": root, "KNOWLEDGE_BASE_PATH": root}


@pytest.mark.scenario
class TestKnowledgeQueryCLI:
    """knowledge query — stats / trigger / category / search / project scope."""

    def test_query_stats(self, seeded_kb, scripts_dir):
        r = _run_cli(
            scripts_dir, "knowledge", "query", "--stats",
            env=_env_for(seeded_kb),
        )
        assert r.returncode == 0, r.stderr
        data = json.loads(r.stdout)
        assert data["stats"]["total_entries"] >= 2

    def test_query_by_trigger_keyword(self, seeded_kb, scripts_dir):
        r = _run_cli(
            scripts_dir,
            "knowledge", "query",
            "--trigger", "cors,跨域",
            env=_env_for(seeded_kb),
        )
        assert r.returncode == 0, r.stderr
        data = json.loads(r.stdout)
        assert isinstance(data, list), data
        names = [e.get("name", "") for e in data]
        assert any("CORS" in n for n in names)

    def test_query_by_trigger_hybrid(self, seeded_kb, scripts_dir):
        r = _run_cli(
            scripts_dir,
            "knowledge", "query",
            "--trigger", "bcrypt password",
            "--mode", "hybrid",
            env=_env_for(seeded_kb),
        )
        assert r.returncode == 0, r.stderr

    def test_query_by_category(self, seeded_kb, scripts_dir):
        r = _run_cli(
            scripts_dir,
            "knowledge", "query",
            "--category", "problem",
            env=_env_for(seeded_kb),
        )
        assert r.returncode == 0, r.stderr
        data = json.loads(r.stdout)
        assert all(e.get("category") == "problem" for e in data)

    def test_query_search(self, seeded_kb, scripts_dir):
        r = _run_cli(
            scripts_dir,
            "knowledge", "query",
            "--search", "vite proxy",
            env=_env_for(seeded_kb),
        )
        assert r.returncode == 0, r.stderr

    def test_query_by_id(self, seeded_kb, scripts_dir):
        r = _run_cli(
            scripts_dir,
            "knowledge", "query",
            "--id", "problem-cors-001",
            env=_env_for(seeded_kb),
        )
        assert r.returncode == 0, r.stderr
        data = json.loads(r.stdout)
        assert data["id"] == "problem-cors-001"

    def test_query_by_tags(self, seeded_kb, scripts_dir):
        r = _run_cli(
            scripts_dir,
            "knowledge", "query",
            "--tags", "cors,vite",
            env=_env_for(seeded_kb),
        )
        assert r.returncode == 0, r.stderr

    def test_query_project_scope(self, built_project, seeded_kb, scripts_dir):
        from codegraph.db import CodeGraphDB

        proj_db = CodeGraphDB(
            built_project / ".opencode" / "codegraph" / "knowledge.db"
        )
        seed_entry(
            proj_db,
            id="proj-only-001",
            name="Project Only Entry",
            triggers=["proj-only-trigger"],
            scope="project",
            project_path=str(built_project),
        )

        r = _run_cli(
            scripts_dir,
            "knowledge", "query",
            "--trigger", "proj-only-trigger",
            "--project", str(built_project),
            env=_env_for(seeded_kb),
        )
        assert r.returncode == 0, r.stderr
        data = json.loads(r.stdout)
        assert any(e.get("name") == "Project Only Entry" for e in data)


@pytest.mark.scenario
class TestKnowledgeTriggerCLI:
    """knowledge trigger — json / context / triggers / merge / summary-only."""

    def test_trigger_json(self, seeded_kb, scripts_dir):
        r = _run_cli(
            scripts_dir,
            "knowledge", "trigger",
            "--input", "修复 CORS 跨域问题",
            "--format", "json",
            env=_env_for(seeded_kb),
        )
        assert r.returncode == 0, r.stderr
        data = json.loads(r.stdout)
        assert "knowledge" in data
        assert "triggers_used" in data

    def test_trigger_context_full_content(self, seeded_kb, scripts_dir):
        """Default context format keeps full solution text (backward compat)."""
        r = _run_cli(
            scripts_dir,
            "knowledge", "trigger",
            "--input", "CORS 跨域 vite",
            "--format", "context",
            env=_env_for(seeded_kb),
        )
        assert r.returncode == 0, r.stderr
        assert "解决方案" in r.stdout or "vite" in r.stdout.lower()

    def test_trigger_context_summary_only(self, seeded_kb, scripts_dir):
        r = _run_cli(
            scripts_dir,
            "knowledge", "trigger",
            "--input", "bcrypt password",
            "--format", "context",
            "--summary-only",
            env=_env_for(seeded_kb),
        )
        assert r.returncode == 0, r.stderr
        assert "摘要" in r.stdout or "bcrypt" in r.stdout.lower()

    def test_trigger_triggers_format(self, seeded_kb, scripts_dir):
        r = _run_cli(
            scripts_dir,
            "knowledge", "trigger",
            "--input", "CORS 跨域",
            "--format", "triggers",
            env=_env_for(seeded_kb),
        )
        assert r.returncode == 0, r.stderr
        assert "cors" in r.stdout.lower() or "跨域" in r.stdout

    def test_trigger_explicit_triggers(self, seeded_kb, scripts_dir):
        r = _run_cli(
            scripts_dir,
            "knowledge", "trigger",
            "--trigger", "bcrypt,password",
            "--format", "json",
            env=_env_for(seeded_kb),
        )
        assert r.returncode == 0, r.stderr

    def test_trigger_with_project(self, built_project, scripts_dir, isolated_knowledge_env):
        r = _run_cli(
            scripts_dir,
            "knowledge", "trigger",
            "--project", str(built_project),
            "--input", "User bcrypt password",
            "--format", "json",
            env=_env_for(isolated_knowledge_env),
        )
        assert r.returncode == 0, r.stderr
        assert "knowledge" in json.loads(r.stdout)

    def test_trigger_merge_preserves_persistent_section(
        self, seeded_kb, scripts_dir, tmp_path,
    ):
        ctx_file = tmp_path / ".knowledge-context.md"
        ctx_file.write_text(
            "## 项目经验（跨会话持久化）\n\n### 2026-03-01 手动笔记\n- 勿删此段\n",
            encoding="utf-8",
        )
        r = _run_cli(
            scripts_dir,
            "knowledge", "trigger",
            "--input", "CORS 跨域",
            "--format", "context",
            "--merge", str(ctx_file),
            env=_env_for(seeded_kb),
        )
        assert r.returncode == 0, r.stderr
        assert "项目经验（跨会话持久化）" in r.stdout
        assert "勿删此段" in r.stdout

    def test_trigger_mode_keyword(self, seeded_kb, scripts_dir):
        r = _run_cli(
            scripts_dir,
            "knowledge", "trigger",
            "--input", "CORS",
            "--mode", "keyword",
            "--format", "json",
            env=_env_for(seeded_kb),
        )
        assert r.returncode == 0, r.stderr


@pytest.mark.scenario
class TestKnowledgeStoreSummarizeCLI:
    def test_store_category_name(self, isolated_knowledge_env, scripts_dir):
        r = _run_cli(
            scripts_dir,
            "knowledge", "store",
            "--category", "experience",
            "--name", "CLI Store Test",
            "--content",
            '{"description":"Integration test store","solution":"Use bcrypt with cost factor 12 for password hashing"}',
            env=_env_for(isolated_knowledge_env),
        )
        assert r.returncode == 0, r.stderr
        data = json.loads(r.stdout)
        assert data["name"] == "CLI Store Test"

    def test_store_from_json_stdin(self, isolated_knowledge_env, scripts_dir):
        payload = json.dumps({
            "category": "problem",
            "name": "Stdin Store",
            "content": {"description": "d", "solution": "s", "symptoms": ["x"]},
            "triggers": ["stdin"],
        })
        r = _run_cli(
            scripts_dir,
            "knowledge", "store", "--from-json",
            env=_env_for(isolated_knowledge_env),
            stdin=payload,
        )
        assert r.returncode == 0, r.stderr
        assert json.loads(r.stdout)["name"] == "Stdin Store"

    def test_summarize_auto_store(self, isolated_knowledge_env, scripts_dir):
        content = "问题：CORS 跨域 blocked → 解决：配置 vite proxy\n"
        r = _run_cli(
            scripts_dir,
            "knowledge", "summarize", "--auto-store", "--format", "json",
            env=_env_for(isolated_knowledge_env),
            stdin=content,
        )
        assert r.returncode == 0, r.stderr
        assert "extracted" in json.loads(r.stdout)


@pytest.mark.scenario
class TestKnowledgeLifecycleIOCLI:
    def test_gc_dry_run(self, seeded_kb, scripts_dir):
        db = seeded_kb["global_db"]
        seed_entry(db, id="stale-001", name="Stale", effectiveness=0.05)

        r = _run_cli(
            scripts_dir,
            "knowledge", "gc", "--dry-run",
            env=_env_for(seeded_kb),
        )
        assert r.returncode == 0, r.stderr
        assert "Would remove" in r.stdout or "stale" in r.stdout.lower()

    def test_decay(self, seeded_kb, scripts_dir):
        r = _run_cli(
            scripts_dir,
            "knowledge", "decay",
            env=_env_for(seeded_kb),
        )
        assert r.returncode == 0, r.stderr

    def test_export_import(self, seeded_kb, scripts_dir, tmp_path):
        export_path = tmp_path / "export.json"
        r_export = _run_cli(
            scripts_dir,
            "knowledge", "export",
            "--output", str(export_path),
            env=_env_for(seeded_kb),
        )
        assert r_export.returncode == 0, r_export.stderr
        assert export_path.exists()

        import_path = tmp_path / "imported.json"
        import_path.write_text(export_path.read_text(encoding="utf-8"), encoding="utf-8")

        r_import = _run_cli(
            scripts_dir,
            "knowledge", "import",
            "--input", str(import_path),
            "--merge", "skip",
            env=_env_for(seeded_kb),
        )
        assert r_import.returncode == 0, r_import.stderr
        stats = json.loads(r_import.stdout)
        assert "imported" in stats or "skipped" in stats

    def test_dashboard_json(self, seeded_kb, scripts_dir):
        r = _run_cli(
            scripts_dir,
            "knowledge", "dashboard", "--json",
            env=_env_for(seeded_kb),
        )
        assert r.returncode == 0, r.stderr
        data = json.loads(r.stdout)
        assert "total_entries" in data or "entries" in str(data)


@pytest.mark.scenario
class TestKnowledgeVsCodeGraphContext:
    """knowledge trigger 与 codegraph context 并存，互不破坏。"""

    def test_knowledge_trigger_alternative_to_codegraph_context(
        self, built_project, scripts_dir, isolated_knowledge_env,
    ):
        kb = _run_cli(
            scripts_dir,
            "knowledge", "trigger",
            "--input", "UserModel authenticate",
            "--project", str(built_project),
            "--format", "context",
            env=_env_for(isolated_knowledge_env),
        )
        cg = _run_cli(
            scripts_dir,
            "codegraph", "context",
            "--project", str(built_project),
            "--input", "UserModel authenticate",
            "--format", "context",
        )
        assert kb.returncode == 0, kb.stderr
        assert cg.returncode == 0, cg.stderr
        assert len(kb.stdout) > 0
        assert "UserModel" in cg.stdout or "项目地图" in cg.stdout

    def test_codegraph_context_json_legacy_keys(self, built_project, scripts_dir):
        r = _run_cli(
            scripts_dir,
            "codegraph", "context",
            "--project", str(built_project),
            "--input", "UserModel password",
            "--format", "json",
        )
        assert r.returncode == 0, r.stderr
        data = json.loads(r.stdout)
        assert data.get("codegraph", {}).get("symbols")
        assert "knowledge" in data
        assert "text" in data  # KnowledgePlane merged text

    def test_knowledge_plane_meta_on_context(self, built_project):
        from codegraph.context import build_task_context

        build_task_context(built_project, "User auth", tier="medium", budget_tokens=800)
        meta = built_project / ".opencode" / ".knowledge-context.meta.json"
        assert meta.exists()
        assert "diagnostics" in json.loads(meta.read_text())


@pytest.mark.scenario
class TestTriggerMergeUnit:
    def test_merge_persistent_sections(self, tmp_path):
        from trigger import merge_persistent_sections, format_for_context

        path = tmp_path / "ctx.md"
        path.write_text(
            "## 项目经验（跨会话持久化）\n\n- 保留项\n",
            encoding="utf-8",
        )
        new = format_for_context({
            "knowledge": {
                "project_local": [],
                "high_relevance": [{
                    "name": "Test",
                    "category": "problem",
                    "content": {"solution": "fix"},
                }],
                "medium_relevance": [],
            }
        })
        merged = merge_persistent_sections(path, new)
        assert "保留项" in merged
        assert "Test" in merged or "fix" in merged
