"""
Pytest configuration and fixtures.
"""

import importlib
import sys
from pathlib import Path

import pytest

# Add all scripts directories to Python path
scripts_dirs = [
    Path(__file__).parent,
    Path(__file__).parent.parent / 'evolving-agent' / 'scripts',
    Path(__file__).parent.parent / 'evolving-agent' / 'scripts' / 'knowledge',
]

for scripts_dir in scripts_dirs:
    if str(scripts_dir) not in sys.path:
        sys.path.insert(0, str(scripts_dir))


def _load_kb_modules():
    """Load knowledge modules (may exist as top-level or knowledge.*)."""
    names = ("backend", "lifecycle", "query", "dashboard", "knowledge_io", "store")
    mods = []
    seen = set()
    for name in names:
        for mod_name in (name, f"knowledge.{name}"):
            try:
                mod = importlib.import_module(mod_name)
            except ImportError:
                continue
            if id(mod) not in seen:
                seen.add(id(mod))
                mods.append(mod)
    return mods


def patch_get_db(monkeypatch, get_db_fn):
    """Patch get_db on every knowledge module alias."""
    for mod in _load_kb_modules():
        if hasattr(mod, "get_db"):
            monkeypatch.setattr(mod, "get_db", get_db_fn, raising=False)


@pytest.fixture
def kb_db(tmp_path, monkeypatch):
    """Isolated CodeGraph SQLite DB for knowledge tests."""
    from codegraph.db import CodeGraphDB

    db = CodeGraphDB(tmp_path / "knowledge.db")

    def _get_db(project_path=None):
        if project_path:
            return CodeGraphDB(
                Path(project_path) / ".opencode" / "codegraph" / "knowledge.db"
            )
        return db

    patch_get_db(monkeypatch, _get_db)
    return db
