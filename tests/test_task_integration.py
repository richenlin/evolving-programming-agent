#!/usr/bin/env python3
"""
Integration tests for task manager - Full lifecycle scenarios.

Tests the complete task management workflow from creation to completion,
including state transitions, dependencies, and error handling.
"""

import tempfile
from pathlib import Path

import pytest

# Import from parent directory
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / 'evolving-agent' / 'scripts'))

from core.task_manager import (
    create_task,
    transition,
    load_feature_list,
    find_task,
    get_status_summary,
)


class TestFullLifecycle:
    """Test complete task lifecycle scenarios."""
    
    def test_full_lifecycle(self):
        """
        Test complete task lifecycle:
        1. Create 3 tasks with dependencies
        2. Complete task-001 through full workflow
        3. Reject and retry task-002
        4. Verify final state
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            
            # 1. Create 3 tasks with dependencies
            task1 = create_task(
                project_root,
                name="Setup Database",
                description="Initialize database schema",
                priority="high"
            )
            assert task1["id"] == "task-001"
            assert task1["status"] == "pending"
            
            task2 = create_task(
                project_root,
                name="Create API Endpoints",
                description="REST API for data access",
                priority="high",
                depends_on=["task-001"]
            )
            assert task2["id"] == "task-002"
            assert task2["depends_on"] == ["task-001"]
            
            task3 = create_task(
                project_root,
                name="Write Tests",
                priority="medium",
                depends_on=["task-002"]
            )
            assert task3["id"] == "task-003"
            
            # 2. Complete task-001: pending → in_progress → review_pending → completed
            t1 = transition(project_root, "task-001", "in_progress")
            assert t1["status"] == "in_progress"
            
            t1 = transition(project_root, "task-001", "review_pending")
            assert t1["status"] == "review_pending"
            
            t1 = transition(project_root, "task-001", "completed", actor="reviewer")
            assert t1["status"] == "completed"
            assert "completed_at" in t1
            
            # 3. Start task-002 and get rejected
            t2 = transition(project_root, "task-002", "in_progress")
            assert t2["status"] == "in_progress"
            
            t2 = transition(project_root, "task-002", "review_pending")
            assert t2["status"] == "review_pending"
            
            # Simulate rejection (reviewer finds issues)
            t2 = transition(project_root, "task-002", "rejected")
            assert t2["status"] == "rejected"
            
            # Fix and retry
            t2 = transition(project_root, "task-002", "in_progress")
            assert t2["status"] == "in_progress"
            
            t2 = transition(project_root, "task-002", "review_pending")
            assert t2["status"] == "review_pending"
            
            # Approved on second attempt
            t2 = transition(project_root, "task-002", "completed", actor="reviewer")
            assert t2["status"] == "completed"
            
            # 4. Verify final state
            summary = get_status_summary(project_root)
            assert summary["total"] == 3
            assert summary["completed"] == 2
            assert summary["pending"] == 1  # task-003 still pending
            
            # Verify task-003 is still pending (dependency satisfied but not started)
            data = load_feature_list(project_root)
            t3 = find_task(data, "task-003")
            assert t3["status"] == "pending"
    
    def test_parallel_tasks(self):
        """Test multiple independent tasks in parallel."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            
            # Create 3 independent tasks
            t1 = create_task(project_root, name="Task A")
            t2 = create_task(project_root, name="Task B")
            t3 = create_task(project_root, name="Task C")
            
            # Start all in parallel
            transition(project_root, "task-001", "in_progress")
            transition(project_root, "task-002", "in_progress")
            transition(project_root, "task-003", "in_progress")
            
            summary = get_status_summary(project_root)
            assert summary["in_progress"] == 3
            
            # Complete all
            for tid in ["task-001", "task-002", "task-003"]:
                transition(project_root, tid, "review_pending")
                transition(project_root, tid, "completed", actor="reviewer")
            
            summary = get_status_summary(project_root)
            assert summary["completed"] == 3


class TestIllegalShortcuts:
    """Test that illegal state transitions are rejected."""
    
    def test_pending_to_completed_shortcut(self):
        """Cannot skip directly from pending to completed."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            
            task = create_task(project_root, name="Test Task")
            
            with pytest.raises(ValueError, match="Invalid transition"):
                transition(project_root, "task-001", "completed", actor="reviewer")
    
    def test_in_progress_to_completed_shortcut(self):
        """Cannot skip review process."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            
            task = create_task(project_root, name="Test Task")
            transition(project_root, "task-001", "in_progress")
            
            with pytest.raises(ValueError, match="Invalid transition"):
                transition(project_root, "task-001", "completed", actor="reviewer")
    
    def test_completed_without_reviewer(self):
        """Only reviewer can mark as completed."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            
            task = create_task(project_root, name="Test Task")
            transition(project_root, "task-001", "in_progress")
            transition(project_root, "task-001", "review_pending")
            
            # Should fail without actor=reviewer
            with pytest.raises(ValueError, match="Only reviewer can mark"):
                transition(project_root, "task-001", "completed")
            
            # Should fail with wrong actor
            with pytest.raises(ValueError, match="Only reviewer can mark"):
                transition(project_root, "task-001", "completed", actor="coder")
            
            # Should succeed with actor=reviewer
            result = transition(project_root, "task-001", "completed", actor="reviewer")
            assert result["status"] == "completed"
    
    def test_invalid_backward_transitions(self):
        """Cannot go backwards in the workflow."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            
            task = create_task(project_root, name="Test Task")
            transition(project_root, "task-001", "in_progress")
            
            # Cannot go from in_progress back to pending
            with pytest.raises(ValueError, match="Invalid transition"):
                transition(project_root, "task-001", "pending")
    
    def test_completed_is_final(self):
        """Cannot transition from completed state."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            
            task = create_task(project_root, name="Test Task")
            transition(project_root, "task-001", "in_progress")
            transition(project_root, "task-001", "review_pending")
            transition(project_root, "task-001", "completed", actor="reviewer")
            
            # Cannot transition from completed
            with pytest.raises(ValueError, match="Invalid.*status"):
                transition(project_root, "task-001", "in_progress")


class TestBlockedTasks:
    """Test blocked task scenarios."""
    
    def test_block_and_unblock(self):
        """Test blocking and unblocking tasks."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            
            task = create_task(project_root, name="Blocked Task")
            
            # Block the task
            t = transition(project_root, "task-001", "in_progress")
            t = transition(project_root, "task-001", "blocked")
            assert t["status"] == "blocked"
            
            # Unblock
            t = transition(project_root, "task-001", "pending")
            assert t["status"] == "pending"
            
            # Can restart
            t = transition(project_root, "task-001", "in_progress")
            assert t["status"] == "in_progress"
    
    def test_blocked_cannot_complete(self):
        """Cannot complete a blocked task directly."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            
            task = create_task(project_root, name="Blocked Task")
            transition(project_root, "task-001", "in_progress")
            transition(project_root, "task-001", "blocked")
            
            # Cannot go from blocked to completed
            with pytest.raises(ValueError, match="Invalid transition"):
                transition(project_root, "task-001", "completed", actor="reviewer")
