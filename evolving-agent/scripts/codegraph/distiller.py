#!/usr/bin/env python3
"""Distiller — infer architecture patterns and frameworks from project structure."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Set

from codegraph.db import CodeGraphDB
from codegraph.node_id import node_id
from codegraph.seeds import DIRECTORY_PATTERNS, FRAMEWORK_IMPORTS, SEEDS


def _sync_global_seeds(db: CodeGraphDB) -> int:
    count = 0
    for seed in SEEDS:
        nid = node_id(seed["kind"], seed["name"], scope="global")
        db.upsert_node({
            "id": nid,
            "kind": seed["kind"],
            "name": seed["name"],
            "summary": seed.get("summary", ""),
            "scope": "global",
            "provenance": seed.get("provenance", "curated"),
        })
        count += 1
    return count


def distill_project(
    project_root: str | Path,
    graph: Dict[str, Any],
    db: CodeGraphDB,
) -> Dict[str, Any]:
    """
    Infer pattern/framework nodes from directory layout and import edges.
    Mirrors curated seeds into project scope.
    """
    root = Path(project_root).resolve()
    patterns_found: Set[str] = set()
    frameworks_found: Set[str] = set()
    edges_added = 0
    nodes_added = 0

    # Directory-based patterns
    for f in graph.get("files", []):
        rel = f.get("path", "")
        if not rel:
            continue
        parts = Path(rel).parts
        for part in parts:
            key = part.lower()
            if key in DIRECTORY_PATTERNS:
                patterns_found.add(DIRECTORY_PATTERNS[key])

    # Import-based frameworks
    for dep in graph.get("dependencies", []):
        if dep.get("type") != "import":
            continue
        spec = (dep.get("spec") or dep.get("to", "")).lower()
        for imp_key, fw_name in FRAMEWORK_IMPORTS.items():
            if imp_key in spec:
                frameworks_found.add(fw_name)

    # Create distilled nodes + mirror global seeds
    seed_count = _sync_global_seeds(db)

    for pname in patterns_found:
        nid = node_id("pattern", pname, scope="project")
        db.upsert_node({
            "id": nid,
            "kind": "pattern",
            "name": pname,
            "summary": f"Detected from project directory structure",
            "scope": "project",
            "provenance": "distilled",
        })
        nodes_added += 1

    for fname in frameworks_found:
        nid = node_id("framework", fname, scope="project")
        db.upsert_node({
            "id": nid,
            "kind": "framework",
            "name": fname,
            "summary": f"Detected from import analysis",
            "scope": "project",
            "provenance": "distilled",
        })
        nodes_added += 1

        # Link symbols that import this framework
        for sym in graph.get("symbols", [])[:500]:
            sym_file = sym.get("file", "")
            for dep in graph.get("dependencies", []):
                if dep.get("type") != "import":
                    continue
                from_file = dep.get("from", "").replace("file:", "")
                spec = (dep.get("spec") or "").lower()
                if from_file == sym_file and any(k in spec for k in FRAMEWORK_IMPORTS if FRAMEWORK_IMPORTS[k] == fname):
                    sid = sym.get("id") or node_id(
                        "symbol", sym.get("name", ""), file=sym_file, line=sym.get("line", 0)
                    )
                    db.upsert_edge(sid, nid, "uses", provenance="distilled")
                    edges_added += 1

    # Entry point detection
    entry_candidates = ["main.py", "app.py", "index.ts", "index.js", "main.go", "lib.rs"]
    for f in graph.get("files", []):
        rel = f.get("path", "")
        base = Path(rel).name
        if base in entry_candidates or rel.endswith("/main.py"):
            nid = node_id("architecture", f"entry:{rel}", scope="project")
            db.upsert_node({
                "id": nid,
                "kind": "architecture",
                "name": f"Entry: {rel}",
                "summary": "Application entry point",
                "file": rel,
                "scope": "project",
                "provenance": "distilled",
            })
            nodes_added += 1

    return {
        "patterns": sorted(patterns_found),
        "frameworks": sorted(frameworks_found),
        "nodes_added": nodes_added,
        "edges_added": edges_added,
        "seeds_synced": seed_count,
    }
