#!/usr/bin/env python3
"""
T04 单元测试：验证 review-checklist.md 中包含安全检查内容
（原 security-checklist.md 已合并到 review-checklist.md）
"""
import re
from pathlib import Path


def _get_checklist_path() -> Path:
    return (
        Path.home()
        / ".config" / "opencode" / "skills" / "evolving-agent"
        / "references" / "review-checklist.md"
    )


def test_security_checklist_exists():
    """验证 review-checklist.md 文件存在"""
    checklist_path = _get_checklist_path()
    assert checklist_path.exists(), f"review-checklist.md 文件不存在: {checklist_path}"
    print(f"✅ 文件存在: {checklist_path}")


def test_security_checklist_has_required_topics():
    """验证文件包含必要的安全主题"""
    checklist_path = _get_checklist_path()
    assert checklist_path.exists(), f"review-checklist.md 文件不存在: {checklist_path}"
    content = checklist_path.read_text()

    required_topics = [
        'TOCTOU',
        'JWT',
        'SSRF',
        'SQL',
        'XSS',
    ]

    missing_topics = []
    for topic in required_topics:
        if topic not in content:
            missing_topics.append(topic)

    if missing_topics:
        raise AssertionError(f"缺少关键安全主题: {', '.join(missing_topics)}")

    print(f"✅ 包含所有关键安全主题")


def test_security_checklist_has_idor():
    """验证文件包含 IDOR 检查"""
    checklist_path = _get_checklist_path()
    assert checklist_path.exists(), f"review-checklist.md 文件不存在: {checklist_path}"
    content = checklist_path.read_text()

    assert 'IDOR' in content, "缺少 IDOR 检查"
    print(f"✅ 包含 IDOR 检查")


def test_security_checklist_has_severity_mapping():
    """验证文件包含严重级别映射"""
    checklist_path = _get_checklist_path()
    assert checklist_path.exists(), f"review-checklist.md 文件不存在: {checklist_path}"
    content = checklist_path.read_text()

    if 'P0' not in content or 'P1' not in content or 'P2' not in content:
        raise AssertionError("缺少严重级别映射（P0/P1/P2）")

    print(f"✅ 包含严重级别映射")


if __name__ == "__main__":
    test_security_checklist_exists()
    test_security_checklist_has_required_topics()
    test_security_checklist_has_idor()
    test_security_checklist_has_severity_mapping()
    print("\n✅ 所有 T04 测试通过")
