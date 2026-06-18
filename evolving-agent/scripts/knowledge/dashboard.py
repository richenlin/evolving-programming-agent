#!/usr/bin/env python3
"""Knowledge dashboard — CodeGraph SQLite stats."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Optional

from backend import get_db


def generate_stats(project_path: Optional[str] = None) -> Dict[str, Any]:
    db_stats = get_db(project_path).stats()
    by_category = db_stats.get("by_category", {})
    return {
        "total_entries": db_stats.get("entries", 0),
        "by_category": by_category,
        "top_used": db_stats.get("top_used", []),
        "recently_added": db_stats.get("recently_added", []),
        "stale_count": db_stats.get("stale_count", 0),
        "avg_effectiveness": db_stats.get("avg_effectiveness", 0.0),
        "codegraph": db_stats,
    }


def format_dashboard(stats: Dict[str, Any]) -> str:
    if stats["total_entries"] == 0:
        return "Knowledge base is empty"

    lines = [
        "=" * 50,
        "Knowledge Base Dashboard (CodeGraph SQLite)",
        "=" * 50,
        f"Total entries: {stats['total_entries']}",
        f"Avg effectiveness: {stats['avg_effectiveness']:.3f}",
    ]
    if stats["stale_count"] > 0:
        lines.append(f"Stale entries (effectiveness < 0.2): {stats['stale_count']}")
    cg = stats.get("codegraph", {})
    if cg.get("symbols"):
        lines.append(f"Indexed symbols: {cg['symbols']}")
    lines.append("")

    lines.append("Category Distribution:")
    max_count = max(stats["by_category"].values()) if stats["by_category"] else 1
    bar_width = 20
    for category, count in stats["by_category"].items():
        if count == 0:
            continue
        filled = int((count / max(max_count, 1)) * bar_width)
        bar = "█" * filled + "░" * (bar_width - filled)
        lines.append(f"  {category:<12} [{bar}] {count}")
    lines.append("")

    if stats["top_used"]:
        lines.append("Top Used Entries:")
        for item in stats["top_used"][:5]:
            lines.append(f"  {item['name'][:35]:<35} {item['usage_count']:>5}")
        lines.append("")

    if stats["recently_added"]:
        lines.append("Recently Added:")
        for item in stats["recently_added"][:5]:
            created = (item.get("created_at") or "")[:10]
            lines.append(f"  [{created}] {item['name']}")

    lines.append("=" * 50)
    return "\n".join(lines)


generate_stats_with_codegraph = generate_stats
