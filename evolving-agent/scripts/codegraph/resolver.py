#!/usr/bin/env python3
"""Resolver — build import/call edges from indexed graph data."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Dict, List, Set, Tuple

from codegraph.db import CodeGraphDB
from codegraph.node_id import module_id, symbol_id

MAX_SYMBOLS_SCAN = 2000
MAX_EDGES = 5000


def _resolve_import_target(spec: str, from_file: str, known_files: Set[str]) -> str | None:
    """Resolve relative import specifier to a project file path."""
    if not spec.startswith("."):
        return None
    base_dir = str(Path(from_file).parent)
    candidate = str(Path(base_dir) / spec).replace("\\", "/")
    variants = [
        candidate,
        f"{candidate}.py",
        f"{candidate}.ts",
        f"{candidate}.tsx",
        f"{candidate}.js",
        f"{candidate}/index.ts",
        f"{candidate}/index.js",
        f"{candidate}/__init__.py",
    ]
    for v in variants:
        norm = str(Path(v)).replace("\\", "/").lstrip("./")
        if norm in known_files:
            return norm
    return None


def resolve_edges_from_graph(
    graph: Dict[str, Any],
    db: CodeGraphDB,
    *,
    provenance: str = "heuristic",
) -> Dict[str, int]:
    """
    Sync graph.json symbols/dependencies into node/edge tables and resolve call edges.
    """
    files = graph.get("files", [])
    symbols = graph.get("symbols", [])
    dependencies = graph.get("dependencies", [])

    known_files: Set[str] = {f.get("path", "") for f in files if f.get("path")}
    edge_count = 0
    node_count = 0

    db.clear_edges()

    # Module + symbol nodes
    for f in files:
        rel = f.get("path", "")
        if not rel:
            continue
        mid = module_id(rel)
        db.upsert_node({
            "id": mid,
            "kind": "module",
            "name": rel,
            "file": rel,
            "scope": "project",
            "provenance": "parsed",
            "meta": {"language": f.get("language", "")},
        })
        node_count += 1
        db.upsert_file({
            "path": rel,
            "lang": f.get("language", ""),
            "size": f.get("size", 0),
        })

    for sym in symbols[:MAX_SYMBOLS_SCAN]:
        rel = sym.get("file", "")
        name = sym.get("name", "")
        line = sym.get("line", 0)
        if not rel or not name:
            continue
        sid = sym.get("id") or symbol_id(rel, name, line)
        db.upsert_node({
            "id": sid,
            "kind": "symbol",
            "name": name,
            "file": rel,
            "line": line,
            "end_line": sym.get("end_line", line),
            "scope": "project",
            "provenance": "parsed",
            "meta": {"symbol_kind": sym.get("kind", "")},
        })
        node_count += 1
        mid = module_id(rel)
        db.upsert_edge(mid, sid, "contains", provenance=provenance)

    # Import edges from parser output
    for dep in dependencies:
        if edge_count >= MAX_EDGES:
            break
        etype = dep.get("type", "import")
        if etype not in ("import", "call"):
            continue
        from_ref = dep.get("from", "")
        to_ref = dep.get("to", "")
        if not from_ref or not to_ref:
            continue

        if from_ref.startswith("file:"):
            from_file = from_ref.replace("file:", "")
        else:
            from_file = from_ref

        if etype == "import":
            spec = dep.get("spec", to_ref)
            target = _resolve_import_target(spec, from_file, known_files)
            if target:
                src = module_id(from_file)
                dst = module_id(target)
                db.upsert_edge(src, dst, "imports", provenance=provenance)
                edge_count += 1
        elif etype == "call":
            caller = dep.get("caller", "")
            callee = dep.get("callee", to_ref)
            if caller and callee:
                caller_sym = next(
                    (s for s in symbols if s.get("file") == from_file and s.get("name") == caller),
                    None,
                )
                if caller_sym:
                    src = caller_sym.get("id") or symbol_id(from_file, caller, caller_sym.get("line", 0))
                    dst_candidates = [s for s in symbols if s.get("name") == callee]
                    for dst_sym in dst_candidates[:3]:
                        dst = dst_sym.get("id") or symbol_id(
                            dst_sym.get("file", ""), callee, dst_sym.get("line", 0)
                        )
                        db.upsert_edge(src, dst, "calls", provenance=provenance)
                        edge_count += 1

    # Heuristic call edges: tokenize symbol names in same file context
    name_index: Dict[str, List[str]] = {}
    for sym in symbols[:MAX_SYMBOLS_SCAN]:
        name = sym.get("name", "")
        if len(name) >= 3 and name[0].islower():
            sid = sym.get("id") or symbol_id(sym.get("file", ""), name, sym.get("line", 0))
            name_index.setdefault(name, []).append(sid)

    token_re = re.compile(r"\b[a-zA-Z_$][a-zA-Z0-9_$]*\b")
    for sym in symbols[:MAX_SYMBOLS_SCAN]:
        if edge_count >= MAX_EDGES:
            break
        body = sym.get("body", "")
        if not body:
            continue
        src = sym.get("id") or symbol_id(sym.get("file", ""), sym.get("name", ""), sym.get("line", 0))
        tokens = set(token_re.findall(body))
        for tok in tokens:
            if tok == sym.get("name") or tok not in name_index:
                continue
            for dst in name_index[tok][:2]:
                if dst != src:
                    db.upsert_edge(src, dst, "calls", provenance=provenance)
                    edge_count += 1
                    if edge_count >= MAX_EDGES:
                        break

    return {"nodes": node_count, "edges": edge_count}
