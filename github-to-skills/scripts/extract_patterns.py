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

    # Generate knowledge addon
    addon = generate_knowledge_addon(repo_info)

    print(addon)


def generate_knowledge_addon(repo_info: dict) -> str:
    """
    Generate knowledge-addon format Markdown from repository info.
    """
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

## 代码规范

## 技术栈

## 最佳实践

## 应用场景
当处理相关技术栈的项目时，自动参考这些范式。
"""
    return template


if __name__ == "__main__":
    main()
