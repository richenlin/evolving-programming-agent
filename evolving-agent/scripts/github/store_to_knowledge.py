#!/usr/bin/env python3
"""
Store to Knowledge Base

将从 GitHub 仓库提取的知识存储到统一知识库。
遵循 references/schema.json 定义的格式。

用法:
    python store_to_knowledge.py --category skill --input extracted.json
    echo '{"name": "...", "content": {...}}' | python store_to_knowledge.py --category skill
"""

import argparse
import json
import hashlib
import os
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional, List


# 路径解析 — 委托给 core.path_resolver（单一权威实现）
_scripts_root = Path(__file__).parent.parent
if str(_scripts_root) not in sys.path:
    sys.path.insert(0, str(_scripts_root))

try:
    from core.path_resolver import get_knowledge_base_dir
    from core.config import CATEGORY_DIRS
except ImportError:
    def get_knowledge_base_dir() -> Path:  # type: ignore[misc]
        """Fallback: 仅在 core.path_resolver 不可用时使用"""
        env_path = os.environ.get('KNOWLEDGE_BASE_PATH')
        if env_path:
            kb_path = Path(env_path)
            if kb_path.exists():
                return kb_path
        opencode_kb = Path.home() / '.config' / 'opencode' / 'knowledge'
        opencode_kb.mkdir(parents=True, exist_ok=True)
        return opencode_kb

    CATEGORY_DIRS = {
        'experience': 'experiences', 'tech-stack': 'tech-stacks',
        'scenario': 'scenarios', 'problem': 'problems',
        'testing': 'testing', 'pattern': 'patterns', 'skill': 'skills',
    }


def generate_id(category: str, name: str) -> str:
    """生成唯一 ID"""
    hash_input = f"{category}-{name}-{datetime.now().isoformat()}"
    hash_suffix = hashlib.md5(hash_input.encode()).hexdigest()[:8]
    return f"{category}-{name.lower().replace(' ', '-')}-{hash_suffix}"


def load_category_index(kb_dir: Path, category: str) -> Dict:
    """加载分类索引"""
    category_dir = kb_dir / CATEGORY_DIRS.get(category, f"{category}s")
    index_path = category_dir / "index.json"
    
    if index_path.exists():
        with open(index_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {"entries": [], "last_updated": None}


def save_category_index(kb_dir: Path, category: str, index: Dict):
    """保存分类索引"""
    category_dir = kb_dir / CATEGORY_DIRS.get(category, f"{category}s")
    category_dir.mkdir(parents=True, exist_ok=True)
    index_path = category_dir / "index.json"
    
    index["last_updated"] = datetime.now().isoformat()
    with open(index_path, 'w', encoding='utf-8') as f:
        json.dump(index, f, ensure_ascii=False, indent=2)


def load_global_index(kb_dir: Path) -> Dict:
    """加载全局索引"""
    index_path = kb_dir / "index.json"
    if index_path.exists():
        with open(index_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {
        "version": "1.0.0",
        "trigger_index": {},
        "category_index": {},
        "stats": {}
    }


def save_global_index(kb_dir: Path, index: Dict):
    """保存全局索引"""
    index["last_updated"] = datetime.now().isoformat()
    index_path = kb_dir / "index.json"
    with open(index_path, 'w', encoding='utf-8') as f:
        json.dump(index, f, ensure_ascii=False, indent=2)


def update_trigger_index(global_index: Dict, entry_id: str, triggers: List[str]):
    """更新触发词索引"""
    trigger_index = global_index.setdefault("trigger_index", {})
    for trigger in triggers:
        trigger_lower = trigger.lower()
        if trigger_lower not in trigger_index:
            trigger_index[trigger_lower] = []
        if entry_id not in trigger_index[trigger_lower]:
            trigger_index[trigger_lower].append(entry_id)


def store_knowledge_entry(
    kb_dir: Path,
    category: str,
    name: str,
    triggers: List[str],
    content: Dict[str, Any],
    sources: List[str],
    tags: Optional[List[str]] = None,
) -> str:
    """Store via unified knowledge.store (CodeGraph SQLite). kb_dir ignored."""
    _knowledge_dir = _scripts_root / "knowledge"
    if str(_knowledge_dir) not in sys.path:
        sys.path.insert(0, str(_knowledge_dir))
    from store import store_knowledge as _store  # noqa: WPS433

    entry = _store(
        category=category,
        name=name,
        content=content,
        sources=sources,
        tags=tags,
        triggers=triggers,
    )
    return entry["id"]


def store_skill(kb_dir: Path, data: Dict, source: str) -> str:
    """存储技能类知识"""
    content = {
        "skill_name": data.get("skill_name", data.get("name", "")),
        "level": data.get("level", "intermediate"),
        "description": data.get("description", ""),
        "key_concepts": data.get("key_concepts", []),
        "practical_tips": data.get("practical_tips", []),
        "common_mistakes": data.get("common_mistakes", [])
    }
    
    return store_knowledge_entry(
        kb_dir=kb_dir,
        category="skill",
        name=data.get("name", data.get("skill_name", "Unknown Skill")),
        triggers=data.get("triggers", []),
        content=content,
        sources=[source] if source else [],
        tags=data.get("tags", [])
    )


def store_tech_stack(kb_dir: Path, data: Dict, source: str) -> str:
    """存储技术栈知识"""
    content = {
        "tech_name": data.get("tech_name", data.get("name", "")),
        "version": data.get("version", ""),
        "best_practices": data.get("best_practices", []),
        "conventions": data.get("conventions", []),
        "common_patterns": data.get("common_patterns", []),
        "gotchas": data.get("gotchas", [])
    }
    
    return store_knowledge_entry(
        kb_dir=kb_dir,
        category="tech-stack",
        name=data.get("name", data.get("tech_name", "Unknown Tech")),
        triggers=data.get("triggers", []),
        content=content,
        sources=[source] if source else [],
        tags=data.get("tags", [])
    )


def store_pattern(kb_dir: Path, data: Dict, source: str) -> str:
    """存储模式知识"""
    content = {
        "pattern_name": data.get("pattern_name", data.get("name", "")),
        "category": data.get("pattern_category", "architecture"),
        "description": data.get("description", ""),
        "when_to_use": data.get("when_to_use", ""),
        "structure": data.get("structure", ""),
        "example": data.get("example", ""),
        "pros": data.get("pros", []),
        "cons": data.get("cons", [])
    }
    
    return store_knowledge_entry(
        kb_dir=kb_dir,
        category="pattern",
        name=data.get("name", data.get("pattern_name", "Unknown Pattern")),
        triggers=data.get("triggers", []),
        content=content,
        sources=[source] if source else [],
        tags=data.get("tags", [])
    )


def main():
    parser = argparse.ArgumentParser(description='存储知识到统一知识库')
    parser.add_argument('--category', '-c', required=True,
                       choices=['skill', 'tech-stack', 'pattern', 'problem', 'testing', 'experience', 'scenario'],
                       help='知识分类')
    parser.add_argument('--input', '-i', help='输入 JSON 文件路径')
    parser.add_argument('--source', '-s', help='知识来源 (如 GitHub URL)')
    parser.add_argument('--kb-dir', help='知识库目录路径 (默认自动检测)')
    
    args = parser.parse_args()
    
    # 确定知识库目录
    if args.kb_dir:
        kb_dir = Path(args.kb_dir)
    else:
        kb_dir = get_knowledge_base_dir()
    
    if not kb_dir.exists():
        print(f"错误: 知识库目录不存在: {kb_dir}", file=sys.stderr)
        sys.exit(1)
    
    # 读取输入数据
    if args.input:
        with open(args.input, 'r', encoding='utf-8') as f:
            data = json.load(f)
    else:
        data = json.load(sys.stdin)
    
    # 支持批量存储
    if isinstance(data, list):
        entries = data
    else:
        entries = [data]
    
    stored_ids = []
    for entry_data in entries:
        category = args.category
        source = args.source or entry_data.get("source", "")
        
        if category == "skill":
            entry_id = store_skill(kb_dir, entry_data, source)
        elif category == "tech-stack":
            entry_id = store_tech_stack(kb_dir, entry_data, source)
        elif category == "pattern":
            entry_id = store_pattern(kb_dir, entry_data, source)
        else:
            # 通用存储
            entry_id = store_knowledge_entry(
                kb_dir=kb_dir,
                category=category,
                name=entry_data.get("name", "Unknown"),
                triggers=entry_data.get("triggers", []),
                content=entry_data.get("content", {}),
                sources=[source] if source else [],
                tags=entry_data.get("tags", [])
            )
        
        stored_ids.append(entry_id)
        print(f"已存储: {entry_id}")
    
    print(f"\n共存储 {len(stored_ids)} 条知识到 {kb_dir}")


if __name__ == "__main__":
    main()
