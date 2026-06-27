"""Tests for multi-platform shared path resolution."""

from pathlib import Path

import pytest


@pytest.fixture
def isolated_home(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.delenv("EVOLVING_AGENT_HOME", raising=False)
    monkeypatch.delenv("XDG_DATA_HOME", raising=False)
    monkeypatch.delenv("CODEGRAPH_DIR", raising=False)
    monkeypatch.delenv("KNOWLEDGE_BASE_PATH", raising=False)
    monkeypatch.delenv("VENV_PYTHON", raising=False)
    return tmp_path


def test_get_agent_home_default(isolated_home):
    from core.path_resolver import get_agent_home

    assert get_agent_home() == isolated_home / ".local" / "share" / "evolving-agent"


def test_get_agent_home_xdg(isolated_home, monkeypatch):
    from core.path_resolver import get_agent_home

    monkeypatch.setenv("XDG_DATA_HOME", str(isolated_home / "xdg"))
    assert get_agent_home() == isolated_home / "xdg" / "evolving-agent"


def test_get_agent_home_override(isolated_home, monkeypatch):
    from core.path_resolver import get_agent_home

    custom = isolated_home / "custom-agent"
    monkeypatch.setenv("EVOLVING_AGENT_HOME", str(custom))
    assert get_agent_home() == custom


def test_get_shared_venv_python(isolated_home, monkeypatch):
    from core.path_resolver import get_shared_venv_python

    monkeypatch.setenv("EVOLVING_AGENT_HOME", str(isolated_home / "agent"))
    expected = isolated_home / "agent" / "runtime" / ".venv" / "bin" / "python"
    assert get_shared_venv_python() == expected


def test_get_knowledge_base_dir_under_agent_home(isolated_home):
    from core.path_resolver import get_agent_home, get_knowledge_base_dir

    kb = get_knowledge_base_dir()
    assert kb == get_agent_home() / "codegraph"
    assert kb.is_dir()


def test_get_knowledge_base_dir_env_override(isolated_home, monkeypatch):
    from core.path_resolver import get_knowledge_base_dir

    custom = isolated_home / "my-kb"
    monkeypatch.setenv("CODEGRAPH_DIR", str(custom))
    assert get_knowledge_base_dir() == custom


def test_get_global_knowledge_db_path(isolated_home):
    from codegraph.paths import get_global_knowledge_db_path
    from core.path_resolver import get_knowledge_base_dir

    assert get_global_knowledge_db_path() == get_knowledge_base_dir() / "knowledge.db"
