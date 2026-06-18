"""Shared helpers for knowledge SQLite tests."""

from datetime import datetime


def seed_entry(kb_db, **overrides):
    now = datetime.now().isoformat()
    entry = {
        "id": overrides.get("id", "experience-test-001"),
        "category": overrides.get("category", "experience"),
        "name": overrides.get("name", "Test Entry"),
        "content": overrides.get(
            "content",
            {"description": "desc", "context": "", "solution": "sol", "pitfalls": []},
        ),
        "triggers": overrides.get("triggers", []),
        "tags": overrides.get("tags", []),
        "sources": overrides.get("sources", []),
        "scope": overrides.get("scope", "global"),
        "codegraph_type": overrides.get("codegraph_type", "solution"),
        "effectiveness": overrides.get("effectiveness", 0.5),
        "usage_count": overrides.get("usage_count", 0),
        "last_used_at": overrides.get("last_used_at"),
        "last_decayed_at": overrides.get("last_decayed_at"),
        "project_path": overrides.get("project_path"),
        "created_at": overrides.get("created_at", now),
        "updated_at": now,
    }
    kb_db.upsert_entry(entry)
    return entry
