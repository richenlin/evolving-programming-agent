#!/usr/bin/env python3
"""
CodeGraph Indexer — scan project source, build graph.json + SQLite symbol FTS index.

Uses tree-sitter AST when available, regex fallback otherwise.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

from codegraph.ast_parser import parse_file, tree_sitter_available
from codegraph.db import get_project_db
from codegraph.paths import get_graph_path, get_index_state_path

IGNORE_DIRS = {
    ".git", ".hg", ".svn", "node_modules", "vendor", "dist", "build",
    "out", "target", "__pycache__", ".venv", "venv", ".opencode",
    ".idea", ".vscode", "coverage", ".next", ".nuxt", "Pods",
}
IGNORE_EXTENSIONS = {
    ".png", ".jpg", ".jpeg", ".gif", ".webp", ".ico", ".svg",
    ".woff", ".woff2", ".ttf", ".eot", ".mp4", ".zip", ".tar",
    ".gz", ".lock", ".min.js", ".map", ".pyc", ".pyo",
}

SOURCE_EXTENSIONS = {
    ".py", ".js", ".jsx", ".ts", ".tsx", ".mjs", ".cjs",
    ".go", ".rs", ".java", ".kt", ".scala", ".rb", ".php",
    ".cs", ".swift", ".vue", ".svelte",
}

LANGUAGE_MAP = {
    ".py": "python", ".js": "javascript", ".jsx": "javascript",
    ".ts": "typescript", ".tsx": "typescript", ".mjs": "javascript",
    ".cjs": "javascript", ".go": "go", ".rs": "rust", ".java": "java",
    ".kt": "kotlin", ".scala": "scala", ".rb": "ruby", ".php": "php",
    ".cs": "csharp", ".swift": "swift", ".vue": "vue", ".svelte": "svelte",
}


def _file_hash(path: Path) -> str:
    try:
        return hashlib.md5(path.read_bytes()).hexdigest()
    except OSError:
        return ""


def _should_scan_file(path: Path) -> bool:
    if path.suffix.lower() in IGNORE_EXTENSIONS:
        return False
    if path.suffix.lower() not in SOURCE_EXTENSIONS:
        return False
    if path.stat().st_size > 512_000:
        return False
    return True


def _iter_source_files(project_root: Path) -> List[Path]:
    files: List[Path] = []
    for path in project_root.rglob("*"):
        if not path.is_file():
            continue
        parts = set(path.relative_to(project_root).parts)
        if parts & IGNORE_DIRS:
            continue
        if any(part in IGNORE_DIRS for part in path.parts):
            continue
        if _should_scan_file(path):
            files.append(path)
    return sorted(files)


def _infer_modules(files: List[str]) -> List[Dict[str, Any]]:
    module_map: Dict[str, List[str]] = {}
    for f in files:
        top = f.split("/")[0] if "/" in f else "."
        module_map.setdefault(top, []).append(f)
    return [
        {"name": name, "path": name if name != "." else "", "files": sorted(flist)}
        for name, flist in sorted(module_map.items())
    ]


def _load_index_state(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {"files": {}}
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return {"files": {}}


def _save_json(path: Path, data: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    tmp.replace(path)


def scan_project(
    project_root: str | Path,
    incremental: bool = True,
    max_files: int = 2000,
) -> Dict[str, Any]:
    """
    Scan project source → graph.json + SQLite symbols_fts index.
    """
    root = Path(project_root).resolve()
    graph_path = get_graph_path(root)
    state_path = get_index_state_path(root)

    prev_state = _load_index_state(state_path)
    prev_graph: Dict[str, Any] = {}
    if graph_path.exists():
        try:
            with open(graph_path, "r", encoding="utf-8") as f:
                prev_graph = json.load(f)
        except (json.JSONDecodeError, OSError):
            prev_graph = {}

    prev_symbols_by_file: Dict[str, List] = {}
    prev_edges_by_file: Dict[str, List] = {}
    prev_calls_by_file: Dict[str, List] = {}
    for sym in prev_graph.get("symbols", []):
        prev_symbols_by_file.setdefault(sym["file"], []).append(sym)
    for edge in prev_graph.get("dependencies", []):
        etype = edge.get("type", "import")
        from_file = edge["from"].replace("file:", "")
        if etype == "import":
            prev_edges_by_file.setdefault(from_file, []).append(edge)
        elif etype == "call":
            prev_calls_by_file.setdefault(from_file, []).append(edge)

    all_files = _iter_source_files(root)[:max_files]
    new_state_files: Dict[str, Dict[str, Any]] = dict(prev_state.get("files", {}))
    file_nodes: List[Dict[str, Any]] = []
    all_symbols: List[Dict[str, Any]] = []
    all_edges: List[Dict[str, Any]] = []
    scanned = 0
    skipped = 0
    ts_count = 0
    regex_count = 0
    rel_paths: List[str] = []

    for path in all_files:
        rel = str(path.relative_to(root))
        rel_paths.append(rel)
        mtime = path.stat().st_mtime
        fhash = _file_hash(path)
        prev_entry = prev_state.get("files", {}).get(rel)
        ext = path.suffix.lower()

        if incremental and prev_entry:
            if prev_entry.get("mtime") == mtime and prev_entry.get("hash") == fhash:
                skipped += 1
                file_nodes.append({
                    "id": f"file:{rel}",
                    "path": rel,
                    "language": prev_entry.get("language", "unknown"),
                    "size": prev_entry.get("size", 0),
                    "parser": prev_entry.get("parser", "regex"),
                })
                all_symbols.extend(prev_symbols_by_file.get(rel, []))
                all_edges.extend(prev_edges_by_file.get(rel, []))
                all_edges.extend(prev_calls_by_file.get(rel, []))
                continue

        try:
            content = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue

        language = LANGUAGE_MAP.get(ext, "unknown")
        file_id = f"file:{rel}"
        parsed = parse_file(content, language, rel, ext)

        if parsed["parser"] == "tree-sitter":
            ts_count += 1
        else:
            regex_count += 1

        file_nodes.append({
            "id": file_id,
            "path": rel,
            "language": language,
            "size": len(content.encode("utf-8")),
            "parser": parsed["parser"],
        })
        all_symbols.extend(parsed["symbols"])
        all_edges.extend(parsed["dependencies"])
        all_edges.extend(parsed.get("calls", []))

        new_state_files[rel] = {
            "mtime": mtime,
            "hash": fhash,
            "language": language,
            "size": len(content.encode("utf-8")),
            "symbol_count": len(parsed["symbols"]),
            "parser": parsed["parser"],
        }
        scanned += 1

    current_set = set(rel_paths)
    for k in list(new_state_files):
        if k not in current_set:
            del new_state_files[k]

    graph = {
        "version": 2,
        "scanned_at": datetime.now().isoformat(),
        "project_root": str(root),
        "index_backend": {
            "ast": "tree-sitter" if tree_sitter_available() else "regex",
            "search": "sqlite-fts5",
        },
        "stats": {
            "file_count": len(file_nodes),
            "symbol_count": len(all_symbols),
            "edge_count": len(all_edges),
            "scanned_this_run": scanned,
            "skipped_unchanged": skipped,
            "parsed_tree_sitter": ts_count,
            "parsed_regex": regex_count,
        },
        "files": file_nodes,
        "symbols": all_symbols,
        "dependencies": all_edges,
        "modules": _infer_modules([f["path"] for f in file_nodes]),
    }

    _save_json(graph_path, graph)
    _save_json(state_path, {
        "last_scan": datetime.now().isoformat(),
        "files": new_state_files,
    })

    # Sync symbols to SQLite FTS5 + v3 graph (node/edge)
    db = get_project_db(root)
    db_symbols = db.replace_symbols(all_symbols)

    graph_sync: Dict[str, Any] = {}
    try:
        from codegraph.resolver import resolve_edges_from_graph
        from codegraph.distiller import distill_project
        from codegraph.project_map import save_project_map

        graph_sync["resolver"] = resolve_edges_from_graph(graph, db)
        graph_sync["distiller"] = distill_project(root, graph, db)
        save_project_map(root, graph)
    except Exception as exc:
        graph_sync["error"] = str(exc)

    db_stats = db.stats()

    return {
        "status": "ok",
        "graph_path": str(graph_path),
        "db_path": str(db.db_path),
        "stats": graph["stats"],
        "index_backend": graph["index_backend"],
        "db_stats": db_stats,
        "graph_sync": graph_sync,
    }
