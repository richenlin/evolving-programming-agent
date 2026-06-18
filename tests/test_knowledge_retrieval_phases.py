#!/usr/bin/env python3
"""
Two-phase dynamic knowledge retrieval scenarios.

1. Design phase  — orchestrator queries with user goal → .design-context.md
2. Coder phase   — per-batch task query → .knowledge-context.md
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

# Same queries as evolving-agent/SKILL.md examples
USER_GOAL = "实现 User 密码哈希，架构选型 bcrypt 与 argon2"
TASK_DESC = "UserModel 添加 password 字段，authenticate 调用链"


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
def built_project(sample_project, isolated_knowledge_env):
    from codegraph.indexer import scan_project
    from codegraph.extractor import extract_session

    scan_project(sample_project, incremental=False)
    result = extract_session(sample_project)
    assert result["status"] == "ok", result
    return sample_project


@pytest.fixture
def scripts_dir():
    return Path(__file__).parent.parent / "evolving-agent" / "scripts"


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


def _write_context(project: Path, filename: str, query: str) -> str:
    from codegraph.context import build_task_context

    content = build_task_context(project, query)
    path = project / ".opencode" / filename
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return content


@pytest.mark.scenario
class TestDesignPhaseRetrieval:
    """Scenario 1: orchestrator design / task breakdown (macro user goal)."""

    def test_design_query_surfaces_architecture_experience(self, built_project):
        from codegraph.context import build_task_context, build_task_context_json

        ctx = build_task_context(built_project, USER_GOAL)
        assert len(ctx) > 50
        lower = ctx.lower()
        assert "bcrypt" in lower or "argon2" in lower or "prisma" in lower

        data = build_task_context_json(built_project, USER_GOAL)
        assert data["query"] == USER_GOAL
        assert "codegraph" in data or "knowledge" in data

    def test_design_query_filters_review_noise(self, built_project, isolated_knowledge_env):
        from codegraph.db import CodeGraphDB
        from codegraph.context import build_task_context

        proj_db = CodeGraphDB(
            built_project / ".opencode" / "codegraph" / "knowledge.db"
        )
        seed_entry(
            proj_db,
            id="design-noise-001",
            name="review发现",
            category="problem",
            content={
                "description": "review发现",
                "solution": "缺少 password 字段校验",
                "symptoms": ["review发现"],
            },
            triggers=["password", "bcrypt"],
            scope="project",
            project_path=str(built_project),
        )

        ctx = build_task_context(built_project, USER_GOAL)
        assert "review发现" not in ctx

    def test_design_context_file_for_orchestrator(self, built_project):
        content = _write_context(built_project, ".design-context.md", USER_GOAL)
        design_path = built_project / ".opencode" / ".design-context.md"

        assert design_path.exists()
        assert design_path.read_text(encoding="utf-8") == content
        assert len(content) > 50

    def test_cli_codegraph_context_for_design_phase(self, built_project, scripts_dir):
        r = _run_cli(
            scripts_dir,
            "codegraph", "context",
            "--project", str(built_project),
            "--input", USER_GOAL,
            "--format", "context",
        )
        assert r.returncode == 0, r.stderr
        out = r.stdout.lower()
        assert len(r.stdout) > 50
        assert "bcrypt" in out or "argon2" in out or "prisma" in out or "user" in out


@pytest.mark.scenario
class TestCoderPhaseRetrieval:
    """Scenario 2: @coder dispatch — per-task context supplement."""

    def test_task_query_surfaces_code_symbols(self, built_project):
        from codegraph.context import build_task_context, build_task_context_json

        ctx = build_task_context(built_project, TASK_DESC)
        assert len(ctx) > 50
        assert "UserModel" in ctx or "authenticate" in ctx or "get_user" in ctx

        data = build_task_context_json(built_project, TASK_DESC)
        assert data["query"] == TASK_DESC
        symbols = data.get("codegraph", {}).get("symbols", [])
        symbol_names = {s.get("name") for s in symbols}
        assert "UserModel" in symbol_names or "authenticate" in symbol_names

    def test_knowledge_context_file_for_coder(self, built_project):
        content = _write_context(built_project, ".knowledge-context.md", TASK_DESC)
        ctx_path = built_project / ".opencode" / ".knowledge-context.md"

        assert ctx_path.exists()
        assert ctx_path.read_text(encoding="utf-8") == content
        assert "UserModel" in content or "authenticate" in content

    def test_cli_codegraph_context_for_coder_dispatch(self, built_project, scripts_dir):
        r = _run_cli(
            scripts_dir,
            "codegraph", "context",
            "--project", str(built_project),
            "--input", TASK_DESC,
            "--format", "context",
        )
        assert r.returncode == 0, r.stderr
        assert "UserModel" in r.stdout or "authenticate" in r.stdout

    def test_coder_context_json_mode(self, built_project, scripts_dir):
        r = _run_cli(
            scripts_dir,
            "codegraph", "context",
            "--project", str(built_project),
            "--input", TASK_DESC,
            "--format", "json",
        )
        assert r.returncode == 0, r.stderr
        data = json.loads(r.stdout)
        assert data.get("query") == TASK_DESC
        assert data.get("codegraph", {}).get("symbols")


@pytest.mark.scenario
class TestTwoPhaseDynamicRetrieval:
    """Design vs coder: same API, different query → different context files."""

    def test_design_and_coder_contexts_differ(self, built_project):
        design = _write_context(built_project, ".design-context.md", USER_GOAL)
        coder = _write_context(built_project, ".knowledge-context.md", TASK_DESC)

        assert design != coder
        assert built_project / ".opencode" / ".design-context.md"
        assert built_project / ".opencode" / ".knowledge-context.md"

    def test_orchestrator_workflow_design_then_coder_batch(self, built_project, scripts_dir):
        """Simulate SKILL.md 3.1a → 3.1 → 3.2: two files, two queries."""
        opencode = built_project / ".opencode"
        opencode.mkdir(parents=True, exist_ok=True)

        design_cli = _run_cli(
            scripts_dir,
            "codegraph", "context",
            "--project", str(built_project),
            "--input", USER_GOAL,
            "--format", "context",
        )
        assert design_cli.returncode == 0, design_cli.stderr
        design_file = opencode / ".design-context.md"
        design_file.write_text(design_cli.stdout, encoding="utf-8")

        task_cli = _run_cli(
            scripts_dir,
            "codegraph", "context",
            "--project", str(built_project),
            "--input", TASK_DESC,
            "--format", "context",
        )
        assert task_cli.returncode == 0, task_cli.stderr
        knowledge_file = opencode / ".knowledge-context.md"
        knowledge_file.write_text(task_cli.stdout, encoding="utf-8")

        design_text = design_file.read_text(encoding="utf-8")
        knowledge_text = knowledge_file.read_text(encoding="utf-8")

        assert len(design_text) > 50
        assert len(knowledge_text) > 50
        assert design_text != knowledge_text
        # Design: macro experience; Coder: concrete symbols
        assert (
            "bcrypt" in design_text.lower()
            or "prisma" in design_text.lower()
            or "argon2" in design_text.lower()
        )
        assert "UserModel" in knowledge_text or "authenticate" in knowledge_text

    def test_per_batch_refresh_changes_coder_context(self, built_project):
        """Each pending batch uses its own TASK_DESC (3.2 per-batch refresh)."""
        from codegraph.context import build_task_context

        task_a = "UserModel password bcrypt hash 字段"
        task_b = "authenticate get_user 调用链"

        ctx_a = _write_context(built_project, ".knowledge-context.md", task_a)
        ctx_b = build_task_context(built_project, task_b)

        assert ctx_a != ctx_b
