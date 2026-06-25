#!/usr/bin/env python3
"""Deterministic node IDs for CodeGraph v3."""

from __future__ import annotations

import hashlib


def node_id(
    kind: str,
    name: str,
    *,
    file: str = "",
    line: int = 0,
    scope: str = "project",
) -> str:
    raw = f"{scope}:{kind}:{name}:{file}:{line}"
    return hashlib.sha1(raw.encode("utf-8")).hexdigest()[:16]


def module_id(file_path: str, scope: str = "project") -> str:
    return node_id("module", file_path, file=file_path, scope=scope)


def symbol_id(file_path: str, name: str, line: int, scope: str = "project") -> str:
    return node_id("symbol", name, file=file_path, line=line, scope=scope)
