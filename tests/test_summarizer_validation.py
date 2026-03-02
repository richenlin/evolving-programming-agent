#!/usr/bin/env python3
"""
Tests for summarizer validation functions.
"""

import sys
from pathlib import Path

import pytest

# Import from parent directory
sys.path.insert(0, str(Path(__file__).parent.parent / 'evolving-agent' / 'scripts' / 'knowledge'))

from summarizer import validate_input


class TestValidateInput:
    """Tests for validate_input function."""
    
    def test_valid_problem_solution_format(self):
        """问题→解决格式应该通过验证"""
        text = "问题：登录失败 → 解决：检查token是否过期"
        is_valid, result = validate_input(text)
        
        assert is_valid is True
        assert result == text
    
    def test_valid_decision_format(self):
        """决策→原因格式应该通过验证"""
        text = "决策：使用PostgreSQL → 原因：需要事务支持"
        is_valid, result = validate_input(text)
        
        assert is_valid is True
        assert result == text
    
    def test_valid_lesson_format(self):
        """教训→避免格式应该通过验证"""
        text = "教训：忘记关闭文件句柄 → 避免：使用with语句"
        is_valid, result = validate_input(text)
        
        assert is_valid is True
        assert result == text
    
    def test_auto_format_free_text(self):
        """自由文本应该被自动矫正为问题→解决格式"""
        text = "遇到了空指针异常。添加了null检查。"
        is_valid, result = validate_input(text)
        
        assert is_valid is True
        assert "问题：" in result
        assert "→" in result
        assert "解决：" in result
        assert "遇到了空指针异常" in result
        assert "添加了null检查" in result
    
    def test_auto_format_single_sentence(self):
        """单句文本应该被包装为通用格式"""
        text = "使用pytest进行单元测试"
        is_valid, result = validate_input(text)
        
        assert is_valid is True
        # 单句会被包装为"经验："格式
        assert "经验：" in result or result == text
    
    def test_invalid_empty_input(self):
        """空输入应该返回False"""
        is_valid, result = validate_input("")
        
        assert is_valid is False
        assert "空" in result or "empty" in result.lower()
    
    def test_invalid_whitespace_only(self):
        """只有空白字符的输入应该返回False"""
        is_valid, result = validate_input("   \n\t  ")
        
        assert is_valid is False
    
    def test_preserves_formatted_text(self):
        """已格式化的文本不应该被修改"""
        text = "问题：API响应慢 → 解决：添加了Redis缓存层"
        is_valid, result = validate_input(text)
        
        assert is_valid is True
        assert result == text
    
    def test_chinese_arrow_format(self):
        """中文箭头格式也应该支持"""
        text = "问题：内存泄漏 -> 解决：及时释放资源"
        is_valid, result = validate_input(text)
        
        assert is_valid is True
    
    def test_multiline_input(self):
        """多行输入应该被正确处理"""
        text = """问题：数据库连接超时
原因：连接池配置过小
解决：增大连接池大小到20"""
        is_valid, result = validate_input(text)
        
        assert is_valid is True
