#!/usr/bin/env python3
"""
T07 单元测试：验证 reviewer 包含 preflight 步骤
"""
import re
from pathlib import Path


def test_reviewer_has_preflight_step():
    """验证 reviewer.md 包含 preflight 步骤"""
    reviewer_path = Path.home() / ".config" / "opencode" / "skills" / "evolving-agent" / "agents" / "reviewer.md"
    
    if not reviewer_path.exists():
        raise AssertionError(f"reviewer.md 文件不存在: {reviewer_path}")
    
    content = reviewer_path.read_text()
    
    # 检查是否包含 preflight 步骤
    if '步骤 0' not in content:
        raise AssertionError("缺少步骤 0：Preflight")
    
    if 'Preflight' not in content:
        raise AssertionError("缺少 Preflight 关键词")
    
    print(f"✅ 包含 preflight 步骤")


def test_preflight_has_change_thresholds():
    """验证 preflight 包含变更阈值策略"""
    reviewer_path = Path.home() / ".config" / "opencode" / "skills" / "evolving-agent" / "agents" / "reviewer.md"
    content = reviewer_path.read_text()
    
    # 检查是否包含变更阈值
    if '200 行' not in content and '200' not in content:
        raise AssertionError("缺少 200 行变更阈值")
    
    if '500 行' not in content and '500' not in content:
        raise AssertionError("缺少 500 行变更阈值")
    
    print(f"✅ 包含变更阈值策略")


def test_step_order():
    """验证步骤顺序正确（步骤 0 在步骤 1 之前）"""
    reviewer_path = Path.home() / ".config" / "opencode" / "skills" / "evolving-agent" / "agents" / "reviewer.md"
    content = reviewer_path.read_text()
    lines = content.split('\n')
    
    step0_line = None
    step1_line = None
    
    for i, line in enumerate(lines):
        if '步骤 0' in line:
            step0_line = i
        if '步骤 1' in line:
            step1_line = i
    
    if step0_line is None:
        raise AssertionError("未找到步骤 0")
    
    if step1_line is None:
        raise AssertionError("未找到步骤 1")
    
    if step0_line >= step1_line:
        raise AssertionError(f"步骤顺序错误：步骤 0 在第 {step0_line} 行，步骤 1 在第 {step1_line} 行")
    
    print(f"✅ 步骤顺序正确：步骤 0 在步骤 1 之前")


if __name__ == "__main__":
    test_reviewer_has_preflight_step()
    test_preflight_has_change_thresholds()
    test_step_order()
    print("\n✅ 所有 T07 测试通过")
