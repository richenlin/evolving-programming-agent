#!/usr/bin/env python3
"""
T06 单元测试：验证 review-checklist.md 中包含移除候选检查内容
（原 removal-plan.md 已合并到 review-checklist.md）
"""
import re
from pathlib import Path


def _get_checklist_path() -> Path:
    return (
        Path.home()
        / ".config" / "opencode" / "skills" / "evolving-agent"
        / "agents" / "references" / "review-checklist.md"
    )


def test_removal_plan_exists():
    """验证 review-checklist.md 文件存在"""
    checklist_path = _get_checklist_path()
    assert checklist_path.exists(), f"review-checklist.md 文件不存在: {checklist_path}"
    print(f"✅ 文件存在: {checklist_path}")


def test_removal_plan_has_deletion_strategies():
    """验证文件包含删除策略判断标准"""
    checklist_path = _get_checklist_path()
    assert checklist_path.exists(), f"review-checklist.md 文件不存在: {checklist_path}"
    content = checklist_path.read_text()

    assert '安全删除' in content or 'Safe' in content, "缺少安全删除策略"
    assert '延迟删除' in content or 'deprecated' in content.lower(), "缺少延迟删除策略"

    print(f"✅ 包含删除策略判断标准")


def test_removal_plan_has_criteria():
    """验证文件包含识别标准"""
    checklist_path = _get_checklist_path()
    assert checklist_path.exists(), f"review-checklist.md 文件不存在: {checklist_path}"
    content = checklist_path.read_text()

    required_criteria = [
        '未调用',
        'Feature Flag',
        '重复',
    ]

    missing_criteria = []
    for criterion in required_criteria:
        if criterion.lower() not in content.lower():
            missing_criteria.append(criterion)

    if missing_criteria:
        raise AssertionError(f"缺少识别标准: {', '.join(missing_criteria)}")

    print(f"✅ 包含识别标准")


def test_removal_plan_has_section_header():
    """验证文件包含移除候选章节"""
    checklist_path = _get_checklist_path()
    assert checklist_path.exists(), f"review-checklist.md 文件不存在: {checklist_path}"
    content = checklist_path.read_text()

    assert '移除候选' in content or '2b' in content, "缺少移除候选章节"
    print(f"✅ 包含移除候选章节")


if __name__ == "__main__":
    test_removal_plan_exists()
    test_removal_plan_has_deletion_strategies()
    test_removal_plan_has_criteria()
    test_removal_plan_has_section_header()
    print("\n✅ 所有 T06 测试通过")
