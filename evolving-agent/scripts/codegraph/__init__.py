"""
CodeGraph — project code graph + session experience extraction.

At programming start: scan project → graph.json
After successful session: extract(intent, decisions, diff, review) → embed → persist
"""

__all__ = [
    "scan_project",
    "extract_session",
    "query_context",
    "format_context",
]


def __getattr__(name: str):
    if name == "scan_project":
        from codegraph.indexer import scan_project
        return scan_project
    if name == "extract_session":
        from codegraph.extractor import extract_session
        return extract_session
    if name == "query_context":
        from codegraph.query import query_context
        return query_context
    if name == "format_context":
        from codegraph.query import format_context
        return format_context
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
