#!/usr/bin/env python3
"""
T03 单元测试：验证 solid-checklist.md 文件存在且内容完整
"""
import re
from pathlib import Path


def test_solid_checklist_exists():
    """验证 solid-checklist.md 文件存在"""
    checklist_path = Path.home() / ".config" / "opencode" / "skills" / "evolving-agent" / "agents" / "references" / "solid-checklist.md"
    
    if not checklist_path.exists():
        raise AssertionError(f"solid-checklist.md 文件不存在: {checklist_path}")
    
    print(f"✅ 文件存在: {checklist_path}")
    return checklist_path


def test_solid_checklist_has_principles():
    """验证文件包含 5 个 SOLID 原则"""
    checklist_path = test_solid_checklist_exists()
    content = checklist_path.read_text()
    
    # 检查 5 个原则都有标题
    principles = {
        'SRP': '单一职责原则',
        'OCP': '开闭原则',
        'LSP': '里氏替换原则',
        'ISP': '接口隔离原则',
        'DIP': '依赖倒置原则'
    }
    
    for abbr, full_name in principles.items():
        if abbr not in content:
            raise AssertionError(f"缺少原则: {abbr} ({full_name})")
        if full_name not in content:
            raise AssertionError(f"缺少原则全称: {full_name}")
    
    print(f"✅ 包含所有 5 个 SOLID 原则")


def test_solid_checklist_has_code_smells():
    """验证文件包含常见代码气味"""
    checklist_path = test_solid_checklist_exists()
    content = checklist_path.read_text()
    
    # 检查是否包含常见代码气味章节
    required_smells = ['Long Method', 'Feature Envy', 'Data Clumps']
    
    for smell in required_smells:
        if smell not in content:
            raise AssertionError(f"缺少代码气味: {smell}")
    
    print(f"✅ 包含常见代码气味检查")


def test_solid_checklist_structure():
    """验证文件结构符合要求"""
    checklist_path = test_solid_checklist_exists()
    content = checklist_path.read_text()
    
    # 统计二级标题数量（应该 >= 5）
    h2_count = len(re.findall(r'^## ', content, re.MULTILINE))
    if h2_count < 5:
        raise AssertionError(f"二级标题数量不足: {h2_count} < 5")
    
    # 统计 SOLID 原则提及次数（应该 >= 5）
    solid_mentions = len(re.findall(r'\b(SRP|OCP|LSP|ISP|DIP)\b', content))
    if solid_mentions < 5:
        raise AssertionError(f"SOLID 原则提及次数不足: {solid_mentions} < 5")
    
    print(f"✅ 文件结构符合要求: {h2_count} 个二级标题, {solid_mentions} 次 SOLID 原则提及")


if __name__ == "__main__":
    test_solid_checklist_exists()
    test_solid_checklist_has_principles()
    test_solid_checklist_has_code_smells()
    test_solid_checklist_structure()
    print("\n✅ 所有 T03 测试通过")
