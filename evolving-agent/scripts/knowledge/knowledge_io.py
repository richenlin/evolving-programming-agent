#!/usr/bin/env python3
"""Knowledge import/export — JSON bundle ↔ CodeGraph SQLite."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from backend import get_db
from store import store_knowledge


def export_all(
    output_path: str,
    format: str = "json",
    project_path: Optional[str] = None,
) -> int:
    entries = get_db(project_path).list_entries(limit=100000)
    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)

    if format == "json":
        payload = {"version": "codegraph-export-1", "entries": entries}
        out.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    else:
        raise ValueError(f"Unsupported export format: {format}")

    return len(entries)


def import_all(
    input_path: str,
    merge_strategy: str = "skip",
    project_path: Optional[str] = None,
) -> Dict[str, int]:
    path = Path(input_path)
    data = json.loads(path.read_text(encoding="utf-8"))

    if isinstance(data, list):
        entries = data
    elif isinstance(data, dict) and "entries" in data:
        entries = data["entries"]
    else:
        entries = [data]

    stats = {"imported": 0, "skipped": 0, "overwritten": 0}
    db = get_db(project_path)

    for raw in entries:
        eid = raw.get("id")
        if not eid:
            stats["skipped"] += 1
            continue
        existing = db.get_entry(eid)
        if existing and merge_strategy == "skip":
            stats["skipped"] += 1
            continue

        store_knowledge(
            category=raw.get("category", "experience"),
            name=raw.get("name", "Unnamed"),
            content=raw.get("content", {}),
            sources=raw.get("sources"),
            tags=raw.get("tags"),
            triggers=raw.get("triggers"),
            entry_id=eid,
            project_path=project_path,
            _db=db,
        )
        if existing:
            stats["overwritten"] += 1
        else:
            stats["imported"] += 1

    return stats
