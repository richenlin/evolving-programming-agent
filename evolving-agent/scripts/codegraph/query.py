#!/usr/bin/env python3
"""
CodeGraph Query — hybrid context from SQLite FTS5 + vectors + graph.json.

Used at task start to inject relevant code structure and past session learnings.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Dict, List, Set

from codegraph.db import get_project_db
from codegraph.embedder import search_vectors
from codegraph.paths import get_graph_path

try:
    from core.path_resolver import get_project_kb_root
except ImportError:
    def get_project_kb_root(project_root):
        return Path(project_root) / ".opencode" / "knowledge"


def _load_graph(project_root: Path) -> Dict[str, Any]:
    path = get_graph_path(project_root)
    if not path.exists():
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return {}


def _tokenize_query(text: str) -> Set[str]:
    tokens: Set[str] = set()
    tokens.update(w.lower() for w in re.findall(r"[a-zA-Z][a-zA-Z0-9_-]{2,}", text))
    tokens.update(re.findall(r"[\u4e00-\u9fa5]{2,4}", text))
    return tokens


def _match_graph_symbols(graph: Dict[str, Any], query: str, limit: int = 8) -> List[Dict[str, Any]]:
    """Fallback symbol match from graph.json when FTS unavailable."""
    tokens = _tokenize_query(query)
    if not tokens:
        return []

    scored: List[tuple] = []
    for sym in graph.get("symbols", []):
        name = sym.get("name", "").lower()
        file_path = sym.get("file", "").lower()
        score = 0
        for t in tokens:
            tl = t.lower()
            if tl == name:
                score += 5
            elif tl in name:
                score += 3
            elif tl in file_path:
                score += 2
        if score > 0:
            scored.append((score, sym))

    scored.sort(key=lambda x: x[0], reverse=True)
    return [s for _, s in scored[:limit]]


def _search_symbols_fts(project_root: Path, query: str, limit: int = 8) -> List[Dict[str, Any]]:
    try:
        hits = get_project_db(project_root).search_symbols(query, limit=limit)
        if hits:
            return hits
    except Exception:
        pass
    return []


def _match_modules(graph: Dict[str, Any], query: str, limit: int = 3) -> List[Dict[str, Any]]:
    tokens = _tokenize_query(query)
    scored: List[tuple] = []
    for mod in graph.get("modules", []):
        name = mod.get("name", "").lower()
        score = sum(2 for t in tokens if t.lower() in name)
        if score > 0:
            scored.append((score, mod))
    scored.sort(key=lambda x: x[0], reverse=True)
    return [m for _, m in scored[:limit]]


def _hybrid_experience_search(
    project_root: Path,
    query: str,
    vector_top_k: int = 5,
    vector_threshold: float = 0.35,
    fts_top_k: int = 5,
) -> List[Dict[str, Any]]:
    """Merge FTS5 keyword + vector semantic hits."""
    merged: Dict[str, Dict[str, Any]] = {}

    # FTS5 from SQLite
    try:
        for hit in get_project_db(project_root).search_entries(query, limit=fts_top_k):
            eid = hit["entry_id"]
            merged[eid] = {
                "entry_id": eid,
                "name": hit["name"],
                "content": hit["content"],
                "type": hit.get("type"),
                "score": hit.get("score", 0.5) * 0.5,
                "sources": ["fts5"],
            }
    except Exception:
        pass

    # Vector search
    for hit in search_vectors(project_root, query, top_k=vector_top_k, threshold=vector_threshold):
        eid = hit["entry_id"]
        vscore = hit["score"]
        if eid in merged:
            merged[eid]["score"] = min(1.0, merged[eid]["score"] + vscore * 0.5)
            merged[eid]["sources"].append("vector")
        else:
            content = {}
            try:
                row = get_project_db(project_root).get_entry(eid)
                if row:
                    content = row.get("content", {})
                    name = row.get("name", hit.get("text", "")[:80])
                else:
                    name = hit.get("text", "")[:80]
            except Exception:
                name = hit.get("text", "")[:80]
            merged[eid] = {
                "entry_id": eid,
                "name": name,
                "content": content,
                "type": hit.get("type"),
                "score": vscore * 0.5,
                "sources": ["vector"],
            }

    results = sorted(merged.values(), key=lambda x: x["score"], reverse=True)
    filtered: List[Dict[str, Any]] = []
    try:
        import sys
        _kd = str(Path(__file__).parent.parent / "knowledge")
        if _kd not in sys.path:
            sys.path.insert(0, _kd)
        from quality import is_low_value_entry
        for item in results:
            ent = {
                "name": item.get("name", ""),
                "category": item.get("type", "experience"),
                "content": item.get("content") or {},
            }
            if not is_low_value_entry(ent):
                filtered.append(item)
        results = filtered
    except ImportError:
        pass
    return results[:max(vector_top_k, fts_top_k)]


def query_context(
    project_root: str | Path,
    query: str,
    vector_top_k: int = 5,
    vector_threshold: float = 0.35,
) -> Dict[str, Any]:
    """
    Build structured context for a task.

    Symbol search: SQLite FTS5 → graph.json fallback
    Experience: FTS5 + vector hybrid
    """
    root = Path(project_root).resolve()
    graph = _load_graph(root)

    symbols = _search_symbols_fts(root, query)
    symbol_source = "fts5"
    if not symbols:
        symbols = _match_graph_symbols(graph, query)
        symbol_source = "graph"

    modules = _match_modules(graph, query)
    experience = _hybrid_experience_search(
        root, query,
        vector_top_k=vector_top_k,
        vector_threshold=vector_threshold,
    )

    db_stats = {}
    try:
        db_stats = get_project_db(root).stats()
    except Exception:
        pass

    return {
        "query": query,
        "graph_stats": graph.get("stats", {}),
        "index_backend": graph.get("index_backend", {}),
        "db_stats": db_stats,
        "symbol_source": symbol_source,
        "symbols": symbols,
        "modules": modules,
        "experience": experience,
    }


def format_context(result: Dict[str, Any], char_budget: int = 4000) -> str:
    """Format query result as markdown for agent context."""
    lines: List[str] = []
    used = 0

    def _append(text: str) -> bool:
        nonlocal used
        if used + len(text) > char_budget:
            return False
        lines.append(text)
        used += len(text)
        return True

    stats = result.get("graph_stats", {})
    backend = result.get("index_backend", {})
    if stats.get("file_count"):
        ast = backend.get("ast", "?")
        search = backend.get("search", "fts5")
        _append(
            f"<!-- CodeGraph: {stats.get('file_count')} files, "
            f"{stats.get('symbol_count', 0)} symbols, ast={ast}, search={search} -->\n"
        )

    symbols = result.get("symbols", [])
    if symbols:
        src = result.get("symbol_source", "graph")
        _append(f"## 项目代码结构（CodeGraph/{src}）\n")
        for sym in symbols[:6]:
            end = sym.get("end_line", sym.get("line"))
            loc = f"{sym.get('file')}:{sym.get('line')}"
            if end and end != sym.get("line"):
                loc = f"{sym.get('file')}:{sym.get('line')}-{end}"
            line = f"- `{sym.get('kind')}` **{sym.get('name')}** @ `{loc}`\n"
            if not _append(line):
                break

    modules = result.get("modules", [])
    if modules and used < char_budget - 100:
        _append("\n**相关模块**: " + ", ".join(m.get("name", "") for m in modules[:3]) + "\n")

    exp = result.get("experience", [])
    if exp:
        _append("\n## 项目经验（FTS5 + 向量）\n")
        per = max(200, (char_budget - used) // max(len(exp), 1))
        for item in exp[:5]:
            name = item.get("name", "Unknown")
            content = item.get("content", {})
            srcs = "+".join(item.get("sources", []))
            block = f"\n### {name} _(score {item.get('score', 0):.2f}, {srcs})_\n"
            if not _append(block):
                break
            for field, label in [("solution", "解决方案"), ("description", "描述")]:
                val = content.get(field, "")
                if val and isinstance(val, str):
                    snippet = val[:per]
                    if not _append(f"**{label}**: {snippet}\n"):
                        break

    return "".join(lines).strip()
