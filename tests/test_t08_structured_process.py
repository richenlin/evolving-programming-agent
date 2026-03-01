#!/usr/bin/env python3
"""
T08 单元测试：验证 reviewer 引入 6 步结构化流程
"""
import re
from pathlib import Path


def test_reviewer_has_structured_steps():
    """验证 reviewer.md 包含结构化的 4 个子步骤"""
    reviewer_path = Path.home() / ".config" / "opencode" / "skills" / "evolving-agent" / "agents" / "reviewer.md"
    
    if not reviewer_path.exists():
        raise AssertionError(f"reviewer.md 文件不存在: {reviewer_path}")
    
    content = reviewer_path.read_text()
    
    # 检查是否包含 4 个子步骤
    required_steps = ['步骤 2a', '步骤 2b', '步骤 2c', '步骤 2d']
    missing_steps = []
    
    for step in required_steps:
        if step not in content:
            missing_steps.append(step)
    
    if missing_steps:
        raise AssertionError(f"缺少子步骤: {', '.join(missing_steps)}")
    
    print(f"✅ 包含所有 4 个结构化子步骤")


def test_reviewer_references_checklists():
    """验证 reviewer 引用了所有 4 个 checklist"""
    reviewer_path = Path.home() / ".config" / "opencode" / "skills" / "evolving-agent" / "agents" / "reviewer.md"
    content = reviewer_path.read_text()
    
    # 检查是否引用了所有 checklist
    required_checklists = [
        'solid-checklist.md',
        'security-checklist.md',
        'quality-checklist.md',
        'removal-plan.md'
    ]
    
    missing_checklists = []
    for checklist in required_checklists:
        if checklist not in content:
            missing_checklists.append(checklist)
    
    if missing_checklists:
        raise AssertionError(f"未引用 checklist: {', '.join(missing_checklists)}")
    
    print(f"✅ 引用了所有 4 个 checklist")


def test_substeps_have_content():
    """验证每个子步骤包含具体内容"""
    reviewer_path = Path.home() / ".config" / "opencode" / "skills" / "evolving-agent" / "agents" / "reviewer.md"
    content = reviewer_path.read_text()
    
    # 检查每个子步骤是否包含检查要点
    substeps = {
        '步骤 2a': ['SOLID', 'SRP', 'OCP', 'LSP'],
        '步骤 2b': ['移除', '死代码', '冗余'],
        '步骤 2c': ['安全', '注入', 'Race Condition'],
        '步骤 2d': ['质量', '错误处理', '边界条件']
    }
    
    for step, keywords in substeps.items():
        # 提取该子步骤的内容（简单方法：查找到下一个步骤之间的内容）
        step_start = content.find(step)
        if step_start == -1:
            raise AssertionError(f"未找到 {step}")
        
        # 查找下一个步骤（或文件结束）
        next_step_start = len(content)
        for next_step in ['步骤 2b', '步骤 2c', '步骤 2d', '步骤 3']:
            pos = content.find(next_step, step_start + len(step))
            if pos != -1 and pos < next_step_start:
                next_step_start = pos
        
        step_content = content[step_start:next_step_start]
        
        # 检查是否至少包含一个关键词
        has_keyword = any(keyword in step_content for keyword in keywords)
        if not has_keyword:
            raise AssertionError(f"{step} 缺少具体内容（关键词: {', '.join(keywords)}）")
    
    print(f"✅ 每个子步骤包含具体内容")


if __name__ == "__main__":
    test_reviewer_has_structured_steps()
    test_reviewer_references_checklists()
    test_substeps_have_content()
    print("\n✅ 所有 T08 测试通过")
