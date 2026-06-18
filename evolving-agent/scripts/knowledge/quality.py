#!/usr/bin/env python3
"""Knowledge entry quality gates — storage and retrieval."""

from __future__ import annotations

import hashlib
import re
from typing import Any, Dict, List, Optional

LOW_VALUE_NAME_RE = re.compile(
    r"^(review\s*发现|review发现|发现|待补充|todo|tbd|n/?a|fix|修复|test\s*entry)$",
    re.IGNORECASE,
)

META_JARGON_RE = re.compile(
    r"(BuildOpts|experience\s*slot|callback\s*注入|storeOf|globalOf|"
    r"hybrid\s*retriever|extension\.ts|experience\s*回调|priority\s*等于\s*\d+)",
    re.IGNORECASE,
)

GENERIC_BOILERPLATE_NAMES = frozenset({
    "pytest best practices",
    "json test",
    "cli test entry",
    "markdown test",
})


def _norm(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "").strip().lower())


def content_fingerprint(entry: Dict[str, Any]) -> str:
    content = entry.get("content") or {}
    parts = [
        entry.get("category", ""),
        _norm(entry.get("name", "")),
        _norm(content.get("solution", "")),
        _norm(content.get("description", "")),
    ]
    raw = "|".join(parts)
    return hashlib.md5(raw.encode()).hexdigest()[:16]


def informative_length(entry: Dict[str, Any]) -> int:
    content = entry.get("content") or {}
    name = _norm(entry.get("name", ""))
    pieces: List[str] = []
    for key in ("description", "solution", "context", "typical_approach"):
        val = content.get(key, "")
        if isinstance(val, str) and val.strip():
            pieces.append(_norm(val))
    for key in ("symptoms", "pitfalls", "best_practices", "root_causes"):
        vals = content.get(key)
        if isinstance(vals, list):
            pieces.extend(_norm(str(x)) for x in vals if x)
    combined = " ".join(p for p in pieces if p)
    if combined == name:
        return len(name)
    return len(combined)


def is_low_value_entry(entry: Dict[str, Any]) -> bool:
    """True if entry should not be stored or shown in agent context."""
    name = (entry.get("name") or "").strip()
    if not name:
        return True

    if LOW_VALUE_NAME_RE.match(name.strip()):
        return True

    if _norm(name) in GENERIC_BOILERPLATE_NAMES:
        return True

    content = entry.get("content") or {}
    desc = content.get("description", "")
    solution = content.get("solution", "")
    symptoms = content.get("symptoms") or []

    blob = f"{name} {desc} {solution}"
    if META_JARGON_RE.search(blob):
        return True

    # Name repeated everywhere with no extra detail
    if _norm(desc) == _norm(name) and _norm(solution) == _norm(name):
        return True
    if symptoms and len(symptoms) == 1 and _norm(str(symptoms[0])) == _norm(name):
        if informative_length(entry) < 30:
            return True

    # Empty shell: no real fields beyond the title
    has_lists = any(
        isinstance(content.get(k), list) and content.get(k)
        for k in ("symptoms", "pitfalls", "best_practices", "root_causes", "solutions", "steps")
    )
    has_text = any(
        isinstance(content.get(k), str) and len(content.get(k, "").strip()) > 8
        for k in ("description", "solution", "context", "typical_approach", "tech_name", "problem_name")
    )
    if not has_lists and not has_text and informative_length(entry) < 15:
        return True

    if len(name) < 10 and not has_text and not has_lists:
        return True

    return False


def entry_relevance_score(entry: Dict[str, Any], mode: str) -> float:
    if mode in ("semantic", "hybrid"):
        return float(entry.get("_relevance_score", 0))
    return float(entry.get("_match_score", 0))


def filter_entries_for_display(
    entries: List[Dict[str, Any]],
    *,
    mode: str = "hybrid",
    min_relevance: float,
    max_items: int,
    seen_fingerprints: Optional[set] = None,
) -> List[Dict[str, Any]]:
    """Filter, dedupe by content fingerprint, and cap result count."""
    seen_fp = seen_fingerprints if seen_fingerprints is not None else set()
    seen_id: set = set()
    kept: List[Dict[str, Any]] = []

    ranked = sorted(
        entries,
        key=lambda e: entry_relevance_score(e, mode),
        reverse=True,
    )
    for entry in ranked:
        eid = entry.get("id", "")
        if eid and eid in seen_id:
            continue
        if is_low_value_entry(entry):
            continue
        score = entry_relevance_score(entry, mode)
        if score < min_relevance:
            continue
        fp = content_fingerprint(entry)
        if fp in seen_fp:
            continue
        if eid:
            seen_id.add(eid)
        seen_fp.add(fp)
        kept.append(entry)
        if len(kept) >= max_items:
            break
    return kept
