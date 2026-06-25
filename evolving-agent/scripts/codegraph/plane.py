#!/usr/bin/env python3
"""
KnowledgePlane — tier-aware unified retrieval for CodeGraph + experience.

Reference: tiantacode V2 core/knowledge/KnowledgePlane.ts
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional, Set

from codegraph.db import get_project_db
from codegraph.merger import format_entry_summary, merge_sections
from codegraph.project_map import build_project_map, format_project_map_markdown
from codegraph.query import query_context, format_context

Tier = Literal["tiny", "small", "medium", "large"]

TIER_LIMITS: Dict[str, Dict[str, Any]] = {
    "tiny": {"experience": 1, "symbols": 0, "neighbors": 0, "patterns": 0},
    "small": {"experience": 2, "symbols": 0, "neighbors": 0, "patterns": 0},
    "medium": {"experience": 4, "symbols": 2, "neighbors": 3, "patterns": 2},
    "large": {"experience": 5, "symbols": 3, "neighbors": 3, "patterns": 4},
}

GRAPH_RATIO_BY_TIER: Dict[str, float] = {
    "tiny": 0.0,
    "small": 0.2,
    "medium": 0.4,
    "large": 0.5,
}


def _retrieve_graph_section(
    project_root: Path,
    query: str,
    limits: Dict[str, Any],
) -> tuple[str, Dict[str, Any]]:
    """GraphProvider — FTS5 nodes + optional neighbor expansion."""
    meta: Dict[str, Any] = {"symbols": [], "neighbors": [], "patterns": []}
    if limits.get("symbols", 0) <= 0:
        return "", meta

    lines: List[str] = ["## 相关代码节点"]
    db = get_project_db(project_root)

    nodes = db.search_nodes(query, limit=limits["symbols"], kind="symbol")
    if not nodes:
        nodes = db.search_nodes(query, limit=limits["symbols"])

    seen: Set[str] = set()
    for node in nodes:
        nid = node.get("id", "")
        if nid in seen:
            continue
        seen.add(nid)
        loc = node.get("file") or ""
        if node.get("line"):
            loc = f"{loc}:{node['line']}"
        lines.append(f"- `{node.get('kind')}` **{node.get('name')}** @ `{loc}`")
        meta["symbols"].append({"id": nid, "name": node.get("name"), "file": node.get("file")})

        if limits.get("neighbors", 0) > 0:
            for nb in db.neighbors(nid, limit=limits["neighbors"]):
                nb_id = nb.get("id", "")
                if nb_id in seen:
                    continue
                seen.add(nb_id)
                nb_loc = nb.get("file") or ""
                if nb.get("line"):
                    nb_loc = f"{nb_loc}:{nb['line']}"
                edge = nb.get("edge_kind", "?")
                lines.append(f"  ↳ ({edge}) `{nb.get('kind')}` **{nb.get('name')}** @ `{nb_loc}`")
                meta["neighbors"].append({"id": nb_id, "name": nb.get("name")})

    if limits.get("patterns", 0) > 0:
        patterns = db.list_nodes(kind="pattern", scope="project", limit=limits["patterns"])
        frameworks = db.list_nodes(kind="framework", scope="project", limit=limits["patterns"])
        concepts = patterns + frameworks
        if concepts:
            lines.append("\n**架构/框架**: " + ", ".join(c.get("name", "") for c in concepts))
            meta["patterns"] = [c.get("name") for c in concepts]

    text = "\n".join(lines) if len(lines) > 1 else ""
    return text, meta


def _retrieve_experience_section(
    project_root: Path,
    query: str,
    limits: Dict[str, Any],
    knowledge_mode: str,
    graph_hit_ids: Set[str],
) -> tuple[str, Dict[str, Any]]:
    """ExperienceProvider — trigger + hybrid with graph anchor boost."""
    meta: Dict[str, Any] = {"entries": []}
    limit = limits.get("experience", 4)
    if limit <= 0:
        return "", meta

    import sys
    knowledge_dir = str(Path(__file__).parent.parent / "knowledge")
    if knowledge_dir not in sys.path:
        sys.path.insert(0, knowledge_dir)
    from trigger import trigger_knowledge  # type: ignore

    kb = trigger_knowledge(
        user_input=query,
        project_dir=str(project_root),
        limit=limit,
        mode=knowledge_mode,
    )

    lines: List[str] = []
    sections = [
        ("项目相关知识", kb.get("knowledge", {}).get("project_local", [])),
        ("相关知识", kb.get("knowledge", {}).get("high_relevance", [])),
        ("可能相关", kb.get("knowledge", {}).get("medium_relevance", [])),
    ]

    count = 0
    for heading, entries in sections:
        if count >= limit:
            break
        section_lines: List[str] = []
        for entry in entries:
            if count >= limit:
                break
            eid = entry.get("id", "")
            name = entry.get("name", "Unknown")
            category = entry.get("category", "")
            content = entry.get("content", {})
            summary = format_entry_summary(content, max_tokens=60)
            if not summary:
                continue

            anchor_boost = ""
            anchors = entry.get("anchor_node_ids") or []
            if graph_hit_ids and anchors and set(anchors) & graph_hit_ids:
                anchor_boost = " 📌"

            section_lines.append(f"### [{category}] {name}{anchor_boost}\n{summary}")
            meta["entries"].append({"id": eid, "name": name, "category": category})
            count += 1

        if section_lines:
            lines.append(f"## {heading}")
            lines.extend(section_lines)

    return "\n\n".join(lines), meta


def query_plane(
    project_root: str | Path,
    user_input: str,
    *,
    tier: Tier = "medium",
    budget_tokens: int = 1500,
    knowledge_mode: str = "hybrid",
    include_project_map: bool = True,
    include_legacy_graph: bool = True,
) -> Dict[str, Any]:
    """
    Unified knowledge query with tier limits and token budget merge.
    """
    root = Path(project_root).resolve()
    limits = TIER_LIMITS.get(tier, TIER_LIMITS["medium"])
    graph_ratio = GRAPH_RATIO_BY_TIER.get(tier, 0.4)
    diagnostics: Dict[str, Any] = {"tier": tier, "budget_tokens": budget_tokens, "errors": []}
    sections: List[Dict[str, Any]] = []

    # Project map (always first, small budget)
    if include_project_map:
        try:
            pmap = build_project_map(root)
            map_md = format_project_map_markdown(pmap, max_tokens=100)
            if map_md:
                sections.append({
                    "id": "project_map",
                    "kind": "graph",
                    "priority": 100,
                    "text": map_md,
                })
                diagnostics["project_map"] = pmap.get("stats", {})
        except Exception as e:
            diagnostics["errors"].append(f"project_map: {e}")

    # Legacy graph context (symbols from FTS5 / graph.json) for medium+
    graph_hit_ids: Set[str] = set()
    if include_legacy_graph and limits.get("symbols", 0) >= 0:
        try:
            graph_result = query_context(root, user_input)
            legacy_md = format_context(
                graph_result,
                char_budget=int(budget_tokens * 4 * graph_ratio * 0.6),
            )
            if legacy_md:
                sections.append({
                    "id": "codegraph_legacy",
                    "kind": "graph",
                    "priority": 90,
                    "text": legacy_md,
                })
            for sym in graph_result.get("symbols", []):
                sid = sym.get("id")
                if sid:
                    graph_hit_ids.add(sid)
            diagnostics["legacy_graph"] = {
                "symbol_count": len(graph_result.get("symbols", [])),
                "experience_count": len(graph_result.get("experience", [])),
            }
        except Exception as e:
            diagnostics["errors"].append(f"legacy_graph: {e}")

    # v3 graph nodes
    try:
        graph_md, graph_meta = _retrieve_graph_section(root, user_input, limits)
        if graph_md:
            sections.append({
                "id": "graph_nodes",
                "kind": "graph",
                "priority": 85,
                "text": graph_md,
            })
        for s in graph_meta.get("symbols", []):
            if s.get("id"):
                graph_hit_ids.add(s["id"])
        diagnostics["graph"] = graph_meta
    except Exception as e:
        diagnostics["errors"].append(f"graph: {e}")

    # Experience
    try:
        exp_md, exp_meta = _retrieve_experience_section(
            root, user_input, limits, knowledge_mode, graph_hit_ids
        )
        if exp_md:
            sections.append({
                "id": "experience",
                "kind": "experience",
                "priority": 80,
                "text": exp_md,
            })
        diagnostics["experience"] = exp_meta
    except Exception as e:
        diagnostics["errors"].append(f"experience: {e}")

    merged = merge_sections(
        sections,
        budget_tokens=budget_tokens,
        graph_ratio=graph_ratio if limits.get("symbols", 0) > 0 else 0.25,
    )

    return {
        "query": user_input,
        "tier": tier,
        "text": merged["text"],
        "tokens_used": merged["tokens_used"],
        "budget_tokens": budget_tokens,
        "sections_included": merged["sections_included"],
        "sections_dropped": merged["sections_dropped"],
        "diagnostics": diagnostics,
    }
