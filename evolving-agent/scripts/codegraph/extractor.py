#!/usr/bin/env python3
"""
CodeGraph Extractor — unified post-session knowledge extraction.

Pipeline:
  intent + decisions + git diff + review notes
  → classify (global vs project) → filter → store → embed

Sources: progress.txt, feature_list.json, git diff
"""

from __future__ import annotations

import json
import re
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional, Set

from codegraph.embedder import persist_vectors
from codegraph.db import get_project_db
from codegraph.paths import get_opencode_dir

import sys as _sys
_knowledge_dir = str(Path(__file__).parent.parent / "knowledge")
if _knowledge_dir not in _sys.path:
    _sys.path.insert(0, _knowledge_dir)

from summarizer import EXTRACTION_PATTERNS, infer_category  # noqa: E402
from store import store_knowledge  # noqa: E402

try:
    from core.path_resolver import get_project_kb_root, get_global_kb_root
except ImportError:
    def get_project_kb_root(project_root):
        from pathlib import Path
        return Path(project_root) / ".opencode" / "codegraph"

    def get_global_kb_root():
        from pathlib import Path
        p = Path.home() / ".config" / "opencode" / "codegraph"
        p.mkdir(parents=True, exist_ok=True)
        return p

Scope = Literal["global", "project"]

TYPE_TO_CATEGORY = {
    "pattern": "pattern",
    "bug-fix": "problem",
    "convention": "tech-stack",
    "solution": "experience",
    "api-usage": "scenario",
}

# Project-scope classification — project-local signals
PROJECT_SCOPE_KEYWORDS = (
    "架构", "选型", "环境配置", "workaround", "业务规则", "项目特有",
    "deployment", "deploy", "docker-compose", "nginx",
    ".env", ".opencode",
)

# Trivial content to skip
TRIVIAL_PATTERNS = (
    r"^简单",
    r"^仅?修改一行",
    r"^formatting",
    r"^lint fix",
    r"^typo",
)

SECTION_RE = {
    "problems": re.compile(r"##\s*遇到的问题\s*\n(.*?)(?=\n##|\Z)", re.DOTALL),
    "decisions": re.compile(r"##\s*关键决策\s*\n(.*?)(?=\n##|\Z)", re.DOTALL),
    "completed": re.compile(r"##\s*本次完成\s*\n(.*?)(?=\n##|\Z)", re.DOTALL),
}


def _read_text(path: Path) -> str:
    if not path.exists():
        return ""
    try:
        return path.read_text(encoding="utf-8")
    except OSError:
        return ""


def _load_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return {}


def _git_diff(project_root: Path, max_chars: int = 8000) -> str:
    try:
        result = subprocess.run(
            ["git", "diff", "HEAD"],
            cwd=project_root,
            capture_output=True,
            text=True,
            timeout=30,
        )
        diff = result.stdout or ""
        if not diff.strip():
            result = subprocess.run(
                ["git", "diff", "--stat", "HEAD~1..HEAD"],
                cwd=project_root,
                capture_output=True,
                text=True,
                timeout=15,
            )
            diff = result.stdout or ""
        return diff[:max_chars]
    except (subprocess.SubprocessError, OSError):
        return ""


def _parse_progress_sections(progress: str) -> Dict[str, List[str]]:
    out: Dict[str, List[str]] = {"problems": [], "decisions": [], "completed": []}
    for key, pattern in SECTION_RE.items():
        m = pattern.search(progress)
        if not m:
            continue
        block = m.group(1).strip()
        for line in block.splitlines():
            line = re.sub(r"^[-*]\s*\[[ x]\]\s*", "", line.strip())
            line = re.sub(r"^[-*]\d+\.\s*", "", line)
            if line:
                out[key].append(line)
    return out


def _item_text(cand: Dict[str, Any]) -> str:
    content = cand.get("content", {})
    return " ".join([
        cand.get("name", ""),
        str(content.get("description", "")),
        str(content.get("solution", "")),
        " ".join(content.get("conventions", []) or []),
    ]).lower()


def classify_scope(cand: Dict[str, Any], ctx: Dict[str, Any]) -> Scope:
    """
    Route to global vs project KB.

    - Architecture / env / project-specific → project
    - Generic bug-fix / pattern / best practice → global
    """
    cg_type = cand.get("codegraph_type", "")
    text = _item_text(cand)
    project_name = (ctx.get("project_name") or "").lower()

    if cg_type == "convention":
        return "project"
    if any(kw in text for kw in PROJECT_SCOPE_KEYWORDS):
        return "project"
    if project_name and project_name in text:
        return "project"
    # Review notes about project-specific files often mention paths
    if re.search(r"(/src/|/lib/|\.opencode/|\.env)", text):
        return "project"
    return "global"


def should_extract(cand: Dict[str, Any], ctx: Dict[str, Any]) -> bool:
    """Quality gate — skip low-value items."""
    text = _item_text(cand)
    name = cand.get("name", "")

    if len(text.strip()) < 15:
        return False

    for pat in TRIVIAL_PATTERNS:
        if re.search(pat, name, re.IGNORECASE):
            return False

    # Diff-only change summary without problems/decisions/reviews is low value
    if name.startswith("变更摘要:"):
        has_signal = (
            ctx.get("problems")
            or ctx.get("decisions")
            or ctx.get("review_notes")
        )
        if not has_signal:
            return False

    return True


def _extract_from_text(text: str) -> List[Dict[str, Any]]:
    items: List[Dict[str, Any]] = []
    seen: Set[tuple] = set()

    for pattern_type, patterns in EXTRACTION_PATTERNS.items():
        for pattern in patterns:
            for m in re.finditer(pattern, text, re.IGNORECASE | re.DOTALL):
                groups = [g.strip() for g in m.groups() if g and g.strip()]
                if not groups:
                    continue
                if pattern_type == "problem_solution" and len(groups) >= 2:
                    name = f"{groups[0][:60]}"
                    content = {
                        "description": groups[0],
                        "solution": groups[1],
                        "symptoms": [groups[0][:120]],
                    }
                    cg_type = "bug-fix"
                elif pattern_type == "decision" and len(groups) >= 2:
                    name = f"决策: {groups[0][:50]}"
                    content = {
                        "description": groups[0],
                        "solution": groups[1],
                        "context": "架构/技术决策",
                    }
                    cg_type = "convention"
                elif pattern_type == "lesson" and len(groups) >= 2:
                    name = f"教训: {groups[0][:50]}"
                    content = {
                        "description": groups[0],
                        "solution": groups[1],
                        "pitfalls": [groups[1][:200]],
                    }
                    cg_type = "pattern"
                elif pattern_type in ("best_practice", "gotcha"):
                    name = groups[0][:80]
                    content = {"description": groups[0], "best_practices": [groups[0]]}
                    cg_type = "pattern"
                else:
                    continue

                key = (cg_type, name)
                if key in seen:
                    continue
                seen.add(key)
                items.append({
                    "name": name,
                    "content": content,
                    "codegraph_type": cg_type,
                    "category": TYPE_TO_CATEGORY.get(
                        cg_type, infer_category(name + " " + str(content))
                    ),
                })
    return items


def _build_session_context(project_root: Path) -> Dict[str, Any]:
    opencode = get_opencode_dir(project_root)
    progress = _read_text(opencode / "progress.txt")
    feature_list = _load_json(opencode / "feature_list.json")
    diff = _git_diff(project_root)

    tasks = feature_list.get("tasks", [])
    completed = [t for t in tasks if t.get("status") == "completed"]
    had_reject = any(
        t.get("review_status") == "reject" or t.get("status") == "rejected"
        for t in tasks
    )

    intent_parts = [
        t.get("name", "") + ": " + t.get("description", "")
        for t in completed[:3]
    ]
    if not intent_parts and tasks:
        pending = next(
            (t for t in tasks if t.get("status") in ("pending", "in_progress")),
            None,
        )
        if pending:
            intent_parts = [pending.get("name", "") + ": " + pending.get("description", "")]

    review_notes: List[str] = []
    for t in tasks:
        for note in t.get("reviewer_notes", []) or []:
            if isinstance(note, str) and note.strip():
                review_notes.append(note.strip())
            elif isinstance(note, dict) and note.get("message"):
                review_notes.append(note["message"])

    sections = _parse_progress_sections(progress)

    return {
        "intent": "; ".join(intent_parts) or feature_list.get("project", ""),
        "project_name": feature_list.get("project", ""),
        "decisions": sections["decisions"],
        "problems": sections["problems"],
        "completed": sections["completed"],
        "diff": diff,
        "review_notes": review_notes,
        "progress_raw": progress,
        "task_count": len(tasks),
        "completed_count": len(completed),
        "had_reject": had_reject,
    }


def _candidates_from_context(ctx: Dict[str, Any]) -> List[Dict[str, Any]]:
    items: List[Dict[str, Any]] = []

    for prob in ctx.get("problems", []):
        items.extend(_extract_from_text(f"问题：{prob}"))
        if "→" in prob or "->" in prob:
            items.extend(_extract_from_text(prob))

    for dec in ctx.get("decisions", []):
        if "→" in dec or "->" in dec or "原因" in dec:
            items.extend(_extract_from_text(
                dec if dec.startswith("决策") else f"决策：{dec}"
            ))
        else:
            items.append({
                "name": f"决策: {dec[:60]}",
                "content": {"description": dec, "conventions": [dec]},
                "codegraph_type": "convention",
                "category": "tech-stack",
            })

    for note in ctx.get("review_notes", []):
        items.extend(_extract_from_text(f"问题：review发现 → 解决：{note}"))

    blob = "\n".join([
        ctx.get("progress_raw", ""),
        ctx.get("intent", ""),
        "\n".join(ctx.get("review_notes", [])),
    ])
    items.extend(_extract_from_text(blob))

    diff = ctx.get("diff", "")
    if diff and len(diff) > 100:
        files_changed = re.findall(r"^\s*(\S+\.\w+)\s*\|", diff, re.MULTILINE)
        if files_changed:
            summary = f"本次变更涉及: {', '.join(files_changed[:8])}"
            items.append({
                "name": f"变更摘要: {files_changed[0]}",
                "content": {
                    "description": summary,
                    "solution": diff[:1500],
                    "context": ctx.get("intent", ""),
                },
                "codegraph_type": "solution",
                "category": "experience",
            })

    seen_names: Set[str] = set()
    unique: List[Dict[str, Any]] = []
    for it in items:
        n = it["name"]
        if n in seen_names:
            continue
        seen_names.add(n)
        unique.append(it)
    return unique


def _session_worth_extracting(ctx: Dict[str, Any]) -> tuple[bool, str]:
    """Session-level skip for pass-only sessions with no discoveries."""
    if ctx.get("problems") or ctx.get("decisions") or ctx.get("review_notes"):
        return True, ""
    if ctx.get("had_reject"):
        return True, ""
    if ctx["completed_count"] == 0:
        return False, "no completed tasks"
    # All pass, no discoveries — skip
    if ctx["completed_count"] > 0 and not ctx.get("problems"):
        return False, "pass-only session with no extractable discoveries"
    return True, ""


def extract_session(
    project_root: str | Path,
    force: bool = False,
) -> Dict[str, Any]:
    """
    Unified knowledge extraction via codegraph extract.

    Reads progress.txt, feature_list.json, git diff.
    Routes entries to global or project KB, embeds project-scoped vectors.
    """
    root = Path(project_root).resolve()
    ctx = _build_session_context(root)

    if not force:
        worth, reason = _session_worth_extracting(ctx)
        if not worth:
            return {
                "status": "skipped",
                "reason": reason,
                "context_summary": {
                    "intent": ctx.get("intent"),
                    "task_count": ctx.get("task_count"),
                    "completed_count": ctx.get("completed_count"),
                },
            }

    candidates = _candidates_from_context(ctx)

    session_id = datetime.now().strftime("%Y%m%d-%H%M")
    sources = [
        f"codegraph-extract:{session_id}",
        f"intent:{ctx.get('intent', '')[:100]}",
    ]

    stored: List[Dict[str, Any]] = []
    vector_items: List[Dict[str, Any]] = []
    skipped = 0

    for cand in candidates:
        if not should_extract(cand, ctx):
            skipped += 1
            continue

        scope = classify_scope(cand, ctx)

        text_for_embed = " ".join([
            cand["name"],
            str(cand["content"].get("description", "")),
            str(cand["content"].get("solution", "")),
        ])

        entry = store_knowledge(
            category=cand["category"],
            name=cand["name"],
            content=cand["content"],
            sources=sources,
            tags=["codegraph", cand.get("codegraph_type", "solution"), scope],
            project_path=str(root) if scope == "project" else None,
        )

        stored.append({
            "id": entry["id"],
            "name": entry["name"],
            "category": entry["category"],
            "type": cand.get("codegraph_type"),
            "scope": scope,
        })

        # Vectors indexed per-project (includes project-scoped experience for retrieval)
        if scope == "project":
            vector_items.append({
                "entry_id": entry["id"],
                "text": text_for_embed,
                "type": cand.get("codegraph_type", "solution"),
                "sources": sources,
            })

    vector_result = persist_vectors(root, vector_items) if vector_items else {"stored": 0}

    db_stats = {}
    try:
        db_stats = get_project_db(root).stats()
    except Exception:
        pass

    if not stored and not force:
        return {
            "status": "skipped",
            "reason": "no entries passed quality filter",
            "candidates": len(candidates),
            "skipped": skipped,
        }

    return {
        "status": "ok",
        "extracted": len(stored),
        "global": sum(1 for e in stored if e["scope"] == "global"),
        "project": sum(1 for e in stored if e["scope"] == "project"),
        "skipped": skipped,
        "entries": stored,
        "vectors": vector_result,
        "db_stats": db_stats,
        "context": {
            "intent": ctx.get("intent"),
            "decisions": len(ctx.get("decisions", [])),
            "problems": len(ctx.get("problems", [])),
            "review_notes": len(ctx.get("review_notes", [])),
            "diff_chars": len(ctx.get("diff", "")),
        },
    }


# Backward-compatible alias
evolve = extract_session
