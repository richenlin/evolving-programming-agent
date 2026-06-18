#!/usr/bin/env python3
"""
Full-scenario tests: graph generation → knowledge build → retrieval.

Covers CodeGraph scan/extract and knowledge trigger/query/export paths.
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
    """Route global + project knowledge DBs under tmp_path (no ~/.config pollution)."""
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
def built_project(sample_project, isolated_knowledge_env):
    """Scan + extract a sample project with isolated KB roots."""
    from codegraph.indexer import scan_project
    from codegraph.extractor import extract_session

    scan_project(sample_project, incremental=False)
    result = extract_session(sample_project)
    assert result["status"] == "ok", result
    return sample_project


def _all_entry_names(project: Path, global_db) -> set[str]:
    from codegraph.db import CodeGraphDB

    names: set[str] = set()
    proj_db = CodeGraphDB(project / ".opencode" / "codegraph" / "knowledge.db")
    for row in proj_db.list_entries(limit=500):
        names.add(row["name"])
    for row in global_db.list_entries(limit=500):
        names.add(row["name"])
    return names


def _run_cli(scripts_dir: Path, *args: str, env: dict | None = None) -> subprocess.CompletedProcess:
    run_py = scripts_dir / "run.py"
    run_env = {**os.environ, "PYTHONPATH": str(scripts_dir)}
    if env:
        run_env.update(env)
    return subprocess.run(
        [sys.executable, str(run_py), *args],
        capture_output=True,
        text=True,
        cwd=str(scripts_dir),
        env=run_env,
    )


@pytest.mark.scenario
class TestGraphGenerationScenarios:
    def test_scan_creates_graph_and_symbol_fts(self, sample_project):
        from codegraph.indexer import scan_project
        from codegraph.db import CodeGraphDB

        result = scan_project(sample_project, incremental=False)
        assert result["status"] == "ok"
        assert result["stats"]["file_count"] >= 2
        assert result["stats"]["symbol_count"] >= 2

        graph_path = sample_project / ".opencode" / "codegraph" / "graph.json"
        assert graph_path.exists()
        graph = json.loads(graph_path.read_text(encoding="utf-8"))
        symbol_names = {s["name"] for s in graph["symbols"]}
        assert "UserModel" in symbol_names
        assert "authenticate" in symbol_names

        db = CodeGraphDB(result["db_path"])
        fts_hits = db.search_symbols("UserModel", limit=5)
        assert any(h["name"] == "UserModel" for h in fts_hits)

    def test_incremental_scan_skips_unchanged_files(self, sample_project):
        from codegraph.indexer import scan_project

        scan_project(sample_project, incremental=False)
        second = scan_project(sample_project, incremental=True)
        assert second["stats"]["skipped_unchanged"] >= 2

    def test_cli_codegraph_scan(self, sample_project, scripts_dir):
        r = _run_cli(
            scripts_dir,
            "codegraph", "scan", "--project", str(sample_project), "--json",
        )
        assert r.returncode == 0, r.stderr
        data = json.loads(r.stdout)
        assert data["status"] == "ok"
        assert data["stats"]["symbol_count"] >= 2


@pytest.mark.scenario
class TestKnowledgeBuildScenarios:
    def test_extract_stores_decisions_and_problems_not_review_noise(
        self, built_project, isolated_knowledge_env,
    ):
        global_db = isolated_knowledge_env["global_db"]
        names = _all_entry_names(built_project, global_db)

        assert any("bcrypt" in n.lower() or "argon2" in n.lower() for n in names)
        assert any("prisma" in n.lower() for n in names)
        assert not any(n == "review发现" for n in names)

        vec_path = (
            built_project / ".opencode" / "codegraph" / "vectors" / "index.json"
        )
        assert vec_path.exists()

    def test_store_rejects_low_value_entries(self, kb_db):
        from store import store_knowledge

        with pytest.raises(ValueError, match="Low-value"):
            store_knowledge(
                category="problem",
                name="review发现",
                content={
                    "description": "review发现",
                    "solution": "缺少 password 字段校验",
                    "symptoms": ["review发现"],
                },
                _db=kb_db,
            )

    def test_store_dedupes_same_content_fingerprint(self, kb_db):
        from store import store_knowledge

        content = {
            "description": "Prisma 初始化报错",
            "solution": "先运行 npx prisma generate",
            "symptoms": ["Prisma 初始化报错"],
        }
        first = store_knowledge(
            category="problem",
            name="Prisma 初始化报错",
            content=content,
            _db=kb_db,
        )
        second = store_knowledge(
            category="problem",
            name="Prisma 初始化报错",
            content=content,
            _db=kb_db,
        )
        assert first["id"] == second["id"]
        assert kb_db.stats()["entries"] == 1

    def test_project_vs_global_scope_routing(self, built_project, isolated_knowledge_env):
        from codegraph.db import CodeGraphDB

        global_db = isolated_knowledge_env["global_db"]
        proj_db = CodeGraphDB(
            built_project / ".opencode" / "codegraph" / "knowledge.db"
        )

        assert proj_db.stats()["entries"] >= 1
        assert global_db.stats()["entries"] >= 1

        proj_names = {r["name"] for r in proj_db.list_entries(limit=100)}
        global_names = {r["name"] for r in global_db.list_entries(limit=100)}
        assert any("bcrypt" in n.lower() for n in proj_names)
        assert any("prisma" in n.lower() for n in global_names)

    def test_extract_skips_pass_only_session(self, tmp_path, isolated_knowledge_env):
        from codegraph.extractor import extract_session

        opencode = tmp_path / ".opencode"
        opencode.mkdir()
        (opencode / "progress.txt").write_text("## 本次完成\n- [x] fix typo\n")
        (opencode / "feature_list.json").write_text(
            json.dumps({
                "project": "pass-only",
                "tasks": [{"id": "t1", "name": "fix typo", "status": "completed"}],
            }),
            encoding="utf-8",
        )

        result = extract_session(tmp_path)
        assert result["status"] == "skipped"
        assert "pass-only" in result.get("reason", "")

    def test_cli_codegraph_extract_and_evolve(self, sample_project, scripts_dir, isolated_knowledge_env):
        scan = _run_cli(
            scripts_dir,
            "codegraph", "scan", "--project", str(sample_project),
        )
        assert scan.returncode == 0, scan.stderr

        extract = _run_cli(
            scripts_dir,
            "codegraph", "extract", "--project", str(sample_project),
        )
        assert extract.returncode == 0, extract.stderr
        data = json.loads(extract.stdout)
        assert data["status"] == "ok"
        assert data["extracted"] >= 1

        evolve = _run_cli(
            scripts_dir,
            "evolve", "--project", str(sample_project), "--force",
        )
        assert evolve.returncode == 0, evolve.stderr
        assert "status" in json.loads(evolve.stdout)


@pytest.mark.scenario
class TestKnowledgeRetrievalScenarios:
    def test_query_context_after_build(self, built_project):
        from codegraph.query import query_context, format_context

        result = query_context(built_project, "User password bcrypt authentication")
        assert any(s["name"] == "UserModel" for s in result["symbols"])

        exp_names = [e.get("name", "") for e in result.get("experience", [])]
        if exp_names:
            assert not any(n == "review发现" for n in exp_names)

        md = format_context(result)
        assert "UserModel" in md or "bcrypt" in md.lower()

    def test_trigger_finds_project_knowledge_and_filters_noise(
        self, built_project, isolated_knowledge_env,
    ):
        from codegraph.db import CodeGraphDB
        from trigger import trigger_knowledge

        proj_db = CodeGraphDB(
            built_project / ".opencode" / "codegraph" / "knowledge.db"
        )
        seed_entry(
            proj_db,
            id="noise-review-001",
            name="review发现",
            category="problem",
            content={
                "description": "review发现",
                "solution": "缺少 password 字段校验",
                "symptoms": ["review发现"],
            },
            triggers=["password", "review"],
            scope="project",
            project_path=str(built_project),
        )

        result = trigger_knowledge(
            user_input="User password bcrypt hash",
            project_dir=str(built_project),
            mode="hybrid",
            limit=10,
        )

        all_items = (
            result["knowledge"]["project_local"]
            + result["knowledge"]["high_relevance"]
            + result["knowledge"]["medium_relevance"]
        )
        names = [e.get("name", "") for e in all_items]
        assert not any(n == "review发现" for n in names)
        assert any("bcrypt" in n.lower() for n in names) or len(all_items) >= 1

    def test_hybrid_search_modes(self, built_project, isolated_knowledge_env):
        from query import query_hybrid, query_by_triggers

        keyword_hits = query_by_triggers(
            ["bcrypt", "prisma"],
            project_path=str(built_project),
        )
        assert isinstance(keyword_hits, list)

        hybrid_hits = query_hybrid("bcrypt password", project_path=str(built_project))
        assert isinstance(hybrid_hits, list)

    def test_build_task_context_includes_graph_and_knowledge(self, built_project):
        from codegraph.context import build_task_context

        ctx = build_task_context(built_project, "authenticate UserModel bcrypt")
        assert isinstance(ctx, str)
        assert len(ctx) > 50

    def test_export_import_roundtrip_on_project_db(self, built_project, tmp_path):
        from codegraph.db import CodeGraphDB
        from knowledge_io import export_all, import_all

        proj_db = CodeGraphDB(
            built_project / ".opencode" / "codegraph" / "knowledge.db"
        )
        assert proj_db.stats()["entries"] >= 1

        export_file = tmp_path / "project_export.json"
        count = export_all(
            str(export_file), format="json", project_path=str(built_project),
        )
        assert count >= 1

        import_proj = tmp_path / "import_proj"
        import_proj.mkdir()
        stats = import_all(
            str(export_file),
            merge_strategy="skip",
            project_path=str(import_proj),
        )
        assert stats["imported"] >= 1
        import_db = CodeGraphDB(
            import_proj / ".opencode" / "codegraph" / "knowledge.db"
        )
        assert import_db.stats()["entries"] >= 1

    def test_global_project_isolation_in_retrieval(
        self, built_project, isolated_knowledge_env,
    ):
        from query import query_by_triggers

        global_db = isolated_knowledge_env["global_db"]
        seed_entry(
            global_db,
            id="global-only-001",
            name="Global React Pattern",
            triggers=["react-global-only"],
            scope="global",
        )

        global_hits = query_by_triggers(["react-global-only"])
        assert any(h["name"] == "Global React Pattern" for h in global_hits)

        proj_hits = query_by_triggers(
            ["react-global-only"],
            project_path=str(built_project),
        )
        proj_names = [h.get("name") for h in proj_hits]
        assert "Global React Pattern" not in proj_names

    def test_cli_knowledge_trigger_and_query(self, built_project, scripts_dir, isolated_knowledge_env):
        trigger = _run_cli(
            scripts_dir,
            "knowledge", "trigger",
            "--project", str(built_project),
            "--input", "User bcrypt password",
            "--format", "json",
        )
        assert trigger.returncode == 0, trigger.stderr
        trig_data = json.loads(trigger.stdout)
        assert "knowledge" in trig_data

        global_root = str(isolated_knowledge_env["global_root"])
        query = _run_cli(
            scripts_dir,
            "knowledge", "query",
            "--trigger", "bcrypt,prisma",
            "--format", "json",
            env={"CODEGRAPH_DIR": global_root, "KNOWLEDGE_BASE_PATH": global_root},
        )
        assert query.returncode == 0, query.stderr

    def test_cli_codegraph_context_query(self, built_project, scripts_dir):
        ctx = _run_cli(
            scripts_dir,
            "codegraph", "query",
            "--project", str(built_project),
            "--input", "UserModel bcrypt",
            "--format", "context",
        )
        assert ctx.returncode == 0, ctx.stderr
        assert "UserModel" in ctx.stdout or "bcrypt" in ctx.stdout.lower()


@pytest.mark.scenario
class TestFullPipelineE2E:
    def test_scan_extract_retrieve_end_to_end(
        self, sample_project, isolated_knowledge_env, scripts_dir,
    ):
        from codegraph.indexer import scan_project
        from codegraph.extractor import extract_session
        from codegraph.query import query_context
        from trigger import trigger_knowledge

        scan = scan_project(sample_project, incremental=False)
        assert scan["status"] == "ok"

        extract = extract_session(sample_project)
        assert extract["status"] == "ok"
        assert extract["extracted"] >= 1

        ctx = query_context(sample_project, "User password bcrypt prisma")
        assert any(s["name"] == "UserModel" for s in ctx["symbols"])

        trig = trigger_knowledge(
            user_input="bcrypt password User model",
            project_dir=str(sample_project),
            mode="hybrid",
        )
        combined = (
            trig["knowledge"]["project_local"]
            + trig["knowledge"]["high_relevance"]
            + trig["knowledge"]["medium_relevance"]
        )
        assert not any(e.get("name") == "review发现" for e in combined)

        cli = _run_cli(
            scripts_dir,
            "codegraph", "query",
            "--project", str(sample_project),
            "--input", "get_user authenticate",
            "--format", "json",
        )
        assert cli.returncode == 0
        cli_data = json.loads(cli.stdout)
        assert cli_data.get("symbols")
