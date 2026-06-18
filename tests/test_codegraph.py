"""Tests for CodeGraph scan, query, extract, embedder."""

import json
import subprocess
import sys
from pathlib import Path

import pytest

SCRIPTS = Path(__file__).parent.parent / "evolving-agent" / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))


def test_scan_project(sample_project):
    from codegraph.indexer import scan_project

    result = scan_project(sample_project, incremental=False)
    assert result["status"] == "ok"
    assert result["stats"]["file_count"] >= 2
    assert result["stats"]["symbol_count"] >= 2

    graph_path = sample_project / ".opencode" / "codegraph" / "graph.json"
    assert graph_path.exists()
    graph = json.loads(graph_path.read_text())
    names = {s["name"] for s in graph["symbols"]}
    assert "UserModel" in names
    assert "get_user" in names


def test_scan_incremental_skips_unchanged(sample_project):
    from codegraph.indexer import scan_project

    scan_project(sample_project, incremental=False)
    result2 = scan_project(sample_project, incremental=True)
    assert result2["stats"]["skipped_unchanged"] >= 2


def test_embedder_hash_fallback():
    from codegraph.embedder import embed_text, cosine_similarity, search_vectors, persist_vectors

    v1, backend, _ = embed_text("User model authentication")
    v2, _, _ = embed_text("User model authentication")
    v3, _, _ = embed_text("completely unrelated quantum physics")

    assert backend == "hash"
    assert len(v1) == len(v2)
    assert cosine_similarity(v1, v2) > 0.99
    assert cosine_similarity(v1, v3) < cosine_similarity(v1, v2)


def test_vector_search(sample_project):
    from codegraph.embedder import persist_vectors, search_vectors

    persist_vectors(sample_project, [
        {"entry_id": "exp-1", "text": "User model bcrypt password hashing", "type": "solution"},
        {"entry_id": "exp-2", "text": "Docker deployment kubernetes", "type": "pattern"},
    ])
    hits = search_vectors(sample_project, "User password hash", top_k=3, threshold=0.2)
    assert len(hits) >= 1
    assert hits[0]["entry_id"] == "exp-1"


def test_query_context(sample_project):
    from codegraph.indexer import scan_project
    from codegraph.query import query_context, format_context

    scan_project(sample_project, incremental=False)
    result = query_context(sample_project, "User model get_user")
    assert any(s["name"] == "UserModel" for s in result["symbols"])

    md = format_context(result)
    assert "UserModel" in md or "CodeGraph" in md


def test_extract_session(sample_project):
    from codegraph.extractor import extract_session

    result = extract_session(sample_project)
    assert result["status"] == "ok"
    assert result["extracted"] >= 1
    assert "global" in result
    assert "project" in result

    kb = sample_project / ".opencode" / "codegraph" / "knowledge.db"
    assert kb.exists()

    from codegraph.db import CodeGraphDB
    db = CodeGraphDB(kb)
    assert db.stats()["entries"] >= 1

    vec_path = sample_project / ".opencode" / "codegraph" / "vectors" / "index.json"
    assert vec_path.exists()


def test_classify_scope():
    from codegraph.extractor import classify_scope

    decision = {
        "name": "决策: 选择 bcrypt",
        "content": {"description": "架构选型", "conventions": ["bcrypt"]},
        "codegraph_type": "convention",
    }
    assert classify_scope(decision, {}) == "project"

    bugfix = {
        "name": "CORS 跨域报错",
        "content": {"description": "CORS error", "solution": "配置 proxy"},
        "codegraph_type": "bug-fix",
    }
    assert classify_scope(bugfix, {}) == "global"


def test_extract_skips_pass_only(tmp_path):
    from codegraph.extractor import extract_session

    opencode = tmp_path / ".opencode"
    opencode.mkdir()
    (opencode / "feature_list.json").write_text(json.dumps({
        "project": "t",
        "tasks": [{"id": "t1", "name": "fix typo", "status": "completed", "reviewer_notes": []}],
    }))
    (opencode / "progress.txt").write_text("## 本次完成\n- [x] fix typo\n")

    result = extract_session(tmp_path)
    assert result["status"] == "skipped"

    result_force = extract_session(tmp_path, force=True)
    assert result_force["status"] in ("ok", "skipped")  # may have no candidates


def test_evolve_cli_alias(sample_project):
    run_py = SCRIPTS / "run.py"
    r = subprocess.run(
        [sys.executable, str(run_py), "evolve", "--project", str(sample_project), "--force"],
        capture_output=True, text=True, cwd=str(SCRIPTS),
    )
    assert r.returncode == 0
    data = json.loads(r.stdout)
    assert "status" in data


def test_build_task_context(sample_project):
    from codegraph.indexer import scan_project
    from codegraph.context import build_task_context

    scan_project(sample_project, incremental=False)
    ctx = build_task_context(sample_project, "User model authentication")
    assert isinstance(ctx, str)


def test_cli_scan_and_extract(sample_project):
    run_py = SCRIPTS / "run.py"
    r = subprocess.run(
        [sys.executable, str(run_py), "codegraph", "scan", "--project", str(sample_project)],
        capture_output=True, text=True, cwd=str(SCRIPTS),
    )
    assert r.returncode == 0

    r2 = subprocess.run(
        [sys.executable, str(run_py), "codegraph", "extract", "--project", str(sample_project)],
        capture_output=True, text=True, cwd=str(SCRIPTS),
    )
    assert r2.returncode == 0
    data = json.loads(r2.stdout)
    assert data["status"] == "ok"
