"""Tests for CodeGraph v3 — KnowledgePlane, merger, project map."""

import json
import sys
from pathlib import Path

import pytest

SCRIPTS = Path(__file__).parent.parent / "evolving-agent" / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))


def test_merger_token_budget():
    from codegraph.merger import merge_sections, estimate_tokens

    sections = [
        {"id": "a", "kind": "graph", "priority": 90, "text": "A" * 400},
        {"id": "b", "kind": "experience", "priority": 80, "text": "B" * 400},
    ]
    result = merge_sections(sections, budget_tokens=50, graph_ratio=0.5)
    assert result["tokens_used"] <= 50
    assert estimate_tokens("hello world") >= 1


def test_format_entry_summary():
    from codegraph.merger import format_entry_summary

    assert "CORS" in format_entry_summary({"summary": "CORS 中间件顺序问题"})
    assert format_entry_summary({"solution": "use bcrypt"}) != ""


def test_v3_nodes_and_edges(sample_project):
    from codegraph.indexer import scan_project
    from codegraph.db import get_project_db

    result = scan_project(sample_project, incremental=False)
    assert "graph_sync" in result
    db = get_project_db(sample_project)
    stats = db.stats()
    assert stats.get("nodes", 0) >= 2
    assert stats.get("edges", 0) >= 0

    hits = db.search_nodes("UserModel", limit=3)
    assert len(hits) >= 1


def test_project_map(sample_project):
    from codegraph.indexer import scan_project
    from codegraph.project_map import build_project_map, format_project_map_markdown, save_project_map

    scan_project(sample_project, incremental=False)
    pmap = build_project_map(sample_project)
    assert pmap.get("stats", {}).get("files", 0) >= 2
    md = format_project_map_markdown(pmap)
    assert "项目地图" in md

    path = save_project_map(sample_project)
    assert path.exists()


def test_knowledge_plane(sample_project):
    from codegraph.indexer import scan_project
    from codegraph.plane import query_plane

    scan_project(sample_project, incremental=False)
    result = query_plane(sample_project, "User model authentication", tier="medium", budget_tokens=800)
    assert "text" in result
    assert result.get("tokens_used", 0) <= 800
    assert "项目地图" in result["text"] or "UserModel" in result["text"]


def test_context_writes_meta(sample_project):
    from codegraph.indexer import scan_project
    from codegraph.context import build_task_context

    scan_project(sample_project, incremental=False)
    build_task_context(sample_project, "User auth", tier="small", budget_tokens=600)
    meta_path = sample_project / ".opencode" / ".knowledge-context.meta.json"
    assert meta_path.exists()
    meta = json.loads(meta_path.read_text())
    assert meta.get("tier") == "small"
    assert "diagnostics" in meta
