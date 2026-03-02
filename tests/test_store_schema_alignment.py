#!/usr/bin/env python3
"""
Tests for store.py schema alignment.
"""

import json
import tempfile
from pathlib import Path

import pytest

# Import from parent directory
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / 'evolving-agent' / 'scripts' / 'knowledge'))

from store import (
    store_experience, store_problem, store_tech_stack,
    store_scenario, store_testing, store_pattern, store_skill,
)


class TestStoreSchemaAlignment:
    """Tests for store.py schema alignment."""

    def test_store_experience_schema(self, tmp_path):
        """store_experience should match schema.json definition"""
        kb_root = tmp_path / 'knowledge'
        kb_root.mkdir(parents=True)

        # store_experience returns the full entry dict
        entry = store_experience(
            name="Test Experience",
            description="Test description",
            context="Test context",
            solution="Test solution",
            pitfalls=["pitfall1", "pitfall2"],
            triggers=["test"],
            tags=["testing"],
            kb_root=kb_root
        )

        # Verify return value
        assert isinstance(entry, dict)
        assert 'id' in entry

        # Load and verify structure on disk
        entry_path = kb_root / 'experiences' / f"{entry['id']}.json"
        assert entry_path.exists()

        with open(entry_path, 'r') as f:
            stored = json.load(f)

        # Verify content structure matches schema
        assert 'content' in stored
        content = stored['content']

        # Schema requires: description, context, solution, pitfalls
        assert 'description' in content
        assert 'context' in content
        assert 'solution' in content
        assert 'pitfalls' in content
        assert isinstance(content['pitfalls'], list)

    def test_store_problem_schema(self, tmp_path):
        """store_problem should match schema.json definition"""
        kb_root = tmp_path / 'knowledge'
        kb_root.mkdir(parents=True)

        entry = store_problem(
            problem_name="Test Problem",
            symptoms=["symptom1"],
            root_causes=["cause1"],
            solutions=[{"description": "solution1"}],
            prevention=["prevention1"],
            triggers=["test"],
            kb_root=kb_root
        )

        assert isinstance(entry, dict)
        assert 'id' in entry

        # Load and verify structure
        entry_path = kb_root / 'problems' / f"{entry['id']}.json"
        assert entry_path.exists()

        with open(entry_path, 'r') as f:
            stored = json.load(f)

        # Verify content structure
        assert 'content' in stored
        content = stored['content']

        # Schema requires: problem_name, symptoms, root_causes, solutions, prevention
        assert 'problem_name' in content
        assert 'symptoms' in content
        assert isinstance(content['symptoms'], list)
        assert 'root_causes' in content
        assert 'solutions' in content
        assert 'prevention' in content

    def test_store_tech_stack_schema(self, tmp_path):
        """store_tech_stack should match schema.json definition"""
        kb_root = tmp_path / 'knowledge'
        kb_root.mkdir(parents=True)

        entry = store_tech_stack(
            tech_name="React",
            version="18.0",
            best_practices=["Use hooks"],
            triggers=["react"],
            kb_root=kb_root
        )

        assert isinstance(entry, dict)
        assert 'id' in entry

        # Load and verify structure
        entry_path = kb_root / 'tech-stacks' / f"{entry['id']}.json"
        assert entry_path.exists()

        with open(entry_path, 'r') as f:
            stored = json.load(f)

        # Verify content structure
        assert 'content' in stored
        content = stored['content']

        # Schema requires: tech_name, version, best_practices
        assert 'tech_name' in content
        assert isinstance(content.get('best_practices', []), list)

    def test_store_scenario_schema(self, tmp_path):
        """store_scenario should match schema.json definition"""
        kb_root = tmp_path / 'knowledge'
        kb_root.mkdir(parents=True)

        entry = store_scenario(
            scenario_name="API Design Scenario",
            description="How to design RESTful APIs",
            typical_approach="Resource-based URLs",
            steps=["Define resources", "Choose HTTP methods"],
            considerations=["versioning", "auth"],
            triggers=["api", "rest"],
            kb_root=kb_root
        )

        assert isinstance(entry, dict)
        assert 'id' in entry

        entry_path = kb_root / 'scenarios' / f"{entry['id']}.json"
        assert entry_path.exists()

        with open(entry_path, 'r') as f:
            stored = json.load(f)

        assert 'content' in stored
        content = stored['content']
        assert 'scenario_name' in content
        assert 'description' in content
        assert 'typical_approach' in content
        assert isinstance(content.get('steps', []), list)

    def test_store_testing_schema(self, tmp_path):
        """store_testing should match schema.json definition"""
        kb_root = tmp_path / 'knowledge'
        kb_root.mkdir(parents=True)

        entry = store_testing(
            name="Pytest Best Practices",
            testing_type="unit",
            framework="pytest",
            best_practices=["Use fixtures", "Parametrize tests"],
            patterns=["AAA pattern"],
            triggers=["pytest", "testing"],
            kb_root=kb_root
        )

        assert isinstance(entry, dict)
        assert 'id' in entry

        entry_path = kb_root / 'testing' / f"{entry['id']}.json"
        assert entry_path.exists()

        with open(entry_path, 'r') as f:
            stored = json.load(f)

        assert 'content' in stored
        content = stored['content']
        assert 'testing_type' in content
        assert isinstance(content.get('best_practices', []), list)
        assert isinstance(content.get('patterns', []), list)

    def test_store_pattern_schema(self, tmp_path):
        """store_pattern should match schema.json definition"""
        kb_root = tmp_path / 'knowledge'
        kb_root.mkdir(parents=True)

        entry = store_pattern(
            pattern_name="Singleton",
            pattern_category="creational",
            description="Ensure only one instance exists",
            when_to_use="When exactly one object is needed",
            pros=["controlled access"],
            cons=["global state"],
            triggers=["singleton", "design-pattern"],
            kb_root=kb_root
        )

        assert isinstance(entry, dict)
        assert 'id' in entry

        entry_path = kb_root / 'patterns' / f"{entry['id']}.json"
        assert entry_path.exists()

        with open(entry_path, 'r') as f:
            stored = json.load(f)

        assert 'content' in stored
        content = stored['content']
        assert 'pattern_name' in content
        assert 'description' in content
        assert 'when_to_use' in content
        assert isinstance(content.get('pros', []), list)
        assert isinstance(content.get('cons', []), list)

    def test_store_skill_schema(self, tmp_path):
        """store_skill should match schema.json definition"""
        kb_root = tmp_path / 'knowledge'
        kb_root.mkdir(parents=True)

        entry = store_skill(
            skill_name="Python Type Hints",
            level="intermediate",
            description="Using type hints for static analysis",
            key_concepts=["annotations", "mypy"],
            practical_tips=["Use Optional for nullable"],
            common_mistakes=["Ignoring Any type"],
            triggers=["python", "type-hints"],
            kb_root=kb_root
        )

        assert isinstance(entry, dict)
        assert 'id' in entry

        entry_path = kb_root / 'skills' / f"{entry['id']}.json"
        assert entry_path.exists()

        with open(entry_path, 'r') as f:
            stored = json.load(f)

        assert 'content' in stored
        content = stored['content']
        assert 'skill_name' in content
        assert 'level' in content
        assert 'description' in content
        assert isinstance(content.get('key_concepts', []), list)
        assert isinstance(content.get('practical_tips', []), list)
