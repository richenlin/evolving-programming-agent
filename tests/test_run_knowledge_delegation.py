#!/usr/bin/env python3
"""Tests for run.py knowledge delegation path (PYTHONPATH + in-process summarize)."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

SCRIPTS = Path(__file__).parent.parent / "evolving-agent" / "scripts"
RUN_PY = SCRIPTS / "run.py"


@pytest.fixture
def isolated_kb(tmp_path, monkeypatch):
    from codegraph.db import CodeGraphDB
    from conftest import patch_get_db

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
    return global_root


class TestRunScriptEnv:
    def test_subprocess_env_includes_scripts_dir(self):
        sys.path.insert(0, str(SCRIPTS))
        import run as run_mod

        env = run_mod._subprocess_env()
        scripts = str(SCRIPTS)
        assert scripts in env.get("PYTHONPATH", "")


class TestSummarizeInProcess:
    def test_summarize_auto_store_without_pythonpath_prefix(self, isolated_kb, tmp_path):
        """Mimics opencode glob: command must start with python, no env prefix."""
        content = (
            "问题：CORS 跨域 blocked by browser → "
            "解决：开发环境配置 vite proxy 转发 /api\n"
        )
        env = {
            **os.environ,
            "CODEGRAPH_DIR": str(isolated_kb),
            "KNOWLEDGE_BASE_PATH": str(isolated_kb),
        }
        # Do NOT set PYTHONPATH — run.py in-process handler must still work
        env.pop("PYTHONPATH", None)

        r = subprocess.run(
            [sys.executable, str(RUN_PY), "knowledge", "summarize", "--auto-store", "--format", "json"],
            input=content,
            capture_output=True,
            text=True,
            cwd=str(SCRIPTS),
            env=env,
        )
        assert r.returncode == 0, r.stderr
        data = json.loads(r.stdout)
        assert "extracted" in data

    def test_knowledge_query_subprocess_has_codegraph_on_path(self, isolated_kb):
        """Delegated query subprocess gets scripts/ via _subprocess_env()."""
        env = {
            **os.environ,
            "CODEGRAPH_DIR": str(isolated_kb),
            "KNOWLEDGE_BASE_PATH": str(isolated_kb),
        }
        env.pop("PYTHONPATH", None)
        r = subprocess.run(
            [
                sys.executable, str(RUN_PY), "knowledge", "query",
                "--trigger", "cors", "--format", "json",
            ],
            capture_output=True,
            text=True,
            cwd=str(SCRIPTS),
            env=env,
        )
        assert r.returncode == 0, r.stderr
