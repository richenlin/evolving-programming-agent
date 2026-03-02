#!/usr/bin/env python3
"""
T08 单元测试：验证 reviewer 引入结构化流程
"""
import re
from pathlib import Path


def test_reviewer_has_structured_steps():
    """验证 reviewer.md 包含结构化的审查子步骤（2a/2b/2c/2d）"""
    reviewer_path = Path.home() / ".config" / "opencode" / "skills" / "evolving-agent" / "agents" / "reviewer.md"
    
    if not reviewer_path.exists():
        raise AssertionError(f"reviewer.md 文件不存在: {reviewer_path}")
    
    content = reviewer_path.read_text()
    
    # 检查是否包含 4 个子步骤标识（2a/2b/2c/2d）
    required_substeps = ['2a', '2b', '2c', '2d']
    missing_steps = []
    
    for step in required_substeps:
        if step not in content:
            missing_steps.append(step)
    
    if missing_steps:
        raise AssertionError(f"缺少子步骤: {', '.join(missing_steps)}")
    
    print(f"✅ 包含所有 4 个结构化子步骤")


def test_reviewer_references_checklists():
    """验证 reviewer 引用了 review-checklist.md"""
    reviewer_path = Path.home() / ".config" / "opencode" / "skills" / "evolving-agent" / "agents" / "reviewer.md"
    content = reviewer_path.read_text()
    
    required_checklists = [
        'review-checklist.md',
    ]
    
    missing_checklists = []
    for checklist in required_checklists:
        if checklist not in content:
            missing_checklists.append(checklist)
    
    if missing_checklists:
        raise AssertionError(f"未引用 checklist: {', '.join(missing_checklists)}")
    
    print(f"✅ 引用了 review-checklist.md")


def test_substeps_have_content():
    """验证审查步骤涵盖 SOLID、移除、安全、质量 四个维度"""
    reviewer_path = Path.home() / ".config" / "opencode" / "skills" / "evolving-agent" / "agents" / "reviewer.md"
    content = reviewer_path.read_text()
    
    # 检查审查步骤描述中包含关键维度
    dimensions = {
        'SOLID + 架构': ['SOLID', 'SRP'],
        '移除候选': ['移除', '死代码'],
        '安全扫描': ['安全', '注入'],
        '代码质量': ['质量', '错误处理'],
    }
    
    for dim_name, keywords in dimensions.items():
        has_keyword = any(kw in content for kw in keywords)
        if not has_keyword:
            raise AssertionError(f"审查步骤缺少维度 {dim_name}（关键词: {', '.join(keywords)}）")
    
    print(f"✅ 审查步骤涵盖 4 个维度")


if __name__ == "__main__":
    test_reviewer_has_structured_steps()
    test_reviewer_references_checklists()
    test_substeps_have_content()
    print("\n✅ 所有 T08 测试通过")
