#!/usr/bin/env python3
"""
CodeGraph SQLite store — symbols + knowledge entries (FTS5 + lifecycle fields).

Storage: $PROJECT/.opencode/codegraph/knowledge.db
Global:  ~/.config/opencode/codegraph/knowledge.db
"""

from __future__ import annotations

import json
import re
import sqlite3
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterator, List, Optional, Set

from codegraph.paths import get_global_knowledge_db_path, get_knowledge_db_path

_SCHEMA = """
PRAGMA journal_mode=WAL;

CREATE TABLE IF NOT EXISTS meta (
    key TEXT PRIMARY KEY,
    value TEXT
);

CREATE TABLE IF NOT EXISTS symbols (
    id TEXT PRIMARY KEY,
    file TEXT NOT NULL,
    name TEXT NOT NULL,
    kind TEXT NOT NULL,
    line INTEGER NOT NULL,
    end_line INTEGER,
    language TEXT
);

CREATE VIRTUAL TABLE IF NOT EXISTS symbols_fts USING fts5(
    symbol_id UNINDEXED,
    name,
    file,
    kind,
    tokenize='unicode61 remove_diacritics 0'
);

CREATE TABLE IF NOT EXISTS entries (
    id TEXT PRIMARY KEY,
    category TEXT NOT NULL,
    name TEXT NOT NULL,
    content_json TEXT NOT NULL,
    scope TEXT DEFAULT 'global',
    codegraph_type TEXT,
    sources_json TEXT,
    tags_json TEXT,
    triggers_json TEXT,
    effectiveness REAL DEFAULT 0.5,
    usage_count INTEGER DEFAULT 0,
    last_used_at TEXT,
    last_decayed_at TEXT,
    project_path TEXT,
    search_text TEXT,
    created_at TEXT,
    updated_at TEXT
);

CREATE VIRTUAL TABLE IF NOT EXISTS entries_fts USING fts5(
    entry_id UNINDEXED,
    name,
    content,
    tags,
    tokenize='unicode61 remove_diacritics 0'
);
"""

_SCHEMA_V3 = """
CREATE TABLE IF NOT EXISTS file (
    path TEXT PRIMARY KEY,
    lang TEXT,
    size INTEGER,
    mtime REAL,
    hash TEXT,
    indexed_at TEXT
);

CREATE TABLE IF NOT EXISTS node (
    id TEXT PRIMARY KEY,
    kind TEXT NOT NULL,
    name TEXT NOT NULL,
    file TEXT,
    line INTEGER,
    end_line INTEGER,
    signature TEXT,
    summary TEXT,
    body TEXT,
    scope TEXT DEFAULT 'project',
    provenance TEXT,
    meta_json TEXT,
    effectiveness REAL DEFAULT 0.5,
    usage_count INTEGER DEFAULT 0,
    created_at TEXT,
    updated_at TEXT
);

CREATE TABLE IF NOT EXISTS edge (
    src TEXT NOT NULL,
    dst TEXT NOT NULL,
    kind TEXT NOT NULL,
    provenance TEXT,
    PRIMARY KEY (src, dst, kind)
);

CREATE VIRTUAL TABLE IF NOT EXISTS node_fts USING fts5(
    node_id UNINDEXED,
    name,
    file,
    kind,
    summary,
    tokenize='unicode61 remove_diacritics 0'
);
"""

_SCHEMA_VERSION = "3"


def _entry_search_text(
    name: str,
    content: Dict[str, Any],
    tags: List[str],
    triggers: Optional[List[str]] = None,
) -> str:
    parts = [name]
    if isinstance(content, dict):
        for k in ("description", "solution", "context", "typical_approach"):
            v = content.get(k)
            if isinstance(v, str):
                parts.append(v)
        for k in ("symptoms", "pitfalls", "best_practices", "conventions"):
            vals = content.get(k)
            if isinstance(vals, list):
                parts.extend(str(x) for x in vals)
    parts.extend(tags or [])
    parts.extend(triggers or [])
    return " ".join(parts)


def _row_to_entry(row: sqlite3.Row) -> Dict[str, Any]:
    keys = row.keys()
    return {
        "id": row["id"],
        "category": row["category"],
        "name": row["name"],
        "content": json.loads(row["content_json"]),
        "scope": row["scope"],
        "codegraph_type": row["codegraph_type"],
        "sources": json.loads(row["sources_json"] or "[]"),
        "tags": json.loads(row["tags_json"] or "[]"),
        "triggers": json.loads(row["triggers_json"] or "[]"),
        "effectiveness": row["effectiveness"],
        "usage_count": row["usage_count"],
        "last_used_at": row["last_used_at"],
        "last_decayed_at": row["last_decayed_at"],
        "project_path": row["project_path"],
        "anchor_node_ids": json.loads(row["anchor_node_ids_json"] or "[]") if "anchor_node_ids_json" in keys else [],
        "anchor_files": json.loads(row["anchor_files_json"] or "[]") if "anchor_files_json" in keys else [],
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
    }


def _row_to_node(row: sqlite3.Row) -> Dict[str, Any]:
    return {
        "id": row["id"],
        "kind": row["kind"],
        "name": row["name"],
        "file": row["file"],
        "line": row["line"],
        "end_line": row["end_line"],
        "signature": row["signature"],
        "summary": row["summary"],
        "body": row["body"],
        "scope": row["scope"],
        "provenance": row["provenance"],
        "meta": json.loads(row["meta_json"] or "{}"),
        "effectiveness": row["effectiveness"],
        "usage_count": row["usage_count"],
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
    }


class CodeGraphDB:
    """SQLite + FTS5 backend for CodeGraph."""

    def __init__(self, db_path: Path):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

    @contextmanager
    def _connect(self) -> Iterator[sqlite3.Connection]:
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()

    def _migrate(self, conn: sqlite3.Connection) -> None:
        cols = {r[1] for r in conn.execute("PRAGMA table_info(entries)").fetchall()}
        additions = {
            "triggers_json": "TEXT",
            "usage_count": "INTEGER DEFAULT 0",
            "last_used_at": "TEXT",
            "last_decayed_at": "TEXT",
            "project_path": "TEXT",
            "anchor_node_ids_json": "TEXT",
            "anchor_files_json": "TEXT",
        }
        for col, typedef in additions.items():
            if col not in cols:
                conn.execute(f"ALTER TABLE entries ADD COLUMN {col} {typedef}")
        conn.executescript(_SCHEMA_V3)

    def init(self) -> None:
        with self._connect() as conn:
            conn.executescript(_SCHEMA)
            self._migrate(conn)
            conn.execute(
                "INSERT OR REPLACE INTO meta(key, value) VALUES (?, ?)",
                ("schema_version", _SCHEMA_VERSION),
            )

    def replace_symbols(self, symbols: List[Dict[str, Any]], language: str = "") -> int:
        self.init()
        with self._connect() as conn:
            conn.execute("DELETE FROM symbols")
            try:
                conn.execute("DELETE FROM symbols_fts")
            except sqlite3.OperationalError:
                conn.execute("DROP TABLE IF EXISTS symbols_fts")
                conn.execute(
                    """CREATE VIRTUAL TABLE symbols_fts USING fts5(
                       symbol_id UNINDEXED, name, file, kind,
                       tokenize='unicode61 remove_diacritics 0')"""
                )
            count = 0
            for sym in symbols:
                sid = sym.get("id", "")
                if not sid:
                    continue
                conn.execute(
                    """INSERT INTO symbols(id, file, name, kind, line, end_line, language)
                       VALUES (?, ?, ?, ?, ?, ?, ?)""",
                    (
                        sid,
                        sym.get("file", ""),
                        sym.get("name", ""),
                        sym.get("kind", ""),
                        sym.get("line", 0),
                        sym.get("end_line", sym.get("line", 0)),
                        language or sym.get("language", ""),
                    ),
                )
                conn.execute(
                    "INSERT INTO symbols_fts(symbol_id, name, file, kind) VALUES (?, ?, ?, ?)",
                    (sid, sym.get("name", ""), sym.get("file", ""), sym.get("kind", "")),
                )
                count += 1
            conn.execute(
                "INSERT OR REPLACE INTO meta(key, value) VALUES (?, ?)",
                ("symbols_updated", datetime.now().isoformat()),
            )
            return count

    def search_symbols(self, query: str, limit: int = 8) -> List[Dict[str, Any]]:
        self.init()
        if not query.strip():
            return []
        tokens = [t for t in re.findall(r"[\w\u4e00-\u9fff]+", query) if len(t) >= 2]
        if not tokens:
            tokens = [query.strip()]
        fts_query = " OR ".join(f"{t}*" for t in tokens[:8])
        with self._connect() as conn:
            try:
                rows = conn.execute(
                    """
                    SELECT s.id, s.file, s.name, s.kind, s.line, s.end_line,
                           bm25(symbols_fts) AS rank
                    FROM symbols_fts f
                    JOIN symbols s ON s.id = f.symbol_id
                    WHERE symbols_fts MATCH ?
                    ORDER BY rank
                    LIMIT ?
                    """,
                    (fts_query, limit),
                ).fetchall()
            except sqlite3.OperationalError:
                return []
            return [
                {
                    "id": r["id"],
                    "file": r["file"],
                    "name": r["name"],
                    "kind": r["kind"],
                    "line": r["line"],
                    "end_line": r["end_line"],
                    "_fts_rank": r["rank"],
                }
                for r in rows
            ]

    def upsert_entry(self, entry: Dict[str, Any]) -> None:
        self.init()
        eid = entry["id"]
        name = entry.get("name", "")
        content = entry.get("content", {})
        tags = entry.get("tags", [])
        triggers = entry.get("triggers", [])
        search_text = _entry_search_text(name, content, tags, triggers)
        now = datetime.now().isoformat()

        with self._connect() as conn:
            existing = conn.execute(
                "SELECT * FROM entries WHERE id = ?", (eid,)
            ).fetchone()

            scope = entry.get("scope", "global")
            sources = entry.get("sources", [])
            cg_type = entry.get("codegraph_type", "")
            effectiveness = entry.get("effectiveness", 0.5)
            usage_count = entry.get("usage_count", 0)
            last_used = entry.get("last_used_at")
            last_decayed = entry.get("last_decayed_at")
            project_path = entry.get("project_path")
            anchor_nodes = json.dumps(entry.get("anchor_node_ids", []), ensure_ascii=False)
            anchor_files = json.dumps(entry.get("anchor_files", []), ensure_ascii=False)

            if existing:
                usage_count = entry.get("usage_count", existing["usage_count"] or 0)
                effectiveness = entry.get("effectiveness", existing["effectiveness"])
                created_at = existing["created_at"]
                if sources and existing["sources_json"]:
                    merged = list(set(json.loads(existing["sources_json"]) + sources))
                    sources = merged
                conn.execute(
                    """UPDATE entries SET category=?, name=?, content_json=?, scope=?,
                       codegraph_type=?, sources_json=?, tags_json=?, triggers_json=?,
                       search_text=?, effectiveness=?, usage_count=?,
                       last_used_at=?, last_decayed_at=?, project_path=?,
                       anchor_node_ids_json=?, anchor_files_json=?, updated_at=?
                       WHERE id=?""",
                    (
                        entry.get("category", ""),
                        name,
                        json.dumps(content, ensure_ascii=False),
                        scope,
                        cg_type,
                        json.dumps(sources, ensure_ascii=False),
                        json.dumps(tags, ensure_ascii=False),
                        json.dumps(triggers, ensure_ascii=False),
                        search_text,
                        effectiveness,
                        usage_count,
                        last_used or existing["last_used_at"],
                        last_decayed or existing["last_decayed_at"],
                        project_path or existing["project_path"],
                        anchor_nodes,
                        anchor_files,
                        now,
                        eid,
                    ),
                )
                conn.execute("DELETE FROM entries_fts WHERE entry_id = ?", (eid,))
            else:
                conn.execute(
                    """INSERT INTO entries
                       (id, category, name, content_json, scope, codegraph_type,
                        sources_json, tags_json, triggers_json, effectiveness,
                        usage_count, last_used_at, last_decayed_at, project_path,
                        anchor_node_ids_json, anchor_files_json,
                        search_text, created_at, updated_at)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        eid,
                        entry.get("category", ""),
                        name,
                        json.dumps(content, ensure_ascii=False),
                        scope,
                        cg_type,
                        json.dumps(sources, ensure_ascii=False),
                        json.dumps(tags, ensure_ascii=False),
                        json.dumps(triggers, ensure_ascii=False),
                        effectiveness,
                        usage_count,
                        last_used,
                        last_decayed,
                        project_path,
                        anchor_nodes,
                        anchor_files,
                        search_text,
                        entry.get("created_at", now),
                        now,
                    ),
                )

            conn.execute(
                "INSERT INTO entries_fts(entry_id, name, content, tags) VALUES (?, ?, ?, ?)",
                (eid, name, search_text, " ".join(tags + triggers)),
            )

    def search_entries(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        self.init()
        if not query.strip():
            return []
        tokens = [t for t in re.findall(r"[\w\u4e00-\u9fff]+", query) if len(t) >= 2]
        if not tokens:
            tokens = [query.strip()]
        fts_query = " OR ".join(f"{t}*" for t in tokens[:8])
        with self._connect() as conn:
            try:
                rows = conn.execute(
                    """
                    SELECT e.*, bm25(entries_fts) AS rank
                    FROM entries_fts f
                    JOIN entries e ON e.id = f.entry_id
                    WHERE entries_fts MATCH ?
                    ORDER BY rank
                    LIMIT ?
                    """,
                    (fts_query, limit),
                ).fetchall()
            except sqlite3.OperationalError:
                return []
            results = []
            for r in rows:
                ent = _row_to_entry(r)
                results.append({
                    "entry_id": ent["id"],
                    "category": ent["category"],
                    "name": ent["name"],
                    "content": ent["content"],
                    "scope": ent["scope"],
                    "type": ent.get("codegraph_type"),
                    "score": max(0.0, min(1.0, -float(r["rank"]) / 10.0)),
                    "source": "fts5",
                    "_entry": ent,
                })
            return results

    def get_entry(self, entry_id: str) -> Optional[Dict[str, Any]]:
        self.init()
        with self._connect() as conn:
            row = conn.execute("SELECT * FROM entries WHERE id = ?", (entry_id,)).fetchone()
            if not row:
                return None
            return _row_to_entry(row)

    def list_entries(
        self,
        category: Optional[str] = None,
        limit: int = 500,
    ) -> List[Dict[str, Any]]:
        self.init()
        with self._connect() as conn:
            if category:
                rows = conn.execute(
                    "SELECT * FROM entries WHERE category = ? ORDER BY updated_at DESC LIMIT ?",
                    (category, limit),
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT * FROM entries ORDER BY updated_at DESC LIMIT ?",
                    (limit,),
                ).fetchall()
            return [_row_to_entry(r) for r in rows]

    def increment_usage(self, entry_id: str) -> None:
        self.init()
        now = datetime.now().isoformat()
        with self._connect() as conn:
            conn.execute(
                """UPDATE entries SET usage_count = usage_count + 1,
                   last_used_at = ?, updated_at = ? WHERE id = ?""",
                (now, now, entry_id),
            )

    def delete_entry(self, entry_id: str) -> bool:
        self.init()
        with self._connect() as conn:
            row = conn.execute("SELECT id FROM entries WHERE id = ?", (entry_id,)).fetchone()
            if not row:
                return False
            conn.execute("DELETE FROM entries WHERE id = ?", (entry_id,))
            conn.execute("DELETE FROM entries_fts WHERE entry_id = ?", (entry_id,))
            return True

    def patch_effectiveness(
        self,
        entry_id: str,
        effectiveness: float,
        *,
        last_decayed_at: Optional[str] = None,
    ) -> bool:
        self.init()
        now = datetime.now().isoformat()
        with self._connect() as conn:
            if last_decayed_at:
                cur = conn.execute(
                    """UPDATE entries SET effectiveness=?, last_decayed_at=?,
                       updated_at=? WHERE id=?""",
                    (effectiveness, last_decayed_at, now, entry_id),
                )
            else:
                cur = conn.execute(
                    "UPDATE entries SET effectiveness=?, updated_at=? WHERE id=?",
                    (effectiveness, now, entry_id),
                )
            return cur.rowcount > 0

    # ------------------------------------------------------------------
    # CodeGraph v3 — node / edge / file
    # ------------------------------------------------------------------

    def upsert_file(self, file_row: Dict[str, Any]) -> None:
        self.init()
        now = datetime.now().isoformat()
        with self._connect() as conn:
            conn.execute(
                """INSERT INTO file(path, lang, size, mtime, hash, indexed_at)
                   VALUES (?, ?, ?, ?, ?, ?)
                   ON CONFLICT(path) DO UPDATE SET
                   lang=excluded.lang, size=excluded.size, mtime=excluded.mtime,
                   hash=excluded.hash, indexed_at=excluded.indexed_at""",
                (
                    file_row.get("path", ""),
                    file_row.get("lang", ""),
                    file_row.get("size", 0),
                    file_row.get("mtime"),
                    file_row.get("hash", ""),
                    now,
                ),
            )

    def upsert_node(self, node: Dict[str, Any]) -> None:
        self.init()
        now = datetime.now().isoformat()
        nid = node["id"]
        meta = json.dumps(node.get("meta", {}), ensure_ascii=False)
        with self._connect() as conn:
            existing = conn.execute("SELECT id FROM node WHERE id = ?", (nid,)).fetchone()
            if existing:
                conn.execute(
                    """UPDATE node SET kind=?, name=?, file=?, line=?, end_line=?,
                       signature=?, summary=?, body=?, scope=?, provenance=?,
                       meta_json=?, updated_at=? WHERE id=?""",
                    (
                        node.get("kind", ""),
                        node.get("name", ""),
                        node.get("file"),
                        node.get("line"),
                        node.get("end_line"),
                        node.get("signature"),
                        node.get("summary"),
                        node.get("body"),
                        node.get("scope", "project"),
                        node.get("provenance", "parsed"),
                        meta,
                        now,
                        nid,
                    ),
                )
                conn.execute("DELETE FROM node_fts WHERE node_id = ?", (nid,))
            else:
                conn.execute(
                    """INSERT INTO node
                       (id, kind, name, file, line, end_line, signature, summary, body,
                        scope, provenance, meta_json, created_at, updated_at)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        nid,
                        node.get("kind", ""),
                        node.get("name", ""),
                        node.get("file"),
                        node.get("line"),
                        node.get("end_line"),
                        node.get("signature"),
                        node.get("summary"),
                        node.get("body"),
                        node.get("scope", "project"),
                        node.get("provenance", "parsed"),
                        meta,
                        now,
                        now,
                    ),
                )
            conn.execute(
                "INSERT INTO node_fts(node_id, name, file, kind, summary) VALUES (?, ?, ?, ?, ?)",
                (
                    nid,
                    node.get("name", ""),
                    node.get("file") or "",
                    node.get("kind", ""),
                    node.get("summary") or "",
                ),
            )

    def upsert_edge(
        self,
        src: str,
        dst: str,
        kind: str,
        *,
        provenance: str = "heuristic",
    ) -> None:
        self.init()
        with self._connect() as conn:
            conn.execute(
                """INSERT OR IGNORE INTO edge(src, dst, kind, provenance)
                   VALUES (?, ?, ?, ?)""",
                (src, dst, kind, provenance),
            )

    def sync_resolver_batch(
        self,
        file_rows: List[Dict[str, Any]],
        nodes: List[Dict[str, Any]],
        edges: List[tuple],
    ) -> Dict[str, int]:
        """
        Batch sync resolver output in one transaction (avoids per-row connect overhead).

        edges: list of (src, dst, kind, provenance) tuples.
        """
        self.init()
        now = datetime.now().isoformat()
        with self._connect() as conn:
            conn.execute("DELETE FROM edge")
            for file_row in file_rows:
                conn.execute(
                    """INSERT INTO file(path, lang, size, mtime, hash, indexed_at)
                       VALUES (?, ?, ?, ?, ?, ?)
                       ON CONFLICT(path) DO UPDATE SET
                       lang=excluded.lang, size=excluded.size, mtime=excluded.mtime,
                       hash=excluded.hash, indexed_at=excluded.indexed_at""",
                    (
                        file_row.get("path", ""),
                        file_row.get("lang", ""),
                        file_row.get("size", 0),
                        file_row.get("mtime"),
                        file_row.get("hash", ""),
                        now,
                    ),
                )
            node_ids = [n["id"] for n in nodes if n.get("id")]
            existing_ids: Set[str] = set()
            if node_ids:
                placeholders = ",".join("?" * len(node_ids))
                rows = conn.execute(
                    f"SELECT id FROM node WHERE id IN ({placeholders})",
                    node_ids,
                ).fetchall()
                existing_ids = {r[0] for r in rows}
            for node in nodes:
                nid = node.get("id")
                if not nid:
                    continue
                meta = json.dumps(node.get("meta", {}), ensure_ascii=False)
                if nid in existing_ids:
                    conn.execute(
                        """UPDATE node SET kind=?, name=?, file=?, line=?, end_line=?,
                           signature=?, summary=?, body=?, scope=?, provenance=?,
                           meta_json=?, updated_at=? WHERE id=?""",
                        (
                            node.get("kind", ""),
                            node.get("name", ""),
                            node.get("file"),
                            node.get("line"),
                            node.get("end_line"),
                            node.get("signature"),
                            node.get("summary"),
                            node.get("body"),
                            node.get("scope", "project"),
                            node.get("provenance", "parsed"),
                            meta,
                            now,
                            nid,
                        ),
                    )
                    conn.execute("DELETE FROM node_fts WHERE node_id = ?", (nid,))
                else:
                    conn.execute(
                        """INSERT INTO node
                           (id, kind, name, file, line, end_line, signature, summary, body,
                            scope, provenance, meta_json, created_at, updated_at)
                           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                        (
                            nid,
                            node.get("kind", ""),
                            node.get("name", ""),
                            node.get("file"),
                            node.get("line"),
                            node.get("end_line"),
                            node.get("signature"),
                            node.get("summary"),
                            node.get("body"),
                            node.get("scope", "project"),
                            node.get("provenance", "parsed"),
                            meta,
                            now,
                            now,
                        ),
                    )
                conn.execute(
                    "INSERT INTO node_fts(node_id, name, file, kind, summary) VALUES (?, ?, ?, ?, ?)",
                    (
                        nid,
                        node.get("name", ""),
                        node.get("file") or "",
                        node.get("kind", ""),
                        node.get("summary") or "",
                    ),
                )
            for src, dst, kind, prov in edges:
                conn.execute(
                    """INSERT OR IGNORE INTO edge(src, dst, kind, provenance)
                       VALUES (?, ?, ?, ?)""",
                    (src, dst, kind, prov),
                )
        return {
            "files": len(file_rows),
            "nodes": len(nodes),
            "edges": len(edges),
        }

    def clear_edges(self) -> None:
        self.init()
        with self._connect() as conn:
            conn.execute("DELETE FROM edge")

    def search_nodes(self, query: str, limit: int = 8, kind: Optional[str] = None) -> List[Dict[str, Any]]:
        self.init()
        if not query.strip():
            return []
        tokens = [t for t in re.findall(r"[\w\u4e00-\u9fff]+", query) if len(t) >= 2]
        if not tokens:
            tokens = [query.strip()]
        fts_query = " OR ".join(f"{t}*" for t in tokens[:8])
        with self._connect() as conn:
            try:
                if kind:
                    rows = conn.execute(
                        """
                        SELECT n.*, bm25(node_fts) AS rank
                        FROM node_fts f
                        JOIN node n ON n.id = f.node_id
                        WHERE node_fts MATCH ? AND n.kind = ?
                        ORDER BY rank
                        LIMIT ?
                        """,
                        (fts_query, kind, limit),
                    ).fetchall()
                else:
                    rows = conn.execute(
                        """
                        SELECT n.*, bm25(node_fts) AS rank
                        FROM node_fts f
                        JOIN node n ON n.id = f.node_id
                        WHERE node_fts MATCH ?
                        ORDER BY rank
                        LIMIT ?
                        """,
                        (fts_query, limit),
                    ).fetchall()
            except sqlite3.OperationalError:
                return []
            results = []
            for r in rows:
                node = _row_to_node(r)
                node["_fts_rank"] = r["rank"]
                results.append(node)
            return results

    def neighbors(
        self,
        node_id: str,
        *,
        edge_kinds: Optional[List[str]] = None,
        limit: int = 5,
    ) -> List[Dict[str, Any]]:
        self.init()
        kinds = edge_kinds or ["calls", "imports", "uses", "contains", "references"]
        placeholders = ",".join("?" for _ in kinds)
        with self._connect() as conn:
            rows = conn.execute(
                f"""
                SELECT n.*, e.kind AS edge_kind, e.src, e.dst
                FROM edge e
                JOIN node n ON (n.id = e.dst OR n.id = e.src)
                WHERE (e.src = ? OR e.dst = ?)
                  AND n.id != ?
                  AND e.kind IN ({placeholders})
                LIMIT ?
                """,
                (node_id, node_id, node_id, *kinds, limit),
            ).fetchall()
            seen: set[str] = set()
            results: List[Dict[str, Any]] = []
            for r in rows:
                if r["id"] in seen:
                    continue
                seen.add(r["id"])
                node = _row_to_node(r)
                node["edge_kind"] = r["edge_kind"]
                results.append(node)
            return results

    def list_nodes(
        self,
        kind: Optional[str] = None,
        scope: Optional[str] = None,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        self.init()
        with self._connect() as conn:
            clauses: List[str] = []
            params: List[Any] = []
            if kind:
                clauses.append("kind = ?")
                params.append(kind)
            if scope:
                clauses.append("scope = ?")
                params.append(scope)
            where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
            params.append(limit)
            rows = conn.execute(
                f"SELECT * FROM node {where} ORDER BY name LIMIT ?",
                params,
            ).fetchall()
            return [_row_to_node(r) for r in rows]

    def stats(self) -> Dict[str, Any]:
        self.init()
        with self._connect() as conn:
            sym = conn.execute("SELECT COUNT(*) FROM symbols").fetchone()[0]
            nodes = conn.execute("SELECT COUNT(*) FROM node").fetchone()[0]
            edges = conn.execute("SELECT COUNT(*) FROM edge").fetchone()[0]
            ent = conn.execute("SELECT COUNT(*) FROM entries").fetchone()[0]
            by_cat: Dict[str, int] = {}
            for row in conn.execute(
                "SELECT category, COUNT(*) AS c FROM entries GROUP BY category"
            ):
                by_cat[row["category"]] = row["c"]
            stale = conn.execute(
                "SELECT COUNT(*) FROM entries WHERE effectiveness < 0.2"
            ).fetchone()[0]
            avg_eff = conn.execute(
                "SELECT AVG(effectiveness) FROM entries"
            ).fetchone()[0]
            top_used = conn.execute(
                """SELECT name, usage_count FROM entries
                   ORDER BY usage_count DESC LIMIT 10"""
            ).fetchall()
            recent = conn.execute(
                """SELECT name, created_at FROM entries
                   ORDER BY created_at DESC LIMIT 10"""
            ).fetchall()
            return {
                "symbols": sym,
                "nodes": nodes,
                "edges": edges,
                "entries": ent,
                "by_category": by_cat,
                "stale_count": stale,
                "avg_effectiveness": round(float(avg_eff or 0), 3),
                "top_used": [
                    {"name": r["name"], "usage_count": r["usage_count"]}
                    for r in top_used
                ],
                "recently_added": [
                    {"name": r["name"], "created_at": r["created_at"] or ""}
                    for r in recent
                ],
            }


def get_project_db(project_root: str | Path) -> CodeGraphDB:
    return CodeGraphDB(get_knowledge_db_path(project_root))


def get_global_db() -> CodeGraphDB:
    return CodeGraphDB(get_global_knowledge_db_path())
