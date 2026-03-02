#!/usr/bin/env python3
"""
Tests for file_utils atomic operations.
"""

import json
import os
import tempfile
from pathlib import Path

import pytest

# Import from parent directory
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / 'evolving-agent' / 'scripts'))

from core.file_utils import atomic_write_json, atomic_read_json


class TestAtomicWrite:
    """Tests for atomic_write_json function."""
    
    def test_atomic_write_creates_file(self, tmp_path):
        """写入后文件存在且内容正确"""
        filepath = tmp_path / "test.json"
        data = {"key": "value", "number": 42}
        
        atomic_write_json(filepath, data)
        
        assert filepath.exists()
        with open(filepath, 'r', encoding='utf-8') as f:
            loaded = json.load(f)
        assert loaded == data
    
    def test_atomic_write_overwrites(self, tmp_path):
        """覆盖写入不丢数据"""
        filepath = tmp_path / "test.json"
        data1 = {"version": 1, "data": "first"}
        data2 = {"version": 2, "data": "second", "extra": "field"}
        
        # Write first version
        atomic_write_json(filepath, data1)
        
        # Overwrite with second version
        atomic_write_json(filepath, data2)
        
        # Verify second version is intact
        loaded = atomic_read_json(filepath)
        assert loaded == data2
        assert loaded["version"] == 2
        assert loaded["extra"] == "field"
    
    def test_atomic_write_no_partial(self, tmp_path):
        """写入过程中不产生不完整文件（验证无 .tmp 残留）"""
        filepath = tmp_path / "test.json"
        data = {"test": "data"}
        
        atomic_write_json(filepath, data)
        
        # Check no .tmp files remain
        tmp_files = list(tmp_path.glob("*.tmp"))
        assert len(tmp_files) == 0, f"Temp files found: {tmp_files}"
        
        # Check no hidden files remain
        hidden_files = list(tmp_path.glob(".*.json.*"))
        assert len(hidden_files) == 0, f"Hidden files found: {hidden_files}"
    
    def test_atomic_write_creates_parent_dirs(self, tmp_path):
        """自动创建父目录"""
        filepath = tmp_path / "subdir" / "deep" / "test.json"
        data = {"nested": "path"}
        
        atomic_write_json(filepath, data)
        
        assert filepath.exists()
        assert filepath.parent.is_dir()


class TestAtomicRead:
    """Tests for atomic_read_json function."""
    
    def test_atomic_read_nonexistent(self, tmp_path):
        """不存在时返回 None"""
        filepath = tmp_path / "nonexistent.json"
        
        result = atomic_read_json(filepath)
        
        assert result is None
    
    def test_atomic_read_existing_file(self, tmp_path):
        """读取已存在的文件"""
        filepath = tmp_path / "test.json"
        data = {"key": "value", "array": [1, 2, 3]}
        
        # Write using standard method
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f)
        
        # Read using atomic_read_json
        loaded = atomic_read_json(filepath)
        
        assert loaded == data
    
    def test_atomic_read_invalid_json(self, tmp_path):
        """读取无效 JSON 时抛出异常"""
        filepath = tmp_path / "invalid.json"
        
        # Write invalid JSON
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write("{ invalid json }")
        
        with pytest.raises(json.JSONDecodeError):
            atomic_read_json(filepath)


class TestAtomicRoundTrip:
    """Tests for write + read round trips."""
    
    def test_round_trip_simple(self, tmp_path):
        """简单数据往返"""
        filepath = tmp_path / "test.json"
        data = {"simple": "data"}
        
        atomic_write_json(filepath, data)
        loaded = atomic_read_json(filepath)
        
        assert loaded == data
    
    def test_round_trip_complex(self, tmp_path):
        """复杂数据往返"""
        filepath = tmp_path / "test.json"
        data = {
            "string": "value",
            "number": 123,
            "float": 3.14,
            "bool": True,
            "null": None,
            "array": [1, 2, 3],
            "nested": {
                "deep": {
                    "value": "nested"
                }
            },
            "unicode": "中文测试 🎉"
        }
        
        atomic_write_json(filepath, data)
        loaded = atomic_read_json(filepath)
        
        assert loaded == data
