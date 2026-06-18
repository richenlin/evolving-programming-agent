#!/usr/bin/env python3
"""Build combined task context: CodeGraph + knowledge trigger.

Design phase: query with user goal → .design-context.md (orchestrator).
Coder dispatch: query with task desc → .knowledge-context.md (@coder).
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Optional

from codegraph.query import query_context, format_context as format_graph_context


def build_task_context(
    project_root: str | Path,
    task_desc: str,
    knowledge_mode: str = "hybrid",
) -> str:
    """
    Merge CodeGraph structural context with knowledge-base retrieval.

    Same entry point for design-phase (macro user goal) and coder-phase
    (per-task description) retrieval; caller chooses task_desc / --input.
    """
    root = Path(project_root).resolve()
    parts: list[str] = []

    # 1. CodeGraph: project structure + vector experience
    try:
        graph_result = query_context(root, task_desc)
        graph_md = format_graph_context(graph_result)
        if graph_md:
            parts.append(graph_md)
    except Exception:
        pass

    # 2. Knowledge trigger: global + project KB
    try:
        import sys
        knowledge_dir = str(Path(__file__).parent.parent / "knowledge")
        if knowledge_dir not in sys.path:
            sys.path.insert(0, knowledge_dir)
        from trigger import trigger_knowledge, format_for_context  # type: ignore

        kb_result = trigger_knowledge(
            user_input=task_desc,
            project_dir=str(root),
            mode=knowledge_mode,
        )
        kb_md = format_for_context(kb_result)
        if kb_md:
            parts.append(kb_md)
    except Exception:
        pass

    return "\n\n".join(parts).strip()


def build_task_context_json(
    project_root: str | Path,
    task_desc: str,
    knowledge_mode: str = "hybrid",
) -> Dict[str, Any]:
    """Structured version for debugging / API."""
    root = Path(project_root).resolve()
    out: Dict[str, Any] = {"query": task_desc}

    try:
        out["codegraph"] = query_context(root, task_desc)
    except Exception as e:
        out["codegraph_error"] = str(e)

    try:
        import sys
        knowledge_dir = str(Path(__file__).parent.parent / "knowledge")
        if knowledge_dir not in sys.path:
            sys.path.insert(0, knowledge_dir)
        from trigger import trigger_knowledge  # type: ignore
        out["knowledge"] = trigger_knowledge(
            user_input=task_desc,
            project_dir=str(root),
            mode=knowledge_mode,
        )
    except Exception as e:
        out["knowledge_error"] = str(e)

    return out
