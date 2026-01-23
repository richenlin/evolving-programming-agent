#!/usr/bin/env python3
"""
Pattern Extractor

Extract programming patterns and best practices from GitHub repository info.
Generate knowledge-addon format Markdown.
"""

import sys
import json
from datetime import datetime


def main():
    # Read repo info from stdin
    repo_info = json.load(sys.stdin)

    # Analyze patterns
    patterns = detect_architecture_patterns(repo_info.get('file_tree', []))

    # Generate knowledge addon
    addon = generate_knowledge_addon(repo_info, patterns)

    print(addon)


def detect_architecture_patterns(file_tree: list) -> list:
    """
    Detect architecture patterns from file tree.
    Returns list of detected patterns.
    """
    patterns = []

    # Check for common architecture patterns
    for path in file_tree:
        path_lower = path.lower()

        if 'features/' in path_lower or 'feature/' in path_lower:
            if 'Feature-Based Architecture' not in patterns:
                patterns.append('Feature-Based Architecture')

        if 'components/' in path_lower or 'component/' in path_lower:
            if 'Component-Based Design' not in patterns:
                patterns.append('Component-Based Design')

        if 'hooks/' in path_lower or 'hook/' in path_lower:
            if 'Custom Hooks Pattern' not in patterns:
                patterns.append('Custom Hooks Pattern')

        if 'models/' in path_lower and 'views/' in path_lower:
            if 'MVC Pattern' not in patterns:
                patterns.append('MVC Pattern')

        if 'src/' in path_lower or 'lib/' in path_lower:
            if 'Monolithic Structure' not in patterns:
                patterns.append('Monolithic Structure')

        if 'services/' in path_lower and 'repositories/' in path_lower:
            if 'Repository Pattern' not in patterns:
                patterns.append('Repository Pattern')

        if 'store/' in path_lower or 'state/' in path_lower:
            if 'State Management Layer' not in patterns:
                patterns.append('State Management Layer')

    return patterns


def generate_knowledge_addon(repo_info: dict, patterns: list) -> str:
    """
    Generate knowledge-addon format Markdown from repository info.
    """
    # Format architecture patterns as list
    architecture_text = '\n'.join(f"- {p}" for p in patterns) if patterns else "- 未检测到明显架构模式"

    template = f"""---
name: {repo_info['name']}-knowledge
type: knowledge-addon
target_skill: programming-assistant
source_repo: {repo_info['url']}
source_hash: {repo_info['latest_hash']}
created_at: {datetime.now().isoformat()}
---

# {repo_info['name']} 学习笔记

## 项目架构

{architecture_text}

## 代码规范

## 技术栈

## 最佳实践

## 应用场景
当处理相关技术栈的项目时，自动参考这些范式。
"""
    return template


if __name__ == "__main__":
    main()
