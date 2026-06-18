#!/usr/bin/env python3
"""Tests for knowledge import/export (CodeGraph SQLite)."""

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / 'evolving-agent' / 'scripts' / 'knowledge'))

from knowledge_io import export_all, import_all
from kb_helpers import seed_entry

_RUN_PY = str(Path(__file__).parent.parent / 'evolving-agent' / 'scripts' / 'run.py')


class TestKnowledgeIO:
    def test_export_import_roundtrip(self, kb_db, tmp_path, monkeypatch):
        seed_entry(
            kb_db,
            id="experience-test-001",
            name="Test Experience",
            content={"description": "Test description", "context": "Test context"},
            triggers=["test"],
            tags=["testing"],
            created_at="2026-03-01T00:00:00",
        )

        export_file = tmp_path / "export.json"
        count = export_all(str(export_file), format="json")
        assert count >= 1

        from codegraph.db import CodeGraphDB
        from conftest import patch_get_db

        import_db = CodeGraphDB(tmp_path / "import.db")
        patch_get_db(monkeypatch, lambda project_path=None: import_db)

        stats = import_all(str(export_file), merge_strategy="skip")
        assert stats["imported"] >= 1
        assert import_db.get_entry("experience-test-001") is not None

    def test_import_skip_existing(self, kb_db, tmp_path):
        seed_entry(
            kb_db,
            id="experience-existing-001",
            name="Existing Entry",
            created_at="2026-01-01T00:00:00",
        )

        export_data = {
            "entries": [
                {
                    "id": "experience-existing-001",
                    "name": "Modified Entry",
                    "category": "experience",
                    "content": {},
                }
            ]
        }
        export_file = tmp_path / "export.json"
        export_file.write_text(json.dumps(export_data))

        stats = import_all(str(export_file), merge_strategy="skip")
        assert stats["skipped"] >= 1
        assert kb_db.get_entry("experience-existing-001")["name"] == "Existing Entry"


class TestKnowledgeIOCLI:
    def test_cli_export_and_import(self, tmp_path, monkeypatch):
        from codegraph.db import CodeGraphDB

        cg_dir = tmp_path / "kb"
        cg_dir.mkdir(parents=True)
        db = CodeGraphDB(cg_dir / "knowledge.db")
        seed_entry(
            db,
            id="experience-cli-001",
            name="CLI Test Entry",
            content={"description": "test", "context": "", "solution": "s", "pitfalls": []},
            triggers=["cli"],
            created_at="2026-03-01T00:00:00",
        )

        monkeypatch.setenv("KNOWLEDGE_BASE_PATH", str(cg_dir))

        export_file = str(tmp_path / "export.json")
        result = subprocess.run(
            [sys.executable, _RUN_PY, "knowledge", "export", "--output", export_file],
            capture_output=True, text=True,
            env={**os.environ, "KNOWLEDGE_BASE_PATH": str(cg_dir)},
        )
        assert result.returncode == 0, result.stderr
        assert "Exported" in result.stdout

        export_data = json.loads(Path(export_file).read_text())
        assert len(export_data.get("entries", [])) >= 1

        cg_dir2 = tmp_path / "kb2"
        cg_dir2.mkdir(parents=True)
        result2 = subprocess.run(
            [sys.executable, _RUN_PY, "knowledge", "import",
             "--input", export_file, "--merge", "skip"],
            capture_output=True, text=True,
            env={**os.environ, "KNOWLEDGE_BASE_PATH": str(cg_dir2)},
        )
        assert result2.returncode == 0, result2.stderr
        stats = json.loads(result2.stdout)
        assert stats["imported"] >= 1

        imported_db = CodeGraphDB(cg_dir2 / "knowledge.db")
        assert imported_db.get_entry("experience-cli-001") is not None
