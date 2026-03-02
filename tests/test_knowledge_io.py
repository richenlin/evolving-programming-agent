#!/usr/bin/env python3
"""
Tests for knowledge import/export.
"""

import json
import subprocess
import tempfile
from pathlib import Path

import pytest

# Import from parent directory
import sys
_SCRIPTS_DIR = str(Path(__file__).parent.parent / 'evolving-agent' / 'scripts')
sys.path.insert(0, str(Path(__file__).parent.parent / 'evolving-agent' / 'scripts' / 'knowledge'))

from knowledge_io import export_all, import_all
import knowledge_io as _kb_io_module

_RUN_PY = str(Path(__file__).parent.parent / 'evolving-agent' / 'scripts' / 'run.py')


class TestKnowledgeIO:
    """Tests for knowledge import/export."""
    
    def test_export_import_roundtrip(self, tmp_path):
        """导出后导入，数据完整一致"""
        # Setup knowledge base
        kb_root = tmp_path / 'knowledge'
        kb_root.mkdir(parents=True)
        
        # Create test entry
        exp_dir = kb_root / 'experiences'
        exp_dir.mkdir(parents=True)
        
        test_entry = {
            "id": "experience-test-001",
            "name": "Test Experience",
            "content": {
                "description": "Test description",
                "context": "Test context"
            },
            "triggers": ["test"],
            "tags": ["testing"],
            "created_at": "2026-03-01T00:00:00"
        }
        
        entry_path = exp_dir / "experience-test-001.json"
        with open(entry_path, 'w') as f:
            json.dump(test_entry, f)
        
        # Mock get_kb_root
        original_get_kb_root = _kb_io_module.get_kb_root
        _kb_io_module.get_kb_root = lambda: kb_root
        
        try:
            # Export
            export_file = tmp_path / "export.json"
            count = export_all(str(export_file), format="json")
            
            # Verify export
            assert count >= 1
            assert export_file.exists()
            
            with open(export_file, 'r') as f:
                export_data = json.load(f)
            
            assert "entries" in export_data
            assert len(export_data["entries"]) >= 1
            
            # Import to new location
            new_kb = tmp_path / 'new_knowledge'
            new_kb.mkdir(parents=True)
            _kb_io_module.get_kb_root = lambda: new_kb
            
            stats = import_all(str(export_file), merge_strategy="skip")
            
            # Verify import
            assert stats["imported"] >= 1
            
        finally:
            _kb_io_module.get_kb_root = original_get_kb_root
    
    def test_import_skip_existing(self, tmp_path):
        """--merge skip 不覆盖已有条目"""
        kb_root = tmp_path / 'knowledge'
        kb_root.mkdir(parents=True)
        
        # Create existing entry
        exp_dir = kb_root / 'experiences'
        exp_dir.mkdir(parents=True)
        
        existing_entry = {
            "id": "experience-existing-001",
            "name": "Existing Entry",
            "created_at": "2026-01-01T00:00:00"
        }
        
        with open(exp_dir / "experience-existing-001.json", 'w') as f:
            json.dump(existing_entry, f)
        
        # Create export file with same entry
        export_data = {
            "entries": [
                {
                    "id": "experience-existing-001",
                    "name": "Modified Entry",
                    "_category": "experiences"
                }
            ]
        }
        
        export_file = tmp_path / "export.json"
        with open(export_file, 'w') as f:
            json.dump(export_data, f)
        
        # Mock get_kb_root
        original_get_kb_root = _kb_io_module.get_kb_root
        _kb_io_module.get_kb_root = lambda: kb_root
        
        try:
            stats = import_all(str(export_file), merge_strategy="skip")
            
            # Should skip existing
            assert stats["skipped"] >= 1
            
            # Verify original not overwritten
            with open(exp_dir / "experience-existing-001.json", 'r') as f:
                entry = json.load(f)
            
            assert entry["name"] == "Existing Entry"
            
        finally:
            _kb_io_module.get_kb_root = original_get_kb_root
    
    def test_export_markdown_format(self, tmp_path):
        """--format markdown 输出可读的 markdown 文档"""
        kb_root = tmp_path / 'knowledge'
        kb_root.mkdir(parents=True)
        
        # Create test entry
        exp_dir = kb_root / 'experiences'
        exp_dir.mkdir(parents=True)
        
        test_entry = {
            "id": "experience-md-001",
            "name": "Markdown Test",
            "content": {
                "description": "Test for markdown export"
            },
            "created_at": "2026-03-01T00:00:00"
        }
        
        with open(exp_dir / "experience-md-001.json", 'w') as f:
            json.dump(test_entry, f)
        
        # Mock get_kb_root
        original_get_kb_root = _kb_io_module.get_kb_root
        _kb_io_module.get_kb_root = lambda: kb_root
        
        try:
            # Export to markdown
            export_file = tmp_path / "export.md"
            count = export_all(str(export_file), format="markdown")
            
            # Verify
            assert export_file.exists()
            
            with open(export_file, 'r') as f:
                content = f.read()
            
            assert "# Knowledge Base Export" in content
            assert "Markdown Test" in content
            
        finally:
            _kb_io_module.get_kb_root = original_get_kb_root


class TestKnowledgeIOCLI:
    """CLI-level tests for knowledge export/import commands."""

    def test_cli_export_and_import(self, tmp_path):
        """run.py knowledge export/import commands work end-to-end"""
        import os
        env = os.environ.copy()
        env['KNOWLEDGE_BASE_PATH'] = str(tmp_path / 'kb')

        # Prepare knowledge base with one entry
        kb_root = tmp_path / 'kb'
        exp_dir = kb_root / 'experiences'
        exp_dir.mkdir(parents=True)
        entry = {
            "id": "experience-cli-001",
            "name": "CLI Test Entry",
            "content": {"description": "test"},
            "triggers": ["cli"],
            "created_at": "2026-03-01T00:00:00"
        }
        with open(exp_dir / "experience-cli-001.json", 'w') as f:
            json.dump(entry, f)

        export_file = str(tmp_path / 'export.json')

        # Test export
        result = subprocess.run(
            [sys.executable, _RUN_PY, 'knowledge', 'export', '--output', export_file],
            capture_output=True, text=True, env=env
        )
        assert result.returncode == 0, f"export failed: {result.stderr}"
        assert 'Exported' in result.stdout

        # Verify export file
        with open(export_file) as f:
            data = json.load(f)
        assert data['total_entries'] >= 1

        # Test import (into empty kb — must pre-create dir so get_kb_root uses it)
        kb2 = tmp_path / 'kb2'
        kb2.mkdir(parents=True)
        env2 = os.environ.copy()
        env2['KNOWLEDGE_BASE_PATH'] = str(kb2)
        result2 = subprocess.run(
            [sys.executable, _RUN_PY, 'knowledge', 'import',
             '--input', export_file, '--merge', 'skip'],
            capture_output=True, text=True, env=env2
        )
        assert result2.returncode == 0, f"import failed: {result2.stderr}"
        stats = json.loads(result2.stdout)
        assert stats['imported'] >= 1
