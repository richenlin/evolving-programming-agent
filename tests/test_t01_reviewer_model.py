#!/usr/bin/env python3
"""
T01 单元测试：验证 reviewer 模型配置正确
"""
import re
from pathlib import Path


def test_reviewer_model_config():
    """验证 reviewer.md 中的 model 配置是否正确"""
    reviewer_path = Path.home() / ".config" / "opencode" / "skills" / "evolving-agent" / "agents" / "reviewer.md"
    
    if not reviewer_path.exists():
        raise AssertionError(f"reviewer.md 文件不存在: {reviewer_path}")
    
    content = reviewer_path.read_text()
    
    # 提取 model 配置
    match = re.search(r'^model:\s*(.+)$', content, re.MULTILINE)
    if not match:
        raise AssertionError("reviewer.md 中未找到 model 配置")
    
    actual_model = match.group(1).strip()
    expected_model = "openrouter/anthropic/claude-sonnet-4.6"
    
    if actual_model != expected_model:
        raise AssertionError(
            f"模型配置错误\n"
            f"期望: {expected_model}\n"
            f"实际: {actual_model}"
        )
    
    print(f"✅ T01 测试通过: reviewer 模型配置正确 ({actual_model})")
    return True


if __name__ == "__main__":
    test_reviewer_model_config()
