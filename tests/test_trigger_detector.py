"""
Unit tests for evolution trigger detector.
"""

import pytest

from core.trigger_detector import extract_session_summary, should_trigger_evolution


@pytest.mark.unit
def test_extract_simple_session():
    """Test extracting session summary with simple conversation."""
    context = """
    用户: 帮我修复这个 bug
    助手: 让我看看...
    助手: 修复成功！
    """
    summary = extract_session_summary(context)
    assert summary['attempts'] == 1
    assert summary['success'] is True
    assert summary['feedback'] is None


@pytest.mark.unit
def test_extract_multiple_attempts():
    """Test extracting session summary with multiple attempts."""
    context = """
    用户: 帮我修复这个 bug
    助手: 第一次尝试...失败了
    用户: 还是不行
    助手: 第二次尝试...又失败了
    用户: 再试试
    助手: 第三次尝试...成功了！
    """
    summary = extract_session_summary(context)
    assert summary['attempts'] >= 2
    assert summary['success'] is True


@pytest.mark.unit
def test_extract_with_feedback():
    """Test extracting user feedback."""
    context = """
    用户: 帮我修复这个 bug
    助手: 让我看看...修复了！
    用户: 记住这个解决方案
    """
    summary = extract_session_summary(context)
    assert summary['feedback'] is not None
    assert '记住' in summary['feedback']


@pytest.mark.unit
def test_should_trigger_multiple_attempts():
    """Test that multiple attempts trigger evolution."""
    summary = {'attempts': 3, 'success': True}
    assert should_trigger_evolution(summary) is True


@pytest.mark.unit
def test_should_not_trigger_single_attempt():
    """Test that single attempt does not trigger evolution."""
    summary = {'attempts': 1, 'success': True}
    assert should_trigger_evolution(summary) is False


@pytest.mark.unit
def test_should_trigger_with_feedback():
    """Test that explicit feedback triggers evolution."""
    summary = {'attempts': 1, 'success': True, 'feedback': '记住这个'}
    assert should_trigger_evolution(summary) is True


@pytest.mark.unit
def test_should_not_trigger_simple_success():
    """Test that simple success without feedback does not trigger."""
    summary = {'attempts': 1, 'success': True, 'feedback': '很好'}
    assert should_trigger_evolution(summary) is False


@pytest.mark.unit
def test_should_trigger_english_feedback():
    """Test that English feedback also triggers evolution."""
    summary = {'attempts': 1, 'success': True, 'feedback': 'Remember this'}
    assert should_trigger_evolution(summary) is True


@pytest.mark.unit
def test_should_not_trigger_no_feedback():
    """Test that no feedback does not trigger."""
    summary = {'attempts': 1, 'success': True, 'feedback': None}
    assert should_trigger_evolution(summary) is False
