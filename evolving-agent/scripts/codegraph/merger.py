#!/usr/bin/env python3
"""KnowledgeMerger — token-budget merge for agent context output."""

from __future__ import annotations

from typing import Any, Dict, List, Optional


def estimate_tokens(text: str) -> int:
    """Rough token estimate (chars / 4)."""
    return max(1, len(text) // 4)


def truncate_to_tokens(text: str, max_tokens: int) -> str:
    if max_tokens <= 0:
        return ""
    max_chars = max_tokens * 4
    if len(text) <= max_chars:
        return text
    truncated = text[:max_chars]
    if "。" in truncated:
        truncated = truncated.rsplit("。", 1)[0] + "。"
    elif "\n" in truncated:
        truncated = truncated.rsplit("\n", 1)[0]
    return truncated.rstrip() + "…"


def merge_sections(
    sections: List[Dict[str, Any]],
    *,
    budget_tokens: int = 1500,
    graph_ratio: float = 0.4,
) -> Dict[str, Any]:
    """
    Merge labeled sections under a token budget.

    Each section: {"id", "priority", "kind": "graph|experience", "text", "meta"?}
    Higher priority sections are included first.
    """
    if budget_tokens <= 0:
        return {"text": "", "tokens_used": 0, "sections_included": [], "sections_dropped": []}

    graph_budget = int(budget_tokens * graph_ratio)
    exp_budget = budget_tokens - graph_budget

    graph_sections = sorted(
        [s for s in sections if s.get("kind") == "graph"],
        key=lambda x: x.get("priority", 0),
        reverse=True,
    )
    exp_sections = sorted(
        [s for s in sections if s.get("kind") != "graph"],
        key=lambda x: x.get("priority", 0),
        reverse=True,
    )

    included: List[str] = []
    dropped: List[str] = []
    parts: List[str] = []
    graph_used = 0
    exp_used = 0

    for sec in graph_sections:
        sid = sec.get("id", "graph")
        text = sec.get("text", "").strip()
        if not text:
            continue
        need = estimate_tokens(text)
        if graph_used + need <= graph_budget:
            parts.append(text)
            graph_used += need
            included.append(sid)
        else:
            remaining = graph_budget - graph_used
            if remaining >= 20:
                clipped = truncate_to_tokens(text, remaining)
                parts.append(clipped)
                graph_used += estimate_tokens(clipped)
                included.append(f"{sid}(truncated)")
            else:
                dropped.append(sid)

    for sec in exp_sections:
        sid = sec.get("id", "experience")
        text = sec.get("text", "").strip()
        if not text:
            continue
        need = estimate_tokens(text)
        if exp_used + need <= exp_budget:
            parts.append(text)
            exp_used += need
            included.append(sid)
        else:
            remaining = exp_budget - exp_used
            if remaining >= 20:
                clipped = truncate_to_tokens(text, remaining)
                parts.append(clipped)
                exp_used += estimate_tokens(clipped)
                included.append(f"{sid}(truncated)")
            else:
                dropped.append(sid)

    merged_text = "\n\n".join(parts).strip()
    return {
        "text": merged_text,
        "tokens_used": graph_used + exp_used,
        "graph_tokens": graph_used,
        "experience_tokens": exp_used,
        "budget_tokens": budget_tokens,
        "sections_included": included,
        "sections_dropped": dropped,
    }


def format_entry_summary(
    content: Dict[str, Any],
    *,
    max_tokens: int = 80,
) -> str:
    """Return compact summary for an experience entry (summary-first)."""
    if not isinstance(content, dict):
        return ""

    summary = content.get("summary")
    if isinstance(summary, str) and summary.strip():
        return truncate_to_tokens(summary.strip(), max_tokens)

    for field in ("solution", "description", "typical_approach"):
        val = content.get(field)
        if isinstance(val, str) and val.strip():
            return truncate_to_tokens(val.strip(), max_tokens)

    symptoms = content.get("symptoms")
    if isinstance(symptoms, list) and symptoms:
        return truncate_to_tokens("; ".join(str(s) for s in symptoms[:2]), max_tokens)

    return ""
