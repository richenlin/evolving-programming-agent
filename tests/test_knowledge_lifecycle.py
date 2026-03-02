#!/usr/bin/env python3
"""
Tests for knowledge lifecycle management.
"""

import json
import tempfile
from datetime import datetime, timedelta
from pathlib import Path

import pytest

# Import from parent directory
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / 'evolving-agent' / 'scripts' / 'knowledge'))

from lifecycle import decay_unused, get_stale_entries, gc, get_kb_root, CATEGORY_DIRS


class TestDecayUnused:
    """Tests for decay_unused function."""
    
    def test_decay_reduces_effectiveness(self, tmp_path):
        """模拟 90 天未用的条目被衰减"""
        # Setup knowledge base
        kb_root = tmp_path / 'knowledge'
        cat_path = kb_root / 'experiences'
        cat_path.mkdir(parents=True)
        
        # Create entry with old last_used_at
        old_date = (datetime.now() - timedelta(days=100)).isoformat()
        entry_data = {
            "id": "experience-old-001",
            "name": "Old Entry",
            "effectiveness": 0.8,
            "last_used_at": old_date
        }
        
        entry_path = cat_path / "experience-old-001.json"
        with open(entry_path, 'w', encoding='utf-8') as f:
            json.dump(entry_data, f)
        
        # Mock get_kb_root
        import lifecycle
        original_get_kb_root = lifecycle.get_kb_root
        lifecycle.get_kb_root = lambda: kb_root
        
        try:
            # Execute decay
            affected = decay_unused(days_threshold=90, decay_rate=0.1)
            
            # Verify
            assert len(affected) == 1
            assert affected[0]['old_effectiveness'] == 0.8
            assert abs(affected[0]['new_effectiveness'] - 0.7) < 0.01  # Float comparison
            
            # Verify file updated
            with open(entry_path, 'r') as f:
                updated = json.load(f)
            assert abs(updated['effectiveness'] - 0.7) < 0.01  # Float comparison
        finally:
            lifecycle.get_kb_root = original_get_kb_root
    
    def test_decay_skips_recently_used(self, tmp_path):
        """最近使用的条目不受影响"""
        # Setup knowledge base
        kb_root = tmp_path / 'knowledge'
        cat_path = kb_root / 'experiences'
        cat_path.mkdir(parents=True)
        
        # Create entry with recent last_used_at
        recent_date = (datetime.now() - timedelta(days=30)).isoformat()
        entry_data = {
            "id": "experience-recent-001",
            "name": "Recent Entry",
            "effectiveness": 0.8,
            "last_used_at": recent_date
        }
        
        entry_path = cat_path / "experience-recent-001.json"
        with open(entry_path, 'w', encoding='utf-8') as f:
            json.dump(entry_data, f)
        
        # Mock get_kb_root
        import lifecycle
        original_get_kb_root = lifecycle.get_kb_root
        lifecycle.get_kb_root = lambda: kb_root
        
        try:
            # Execute decay
            affected = decay_unused(days_threshold=90, decay_rate=0.1)
            
            # Verify not affected
            assert len(affected) == 0
            
            # Verify file not changed
            with open(entry_path, 'r') as f:
                unchanged = json.load(f)
            assert unchanged['effectiveness'] == 0.8
        finally:
            lifecycle.get_kb_root = original_get_kb_root
    
    def test_effectiveness_floor_at_zero(self, tmp_path):
        """effectiveness 不低于 0"""
        # Setup knowledge base
        kb_root = tmp_path / 'knowledge'
        cat_path = kb_root / 'experiences'
        cat_path.mkdir(parents=True)
        
        # Create entry with very low effectiveness
        old_date = (datetime.now() - timedelta(days=100)).isoformat()
        entry_data = {
            "id": "experience-low-001",
            "name": "Low Effectiveness Entry",
            "effectiveness": 0.05,
            "last_used_at": old_date
        }
        
        entry_path = cat_path / "experience-low-001.json"
        with open(entry_path, 'w', encoding='utf-8') as f:
            json.dump(entry_data, f)
        
        # Mock get_kb_root
        import lifecycle
        original_get_kb_root = lifecycle.get_kb_root
        lifecycle.get_kb_root = lambda: kb_root
        
        try:
            # Execute decay with high rate
            affected = decay_unused(days_threshold=90, decay_rate=0.1)
            
            # Verify
            assert len(affected) == 1
            assert affected[0]['new_effectiveness'] >= 0.0
            
            # Verify file updated
            with open(entry_path, 'r') as f:
                updated = json.load(f)
            assert updated['effectiveness'] >= 0.0
        finally:
            lifecycle.get_kb_root = original_get_kb_root


class TestGetStaleEntries:
    """Tests for get_stale_entries function."""
    
    def test_get_stale_entries(self, tmp_path):
        """正确返回低分条目"""
        # Setup knowledge base
        kb_root = tmp_path / 'knowledge'
        cat_path = kb_root / 'experiences'
        cat_path.mkdir(parents=True)
        
        # Create stale entry
        stale_entry = {
            "id": "experience-stale-001",
            "name": "Stale Entry",
            "effectiveness": 0.05
        }
        
        # Create good entry
        good_entry = {
            "id": "experience-good-001",
            "name": "Good Entry",
            "effectiveness": 0.8
        }
        
        with open(cat_path / "experience-stale-001.json", 'w') as f:
            json.dump(stale_entry, f)
        
        with open(cat_path / "experience-good-001.json", 'w') as f:
            json.dump(good_entry, f)
        
        # Mock get_kb_root
        import lifecycle
        original_get_kb_root = lifecycle.get_kb_root
        lifecycle.get_kb_root = lambda: kb_root
        
        try:
            # Get stale entries
            stale = get_stale_entries(effectiveness_threshold=0.1)
            
            # Verify
            assert len(stale) == 1
            assert stale[0]['id'] == "experience-stale-001"
        finally:
            lifecycle.get_kb_root = original_get_kb_root


class TestGC:
    """Tests for gc function."""
    
    def test_gc_removes_stale(self, tmp_path):
        """gc 删除低分条目"""
        # Setup knowledge base
        kb_root = tmp_path / 'knowledge'
        cat_path = kb_root / 'experiences'
        cat_path.mkdir(parents=True)
        
        # Create stale entry
        stale_entry = {
            "id": "experience-gc-001",
            "name": "Stale Entry for GC",
            "effectiveness": 0.05
        }
        
        entry_path = cat_path / "experience-gc-001.json"
        with open(entry_path, 'w', encoding='utf-8') as f:
            json.dump(stale_entry, f)
        
        # Mock get_kb_root
        import lifecycle
        original_get_kb_root = lifecycle.get_kb_root
        lifecycle.get_kb_root = lambda: kb_root
        
        try:
            # Execute GC
            removed = gc(threshold=0.1, dry_run=False)
            
            # Verify
            assert len(removed) == 1
            assert not entry_path.exists()
        finally:
            lifecycle.get_kb_root = original_get_kb_root
    
    def test_gc_dry_run(self, tmp_path):
        """dry_run 模式不删除文件"""
        # Setup knowledge base
        kb_root = tmp_path / 'knowledge'
        cat_path = kb_root / 'experiences'
        cat_path.mkdir(parents=True)
        
        # Create stale entry
        stale_entry = {
            "id": "experience-dry-001",
            "name": "Stale Entry for Dry Run",
            "effectiveness": 0.05
        }
        
        entry_path = cat_path / "experience-dry-001.json"
        with open(entry_path, 'w', encoding='utf-8') as f:
            json.dump(stale_entry, f)
        
        # Mock get_kb_root
        import lifecycle
        original_get_kb_root = lifecycle.get_kb_root
        lifecycle.get_kb_root = lambda: kb_root
        
        try:
            # Execute GC in dry run mode
            would_remove = gc(threshold=0.1, dry_run=True)
            
            # Verify
            assert len(would_remove) == 1
            assert entry_path.exists()  # File should still exist
        finally:
            lifecycle.get_kb_root = original_get_kb_root
