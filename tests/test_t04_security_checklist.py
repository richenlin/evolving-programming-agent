#!/usr/bin/env python3
"""
T04 单元测试：验证 security-checklist.md 文件存在且内容完整
"""
import re
from pathlib import Path


def test_security_checklist_exists():
    """验证 security-checklist.md 文件存在"""
    checklist_path = Path.home() / ".config" / "opencode" / "skills" / "evolving-agent" / "agents" / "references" / "security-checklist.md"
    
    if not checklist_path.exists():
        raise AssertionError(f"security-checklist.md 文件不存在: {checklist_path}")
    
    print(f"✅ 文件存在: {checklist_path}")
    return checklist_path


def test_security_checklist_has_required_topics():
    """验证文件包含必要的安全主题"""
    checklist_path = test_security_checklist_exists()
    content = checklist_path.read_text()
    
    # 检查关键安全主题
    required_topics = [
        'TOCTOU',
        'Race Condition',
        'JWT',
        'SSRF',
        'SQL 注入',
        'XSS',
    ]
    
    missing_topics = []
    for topic in required_topics:
        if topic not in content:
            missing_topics.append(topic)
    
    if missing_topics:
        raise AssertionError(f"缺少关键安全主题: {', '.join(missing_topics)}")
    
    print(f"✅ 包含所有关键安全主题")


def test_security_checklist_has_examples():
    """验证文件包含反模式示例"""
    checklist_path = test_security_checklist_exists()
    content = checklist_path.read_text()
    
    # 检查是否包含反模式标记
    if '❌' not in content:
        raise AssertionError("缺少反模式示例（应使用 ❌ 标记）")
    
    # 检查是否包含正确模式标记
    if '✅' not in content:
        raise AssertionError("缺少正确模式示例（应使用 ✅ 标记）")
    
    print(f"✅ 包含反模式和正确模式示例")


def test_security_checklist_has_severity_mapping():
    """验证文件包含严重级别映射"""
    checklist_path = test_security_checklist_exists()
    content = checklist_path.read_text()
    
    # 检查是否包含严重级别
    if 'P0' not in content or 'P1' not in content or 'P2' not in content:
        raise AssertionError("缺少严重级别映射（P0/P1/P2）")
    
    print(f"✅ 包含严重级别映射")


if __name__ == "__main__":
    test_security_checklist_exists()
    test_security_checklist_has_required_topics()
    test_security_checklist_has_examples()
    test_security_checklist_has_severity_mapping()
    print("\n✅ 所有 T04 测试通过")
