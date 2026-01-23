#!/usr/bin/env python3
"""
YAML Frontmatter Parser Utility

A reusable function to parse YAML frontmatter from markdown files.
"""

import re
from pathlib import Path

try:
    import yaml
    HAS_YAML = True
except ImportError:
    HAS_YAML = False


def parse_frontmatter(file_path: str) -> dict:
    """
    Parse YAML frontmatter from a markdown file.

    Args:
        file_path: Path to the markdown file

    Returns:
        dict: Parsed frontmatter as dictionary, or empty dict if parsing fails
    """
    try:
        content = Path(file_path).read_text(encoding='utf-8')
    except Exception:
        return {}

    # Find YAML frontmatter between first two --- markers
    parts = content.split('---')
    if len(parts) < 3:
        return {}

    frontmatter_text = parts[1].strip()
    if not frontmatter_text:
        return {}

    # Parse YAML if available, otherwise use regex for basic key-value pairs
    if HAS_YAML:
        try:
            import yaml as yaml_module
            return yaml_module.safe_load(frontmatter_text) or {}
        except Exception:
            return {}
    else:
        # Fallback: basic regex parsing for key: value pairs
        metadata = {}
        for line in frontmatter_text.split('\n'):
            line = line.strip()
            if ':' in line:
                key, value = line.split(':', 1)
                metadata[key.strip()] = value.strip()
        return metadata


if __name__ == "__main__":
    # Simple test
    import sys
    if len(sys.argv) > 1:
        result = parse_frontmatter(sys.argv[1])
        print(result)
    else:
        print("Usage: python frontmatter_parser.py <file_path>")
