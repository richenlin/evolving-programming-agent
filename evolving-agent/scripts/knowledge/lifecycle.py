#!/usr/bin/env python3
"""Knowledge lifecycle — decay / gc on CodeGraph SQLite."""

from __future__ import annotations

import sys
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

try:
    from core.config import DECAY_DAYS_THRESHOLD, DECAY_RATE, GC_EFFECTIVENESS_THRESHOLD
except ImportError:
    DECAY_DAYS_THRESHOLD = 90
    DECAY_RATE = 0.1
    GC_EFFECTIVENESS_THRESHOLD = 0.1

from backend import get_db


def decay_unused(
    days_threshold: int = DECAY_DAYS_THRESHOLD,
    decay_rate: float = DECAY_RATE,
    project_path: Optional[str] = None,
) -> List[Dict[str, Any]]:
    db = get_db(project_path)
    threshold_date = datetime.now() - timedelta(days=days_threshold)
    affected: List[Dict[str, Any]] = []

    for entry in db.list_entries(limit=10000):
        last_used_str = entry.get("last_used_at") or entry.get("created_at")
        if not last_used_str:
            continue
        try:
            last_used = datetime.fromisoformat(last_used_str.replace("Z", "+00:00"))
        except (ValueError, AttributeError):
            continue
        if last_used > threshold_date:
            continue

        current = entry.get("effectiveness", 0.5)
        new_eff = max(0.0, current - decay_rate)
        if new_eff == current:
            continue

        db.patch_effectiveness(
            entry["id"],
            new_eff,
            last_decayed_at=datetime.now().isoformat(),
        )
        affected.append({
            "id": entry.get("id"),
            "name": entry.get("name"),
            "old_effectiveness": current,
            "new_effectiveness": new_eff,
        })

    return affected


def get_stale_entries(
    effectiveness_threshold: float = GC_EFFECTIVENESS_THRESHOLD,
    project_path: Optional[str] = None,
) -> List[Dict[str, Any]]:
    return [
        e for e in get_db(project_path).list_entries(limit=10000)
        if e.get("effectiveness", 0.5) < effectiveness_threshold
    ]


def gc(
    threshold: float = GC_EFFECTIVENESS_THRESHOLD,
    dry_run: bool = False,
    project_path: Optional[str] = None,
) -> List[Dict[str, Any]]:
    stale = get_stale_entries(threshold, project_path)
    if not dry_run:
        db = get_db(project_path)
        for entry in stale:
            eid = entry.get("id")
            if eid:
                db.delete_entry(eid)
    return stale


if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("action", choices=["decay", "gc"])
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--project")
    args = p.parse_args()
    if args.action == "decay":
        for e in decay_unused(project_path=args.project):
            print(e, file=sys.stderr)
    else:
        for e in gc(dry_run=args.dry_run, project_path=args.project):
            print(e.get("id"), e.get("name"))
