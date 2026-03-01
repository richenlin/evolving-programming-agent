#!/usr/bin/env python3
"""
T06 单元测试：验证 removal-plan.md 文件存在且内容完整
"""
import re
from pathlib import Path


def test_removal_plan_exists():
    """验证 removal-plan.md 文件存在"""
    checklist_path = Path.home() / ".config" / "opencode" / "skills" / "evolving-agent" / "agents" / "references" / "removal-plan.md"
    
    if not checklist_path.exists():
        raise AssertionError(f"removal-plan.md 文件不存在: {checklist_path}")
    
    print(f"✅ 文件存在: {checklist_path}")
    return checklist_path


def test_removal_plan_has_deletion_strategies():
    """验证文件包含删除策略判断标准"""
    checklist_path = test_removal_plan_exists()
    content = checklist_path.read_text()
    
    # 检查是否包含"安全删除"和"延迟删除"
    if '安全删除' not in content and 'Safe Deletion' not in content:
        raise AssertionError("缺少安全删除策略")
    
    if '延迟删除' not in content and 'Deferred Deletion' not in content and 'defer' not in content:
        raise AssertionError("缺少延迟删除策略")
    
    print(f"✅ 包含删除策略判断标准")


def test_removal_plan_has_output_template():
    """验证文件包含输出模板"""
    checklist_path = test_removal_plan_exists()
    content = checklist_path.read_text()
    
    # 检查是否包含输出模板章节
    if '输出模板' not in content and 'Output' not in content:
        raise AssertionError("缺少输出模板章节")
    
    # 检查是否包含表格格式
    if '```markdown' not in content:
        raise AssertionError("缺少 markdown 示例")
    
    print(f"✅ 包含输出模板")


def test_removal_plan_has_criteria():
    """验证文件包含识别标准"""
    checklist_path = test_removal_plan_exists()
    content = checklist_path.read_text()
    
    # 检查是否包含识别标准
    required_criteria = [
        '未调用',  # unused functions
        'feature flag',
        '重复',  # duplicate
    ]
    
    missing_criteria = []
    for criterion in required_criteria:
        if criterion.lower() not in content.lower():
            missing_criteria.append(criterion)
    
    if missing_criteria:
        raise AssertionError(f"缺少识别标准: {', '.join(missing_criteria)}")
    
    print(f"✅ 包含识别标准")


if __name__ == "__main__":
    test_removal_plan_exists()
    test_removal_plan_has_deletion_strategies()
    test_removal_plan_has_output_template()
    test_removal_plan_has_criteria()
    print("\n✅ 所有 T06 测试通过")
