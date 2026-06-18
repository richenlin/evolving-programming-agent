#!/usr/bin/env python3
"""
Unified Knowledge Query — CodeGraph SQLite FTS5.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

try:
    import jieba
    HAS_JIEBA = True
except ImportError:
    HAS_JIEBA = False

try:
    from core.config import (
        FUZZY_MATCH_THRESHOLD,
        RELEVANCE_WEIGHTS,
        RECENCY_DECAY_DAYS,
        USAGE_NORMALIZATION,
        TOP_K_RESULTS,
        CATEGORY_DIRS,
        FUZZY_MATCH_EFF_SCALE,
        FUZZY_MATCH_REC_SCALE,
    )
except ImportError:
    FUZZY_MATCH_THRESHOLD = 0.72
    RELEVANCE_WEIGHTS = {
        "trigger_match": 0.4,
        "effectiveness": 0.3,
        "recency": 0.2,
        "usage": 0.1,
    }
    RECENCY_DECAY_DAYS = 365.0
    USAGE_NORMALIZATION = 100.0
    TOP_K_RESULTS = 10
    CATEGORY_DIRS = {
        "experience": "experiences",
        "tech-stack": "tech-stacks",
        "scenario": "scenarios",
        "problem": "problems",
        "testing": "testing",
        "pattern": "patterns",
        "skill": "skills",
    }
    FUZZY_MATCH_EFF_SCALE = 0.35
    FUZZY_MATCH_REC_SCALE = 0.50

from backend import get_db

# Synonym map trimmed — full map preserved in repo history; key groups kept for recall
SYNONYM_MAP: Dict[str, List[str]] = {
    "优化": ["optimize", "optimization", "performance", "性能"],
    "optimize": ["优化", "optimization", "performance"],
    "错误": ["error", "bug", "issue", "报错"],
    "error": ["错误", "bug", "issue"],
    "bug": ["错误", "error", "issue"],
    "测试": ["test", "testing", "spec"],
    "test": ["测试", "testing"],
    "跨域": ["cors", "cross-origin", "proxy"],
    "cors": ["跨域", "cross-origin"],
    "认证": ["auth", "authentication", "登录", "login"],
    "auth": ["认证", "login"],
    "部署": ["deploy", "deployment", "ci", "cd"],
    "deploy": ["部署", "deployment"],
    "数据库": ["database", "db", "sql"],
    "database": ["数据库", "db"],
    "接口": ["api", "endpoint", "rest"],
    "api": ["接口", "endpoint"],
    "重构": ["refactor", "restructure"],
    "refactor": ["重构"],
    "异步": ["async", "promise", "await"],
    "async": ["异步", "promise"],
}


def expand_with_synonyms(tokens: List[str], max_expansions: int = 3, max_total: int = 30) -> List[str]:
    expanded = list(tokens)
    for token in tokens:
        if len(expanded) >= max_total:
            break
        for syn in SYNONYM_MAP.get(token.lower(), [])[:max_expansions]:
            if len(expanded) >= max_total:
                break
            if syn.lower() not in {t.lower() for t in expanded}:
                expanded.append(syn)
    return expanded


def tokenize(text: str) -> List[str]:
    if HAS_JIEBA:
        tokens = jieba.lcut(text)
        return [t for t in tokens if t.strip() and re.search(r"[\w\u4e00-\u9fff]", t)]
    return re.findall(r"[\u4e00-\u9fff]+|[a-zA-Z0-9]+", text.lower())


def fuzzy_match(
    query_tokens: List[str],
    trigger_tokens: List[str],
    threshold: float = FUZZY_MATCH_THRESHOLD,
) -> float:
    max_score = 0.0
    for query in query_tokens:
        for trigger in trigger_tokens:
            score = SequenceMatcher(None, query.lower(), trigger.lower()).ratio()
            max_score = max(max_score, score)
            if max_score == 1.0:
                return 1.0
    return max_score if max_score >= threshold else 0.0


def compute_relevance(entry: Dict[str, Any], query_tokens: List[str]) -> float:
    raw_match = entry.get("_match_score", 0)
    is_semantic = entry.get("_match_type") in ("semantic", "fts5")

    if raw_match == 0 and not is_semantic:
        return 0.0

    match_score = min(1.0, raw_match / 3.0) if not is_semantic else float(entry.get("_relevance_score", 0.5))
    effectiveness = entry.get("effectiveness", 0.5)

    last_used_str = entry.get("last_used_at") or entry.get("created_at")
    if last_used_str:
        try:
            last_used = datetime.fromisoformat(last_used_str.replace("Z", "+00:00"))
            days_since_use = (datetime.now(last_used.tzinfo) - last_used).days
            recency = max(0.0, 1.0 - (days_since_use / RECENCY_DECAY_DAYS))
        except (ValueError, TypeError, OSError):
            recency = 0.5
    else:
        recency = 0.5

    usage_normalized = min(1.0, entry.get("usage_count", 0) / USAGE_NORMALIZATION)

    if not is_semantic and raw_match < 2:
        eff_weight = RELEVANCE_WEIGHTS["effectiveness"] * FUZZY_MATCH_EFF_SCALE
        rec_weight = RELEVANCE_WEIGHTS["recency"] * FUZZY_MATCH_REC_SCALE
    else:
        eff_weight = RELEVANCE_WEIGHTS["effectiveness"]
        rec_weight = RELEVANCE_WEIGHTS["recency"]

    if is_semantic:
        return (
            match_score * 0.6
            + effectiveness * eff_weight
            + recency * rec_weight
            + usage_normalized * RELEVANCE_WEIGHTS["usage"]
        )

    return (
        match_score * RELEVANCE_WEIGHTS["trigger_match"]
        + effectiveness * eff_weight
        + recency * rec_weight
        + usage_normalized * RELEVANCE_WEIGHTS["usage"]
    )


def _score_triggers(entry_triggers: List[str], query_triggers: List[str]) -> float:
    score = 0.0
    entry_lower = {t.lower() for t in entry_triggers}
    for qt in query_triggers:
        ql = qt.lower()
        if ql in entry_lower:
            score += 3
            continue
        for et in entry_lower:
            if ql in et or et in ql:
                score += 2
                break
        else:
            fz = fuzzy_match(tokenize(ql), [et for et in entry_lower])
            if fz > 0:
                score += fz
    return score


def _hits_to_entries(hits: List[Dict[str, Any]], triggers: List[str]) -> List[Dict[str, Any]]:
    results: List[Dict[str, Any]] = []
    for hit in hits:
        ent = hit.get("_entry")
        if not ent:
            continue
        entry = dict(ent)
        entry["_match_score"] = _score_triggers(entry.get("triggers", []), triggers) or hit.get("score", 0) * 3
        entry["_match_type"] = hit.get("source", "fts5")
        entry["_relevance_score"] = compute_relevance(entry, triggers)
        results.append(entry)
    results.sort(key=lambda x: x.get("_relevance_score", 0), reverse=True)
    return results


def batch_update_usage(entries: List[tuple]) -> None:
    """Legacy API — increment usage in SQLite."""
    seen: Set[str] = set()
    for item in entries:
        entry = item[1] if isinstance(item, tuple) else item
        eid = entry.get("id")
        if eid and eid not in seen:
            seen.add(eid)
            project_path = entry.get("project_path")
            try:
                get_db(project_path).increment_usage(eid)
            except Exception:
                pass


def query_by_triggers(
    triggers: List[str],
    limit: int = TOP_K_RESULTS,
    use_synonyms: bool = True,
    project_path: Optional[str] = None,
) -> List[Dict[str, Any]]:
    if use_synonyms:
        triggers = expand_with_synonyms(triggers, max_expansions=2)
    db = get_db(project_path)
    query_text = " ".join(triggers)
    hits = db.search_entries(query_text, limit=limit * 2)
    results = _hits_to_entries(hits, triggers)[:limit]
    if results:
        batch_update_usage([(None, e) for e in results])
    return results


def query_by_triggers_in(
    triggers: List[str],
    kb_root: Optional[Path] = None,
    limit: int = TOP_K_RESULTS,
    use_synonyms: bool = True,
    project_path: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Project-scoped trigger query. kb_root ignored (SQLite-only)."""
    if project_path is None and kb_root is not None:
        p = Path(kb_root)
        if p.name == "codegraph" and p.parent.name == ".opencode":
            project_path = str(p.parent.parent)
    return query_by_triggers(triggers, limit=limit, use_synonyms=use_synonyms, project_path=project_path)


def query_semantic(
    query_text: str,
    limit: int = TOP_K_RESULTS,
    project_path: Optional[str] = None,
) -> List[Dict[str, Any]]:
    db = get_db(project_path)
    hits = db.search_entries(query_text, limit=limit)
    results: List[Dict[str, Any]] = []
    for hit in hits:
        ent = hit.get("_entry")
        if not ent:
            continue
        entry = dict(ent)
        entry["_relevance_score"] = hit.get("score", 0.5)
        entry["_match_type"] = "semantic"
        entry["_match_score"] = hit.get("score", 0.5) * 3
        results.append(entry)
    if results:
        batch_update_usage([(None, e) for e in results])
    return results


def query_hybrid(
    query_text: str,
    limit: int = TOP_K_RESULTS,
    project_path: Optional[str] = None,
) -> List[Dict[str, Any]]:
    tokens = query_text.replace(",", " ").split()
    keyword_results = query_by_triggers(tokens, limit=limit, project_path=project_path)
    semantic_results = query_semantic(query_text, limit=limit, project_path=project_path)

    seen: Set[str] = set()
    merged: List[Dict[str, Any]] = []
    for entry in keyword_results + semantic_results:
        eid = entry.get("id", "")
        if eid and eid not in seen:
            seen.add(eid)
            merged.append(entry)

    merged.sort(key=lambda x: x.get("_relevance_score", 0), reverse=True)
    return merged[:limit]


def query_by_category(
    category: str,
    limit: int = 20,
    project_path: Optional[str] = None,
) -> List[Dict[str, Any]]:
    return get_db(project_path).list_entries(category=category, limit=limit)


def query_by_tags(tags: List[str], limit: int = 20, project_path: Optional[str] = None) -> List[Dict[str, Any]]:
    tag_set = {t.lower() for t in tags}
    results = []
    for entry in get_db(project_path).list_entries(limit=500):
        entry_tags = {t.lower() for t in entry.get("tags", [])}
        if tag_set & entry_tags:
            results.append(entry)
        if len(results) >= limit:
            break
    return results


def search_content(keyword: str, limit: int = 10, project_path: Optional[str] = None) -> List[Dict[str, Any]]:
    return query_semantic(keyword, limit=limit, project_path=project_path)


def get_entry(entry_id: str, project_path: Optional[str] = None) -> Optional[Dict[str, Any]]:
    return get_db(project_path).get_entry(entry_id)


def get_global_index() -> Dict[str, Any]:
    stats = get_stats()
    return {
        "version": "codegraph-2",
        "last_updated": datetime.now().isoformat(),
        "stats": stats.get("stats", {}),
        "trigger_index": {},
    }


def get_stats(project_path: Optional[str] = None) -> Dict[str, Any]:
    db_stats = get_db(project_path).stats()
    return {
        "version": "codegraph-2",
        "last_updated": datetime.now().isoformat(),
        "stats": {
            "total_entries": db_stats.get("entries", 0),
            "by_category": db_stats.get("by_category", {}),
        },
        "codegraph": db_stats,
        "trigger_count": 0,
        "recent_entries": [r.get("name") for r in db_stats.get("recently_added", [])],
    }


def format_output(data: Any, fmt: str = "json") -> str:
    if fmt == "json":
        return json.dumps(data, indent=2, ensure_ascii=False)
    if fmt == "markdown" and isinstance(data, list):
        lines = []
        for entry in data:
            lines.append(f"### {entry.get('name', 'Unknown')}")
            lines.append(f"- **Category**: {entry.get('category', 'N/A')}")
            lines.append("")
        return "\n".join(lines)
    return str(data)


def main():
    parser = argparse.ArgumentParser(description="Query knowledge (CodeGraph SQLite)")
    parser.add_argument("--trigger", "-t")
    parser.add_argument("--category", "-c", choices=list(CATEGORY_DIRS.keys()))
    parser.add_argument("--tags")
    parser.add_argument("--search", "-s")
    parser.add_argument("--id")
    parser.add_argument("--stats", action="store_true")
    parser.add_argument("--limit", "-l", type=int, default=10)
    parser.add_argument("--format", "-f", choices=["json", "markdown"], default="json")
    parser.add_argument("--mode", "-m", choices=["keyword", "semantic", "hybrid"], default="keyword")
    parser.add_argument("--project", "-p")
    args = parser.parse_args()

    pp = args.project

    if args.stats:
        result = get_stats(pp)
    elif args.id:
        result = get_entry(args.id, pp)
    elif args.trigger:
        triggers = [t.strip() for t in args.trigger.split(",")]
        query_text = " ".join(triggers)
        if args.mode == "semantic":
            result = query_semantic(query_text, args.limit, pp)
        elif args.mode == "hybrid":
            result = query_hybrid(query_text, args.limit, pp)
        else:
            result = query_by_triggers(triggers, args.limit, project_path=pp)
    elif args.category:
        result = query_by_category(args.category, args.limit, pp)
    elif args.tags:
        result = query_by_tags([t.strip() for t in args.tags.split(",")], args.limit, pp)
    elif args.search:
        result = search_content(args.search, args.limit, pp)
    else:
        result = get_stats(pp)

    print(format_output(result, args.format))


if __name__ == "__main__":
    main()
