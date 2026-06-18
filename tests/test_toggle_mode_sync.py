#!/usr/bin/env python3
"""Tests for mode --init project asset sync (agents purge + local scripts)."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

SCRIPTS = Path(__file__).parent.parent / "evolving-agent" / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))


@pytest.fixture
def git_project(tmp_path):
    """Minimal git repo with .opencode layout."""
    subprocess.run(["git", "init"], cwd=tmp_path, capture_output=True, check=True)
    (tmp_path / ".opencode").mkdir()
    return tmp_path


class TestCopyScriptsProjectSync:
    def test_init_removes_deprecated_evolver_agent(self, git_project, monkeypatch):
        from core import toggle_mode as tm

        agents_dir = git_project / ".opencode" / "agents"
        agents_dir.mkdir(parents=True)
        (agents_dir / "evolver.md").write_text("# legacy evolver\n", encoding="utf-8")
        (agents_dir / "coder.md").write_text("# old coder\n", encoding="utf-8")

        monkeypatch.setattr(tm, "get_workspace_root", lambda: git_project)
        monkeypatch.setattr(tm, "_get_skill_version", lambda: "test-version-001")
        monkeypatch.setattr(tm, "_read_local_version", lambda _root: "test-version-001")

        local_scripts = git_project / ".opencode" / "scripts"
        local_scripts.mkdir(parents=True)
        (local_scripts / "run.py").write_text("# stub\n", encoding="utf-8")

        msg = tm.copy_scripts_to_project()

        assert "evolver" not in msg.lower() or "无需更新" in msg
        assert not (agents_dir / "evolver.md").exists()
        assert (agents_dir / "coder.md").exists()
        assert "coder" in (agents_dir / "coder.md").read_text(encoding="utf-8").lower()

    def test_init_writes_local_run_py_path(self, git_project, monkeypatch):
        from core import toggle_mode as tm

        monkeypatch.setattr(tm, "get_workspace_root", lambda: git_project)
        monkeypatch.setattr(tm, "_get_skill_version", lambda: "v-new")
        monkeypatch.setattr(tm, "_read_local_version", lambda _root: "")

        tm.copy_scripts_to_project()

        run_py = git_project / ".opencode" / "scripts" / "run.py"
        assert run_py.exists()
        marker = git_project / ".opencode" / ".run_py_path"
        assert marker.exists()
        assert str(run_py) in marker.read_text(encoding="utf-8")

    def test_extract_cli_uses_local_scripts_without_subagent(self, git_project, monkeypatch):
        """Knowledge extract is in-process via local run.py — no evolver agent."""
        from core import toggle_mode as tm

        monkeypatch.setattr(tm, "get_workspace_root", lambda: git_project)
        monkeypatch.setattr(tm, "_get_skill_version", lambda: "v-cli")
        monkeypatch.setattr(tm, "_read_local_version", lambda _root: "")

        tm.copy_scripts_to_project()
        run_py = git_project / ".opencode" / "scripts" / "run.py"
        assert run_py.exists()

        opencode = git_project / ".opencode"
        opencode.mkdir(exist_ok=True)
        (opencode / "progress.txt").write_text(
            "## 遇到的问题\n- Foo 报错 → 解决：运行 bar\n",
            encoding="utf-8",
        )
        (opencode / "feature_list.json").write_text(
            '{"project":"t","tasks":[{"id":"t1","name":"x","status":"completed","reviewer_notes":["note"]}]}',
            encoding="utf-8",
        )

        r = subprocess.run(
            [sys.executable, str(run_py), "codegraph", "extract", "--project", str(git_project)],
            capture_output=True,
            text=True,
            cwd=str(git_project / ".opencode" / "scripts"),
            env={**dict(**__import__("os").environ), "PYTHONPATH": str(SCRIPTS)},
        )
        assert r.returncode == 0, r.stderr
        assert "status" in r.stdout
