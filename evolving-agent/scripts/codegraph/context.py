#!/usr/bin/env python3
"""Build combined task context: KnowledgePlane + legacy knowledge API compat."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Literal, Optional

from codegraph.plane import query_plane
from codegraph.query import query_context

MetaTier = Literal["tiny", "small", "medium", "large"]


def _legacy_knowledge_payload(
    project_root: Path,
    task_desc: str,
    knowledge_mode: str,
) -> Dict[str, Any]:
    import sys

    knowledge_dir = str(Path(__file__).parent.parent / "knowledge")
    if knowledge_dir not in sys.path:
        sys.path.insert(0, knowledge_dir)
    from trigger import trigger_knowledge  # type: ignore

    return trigger_knowledge(
        user_input=task_desc,
        project_dir=str(project_root),
        mode=knowledge_mode,
    )


def build_task_context(
    project_root: str | Path,
    task_desc: str,
    knowledge_mode: str = "hybrid",
    *,
    tier: MetaTier = "medium",
    budget_tokens: int = 1500,
    meta_path: Optional[str | Path] = None,
    use_plane: bool = True,
) -> str:
    """
    Merge CodeGraph + KB via KnowledgePlane (default) with token budget.

    use_plane=False falls back to legacy merge (codegraph query + knowledge trigger).
    """
    root = Path(project_root).resolve()

    if not use_plane:
        return _build_legacy_context_text(root, task_desc, knowledge_mode)

    result = query_plane(
        root,
        task_desc,
        tier=tier,
        budget_tokens=budget_tokens,
        knowledge_mode=knowledge_mode,
    )

    meta_file = Path(meta_path) if meta_path else root / ".opencode" / ".knowledge-context.meta.json"
    try:
        meta_file.parent.mkdir(parents=True, exist_ok=True)
        meta_file.write_text(
            json.dumps(
                {
                    "query": task_desc,
                    "tier": tier,
                    "budget_tokens": budget_tokens,
                    "tokens_used": result.get("tokens_used", 0),
                    "sections_included": result.get("sections_included", []),
                    "sections_dropped": result.get("sections_dropped", []),
                    "diagnostics": result.get("diagnostics", {}),
                },
                indent=2,
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )
    except OSError:
        pass

    return result.get("text", "")


def _build_legacy_context_text(
    root: Path,
    task_desc: str,
    knowledge_mode: str,
) -> str:
    from codegraph.query import format_context

    parts: list[str] = []
    try:
        graph_result = query_context(root, task_desc)
        graph_md = format_context(graph_result)
        if graph_md:
            parts.append(graph_md)
    except Exception:
        pass
    try:
        import sys
        knowledge_dir = str(Path(__file__).parent.parent / "knowledge")
        if knowledge_dir not in sys.path:
            sys.path.insert(0, knowledge_dir)
        from trigger import format_for_context  # type: ignore

        kb_result = _legacy_knowledge_payload(root, task_desc, knowledge_mode)
        kb_md = format_for_context(kb_result, summary_only=False)
        if kb_md:
            parts.append(kb_md)
    except Exception:
        pass
    return "\n\n".join(parts).strip()


def build_task_context_json(
    project_root: str | Path,
    task_desc: str,
    knowledge_mode: str = "hybrid",
    *,
    tier: MetaTier = "medium",
    budget_tokens: int = 1500,
) -> Dict[str, Any]:
    """Structured version — includes KnowledgePlane result + legacy codegraph/knowledge keys."""
    root = Path(project_root).resolve()
    out: Dict[str, Any] = {"query": task_desc}

    try:
        out["codegraph"] = query_context(root, task_desc)
    except Exception as e:
        out["codegraph_error"] = str(e)

    try:
        out["knowledge"] = _legacy_knowledge_payload(root, task_desc, knowledge_mode)
    except Exception as e:
        out["knowledge_error"] = str(e)

    try:
        plane = query_plane(
            root,
            task_desc,
            tier=tier,
            budget_tokens=budget_tokens,
            knowledge_mode=knowledge_mode,
        )
        out.update(plane)
    except Exception as e:
        out["plane_error"] = str(e)

    return out
