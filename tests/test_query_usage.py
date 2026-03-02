#!/usr/bin/env python3
"""
Tests for knowledge query usage tracking.
"""

import json
import tempfile
from datetime import datetime
from pathlib import Path

import pytest

# Import from parent directory
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / 'evolving-agent' / 'scripts' / 'knowledge'))

from query import update_usage, load_json


class TestUpdateUsage:
    """Tests for update_usage function."""
    
    def test_update_usage_increments_count(self):
        """usage_count应该递增"""
        with tempfile.TemporaryDirectory() as tmpdir:
            entry_path = Path(tmpdir) / "test-entry.json"
            entry_data = {
                "id": "test-001",
                "name": "Test Entry",
                "usage_count": 5,
                "last_used_at": "2026-01-01T00:00:00"
            }
            
            # Write initial entry
            with open(entry_path, 'w', encoding='utf-8') as f:
                json.dump(entry_data, f)
            
            # Update usage
            update_usage(entry_path, entry_data)
            
            # Verify
            updated = load_json(entry_path)
            assert updated['usage_count'] == 6
    
    def test_update_usage_sets_timestamp(self):
        """last_used_at应该更新为当前时间"""
        with tempfile.TemporaryDirectory() as tmpdir:
            entry_path = Path(tmpdir) / "test-entry.json"
            old_time = "2026-01-01T00:00:00"
            entry_data = {
                "id": "test-002",
                "name": "Test Entry",
                "usage_count": 0,
                "last_used_at": old_time
            }
            
            # Write initial entry
            with open(entry_path, 'w', encoding='utf-8') as f:
                json.dump(entry_data, f)
            
            # Update usage
            update_usage(entry_path, entry_data)
            
            # Verify timestamp updated
            updated = load_json(entry_path)
            assert updated['last_used_at'] != old_time
            # Verify it's a valid ISO timestamp
            datetime.fromisoformat(updated['last_used_at'])
    
    def test_update_usage_handles_missing_count(self):
        """如果usage_count不存在，应该初始化为1"""
        with tempfile.TemporaryDirectory() as tmpdir:
            entry_path = Path(tmpdir) / "test-entry.json"
            entry_data = {
                "id": "test-003",
                "name": "Test Entry"
            }
            
            # Write initial entry
            with open(entry_path, 'w', encoding='utf-8') as f:
                json.dump(entry_data, f)
            
            # Update usage
            update_usage(entry_path, entry_data)
            
            # Verify
            updated = load_json(entry_path)
            assert updated['usage_count'] == 1
    
    def test_update_usage_handles_nonexistent_file(self):
        """文件不存在时应该静默失败"""
        with tempfile.TemporaryDirectory() as tmpdir:
            entry_path = Path(tmpdir) / "nonexistent.json"
            entry_data = {"id": "test-004", "name": "Test"}
            
            # Should not raise exception
            update_usage(entry_path, entry_data)
    
    def test_update_usage_preserves_other_fields(self):
        """更新usage时不应该影响其他字段"""
        with tempfile.TemporaryDirectory() as tmpdir:
            entry_path = Path(tmpdir) / "test-entry.json"
            entry_data = {
                "id": "test-005",
                "name": "Test Entry",
                "category": "problem",
                "tags": ["python", "testing"],
                "effectiveness": 0.85,
                "usage_count": 10
            }
            
            # Write initial entry
            with open(entry_path, 'w', encoding='utf-8') as f:
                json.dump(entry_data, f)
            
            # Update usage
            update_usage(entry_path, entry_data)
            
            # Verify other fields preserved
            updated = load_json(entry_path)
            assert updated['name'] == "Test Entry"
            assert updated['category'] == "problem"
            assert updated['tags'] == ["python", "testing"]
            assert updated['effectiveness'] == 0.85
            assert updated['usage_count'] == 11
