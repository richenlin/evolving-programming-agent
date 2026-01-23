#!/usr/bin/env python3
"""
Pattern Extractor v2.0

Extract programming patterns and best practices from GitHub repository info.
Now outputs structured JSON for progressive knowledge storage.

Two output modes:
1. --markdown: Generate knowledge-addon Markdown (legacy)
2. --json: Output structured JSON for store_knowledge.py (new)
3. --store: Directly store to knowledge base (new)
"""

import sys
import json
import re
import os
from pathlib import Path
from datetime import datetime
from typing import Optional


def main():
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Extract patterns from GitHub repository',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Legacy: Generate Markdown addon
  python fetch_github_info.py <url> | python extract_patterns.py --markdown
  
  # New: Output JSON for further processing
  python fetch_github_info.py <url> | python extract_patterns.py --json
  
  # New: Directly store to knowledge base
  python fetch_github_info.py <url> | python extract_patterns.py --store
        """
    )
    
    parser.add_argument(
        '--markdown', '-m',
        action='store_true',
        help='Output as knowledge-addon Markdown (legacy)'
    )
    parser.add_argument(
        '--json', '-j',
        action='store_true',
        help='Output as structured JSON'
    )
    parser.add_argument(
        '--store', '-s',
        action='store_true',
        help='Directly store to knowledge base'
    )
    parser.add_argument(
        '--knowledge-dir',
        help='Knowledge directory path (for --store mode)'
    )
    
    args = parser.parse_args()
    
    # Default to markdown if no option specified
    if not args.markdown and not args.json and not args.store:
        args.markdown = True
    
    # Read repo info from stdin
    repo_info = json.load(sys.stdin)

    # Analyze patterns
    architecture_patterns = detect_architecture_patterns(repo_info.get('file_tree', []))
    tech_stack = detect_tech_stack(repo_info.get('readme', ''))
    conventions = detect_conventions(repo_info.get('readme', ''))
    practices = extract_best_practices(repo_info.get('readme', ''))

    if args.json or args.store:
        # New structured output
        output = {
            'name': repo_info.get('name', 'unknown'),
            'url': repo_info.get('url', ''),
            'hash': repo_info.get('latest_hash', ''),
            'extracted_at': datetime.now().isoformat(),
            'architecture_patterns': architecture_patterns,
            'tech_stack': tech_stack,
            'conventions': conventions,
            'practices': practices
        }
        
        if args.store:
            # Directly store to knowledge base
            store_to_knowledge_base(output, args.knowledge_dir)
        else:
            print(json.dumps(output, indent=2, ensure_ascii=False))
    else:
        # Legacy Markdown output
        addon = generate_knowledge_addon(repo_info, architecture_patterns, tech_stack, conventions, practices)
        print(addon)


def store_to_knowledge_base(extracted: dict, knowledge_dir: Optional[str] = None):
    """Store extracted knowledge to the knowledge base."""
    # Import store_knowledge module
    script_dir = Path(__file__).parent
    sys.path.insert(0, str(script_dir))
    
    try:
        from store_knowledge import (
            store_framework_knowledge,
            store_pattern_knowledge,
            store_practice_knowledge,
            record_repo_learned,
            ensure_directories,
            get_knowledge_dir
        )
    except ImportError as e:
        print(f"Error importing store_knowledge: {e}", file=sys.stderr)
        sys.exit(1)
    
    kb_dir = Path(knowledge_dir) if knowledge_dir else get_knowledge_dir()
    ensure_directories(kb_dir)
    
    source_repo = extracted.get('url', '')
    repo_name = extracted.get('name', 'unknown')
    
    # Get frameworks
    tech_stack = extracted.get('tech_stack', {})
    frameworks = tech_stack.get('frameworks', [])
    
    # Store framework knowledge
    for framework in frameworks:
        store_framework_knowledge(
            kb_dir,
            framework=framework,
            source_repo=source_repo,
            patterns=extracted.get('architecture_patterns', []),
            conventions=extracted.get('conventions', [])
        )
    
    # Store architecture patterns
    for pattern in extracted.get('architecture_patterns', []):
        store_pattern_knowledge(
            kb_dir,
            pattern=pattern,
            source_repo=source_repo,
            applicable_to=frameworks
        )
    
    # Store practices
    for practice in extracted.get('practices', []):
        store_practice_knowledge(
            kb_dir,
            practice=practice,
            source_repo=source_repo
        )
    
    # Record repo
    record_repo_learned(kb_dir, source_repo, repo_name)
    
    print(f"Successfully stored knowledge from {repo_name}")
    print(f"  - Frameworks: {len(frameworks)}")
    print(f"  - Patterns: {len(extracted.get('architecture_patterns', []))}")
    print(f"  - Practices: {len(extracted.get('practices', []))}")


def detect_conventions(readme: str) -> list:
    """Detect code conventions from README."""
    conventions = []
    readme_lower = readme.lower()

    convention_checks = [
        ('prettier', '代码格式化: Prettier'),
        ('eslint', '代码检查: ESLint'),
        ('typescript', '类型安全: TypeScript'),
        ('husky', '提交前检查: Git Hooks'),
        ('pre-commit', '提交前检查: Git Hooks'),
        ('conventional commits', '提交规范: Conventional Commits'),
        ('semantic versioning', '版本管理: Semantic Versioning'),
        ('golint', '代码检查: golint'),
        ('gofmt', '代码格式化: gofmt'),
        ('checkstyle', '代码检查: Checkstyle'),
        ('spotless', '代码格式化: Spotless'),
        ('black', '代码格式化: Black'),
        ('flake8', '代码检查: Flake8'),
        ('mypy', '类型检查: mypy'),
        ('rustfmt', '代码格式化: rustfmt'),
        ('clippy', '代码检查: Clippy'),
    ]
    
    for keyword, convention in convention_checks:
        if keyword in readme_lower and convention not in conventions:
            conventions.append(convention)

    return conventions


def extract_best_practices(readme: str) -> list:
    """Extract best practices from README."""
    practices = []
    readme_lower = readme.lower()

    practice_checks = [
        (['testing', 'test coverage', 'unit test'], '完整的测试覆盖'),
        (['documentation', 'docs'], '完善的文档说明'),
        (['ci/cd', 'github actions', 'gitlab ci', 'jenkins'], '自动化 CI/CD 流程'),
        (['docker', 'container', 'kubernetes'], '容器化部署支持'),
        (['environment variable', '.env'], '环境变量配置管理'),
        (['logging', 'observability'], '日志和可观测性'),
        (['security', 'authentication', 'authorization'], '安全性设计'),
        (['api versioning', 'backward compatible'], 'API 版本管理'),
        (['error handling', 'graceful'], '错误处理机制'),
        (['dependency injection', 'di'], '依赖注入'),
    ]
    
    for keywords, practice in practice_checks:
        if any(kw in readme_lower for kw in keywords) and practice not in practices:
            practices.append(practice)

    return practices


def detect_tech_stack(readme: str) -> dict:
    """Detect technology stack from README content."""
    readme_lower = readme.lower()

    tech_stack = {
        'frameworks': [],
        'tools': [],
        'libraries': []
    }

    # Frameworks (extended)
    frameworks = {
        # JavaScript/TypeScript
        'react': 'React', 'vue': 'Vue', 'angular': 'Angular', 'svelte': 'Svelte',
        'next.js': 'Next', 'nuxt.js': 'Nuxt', 'express': 'Express', 'fastify': 'Fastify',
        'nest.js': 'NestJS', 'remix': 'Remix', 'astro': 'Astro',
        # Python
        'django': 'Django', 'flask': 'Flask', 'fastapi': 'FastAPI',
        # Go
        'gin': 'Gin', 'fiber': 'Fiber', 'echo': 'Echo', 'chi': 'Chi',
        # Java
        'spring boot': 'Spring Boot', 'spring': 'Spring', 'quarkus': 'Quarkus',
        'micronaut': 'Micronaut',
        # Ruby
        'rails': 'Rails', 'sinatra': 'Sinatra',
        # PHP
        'laravel': 'Laravel', 'symfony': 'Symfony',
        # Rust
        'actix': 'Actix', 'axum': 'Axum', 'rocket': 'Rocket',
    }
    
    for keyword, name in frameworks.items():
        if keyword in readme_lower and name not in tech_stack['frameworks']:
            tech_stack['frameworks'].append(name)

    # Tools (extended)
    tools = {
        # Languages
        'typescript': 'TypeScript', 'javascript': 'JavaScript', 'python': 'Python',
        'golang': 'Go', 'go ': 'Go', 'rust': 'Rust', 'java': 'Java', 'kotlin': 'Kotlin',
        # Package managers
        'npm': 'npm', 'yarn': 'Yarn', 'pnpm': 'pnpm', 'pip': 'pip', 'poetry': 'Poetry',
        'maven': 'Maven', 'gradle': 'Gradle', 'cargo': 'Cargo',
        # DevOps
        'docker': 'Docker', 'kubernetes': 'Kubernetes', 'jenkins': 'Jenkins',
        'github actions': 'GitHub Actions', 'gitlab ci': 'GitLab CI',
        # Build tools
        'webpack': 'Webpack', 'vite': 'Vite', 'parcel': 'Parcel', 'esbuild': 'esbuild',
        # Testing
        'jest': 'Jest', 'vitest': 'Vitest', 'playwright': 'Playwright', 'cypress': 'Cypress',
        'pytest': 'pytest', 'junit': 'JUnit', 'testify': 'testify',
        # Databases
        'mongodb': 'MongoDB', 'postgresql': 'PostgreSQL', 'mysql': 'MySQL',
        'redis': 'Redis', 'sqlite': 'SQLite', 'elasticsearch': 'Elasticsearch',
    }
    
    for keyword, name in tools.items():
        if keyword in readme_lower and name not in tech_stack['tools']:
            tech_stack['tools'].append(name)

    # Libraries (extended)
    libraries = {
        # JavaScript
        'react query': 'React Query', 'zustand': 'Zustand', 'redux': 'Redux',
        'axios': 'Axios', 'zod': 'Zod', 'yup': 'Yup',
        'tailwind': 'Tailwind', 'material-ui': 'Material UI', 'ant design': 'Ant Design',
        'prisma': 'Prisma', 'sequelize': 'Sequelize', 'typeorm': 'TypeORM',
        # Go
        'gorm': 'GORM', 'sqlx': 'sqlx', 'viper': 'Viper', 'cobra': 'Cobra',
        # Java
        'mybatis': 'MyBatis', 'hibernate': 'Hibernate', 'lombok': 'Lombok',
        # Python
        'sqlalchemy': 'SQLAlchemy', 'celery': 'Celery', 'pydantic': 'Pydantic',
    }
    
    for keyword, name in libraries.items():
        if keyword in readme_lower and name not in tech_stack['libraries']:
            tech_stack['libraries'].append(name)

    return tech_stack


def detect_architecture_patterns(file_tree: list) -> list:
    """Detect architecture patterns from file tree."""
    patterns = []
    file_tree_str = ' '.join(file_tree).lower()

    pattern_checks = [
        (['features/', 'feature/'], 'Feature-Based Architecture'),
        (['components/', 'component/'], 'Component-Based Design'),
        (['hooks/', 'hook/'], 'Custom Hooks Pattern'),
        (['services/', 'repositories/'], 'Repository Pattern'),
        (['store/', 'state/'], 'State Management Layer'),
        (['domain/', 'entities/'], 'Domain-Driven Design'),
        (['handlers/', 'controllers/'], 'Handler/Controller Pattern'),
        (['middleware/', 'middlewares/'], 'Middleware Pattern'),
        (['internal/', 'pkg/'], 'Go Standard Layout'),
        (['cmd/', 'internal/'], 'Go CLI Application'),
        (['src/main/java/', 'src/test/java/'], 'Maven Standard Layout'),
        (['layers/', 'layer/'], 'Layered Architecture'),
        (['modules/', 'module/'], 'Modular Architecture'),
        (['api/', 'routes/'], 'API Routes Pattern'),
        (['utils/', 'helpers/'], 'Utility Pattern'),
    ]
    
    for keywords, pattern in pattern_checks:
        if any(kw in file_tree_str for kw in keywords) and pattern not in patterns:
            patterns.append(pattern)

    return patterns


def generate_knowledge_addon(repo_info: dict, patterns: list, tech_stack: dict, conventions: list, practices: list) -> str:
    """Generate knowledge-addon format Markdown (legacy format)."""
    architecture_text = '\n'.join(f"- {p}" for p in patterns) if patterns else "- 未检测到明显架构模式"

    stack_sections = []
    if tech_stack.get('frameworks'):
        stack_sections.append(f"### 框架\n" + '\n'.join(f"- {fw}" for fw in tech_stack['frameworks']))
    if tech_stack.get('tools'):
        stack_sections.append(f"### 工具\n" + '\n'.join(f"- {t}" for t in tech_stack['tools']))
    if tech_stack.get('libraries'):
        stack_sections.append(f"### 库\n" + '\n'.join(f"- {l}" for l in tech_stack['libraries']))

    tech_stack_text = '\n\n'.join(stack_sections) if stack_sections else "- 未检测到明显技术栈"
    conventions_text = '\n'.join(f"- {c}" for c in conventions) if conventions else "- 未检测到明显代码规范"
    practices_text = '\n'.join(f"- {p}" for p in practices) if practices else "- 未检测到明显最佳实践"

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

{conventions_text}

## 技术栈

{tech_stack_text}

## 最佳实践

{practices_text}

## 应用场景
当处理相关技术栈的项目时，自动参考这些范式。
"""
    return template


if __name__ == "__main__":
    main()
