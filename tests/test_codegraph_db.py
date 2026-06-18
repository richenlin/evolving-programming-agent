"""Tests for SQLite FTS5 and tree-sitter AST layer."""

import json
import sys
from pathlib import Path

import pytest

SCRIPTS = Path(__file__).parent.parent / "evolving-agent" / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))


@pytest.fixture
def sample_project(tmp_path):
    """Minimal Python project for CodeGraph scan."""
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "user.py").write_text(
        "class UserModel:\n    pass\n\ndef get_user():\n    return UserModel()\n",
        encoding="utf-8",
    )
    (tmp_path / "src" / "auth.py").write_text(
        "from user import get_user\n\ndef authenticate():\n    return get_user()\n",
        encoding="utf-8",
    )
    opencode = tmp_path / ".opencode"
    opencode.mkdir()
    (opencode / "progress.txt").write_text("## 关键决策\n- bcrypt → 原因：成熟\n", encoding="utf-8")
    (opencode / "feature_list.json").write_text(
        json.dumps({
            "project": "test",
            "tasks": [{"id": "t1", "name": "User", "status": "completed", "reviewer_notes": []}],
        }),
        encoding="utf-8",
    )
    return tmp_path


def test_ast_parser_python():
    from codegraph.ast_parser import parse_file

    code = (
        "import os\n\n"
        "class UserModel:\n    pass\n\n"
        "def get_user():\n    return UserModel()\n"
    )
    result = parse_file(code, "python", "src/user.py", ".py")
    names = {s["name"] for s in result["symbols"]}
    assert "UserModel" in names
    assert "get_user" in names
    assert result["parser"] in ("tree-sitter", "regex")
    if result["parser"] == "tree-sitter":
        assert any(s.get("end_line", 0) >= s["line"] for s in result["symbols"])


def test_db_symbols_fts(tmp_path):
    from codegraph.db import CodeGraphDB

    db_path = tmp_path / "test.db"
    db = CodeGraphDB(db_path)
    symbols = [
        {"id": "sym:a.py:UserModel:1", "file": "a.py", "name": "UserModel", "kind": "class", "line": 1},
        {"id": "sym:b.py:authenticate:5", "file": "b.py", "name": "authenticate", "kind": "function", "line": 5},
    ]
    db.replace_symbols(symbols)
    hits = db.search_symbols("UserModel", limit=5)
    assert len(hits) >= 1
    assert hits[0]["name"] == "UserModel"


def test_db_entries_fts(tmp_path):
    from codegraph.db import CodeGraphDB

    db = CodeGraphDB(tmp_path / "knowledge.db")
    db.upsert_entry({
        "id": "exp-test-1",
        "category": "experience",
        "name": "CORS 跨域修复",
        "content": {"description": "跨域问题", "solution": "配置 vite proxy"},
        "scope": "project",
        "codegraph_type": "bug-fix",
        "tags": ["cors", "vite"],
        "sources": ["test"],
    })
    hits = db.search_entries("CORS proxy", limit=3)
    assert len(hits) >= 1
    assert hits[0]["entry_id"] == "exp-test-1"


def test_scan_creates_sqlite_db(sample_project):
    from codegraph.indexer import scan_project
    from codegraph.paths import get_knowledge_db_path

    result = scan_project(sample_project, incremental=False)
    db_path = get_knowledge_db_path(sample_project)
    assert db_path.exists()
    assert result.get("db_stats", {}).get("symbols", 0) >= 2
    assert "index_backend" in result


def test_query_uses_fts5(sample_project):
    from codegraph.indexer import scan_project
    from codegraph.db import get_project_db
    from codegraph.query import query_context

    scan_project(sample_project, incremental=False)
    db = get_project_db(sample_project)
    db.upsert_entry({
        "id": "exp-fts-1",
        "category": "experience",
        "name": "User password bcrypt",
        "content": {"solution": "use bcrypt for password hashing"},
        "scope": "project",
        "codegraph_type": "solution",
        "tags": ["bcrypt"],
        "sources": ["test"],
    })

    result = query_context(sample_project, "UserModel get_user")
    assert result.get("symbol_source") in ("fts5", "graph")
    assert any(s["name"] == "UserModel" for s in result["symbols"])

    result2 = query_context(sample_project, "bcrypt password")
    assert len(result2.get("experience", [])) >= 1
