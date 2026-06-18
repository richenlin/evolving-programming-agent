#!/usr/bin/env python3
"""Knowledge storage backend — CodeGraph SQLite only."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from codegraph.db import CodeGraphDB, get_project_db


def _global_db_path() -> Path:
    try:
        from core.path_resolver import get_knowledge_base_dir
        return get_knowledge_base_dir() / "knowledge.db"
    except ImportError:
        from codegraph.paths import get_global_knowledge_db_path
        return get_global_knowledge_db_path()


def get_db(project_path: Optional[str | Path] = None) -> CodeGraphDB:
    """Global DB when project_path is None, else project-scoped DB."""
    if project_path:
        return get_project_db(project_path)
    return CodeGraphDB(_global_db_path())


def infer_codegraph_type(entry: dict) -> str:
    tags = entry.get("tags") or []
    for tag in tags:
        if tag in ("pattern", "bug-fix", "convention", "solution", "api-usage"):
            return tag
    category = entry.get("category", "")
    if category == "problem":
        return "bug-fix"
    if category == "pattern":
        return "pattern"
    if category in ("tech-stack", "skill"):
        return "convention"
    return "solution"
