#!/usr/bin/env python3
"""
Unified Knowledge Store — CodeGraph SQLite only.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re as _re
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    from core.config import VALID_CATEGORIES
except ImportError:
    VALID_CATEGORIES = [
        "experience", "tech-stack", "scenario", "problem",
        "testing", "pattern", "skill",
    ]

from backend import get_db, infer_codegraph_type
from quality import is_low_value_entry, content_fingerprint

NOISE_PREFIXES = (
    '经验:', '经验：', '经验: ', '经验： ',
    '最佳实践:', '最佳实践：', '最佳实践: ', '最佳实践： ',
    '注意:', '注意：', '注意: ', '注意： ',
    '偏好:', '偏好：', '偏好: ', '偏好： ',
    '问题:', '问题：', '问题: ', '问题： ',
    '解决:', '解决：', '解决: ', '解决： ',
)

STOP_WORDS = {
    'a', 'an', 'the', 'is', 'are', 'was', 'were', 'be', 'been',
    'to', 'of', 'in', 'for', 'on', 'with', 'at', 'by', 'from',
    'and', 'or', 'but', 'not', 'as', 'if', 'when', 'than',
    'this', 'that', 'these', 'those', 'has', 'have', 'had',
    'will', 'would', 'can', 'could', 'should', 'may', 'might',
    '经验', '解决', '问题', '注意', '偏好', '最佳实践',
    '需要', '使用', '通过', '进行', '可以', '应该',
    '的', '了', '在', '是', '和', '与', '或', '但',
}


def generate_id(category: str, name: str) -> str:
    hash_input = f"{category}:{name}:{datetime.now().isoformat()}"
    hash_suffix = hashlib.md5(hash_input.encode()).hexdigest()[:8]
    name_slug = name.lower().replace(' ', '-').replace('/', '-')[:30]
    return f"{category}-{name_slug}-{hash_suffix}"


def _clean_name(name: str) -> str:
    for prefix in NOISE_PREFIXES:
        if name.startswith(prefix):
            name = name[len(prefix):]
    return name.strip()


def extract_triggers(
    name: str,
    content: Dict[str, Any],
    tags: Optional[List[str]] = None,
) -> List[str]:
    triggers: set = set()
    cleaned_name = _clean_name(name)

    en_words = _re.findall(r'\b[a-zA-Z][a-zA-Z0-9\-\.]+\b', cleaned_name.lower())
    triggers.update(w for w in en_words if len(w) >= 3)
    zh_words = _re.findall(r'[\u4e00-\u9fa5]{2,4}', cleaned_name)
    triggers.update(zh_words)
    tech_terms = _re.findall(r'[a-zA-Z]+[\-\.][a-zA-Z]+', cleaned_name.lower())
    triggers.update(tech_terms)

    if tags:
        triggers.update(t.lower() for t in tags)

    related_tech = content.get('related_tech', [])
    triggers.update(t.lower() for t in related_tech)

    if 'tech_name' in content:
        triggers.add(content['tech_name'].lower())
    if 'framework' in content:
        triggers.add(str(content['framework']).lower())

    for field in ('description', 'solution', 'problem_name', 'scenario_name'):
        text = content.get(field, '')
        if text and isinstance(text, str):
            en_f = _re.findall(r'\b[a-zA-Z][a-zA-Z0-9\-\.]+\b', text.lower())
            triggers.update(w for w in en_f if len(w) >= 3)
            zh_f = _re.findall(r'[\u4e00-\u9fa5]{2,4}', text)
            triggers.update(zh_f)

    triggers = {t for t in triggers if len(t) > 1 and t.lower() not in STOP_WORDS}
    return sorted(triggers)


def store_knowledge(
    category: str,
    name: str,
    content: Dict[str, Any],
    sources: Optional[List[str]] = None,
    tags: Optional[List[str]] = None,
    triggers: Optional[List[str]] = None,
    entry_id: Optional[str] = None,
    project_path: Optional[str] = None,
    _db=None,
) -> Dict[str, Any]:
    if category not in VALID_CATEGORIES:
        raise ValueError(f"Invalid category: {category}. Must be one of: {VALID_CATEGORIES}")

    db = _db or get_db(project_path)
    scope = "project" if project_path else "global"

    probe = {"category": category, "name": name, "content": content}
    if is_low_value_entry(probe):
        raise ValueError(f"Low-value knowledge entry rejected: {name[:80]}")

    if not entry_id:
        fp = content_fingerprint(probe)
        for row in db.list_entries(category=category, limit=2000):
            if content_fingerprint(row) == fp:
                entry_id = row["id"]
                break

    if not entry_id:
        entry_id = generate_id(category, name)

    if triggers is None:
        triggers = extract_triggers(name, content, tags)
    else:
        triggers = list(set(triggers + extract_triggers(name, content, tags)))

    now = datetime.now().isoformat()
    existing = db.get_entry(entry_id) or {}

    merged_sources = list(sources or [])
    if existing.get("sources"):
        merged_sources = list(set(existing["sources"] + merged_sources))

    entry: Dict[str, Any] = {
        "id": entry_id,
        "category": category,
        "name": name,
        "triggers": triggers,
        "content": content,
        "sources": merged_sources,
        "tags": tags or existing.get("tags", []),
        "created_at": existing.get("created_at", now),
        "updated_at": now,
        "usage_count": existing.get("usage_count", 0),
        "effectiveness": existing.get("effectiveness", 0.5),
        "scope": scope,
        "project_path": project_path,
        "codegraph_type": infer_codegraph_type({
            "category": category,
            "tags": tags or [],
        }),
    }

    db.upsert_entry(entry)
    return entry


def store_experience(
    name: str,
    description: str,
    solution: str,
    context: Optional[str] = None,
    pitfalls: Optional[List[str]] = None,
    related_tech: Optional[List[str]] = None,
    sources: Optional[List[str]] = None,
    tags: Optional[List[str]] = None,
    triggers: Optional[List[str]] = None,
    project_path: Optional[str] = None,
    _db=None,
    **kwargs,
) -> Dict[str, Any]:
    content = {
        'description': description,
        'context': context or '',
        'solution': solution,
        'pitfalls': pitfalls or [],
        'related_tech': related_tech or [],
    }
    return store_knowledge(
        'experience', name, content, sources, tags,
        triggers=triggers, project_path=project_path, _db=_db,
    )


def store_tech_stack(
    tech_name: str,
    best_practices: Optional[List[str]] = None,
    conventions: Optional[List[str]] = None,
    common_patterns: Optional[List[str]] = None,
    gotchas: Optional[List[str]] = None,
    version: Optional[str] = None,
    sources: Optional[List[str]] = None,
    triggers: Optional[List[str]] = None,
    project_path: Optional[str] = None,
    _db=None,
    **kwargs,
) -> Dict[str, Any]:
    if 'name' in kwargs and not tech_name:
        tech_name = kwargs.pop('name')
    content = {
        'tech_name': tech_name,
        'version': kwargs.get('version', version or ''),
        'best_practices': best_practices or [],
        'conventions': conventions or [],
        'common_patterns': common_patterns or [],
        'gotchas': gotchas or [],
    }
    return store_knowledge(
        'tech-stack', tech_name, content, sources,
        [tech_name.lower()], triggers=triggers,
        project_path=project_path, _db=_db,
    )


def store_scenario(
    scenario_name: str,
    description: str,
    typical_approach: str,
    steps: Optional[List[str]] = None,
    considerations: Optional[List[str]] = None,
    related_tech: Optional[List[str]] = None,
    sources: Optional[List[str]] = None,
    triggers: Optional[List[str]] = None,
    project_path: Optional[str] = None,
    _db=None,
) -> Dict[str, Any]:
    content = {
        'scenario_name': scenario_name,
        'description': description,
        'typical_approach': typical_approach,
        'steps': steps or [],
        'considerations': considerations or [],
        'related_tech': related_tech or [],
    }
    return store_knowledge(
        'scenario', scenario_name, content, sources,
        triggers=triggers, project_path=project_path, _db=_db,
    )


def store_problem(
    problem_name: str,
    symptoms: List[str],
    root_causes: List[str],
    solutions: List[Dict[str, str]],
    prevention: Optional[List[str]] = None,
    sources: Optional[List[str]] = None,
    tags: Optional[List[str]] = None,
    triggers: Optional[List[str]] = None,
    project_path: Optional[str] = None,
    _db=None,
) -> Dict[str, Any]:
    content = {
        'problem_name': problem_name,
        'symptoms': symptoms,
        'root_causes': root_causes,
        'solutions': solutions,
        'prevention': prevention or [],
    }
    return store_knowledge(
        'problem', problem_name, content, sources, tags,
        triggers=triggers, project_path=project_path, _db=_db,
    )


def store_testing(
    name: str,
    testing_type: str,
    framework: Optional[str] = None,
    best_practices: Optional[List[str]] = None,
    patterns: Optional[List[str]] = None,
    anti_patterns: Optional[List[str]] = None,
    example_structure: Optional[str] = None,
    sources: Optional[List[str]] = None,
    triggers: Optional[List[str]] = None,
    project_path: Optional[str] = None,
    _db=None,
) -> Dict[str, Any]:
    content = {
        'testing_type': testing_type,
        'framework': framework or '',
        'best_practices': best_practices or [],
        'patterns': patterns or [],
        'anti_patterns': anti_patterns or [],
        'example_structure': example_structure or '',
    }
    tags = [testing_type, 'testing']
    if framework:
        tags.append(framework.lower())
    return store_knowledge(
        'testing', name, content, sources, tags,
        triggers=triggers, project_path=project_path, _db=_db,
    )


def store_pattern(
    pattern_name: str,
    pattern_category: str,
    description: str,
    when_to_use: str,
    structure: Optional[str] = None,
    example: Optional[str] = None,
    pros: Optional[List[str]] = None,
    cons: Optional[List[str]] = None,
    sources: Optional[List[str]] = None,
    triggers: Optional[List[str]] = None,
    project_path: Optional[str] = None,
    _db=None,
) -> Dict[str, Any]:
    content = {
        'pattern_name': pattern_name,
        'category': pattern_category,
        'description': description,
        'when_to_use': when_to_use,
        'structure': structure or '',
        'example': example or '',
        'pros': pros or [],
        'cons': cons or [],
    }
    return store_knowledge(
        'pattern', pattern_name, content, sources, [pattern_category],
        triggers=triggers, project_path=project_path, _db=_db,
    )


def store_skill(
    skill_name: str,
    level: str,
    description: str,
    key_concepts: Optional[List[str]] = None,
    practical_tips: Optional[List[str]] = None,
    common_mistakes: Optional[List[str]] = None,
    sources: Optional[List[str]] = None,
    triggers: Optional[List[str]] = None,
    project_path: Optional[str] = None,
    _db=None,
) -> Dict[str, Any]:
    content = {
        'skill_name': skill_name,
        'level': level,
        'description': description,
        'key_concepts': key_concepts or [],
        'practical_tips': practical_tips or [],
        'common_mistakes': common_mistakes or [],
    }
    return store_knowledge(
        'skill', skill_name, content, sources, [level],
        triggers=triggers, project_path=project_path, _db=_db,
    )


def main():
    parser = argparse.ArgumentParser(description='Store knowledge (CodeGraph SQLite)')
    parser.add_argument('--category', '-c', choices=VALID_CATEGORIES)
    parser.add_argument('--name', '-n')
    parser.add_argument('--content')
    parser.add_argument('--source', '-s')
    parser.add_argument('--tags', '-t')
    parser.add_argument('--project', '-p', help='Project root for project-scoped storage')
    parser.add_argument('--from-json', action='store_true')
    args = parser.parse_args()

    project_path = args.project

    if args.from_json:
        data = json.load(sys.stdin)
        entry = store_knowledge(
            category=data.get('category', 'experience'),
            name=data.get('name', 'Unnamed'),
            content=data.get('content', {}),
            sources=[args.source] if args.source else data.get('sources'),
            tags=data.get('tags'),
            triggers=data.get('triggers'),
            project_path=project_path,
        )
        print(json.dumps(entry, indent=2, ensure_ascii=False))
    elif args.category and args.name:
        content = json.loads(args.content) if args.content else {}
        entry = store_knowledge(
            category=args.category,
            name=args.name,
            content=content,
            sources=[args.source] if args.source else None,
            tags=args.tags.split(',') if args.tags else None,
            project_path=project_path,
        )
        print(json.dumps(entry, indent=2, ensure_ascii=False))
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
