#!/usr/bin/env python3
"""
Skill Health Checker

Scan skills directory and generate health status report.
"""

import argparse
import sys
import os
import json
from datetime import datetime
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(
        description='Check health status of all skills',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python health_check.py
  python health_check.py --skills-dir ~/.config/opencode/skill
  python health_check.py --format json
  python health_check.py --format table
        """
    )

    parser.add_argument(
        '--skills-dir',
        default=os.path.expanduser('~/.config/opencode/skill'),
        help='Skills directory path (default: ~/.config/opencode/skill)'
    )

    parser.add_argument(
        '--format',
        choices=['json', 'table'],
        default='json',
        help='Output format (default: json)'
    )

    args = parser.parse_args()

    skills_dir = Path(args.skills_dir)

    # Validate skills directory
    if not skills_dir.exists():
        print(f"Error: Skills directory does not exist: {skills_dir}", file=sys.stderr)
        sys.exit(1)

    if not skills_dir.is_dir():
        print(f"Error: Skills path is not a directory: {skills_dir}", file=sys.stderr)
        sys.exit(1)

    # Scan skills
    skills = scan_skills(skills_dir)

    # Generate report
    report = {
        'timestamp': datetime.now().isoformat(),
        'total': len(skills),
        'skills': skills
    }

    # Output report
    if args.format == 'json':
        print(json.dumps(report, indent=2))
    else:
        print_table_report(report)


def scan_skills(skills_dir: Path) -> list:
    """Scan skills directory and return skill list."""
    skills = []

    for item in skills_dir.iterdir():
        # Skip hidden directories
        if item.name.startswith('.'):
            continue

        if not item.is_dir():
            continue

        # Check if skill directory contains SKILL.md
        skill_md = item / 'SKILL.md'
        if not skill_md.exists():
            continue

        skills.append(item.name)

    return skills


def print_table_report(report: dict):
    """Print report in table format."""
    print(f"Skill 扫描报告")
    print(f"{'='*60}")
    print(f"总计: {report['total']} 个 skill")
    print(f"时间: {report['timestamp']}")
    print()

    if report['skills']:
        print("技能列表:")
        for skill_name in report['skills']:
            print(f"  - {skill_name}")
    else:
        print("未找到任何 skill")


if __name__ == "__main__":
    main()
