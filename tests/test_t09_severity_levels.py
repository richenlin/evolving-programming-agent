#!/usr/bin/env python3
"""
T09 单元测试：验证 reviewer 严重级别对齐 P0-P3
"""
import re
from pathlib import Path


def test_reviewer_has_severity_levels():
    """验证 reviewer.md 包含 P0-P3 四个严重级别"""
    reviewer_path = Path.home() / ".config" / "opencode" / "skills" / "evolving-agent" / "agents" / "reviewer.md"
    
    if not reviewer_path.exists():
        raise AssertionError(f"reviewer.md 文件不存在: {reviewer_path}")
    
    content = reviewer_path.read_text()
    
    # 检查是否包含 P0-P3 四个级别
    required_levels = ['P0', 'P1', 'P2', 'P3']
    missing_levels = []
    
    for level in required_levels:
        if level not in content:
            missing_levels.append(level)
    
    if missing_levels:
        raise AssertionError(f"缺少严重级别: {', '.join(missing_levels)}")
    
    print(f"✅ 包含所有 4 个严重级别 (P0-P3)")


def test_reviewer_has_severity_table():
    """验证 reviewer.md 包含严重级别表格"""
    reviewer_path = Path.home() / ".config" / "opencode" / "skills" / "evolving-agent" / "agents" / "reviewer.md"
    content = reviewer_path.read_text()
    
    # 检查是否包含严重级别章节
    if '严重级别' not in content:
        raise AssertionError("缺少严重级别章节")
    
    # 检查是否包含表格（至少有 | 符号）
    if 'Critical' not in content or 'High' not in content or 'Medium' not in content or 'Low' not in content:
        raise AssertionError("严重级别表格缺少级别名称")
    
    print(f"✅ 包含严重级别表格")


def test_reviewer_example_format():
    """验证 reviewer_notes 示例使用 [Px] 格式"""
    reviewer_path = Path.home() / ".config" / "opencode" / "skills" / "evolving-agent" / "agents" / "reviewer.md"
    content = reviewer_path.read_text()
    
    # 检查示例是否使用 [Px] 格式
    pattern = r'\[P[0-3]\]'
    matches = re.findall(pattern, content)
    
    if len(matches) < 3:
        raise AssertionError(f"示例中 [Px] 格式数量不足: {len(matches)} < 3")
    
    # 检查是否包含 file:line 格式
    if not re.search(r'\.py:\d+', content):
        raise AssertionError("示例缺少 file:line 格式")
    
    print(f"✅ reviewer_notes 示例使用正确的 [Px] 格式")


def test_no_old_severity_format():
    """验证不再使用旧的严重级别格式"""
    reviewer_path = Path.home() / ".config" / "opencode" / "skills" / "evolving-agent" / "agents" / "reviewer.md"
    content = reviewer_path.read_text()
    
    # 检查是否移除了旧的严重级别格式
    old_formats = ['【严重】', '【一般】', '【建议】']
    found_old = []
    
    for old_format in old_formats:
        if old_format in content:
            found_old.append(old_format)
    
    if found_old:
        raise AssertionError(f"仍使用旧的严重级别格式: {', '.join(found_old)}")
    
    print(f"✅ 已移除旧的严重级别格式")


if __name__ == "__main__":
    test_reviewer_has_severity_levels()
    test_reviewer_has_severity_table()
    test_reviewer_example_format()
    test_no_old_severity_format()
    print("\n✅ 所有 T09 测试通过")
