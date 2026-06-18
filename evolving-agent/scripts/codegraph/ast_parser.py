#!/usr/bin/env python3
"""
AST parser — tree-sitter when available, regex fallback otherwise.

Extracts symbols (functions, classes, types) and import edges from source files.
"""

from __future__ import annotations

import re
from functools import lru_cache
from typing import Any, Dict, List, Optional, Tuple

# ---------------------------------------------------------------------------
# Regex fallback (from legacy indexer)
# ---------------------------------------------------------------------------

_SYMBOL_PATTERNS: Dict[str, List[Tuple[str, str]]] = {
    "python": [
        ("function", r"^def\s+(\w+)\s*\("),
        ("class", r"^class\s+(\w+)"),
    ],
    "javascript": [
        ("function", r"(?:export\s+)?(?:async\s+)?function\s+(\w+)\s*\("),
        ("class", r"(?:export\s+)?class\s+(\w+)"),
        ("const", r"(?:export\s+)?const\s+(\w+)\s*="),
    ],
    "typescript": [
        ("function", r"(?:export\s+)?(?:async\s+)?function\s+(\w+)\s*[<(]"),
        ("class", r"(?:export\s+)?class\s+(\w+)"),
        ("interface", r"(?:export\s+)?interface\s+(\w+)"),
        ("type", r"(?:export\s+)?type\s+(\w+)\s*="),
    ],
    "go": [
        ("function", r"^func\s+(?:\(\w+\s+\*?\w+\)\s+)?(\w+)\s*\("),
        ("type", r"^type\s+(\w+)\s+(?:struct|interface)"),
    ],
    "rust": [
        ("function", r"^(?:pub\s+)?fn\s+(\w+)\s*[(<]"),
        ("struct", r"^(?:pub\s+)?struct\s+(\w+)"),
        ("enum", r"^(?:pub\s+)?enum\s+(\w+)"),
        ("trait", r"^(?:pub\s+)?trait\s+(\w+)"),
    ],
    "java": [
        ("class", r"(?:public\s+)?(?:abstract\s+)?class\s+(\w+)"),
        ("interface", r"(?:public\s+)?interface\s+(\w+)"),
        ("method", r"(?:public|private|protected)\s+\S+\s+(\w+)\s*\("),
    ],
}

_IMPORT_PATTERNS: Dict[str, re.Pattern] = {
    "python": re.compile(r"^(?:from\s+([\w.]+)\s+import|import\s+([\w.]+))"),
    "javascript": re.compile(r"""^import\s+(?:.+?\s+from\s+)?['"]([^'"]+)['"]"""),
    "typescript": re.compile(r"""^import\s+(?:.+?\s+from\s+)?['"]([^'"]+)['"]"""),
    "go": re.compile(r"""^import\s+(?:\(\s*)?["']([^"']+)["']"""),
    "rust": re.compile(r"""^use\s+([\w:]+(?:::\*)?)"""),
    "java": re.compile(r"""^import\s+([\w.]+)"""),
}

# tree-sitter language id → pip package suffix
_TS_PACKAGES = {
    "python": "tree_sitter_python",
    "javascript": "tree_sitter_javascript",
    "typescript": "tree_sitter_typescript",
}

# typescript uses tsx/typescript sub-grammar
_TS_GRAMMAR = {
    "typescript": "typescript",
    "tsx": "tsx",
}


def _regex_symbols(content: str, language: str, rel_path: str) -> List[Dict[str, Any]]:
    symbols: List[Dict[str, Any]] = []
    patterns = _SYMBOL_PATTERNS.get(language, _SYMBOL_PATTERNS.get("javascript", []))
    for line_no, line in enumerate(content.splitlines(), start=1):
        stripped = line.strip()
        for kind, pattern in patterns:
            m = re.match(pattern, stripped)
            if m:
                name = m.group(1)
                symbols.append({
                    "id": f"sym:{rel_path}:{name}:{line_no}",
                    "file": rel_path,
                    "name": name,
                    "kind": kind,
                    "line": line_no,
                    "end_line": line_no,
                })
    return symbols


def _regex_imports(content: str, language: str, file_id: str) -> List[Dict[str, Any]]:
    edges: List[Dict[str, Any]] = []
    pattern = _IMPORT_PATTERNS.get(language)
    if not pattern:
        return edges
    for line in content.splitlines():
        stripped = line.strip()
        m = pattern.match(stripped)
        if not m:
            continue
        target = next(g for g in m.groups() if g)
        edges.append({"from": file_id, "to": f"mod:{target}", "type": "import"})
    return edges


# ---------------------------------------------------------------------------
# tree-sitter
# ---------------------------------------------------------------------------

@lru_cache(maxsize=16)
def _load_ts_language(language: str, ext: str = "") -> Optional[Any]:
    pkg = _TS_PACKAGES.get(language)
    if not pkg:
        return None
    try:
        mod = __import__(pkg)
        from tree_sitter import Language
        if language == "typescript":
            grammar = _TS_GRAMMAR.get(ext.lstrip(".") if ext else "typescript", "typescript")
            return Language(getattr(mod, grammar).language())
        return Language(mod.language())
    except Exception:
        return None


def _node_text(content: bytes, node) -> str:
    return content[node.start_byte:node.end_byte].decode("utf-8", errors="replace")


# Symbol node types per language grammar
_TS_SYMBOL_TYPES: Dict[str, Dict[str, str]] = {
    "python": {
        "function_definition": "function",
        "class_definition": "class",
    },
    "javascript": {
        "function_declaration": "function",
        "class_declaration": "class",
        "method_definition": "method",
        "arrow_function": "function",
    },
    "typescript": {
        "function_declaration": "function",
        "class_declaration": "class",
        "method_definition": "method",
        "interface_declaration": "interface",
        "type_alias_declaration": "type",
        "enum_declaration": "enum",
    },
}

_TS_IMPORT_TYPES = {
    "python": ("import_statement", "import_from_statement"),
    "javascript": ("import_statement",),
    "typescript": ("import_statement",),
}


def _ts_extract(content: str, language: str, rel_path: str, ext: str) -> Tuple[List[Dict], List[Dict], List[str]]:
    """Returns (symbols, edges, call_targets)."""
    lang = _load_ts_language(language, ext)
    if lang is None:
        return [], [], []

    try:
        from tree_sitter import Parser
        parser = Parser(lang)
        src = content.encode("utf-8")
        tree = parser.parse(src)
    except Exception:
        return [], [], []

    file_id = f"file:{rel_path}"
    symbols: List[Dict[str, Any]] = []
    edges: List[Dict[str, Any]] = []
    calls: List[str] = []
    type_map = _TS_SYMBOL_TYPES.get(language, _TS_SYMBOL_TYPES.get("typescript", {}))
    import_types = _TS_IMPORT_TYPES.get(language, ())

    def walk(node) -> None:
        ntype = node.type
        if ntype in type_map:
            name_node = node.child_by_field_name("name")
            if name_node:
                name = _node_text(src, name_node)
                line = node.start_point[0] + 1
                end_line = node.end_point[0] + 1
                symbols.append({
                    "id": f"sym:{rel_path}:{name}:{line}",
                    "file": rel_path,
                    "name": name,
                    "kind": type_map[ntype],
                    "line": line,
                    "end_line": end_line,
                })
        if ntype in import_types:
            text = _node_text(src, node).strip()
            for part in re.findall(r"['\"]([^'\"]+)['\"]", text):
                edges.append({"from": file_id, "to": f"mod:{part}", "type": "import"})
            if language == "python":
                m = re.match(r"^(?:from\s+([\w.]+)|import\s+([\w.]+))", text)
                if m:
                    target = next(g for g in m.groups() if g)
                    edges.append({"from": file_id, "to": f"mod:{target}", "type": "import"})
        if ntype == "call":
            fn = node.child_by_field_name("function")
            if fn:
                calls.append(_node_text(src, fn))
        for child in node.children:
            walk(child)

    walk(tree.root_node)
    return symbols, edges, calls


def parse_file(
    content: str,
    language: str,
    rel_path: str,
    ext: str = "",
) -> Dict[str, Any]:
    """
    Parse a source file for symbols and imports.

    Returns:
        {
          symbols, dependencies, calls,
          parser: "tree-sitter" | "regex"
        }
    """
    file_id = f"file:{rel_path}"
    ts_symbols, ts_edges, calls = _ts_extract(content, language, rel_path, ext)

    if ts_symbols or ts_edges:
        return {
            "symbols": ts_symbols,
            "dependencies": ts_edges,
            "calls": [{"from": file_id, "to": c, "type": "call"} for c in calls[:50]],
            "parser": "tree-sitter",
        }

    return {
        "symbols": _regex_symbols(content, language, rel_path),
        "dependencies": _regex_imports(content, language, file_id),
        "calls": [],
        "parser": "regex",
    }


def tree_sitter_available() -> bool:
    return _load_ts_language("python") is not None
