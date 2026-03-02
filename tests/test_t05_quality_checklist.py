#!/usr/bin/env python3
"""
T05 单元测试：验证 quality-checklist.md 文件存在且内容完整
"""
import re
from pathlib import Path


def _get_checklist_path() -> Path:
    return (
        Path.home()
        / ".config" / "opencode" / "skills" / "evolving-agent"
        / "agents" / "references" / "quality-checklist.md"
    )


def test_quality_checklist_exists():
    """验证 quality-checklist.md 文件存在"""
    checklist_path = _get_checklist_path()
    assert checklist_path.exists(), f"quality-checklist.md 文件不存在: {checklist_path}"
    print(f"✅ 文件存在: {checklist_path}")


def test_quality_checklist_has_required_sections():
    """验证文件包含必要的章节"""
    checklist_path = _get_checklist_path()
    assert checklist_path.exists(), f"quality-checklist.md 文件不存在: {checklist_path}"
    content = checklist_path.read_text()

    # 检查关键章节
    required_sections = [
        '错误处理',
        '性能',
        '边界条件',
        'N+1',
        'cache',
        'null',
    ]

    missing_sections = [s for s in required_sections if s.lower() not in content.lower()]
    assert not missing_sections, f"缺少关键章节: {', '.join(missing_sections)}"
    print(f"✅ 包含所有关键章节")


def test_quality_checklist_has_anti_patterns():
    """验证文件包含反模式示例"""
    checklist_path = _get_checklist_path()
    assert checklist_path.exists(), f"quality-checklist.md 文件不存在: {checklist_path}"
    content = checklist_path.read_text()

    assert 'N+1' in content, "缺少 N+1 查询反例"
    assert 'truthy' in content.lower(), "缺少边界条件 anti-pattern（truthy check）"
    print(f"✅ 包含反模式示例")


def test_quality_checklist_has_code_examples():
    """验证文件包含代码示例"""
    checklist_path = _get_checklist_path()
    assert checklist_path.exists(), f"quality-checklist.md 文件不存在: {checklist_path}"
    content = checklist_path.read_text()
    
    # 检查是否包含代码块
    if '```python' not in content and '```javascript' not in content:
        raise AssertionError("缺少代码示例")
    
    # 检查是否包含反模式标记
    if '❌' not in content or '✅' not in content:
        raise AssertionError("缺少反模式/正确模式标记")
    
    print(f"✅ 包含代码示例")


if __name__ == "__main__":
    test_quality_checklist_exists()
    test_quality_checklist_has_required_sections()
    test_quality_checklist_has_anti_patterns()
    test_quality_checklist_has_code_examples()
    print("\n✅ 所有 T05 测试通过")
