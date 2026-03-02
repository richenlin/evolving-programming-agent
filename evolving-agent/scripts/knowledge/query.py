#!/usr/bin/env python3
"""
Unified Knowledge Query

统一知识库查询接口：
- 按关键字触发查询
- 按分类查询
- 按标签查询
- 全文搜索
"""

import argparse
import json
import os
import re
import sys
from datetime import datetime
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

# Optional jieba import for Chinese tokenization
try:
    import jieba
    HAS_JIEBA = True
except ImportError:
    HAS_JIEBA = False

# Import config constants
try:
    from core.config import (
        FUZZY_MATCH_THRESHOLD,
        RELEVANCE_WEIGHTS,
        RECENCY_DECAY_DAYS,
        USAGE_NORMALIZATION,
        TOP_K_RESULTS,
    )
except ImportError:
    FUZZY_MATCH_THRESHOLD = 0.6
    RELEVANCE_WEIGHTS = {
        "trigger_match": 0.4,
        "effectiveness": 0.3,
        "recency": 0.2,
        "usage": 0.1,
    }
    RECENCY_DECAY_DAYS = 365.0
    USAGE_NORMALIZATION = 100.0
    TOP_K_RESULTS = 10

def tokenize(text: str) -> List[str]:
    """
    Tokenize text into a list of tokens.

    Uses jieba for Chinese tokenization if available; otherwise falls back
    to whitespace splitting + regex extraction of Chinese characters and
    ASCII alphanumeric sequences.

    Args:
        text: Input text (may contain Chinese, English, or mixed content)

    Returns:
        List of non-empty token strings
    """
    if HAS_JIEBA:
        tokens = jieba.lcut(text)
        # Filter empty strings and pure punctuation/whitespace
        return [t for t in tokens if t.strip() and re.search(r'[\w\u4e00-\u9fff]', t)]
    else:
        # Fallback: split by whitespace and extract Chinese words + ASCII words
        return re.findall(r'[\u4e00-\u9fff]+|[a-zA-Z0-9]+', text.lower())


# Import atomic_write_json from file_utils
try:
    from core.file_utils import atomic_write_json
except ImportError:
    # Fallback if file_utils is not available
    def atomic_write_json(filepath, data):
        """Fallback atomic write"""
        filepath = Path(filepath)
        filepath.parent.mkdir(parents=True, exist_ok=True)
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)


# Category to directory mapping
CATEGORY_DIRS = {
    'experience': 'experiences',
    'tech-stack': 'tech-stacks',
    'scenario': 'scenarios',
    'problem': 'problems',
    'testing': 'testing',
    'pattern': 'patterns',
    'skill': 'skills'
}


# 路径解析器导入 — 使用专用 sentinel 避免与 None/False 混淆
_UNINITIALIZED = object()
_path_resolver_module = _UNINITIALIZED


def _try_import_path_resolver():
    """尝试导入 path_resolver 模块，结果缓存。返回模块或 None（表示不可用）。"""
    global _path_resolver_module
    if _path_resolver_module is not _UNINITIALIZED:
        return _path_resolver_module  # None 表示之前导入失败

    # 添加 path_resolver 所在目录到 Python path
    script_dir = Path(__file__).parent
    core_scripts = script_dir.parent / 'core'
    if core_scripts.exists() and str(core_scripts) not in sys.path:
        sys.path.insert(0, str(core_scripts))

    try:
        import path_resolver
        _path_resolver_module = path_resolver
    except ImportError:
        _path_resolver_module = None

    return _path_resolver_module


def get_kb_root() -> Path:
    """
    Get knowledge base root directory.
    
    使用统一的 path_resolver 模块进行跨平台路径解析。
    支持 OpenCode (~/.config/opencode/skills/) 和 Claude Code (~/.claude/skills/)。
    """
    # 1. 优先使用 path_resolver
    resolver = _try_import_path_resolver()
    if resolver:
        return resolver.get_knowledge_base_dir()
    
    # 2. Fallback: 内置路径解析逻辑
    env_path = os.environ.get('KNOWLEDGE_BASE_PATH')
    if env_path:
        kb_path = Path(env_path)
        if kb_path.exists():
            return kb_path
    
    opencode_kb = Path.home() / '.config' / 'opencode' / 'knowledge'
    if opencode_kb.exists():
        return opencode_kb
    
    claude_kb = Path.home() / '.claude' / 'knowledge'
    if claude_kb.exists():
        return claude_kb
    
    opencode_kb.mkdir(parents=True, exist_ok=True)
    return opencode_kb


def load_json(path: Path) -> Dict[str, Any]:
    """Safely load JSON file."""
    if not path.exists():
        return {}
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return {}


def update_usage(entry_path: Path, entry_data: Dict[str, Any]) -> None:
    """
    Update usage statistics for a knowledge entry.
    
    Increments usage_count and updates last_used_at timestamp.
    Uses atomic write to prevent corruption.
    
    Args:
        entry_path: Path to the entry JSON file
        entry_data: Entry data dict (will be modified in place)
    """
    if not entry_path.exists():
        return
    
    # Update usage statistics
    entry_data['usage_count'] = entry_data.get('usage_count', 0) + 1
    entry_data['last_used_at'] = datetime.now().isoformat()
    
    # Atomic write to prevent corruption
    try:
        atomic_write_json(entry_path, entry_data)
    except Exception:
        # Silently fail if write fails (don't break query)
        pass


def fuzzy_match(query_tokens: List[str], trigger_tokens: List[str], threshold: float = FUZZY_MATCH_THRESHOLD) -> float:
    """
    计算查询词和触发词之间的模糊匹配分数。
    
    使用 difflib.SequenceMatcher 进行模糊匹配。
    
    Args:
        query_tokens: 查询词列表
        trigger_tokens: 触发词列表
        threshold: 匹配阈值（默认 0.6）
        
    Returns:
        最高相似度分数（0.0 到 1.0）
    """
    max_score = 0.0
    
    for query in query_tokens:
        query_lower = query.lower()
        for trigger in trigger_tokens:
            trigger_lower = trigger.lower()
            
            # Calculate similarity
            matcher = SequenceMatcher(None, query_lower, trigger_lower)
            score = matcher.ratio()
            
            if score > max_score:
                max_score = score
            
            # Early exit if perfect match
            if max_score == 1.0:
                return 1.0
    
    return max_score if max_score >= threshold else 0.0


def compute_relevance(entry: Dict[str, Any], query_tokens: List[str]) -> float:
    """
    计算知识条目的相关性分数。
    
    综合评分 = 触发词匹配分 × 0.4 + effectiveness × 0.3 + recency × 0.2 + usage_count 归一化 × 0.1
    
    Args:
        entry: 知识条目
        query_tokens: 查询词列表
        
    Returns:
        相关性分数（0.0 到 1.0）
    """
    # 1. Trigger match score (0.4 weight)
    match_score = entry.get('_match_score', 0) / 3.0  # Normalize to 0-1 (max score is 3)
    
    # 2. Effectiveness (0.3 weight)
    effectiveness = entry.get('effectiveness', 0.5)
    
    # 3. Recency (recency weight)
    last_used_str = entry.get('last_used_at') or entry.get('created_at')
    if last_used_str:
        try:
            last_used = datetime.fromisoformat(last_used_str.replace('Z', '+00:00'))
            days_since_use = (datetime.now(last_used.tzinfo) - last_used).days
            recency = max(0.0, 1.0 - (days_since_use / RECENCY_DECAY_DAYS))
        except (ValueError, TypeError, OSError):
            recency = 0.5
    else:
        recency = 0.5
    
    # 4. Usage count (usage weight, normalized)
    usage_count = entry.get('usage_count', 0)
    usage_normalized = min(1.0, usage_count / USAGE_NORMALIZATION)
    
    # Combine scores using configured weights
    relevance = (
        match_score * RELEVANCE_WEIGHTS["trigger_match"] +
        effectiveness * RELEVANCE_WEIGHTS["effectiveness"] +
        recency * RELEVANCE_WEIGHTS["recency"] +
        usage_normalized * RELEVANCE_WEIGHTS["usage"]
    )
    
    return relevance


def get_global_index() -> Dict[str, Any]:
    """Load global index."""
    return load_json(get_kb_root() / 'index.json')


def query_by_triggers(
    triggers: List[str],
    limit: int = TOP_K_RESULTS,
    project_root=None,
) -> List[Dict[str, Any]]:
    """
    根据触发关键字查询知识。
    
    支持精确匹配、部分匹配和模糊匹配。
    当指定 project_root 时，先查项目级知识库再查全局，合并去重。
    
    Args:
        triggers: 触发关键字列表
        limit: 返回结果数量限制
        project_root: 项目根目录。如果指定，先查 $PROJECT_ROOT/.opencode/knowledge/ 再查全局。
        
    Returns:
        匹配的知识条目列表，按匹配度排序
    """
    if project_root is not None:
        project_kb = Path(project_root) / '.opencode' / 'knowledge'
        results: List[Dict[str, Any]] = []
        seen_ids: Set[str] = set()

        # 1. Query project-level KB first
        if project_kb.exists():
            project_results = _query_by_triggers_single_root(triggers, limit, project_kb)
            for entry in project_results:
                eid = entry.get('id', '')
                if eid not in seen_ids:
                    seen_ids.add(eid)
                    entry['_source'] = 'project'
                    results.append(entry)

        # 2. Query global KB
        global_results = _query_by_triggers_single_root(triggers, limit, get_kb_root())
        for entry in global_results:
            eid = entry.get('id', '')
            if eid not in seen_ids:
                seen_ids.add(eid)
                entry['_source'] = 'global'
                results.append(entry)

        # Re-sort merged results by relevance and trim
        results.sort(key=lambda x: x.get('_relevance_score', 0), reverse=True)
        return results[:limit]

    return _query_by_triggers_single_root(triggers, limit, get_kb_root())


def _query_by_triggers_single_root(
    triggers: List[str], limit: int, kb_root
) -> List[Dict[str, Any]]:
    """
    Internal: query a single knowledge base root by triggers.
    """
    index = load_json(kb_root / 'index.json')
    trigger_index = index.get('trigger_index', {})
    
    # Track matches with type information
    entry_info: Dict[str, Dict[str, Any]] = {}  # entry_id -> {score, match_type}
    
    for trigger in triggers:
        trigger_lower = trigger.lower()
        
        # 1. Exact match (highest priority)
        if trigger_lower in trigger_index:
            for entry_id in trigger_index[trigger_lower]:
                if entry_id not in entry_info:
                    entry_info[entry_id] = {'score': 0, 'match_type': 'exact'}
                entry_info[entry_id]['score'] += 3  # Highest weight
        
        # 2. Partial match (medium priority)
        for indexed_trigger, entry_ids in trigger_index.items():
            if trigger_lower in indexed_trigger or indexed_trigger in trigger_lower:
                for entry_id in entry_ids:
                    if entry_id not in entry_info:
                        entry_info[entry_id] = {'score': 0, 'match_type': 'partial'}
                    elif entry_info[entry_id]['match_type'] == 'exact':
                        continue  # Don't downgrade exact match
                    entry_info[entry_id]['score'] += 2
        
        # 3. Fuzzy match (lowest priority) — use tokenize for richer token coverage
        trigger_tokens = tokenize(trigger)
        for indexed_trigger, entry_ids in trigger_index.items():
            indexed_tokens = tokenize(indexed_trigger)
            fuzzy_score = fuzzy_match(
                trigger_tokens if trigger_tokens else [trigger],
                indexed_tokens if indexed_tokens else [indexed_trigger],
                threshold=FUZZY_MATCH_THRESHOLD
            )
            if fuzzy_score > 0:
                for entry_id in entry_ids:
                    if entry_id not in entry_info:
                        entry_info[entry_id] = {
                            'score': fuzzy_score,  # Use fuzzy score directly
                            'match_type': 'fuzzy'
                        }
    
    if not entry_info:
        return []
    
    # Sort by score
    sorted_entries = sorted(
        entry_info.items(),
        key=lambda x: x[1]['score'],
        reverse=True
    )
    
    # Load entry details
    results: List[Dict[str, Any]] = []
    for entry_id, info in sorted_entries[:limit]:
        # Determine category from entry_id
        category = entry_id.split('-')[0] if '-' in entry_id else 'experience'
        cat_dir = CATEGORY_DIRS.get(category, 'experiences')
        
        entry_path = kb_root / cat_dir / f"{entry_id}.json"
        if entry_path.exists():
            entry = load_json(entry_path)
            entry['_match_score'] = info['score']
            entry['_match_type'] = info['match_type']
            
            # Compute relevance score
            entry['_relevance_score'] = compute_relevance(entry, triggers)
            
            results.append(entry)
            
            # Update usage statistics
            update_usage(entry_path, entry)
    
    # Sort by relevance score
    results.sort(key=lambda x: x.get('_relevance_score', 0), reverse=True)
    
    return results


def query_by_category(category: str, limit: int = 20) -> List[Dict[str, Any]]:
    """
    按分类查询所有知识条目。
    
    Args:
        category: 知识分类
        limit: 返回数量限制
    
    Returns:
        该分类下的知识条目列表
    """
    kb_root = get_kb_root()
    cat_dir = CATEGORY_DIRS.get(category)
    if not cat_dir:
        return []
    
    cat_path = kb_root / cat_dir
    if not cat_path.exists():
        return []
    
    results: List[Dict[str, Any]] = []
    for entry_file in cat_path.glob('*.json'):
        if entry_file.name == 'index.json':
            continue
        entry = load_json(entry_file)
        if entry:
            results.append(entry)
        if len(results) >= limit:
            break
    
    # Sort by effectiveness and usage
    results.sort(key=lambda x: (x.get('effectiveness', 0), x.get('usage_count', 0)), reverse=True)
    return results


def query_by_tags(tags: List[str], limit: int = 10) -> List[Dict[str, Any]]:
    """
    按标签查询知识。
    
    Args:
        tags: 标签列表
        limit: 返回数量限制
    
    Returns:
        匹配标签的知识条目列表
    """
    kb_root = get_kb_root()
    tags_lower = [t.lower() for t in tags]
    results: List[Dict[str, Any]] = []
    
    # Search all categories
    for cat_dir in CATEGORY_DIRS.values():
        cat_path = kb_root / cat_dir
        if not cat_path.exists():
            continue
        
        for entry_file in cat_path.glob('*.json'):
            if entry_file.name == 'index.json':
                continue
            entry = load_json(entry_file)
            if not entry:
                continue
            
            entry_tags = [t.lower() for t in entry.get('tags', [])]
            if any(tag in entry_tags for tag in tags_lower):
                results.append(entry)
                if len(results) >= limit:
                    break
        
        if len(results) >= limit:
            break
    
    return results


def search_content(keyword: str, limit: int = 10) -> List[Dict[str, Any]]:
    """
    全文搜索知识内容。
    
    Args:
        keyword: 搜索关键字
        limit: 返回数量限制
    
    Returns:
        包含关键字的知识条目列表
    """
    kb_root = get_kb_root()
    keyword_lower = keyword.lower()
    results: List[Dict[str, Any]] = []
    
    # Search all categories
    for cat_dir in CATEGORY_DIRS.values():
        cat_path = kb_root / cat_dir
        if not cat_path.exists():
            continue
        
        for entry_file in cat_path.glob('*.json'):
            if entry_file.name == 'index.json':
                continue
            
            # Read raw content for search
            try:
                content_str = entry_file.read_text(encoding='utf-8').lower()
                if keyword_lower in content_str:
                    entry = load_json(entry_file)
                    if entry:
                        # Update usage statistics
                        update_usage(entry_file, entry)
                        results.append(entry)
                        if len(results) >= limit:
                            break
            except IOError:
                continue
        
        if len(results) >= limit:
            break
    
    return results


def get_entry(entry_id: str) -> Optional[Dict[str, Any]]:
    """
    获取单个知识条目。
    
    Args:
        entry_id: 知识条目ID
    
    Returns:
        知识条目，如不存在则返回 None
    """
    kb_root = get_kb_root()
    
    # Try to determine category from ID
    parts = entry_id.split('-')
    if parts:
        category = parts[0]
        cat_dir = CATEGORY_DIRS.get(category)
        if cat_dir:
            entry_path = kb_root / cat_dir / f"{entry_id}.json"
            if entry_path.exists():
                return load_json(entry_path)
    
    # Fallback: search all categories
    for cat_dir in CATEGORY_DIRS.values():
        entry_path = kb_root / cat_dir / f"{entry_id}.json"
        if entry_path.exists():
            return load_json(entry_path)
    
    return None


def query_semantic(query_text: str, limit: int = TOP_K_RESULTS) -> List[Dict[str, Any]]:
    """
    Semantic search using embeddings.

    Falls back to keyword search if sentence-transformers is not installed.

    Args:
        query_text: Natural language query
        limit: Max results

    Returns:
        Matched knowledge entries with _relevance_score
    """
    try:
        from embedding import HAS_EMBEDDING, search as semantic_search
    except ImportError:
        HAS_EMBEDDING = False

    if not HAS_EMBEDDING:
        print("Warning: sentence-transformers not installed, falling back to keyword search",
              file=sys.stderr)
        tokens = query_text.replace(',', ' ').split()
        return query_by_triggers(tokens, limit=limit)

    kb_root = get_kb_root()
    hits = semantic_search(query_text, kb_root, top_k=limit)

    results: List[Dict[str, Any]] = []
    for entry_id, score in hits:
        entry = get_entry(entry_id)
        if entry:
            entry['_relevance_score'] = score
            entry['_match_type'] = 'semantic'
            results.append(entry)

    return results


def query_hybrid(query_text: str, limit: int = TOP_K_RESULTS) -> List[Dict[str, Any]]:
    """
    Hybrid search: combine keyword + semantic results.

    Args:
        query_text: Query string
        limit: Max results

    Returns:
        Merged and deduplicated results
    """
    tokens = query_text.replace(',', ' ').split()
    keyword_results = query_by_triggers(tokens, limit=limit)
    semantic_results = query_semantic(query_text, limit=limit)

    seen_ids: Set[str] = set()
    merged: List[Dict[str, Any]] = []

    for entry in keyword_results:
        eid = entry.get('id', '')
        if eid not in seen_ids:
            seen_ids.add(eid)
            merged.append(entry)

    for entry in semantic_results:
        eid = entry.get('id', '')
        if eid not in seen_ids:
            seen_ids.add(eid)
            merged.append(entry)

    merged.sort(key=lambda x: x.get('_relevance_score', 0), reverse=True)
    return merged[:limit]


def get_stats() -> Dict[str, Any]:
    """获取知识库统计信息。"""
    index = get_global_index()
    return {
        'version': index.get('version', 'unknown'),
        'last_updated': index.get('last_updated'),
        'stats': index.get('stats', {}),
        'trigger_count': len(index.get('trigger_index', {})),
        'recent_entries': index.get('recent_entries', [])[:5]
    }


def format_output(data: Any, fmt: str = 'json') -> str:
    """Format output based on type."""
    if fmt == 'json':
        return json.dumps(data, indent=2, ensure_ascii=False)
    elif fmt == 'markdown':
        if isinstance(data, list):
            lines = []
            for entry in data:
                lines.append(f"### {entry.get('name', 'Unknown')}")
                lines.append(f"- **Category**: {entry.get('category', 'N/A')}")
                lines.append(f"- **Triggers**: {', '.join(entry.get('triggers', [])[:5])}")
                content = entry.get('content', {})
                if 'description' in content:
                    lines.append(f"- **Description**: {content['description'][:100]}...")
                lines.append("")
            return '\n'.join(lines)
        elif isinstance(data, dict):
            lines = []
            for key, value in data.items():
                if isinstance(value, (list, dict)):
                    lines.append(f"**{key}**: {json.dumps(value, ensure_ascii=False)}")
                else:
                    lines.append(f"**{key}**: {value}")
            return '\n'.join(lines)
    return str(data)


def main():
    parser = argparse.ArgumentParser(
        description='Query unified knowledge base',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Query by triggers (most common)
  python knowledge_query.py --trigger react,hooks,state
  
  # Query by category
  python knowledge_query.py --category problem
  
  # Search content
  python knowledge_query.py --search "跨域"
  
  # Get single entry
  python knowledge_query.py --id problem-cors-abc123
  
  # Get stats
  python knowledge_query.py --stats
        """
    )
    
    parser.add_argument('--trigger', '-t', help='Comma-separated trigger keywords')
    parser.add_argument('--category', '-c', choices=list(CATEGORY_DIRS.keys()),
                        help='Query by category')
    parser.add_argument('--tags', help='Comma-separated tags')
    parser.add_argument('--search', '-s', help='Full-text search keyword')
    parser.add_argument('--id', help='Get entry by ID')
    parser.add_argument('--stats', action='store_true', help='Show knowledge base stats')
    parser.add_argument('--limit', '-l', type=int, default=10, help='Result limit')
    parser.add_argument('--format', '-f', choices=['json', 'markdown'], default='json',
                        help='Output format')
    parser.add_argument('--mode', '-m', choices=['keyword', 'semantic', 'hybrid'],
                        default='keyword',
                        help='Search mode: keyword (default), semantic, hybrid')
    
    args = parser.parse_args()
    
    if args.stats:
        result = get_stats()
    elif args.id:
        result = get_entry(args.id)
        if not result:
            print(f"Entry not found: {args.id}", file=sys.stderr)
            sys.exit(1)
    elif args.trigger:
        triggers = [t.strip() for t in args.trigger.split(',')]
        query_text = ' '.join(triggers)
        if args.mode == 'semantic':
            result = query_semantic(query_text, args.limit)
        elif args.mode == 'hybrid':
            result = query_hybrid(query_text, args.limit)
        else:
            result = query_by_triggers(triggers, args.limit)
    elif args.category:
        result = query_by_category(args.category, args.limit)
    elif args.tags:
        tags = [t.strip() for t in args.tags.split(',')]
        result = query_by_tags(tags, args.limit)
    elif args.search:
        result = search_content(args.search, args.limit)
    else:
        # Default: show stats
        result = get_stats()
    
    print(format_output(result, args.format))


if __name__ == '__main__':
    main()
