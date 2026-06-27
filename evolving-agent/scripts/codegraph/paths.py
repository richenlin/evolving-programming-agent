#!/usr/bin/env python3
"""CodeGraph path helpers."""

from pathlib import Path


def get_codegraph_dir(project_root: str | Path) -> Path:
    """Return $PROJECT_ROOT/.opencode/codegraph/ (created if missing)."""
    root = Path(project_root).resolve()
    cg_dir = root / ".opencode" / "codegraph"
    cg_dir.mkdir(parents=True, exist_ok=True)
    return cg_dir


def get_graph_path(project_root: str | Path) -> Path:
    return get_codegraph_dir(project_root) / "graph.json"


def get_index_state_path(project_root: str | Path) -> Path:
    return get_codegraph_dir(project_root) / "index-state.json"


def get_vectors_path(project_root: str | Path) -> Path:
    return get_codegraph_dir(project_root) / "vectors" / "index.json"


def get_knowledge_db_path(project_root: str | Path) -> Path:
    """Project knowledge.db — SQLite FTS5 + entries."""
    return get_codegraph_dir(project_root) / "knowledge.db"


def get_global_knowledge_db_path() -> Path:
    """Global CodeGraph knowledge.db (shared across platforms)."""
    try:
        from core.path_resolver import get_knowledge_base_dir
        return get_knowledge_base_dir() / "knowledge.db"
    except ImportError:
        p = Path.home() / ".local" / "share" / "evolving-agent" / "codegraph"
        p.mkdir(parents=True, exist_ok=True)
        return p / "knowledge.db"


def get_opencode_dir(project_root: str | Path) -> Path:
    return Path(project_root).resolve() / ".opencode"
