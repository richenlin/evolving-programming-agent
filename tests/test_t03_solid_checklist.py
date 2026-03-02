#!/usr/bin/env python3
"""
T03 单元测试：验证 review-checklist.md 中包含 SOLID 检查内容
（原 solid-checklist.md 已合并到 review-checklist.md）
"""
import re
from pathlib import Path


def _get_checklist_path() -> Path:
    """返回 review-checklist.md 的路径。"""
    return (
        Path.home()
        / ".config"
        / "opencode"
        / "skills"
        / "evolving-agent"
        / "agents"
        / "references"
        / "review-checklist.md"
    )


def test_solid_checklist_exists():
    """验证 review-checklist.md 文件存在"""
    checklist_path = _get_checklist_path()
    assert checklist_path.exists(), f"review-checklist.md 文件不存在: {checklist_path}"
    print(f"✅ 文件存在: {checklist_path}")


def test_solid_checklist_has_principles():
    """验证文件包含 5 个 SOLID 原则"""
    checklist_path = _get_checklist_path()
    assert checklist_path.exists(), f"review-checklist.md 文件不存在: {checklist_path}"
    content = checklist_path.read_text()

    principles = ['SRP', 'OCP', 'LSP', 'ISP', 'DIP']

    for abbr in principles:
        assert abbr in content, f"缺少原则: {abbr}"

    print(f"✅ 包含所有 5 个 SOLID 原则")


def test_solid_checklist_has_code_smells():
    """验证文件包含常见代码气味"""
    checklist_path = _get_checklist_path()
    assert checklist_path.exists(), f"review-checklist.md 文件不存在: {checklist_path}"
    content = checklist_path.read_text()

    required_smells = ['Long Method', 'Feature Envy', 'Data Clumps']

    for smell in required_smells:
        assert smell in content, f"缺少代码气味: {smell}"

    print(f"✅ 包含常见代码气味检查")


def test_solid_checklist_structure():
    """验证文件结构包含 SOLID 章节"""
    checklist_path = _get_checklist_path()
    assert checklist_path.exists(), f"review-checklist.md 文件不存在: {checklist_path}"
    content = checklist_path.read_text()

    # 统计 SOLID 原则提及次数（应该 >= 5）
    solid_mentions = len(re.findall(r'\b(SRP|OCP|LSP|ISP|DIP)\b', content))
    assert solid_mentions >= 5, f"SOLID 原则提及次数不足: {solid_mentions} < 5"

    print(f"✅ 文件结构符合要求: {solid_mentions} 次 SOLID 原则提及")


if __name__ == "__main__":
    test_solid_checklist_exists()
    test_solid_checklist_has_principles()
    test_solid_checklist_has_code_smells()
    test_solid_checklist_structure()
    print("\n✅ 所有 T03 测试通过")
