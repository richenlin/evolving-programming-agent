#!/usr/bin/env python3
"""
T01 单元测试：验证 reviewer 模型配置正确
"""
import re

from conftest import REVIEWER_MODEL, resolve_evolving_agent_path


def test_reviewer_model_config():
    """验证 reviewer.md 中的 model 配置是否正确"""
    reviewer_path = resolve_evolving_agent_path("agents", "reviewer.md")
    content = reviewer_path.read_text(encoding="utf-8")

    match = re.search(r"^model:\s*(.+)$", content, re.MULTILINE)
    assert match, "reviewer.md 中未找到 model 配置"

    actual_model = match.group(1).strip()
    assert actual_model == REVIEWER_MODEL, (
        f"模型配置错误\n期望: {REVIEWER_MODEL}\n实际: {actual_model}\n文件: {reviewer_path}"
    )


if __name__ == "__main__":
    test_reviewer_model_config()
    print(f"✅ T01 测试通过: reviewer 模型配置正确 ({REVIEWER_MODEL})")
