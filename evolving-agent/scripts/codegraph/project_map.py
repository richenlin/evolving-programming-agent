#!/usr/bin/env python3
"""Project Map — compact project cognition snapshot for task start."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

from codegraph.db import get_project_db
from codegraph.paths import get_codegraph_dir, get_graph_path


def get_project_map_path(project_root: str | Path) -> Path:
    return get_codegraph_dir(project_root) / "project-map.json"


def build_project_map(project_root: str | Path, graph: Dict[str, Any] | None = None) -> Dict[str, Any]:
    """Build structured project map from graph + DB."""
    root = Path(project_root).resolve()
    if graph is None:
        graph_path = get_graph_path(root)
        graph = {}
        if graph_path.exists():
            try:
                graph = json.loads(graph_path.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                pass

    stats = graph.get("stats", {})
    modules = graph.get("modules", [])

    # Language distribution
    lang_counts: Dict[str, int] = {}
    for f in graph.get("files", []):
        lang = f.get("language", "unknown")
        lang_counts[lang] = lang_counts.get(lang, 0) + 1
    top_langs = sorted(lang_counts.items(), key=lambda x: x[1], reverse=True)[:3]

    # Hot symbols (by name frequency in calls — simplified: first N unique)
    symbols = graph.get("symbols", [])
    sym_by_module: Dict[str, int] = {}
    for sym in symbols:
        mod = sym.get("file", "").split("/")[0] if "/" in sym.get("file", "") else "."
        sym_by_module[mod] = sym_by_module.get(mod, 0) + 1

    db_stats: Dict[str, Any] = {}
    patterns: List[str] = []
    frameworks: List[str] = []
    try:
        db = get_project_db(root)
        db_stats = db.stats()
        for node in db.list_nodes(kind="pattern", limit=10):
            patterns.append(node.get("name", ""))
        for node in db.list_nodes(kind="framework", limit=10):
            frameworks.append(node.get("name", ""))
    except Exception:
        pass

    pmap = {
        "version": 1,
        "project_root": str(root),
        "languages": [{"name": l, "files": c} for l, c in top_langs],
        "stats": {
            "files": stats.get("file_count", 0),
            "symbols": stats.get("symbol_count", 0),
            "edges": stats.get("edge_count", 0),
        },
        "modules": [
            {"name": m.get("name", ""), "file_count": len(m.get("files", []))}
            for m in modules[:12]
        ],
        "patterns": patterns[:8],
        "frameworks": frameworks[:8],
        "experience": db_stats.get("by_category", {}),
        "hot_symbols": [
            {"name": s.get("name"), "file": s.get("file"), "kind": s.get("kind")}
            for s in symbols[:8]
        ],
    }
    return pmap


def format_project_map_markdown(pmap: Dict[str, Any], *, max_tokens: int = 400) -> str:
    """Format project map as markdown section (~300-500 tokens)."""
    lines: List[str] = ["## 项目地图"]

    langs = pmap.get("languages", [])
    if langs:
        lang_str = ", ".join(f"{l['name']}({l['files']})" for l in langs)
        lines.append(f"- **语言**: {lang_str}")

    fw = pmap.get("frameworks", [])
    if fw:
        lines.append(f"- **框架**: {', '.join(fw[:6])}")

    stats = pmap.get("stats", {})
    if stats.get("files"):
        lines.append(
            f"- **规模**: {stats.get('files', 0)} 文件, "
            f"{stats.get('symbols', 0)} 符号, {stats.get('edges', 0)} 边"
        )

    patterns = pmap.get("patterns", [])
    if patterns:
        lines.append(f"- **架构模式**: {', '.join(patterns[:5])}")

    modules = pmap.get("modules", [])
    if modules:
        mod_str = " | ".join(
            f"{m['name']}({m['file_count']})" for m in modules[:6] if m.get("name")
        )
        if mod_str:
            lines.append(f"- **模块**: {mod_str}")

    exp = pmap.get("experience", {})
    if exp:
        exp_str = ", ".join(f"{k}×{v}" for k, v in sorted(exp.items()))
        lines.append(f"- **项目经验**: {exp_str}")

    hot = pmap.get("hot_symbols", [])
    if hot:
        sym_str = ", ".join(
            f"{s.get('name')}" for s in hot[:5] if s.get("name")
        )
        if sym_str:
            lines.append(f"- **符号采样**: {sym_str}")

    text = "\n".join(lines)
    max_chars = max_tokens * 4
    if len(text) > max_chars:
        text = text[:max_chars].rsplit("\n", 1)[0] + "\n…"
    return text


def save_project_map(project_root: str | Path, graph: Dict[str, Any] | None = None) -> Path:
    pmap = build_project_map(project_root, graph)
    path = get_project_map_path(project_root)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(pmap, indent=2, ensure_ascii=False), encoding="utf-8")
    return path
