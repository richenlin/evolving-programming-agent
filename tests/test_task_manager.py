#!/usr/bin/env python3
"""
Tests for task_manager state machine.
"""

import tempfile
from datetime import datetime
from pathlib import Path

import pytest

# Import from parent directory
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / 'evolving-agent' / 'scripts'))

from core.task_manager import (
    VALID_TRANSITIONS,
    get_project_root,
    load_feature_list,
    save_feature_list,
    find_task,
    transition,
    init_feature_list,
    create_task,
    get_status_summary,
)


class TestValidTransitions:
    """Tests for valid state transitions."""
    
    def test_valid_transition_pending_to_in_progress(self, tmp_path):
        """pending → in_progress is valid"""
        # Setup
        feature_list = {
            "tasks": [
                {
                    "id": "TASK-001",
                    "name": "Test Task",
                    "status": "pending",
                    "created_at": "2026-03-01T00:00:00Z",
                    "updated_at": "2026-03-01T00:00:00Z"
                }
            ]
        }
        save_feature_list(tmp_path, feature_list)
        
        # Execute
        updated_task = transition(tmp_path, "TASK-001", "in_progress")
        
        # Verify
        assert updated_task["status"] == "in_progress"
        
        # Verify saved
        data = load_feature_list(tmp_path)
        task = find_task(data, "TASK-001")
        assert task["status"] == "in_progress"
    
    def test_valid_transition_in_progress_to_review_pending(self, tmp_path):
        """in_progress → review_pending is valid"""
        # Setup
        feature_list = {
            "tasks": [
                {
                    "id": "TASK-001",
                    "name": "Test Task",
                    "status": "in_progress",
                    "created_at": "2026-03-01T00:00:00Z",
                    "updated_at": "2026-03-01T00:00:00Z"
                }
            ]
        }
        save_feature_list(tmp_path, feature_list)
        
        # Execute
        updated_task = transition(tmp_path, "TASK-001", "review_pending")
        
        # Verify
        assert updated_task["status"] == "review_pending"
    
    def test_valid_transition_review_pending_to_completed_by_reviewer(self, tmp_path):
        """review_pending → completed by reviewer is valid (with reviewer_notes)"""
        # Setup
        feature_list = {
            "tasks": [
                {
                    "id": "TASK-001",
                    "name": "Test Task",
                    "status": "review_pending",
                    "created_at": "2026-03-01T00:00:00Z",
                    "updated_at": "2026-03-01T00:00:00Z"
                }
            ]
        }
        save_feature_list(tmp_path, feature_list)
        
        # Execute
        updated_task = transition(
            tmp_path,
            "TASK-001",
            "completed",
            actor="reviewer",
            reviewer_notes="LGTM: no issues found"
        )
        
        # Verify
        assert updated_task["status"] == "completed"
        assert "completed_at" in updated_task
        assert updated_task["reviewer_notes"] == "LGTM: no issues found"


class TestIdempotentTransitions:
    """Tests for idempotent (same-state) transitions."""

    def _make_task(self, tmp_path, status):
        """Helper: create task and advance to given status."""
        task = create_task(tmp_path, name="Test Task")
        if status == "pending":
            return task
        transition(tmp_path, task["id"], "in_progress")
        if status == "in_progress":
            return task
        transition(tmp_path, task["id"], "review_pending")
        if status == "review_pending":
            return task
        transition(tmp_path, task["id"], "completed", actor="reviewer",
                   reviewer_notes="LGTM: no issues found")
        return task

    def test_idempotent_pending_to_pending(self, tmp_path):
        """pending → pending is a no-op, does not raise"""
        task = create_task(tmp_path, name="Test Task")
        original_updated_at = task["updated_at"]

        result = transition(tmp_path, task["id"], "pending")
        assert result["status"] == "pending"
        assert result["updated_at"] == original_updated_at

    def test_idempotent_in_progress_to_in_progress(self, tmp_path):
        """in_progress → in_progress is a no-op, does not raise"""
        task = create_task(tmp_path, name="Test Task")
        transition(tmp_path, task["id"], "in_progress")
        data = load_feature_list(tmp_path)
        task_after = find_task(data, task["id"])
        original_updated_at = task_after["updated_at"]

        result = transition(tmp_path, task["id"], "in_progress")
        assert result["status"] == "in_progress"
        assert result["updated_at"] == original_updated_at

    def test_idempotent_completed_to_completed(self, tmp_path):
        """completed → completed is a no-op, does not require actor=reviewer"""
        task = create_task(tmp_path, name="Test Task")
        transition(tmp_path, task["id"], "in_progress")
        transition(tmp_path, task["id"], "review_pending")
        transition(tmp_path, task["id"], "completed", actor="reviewer",
                   reviewer_notes="LGTM: no issues found")

        # completed → completed without actor should not raise (idempotent)
        result = transition(tmp_path, task["id"], "completed")
        assert result["status"] == "completed"


class TestInvalidTransitions:
    """Tests for invalid state transitions."""

    def test_reject_completed_without_reviewer(self, tmp_path):
        """Only reviewer can mark as completed"""
        # Setup
        feature_list = {
            "tasks": [
                {
                    "id": "TASK-001",
                    "name": "Test Task",
                    "status": "review_pending",
                    "created_at": "2026-03-01T00:00:00Z",
                    "updated_at": "2026-03-01T00:00:00Z"
                }
            ]
        }
        save_feature_list(tmp_path, feature_list)
        
        # Execute & Verify
        with pytest.raises(ValueError, match="Only reviewer can mark"):
            transition(tmp_path, "TASK-001", "completed", actor="coder")
    
    def test_reject_illegal_transition(self, tmp_path):
        """pending → completed is invalid"""
        # Setup
        feature_list = {
            "tasks": [
                {
                    "id": "TASK-001",
                    "name": "Test Task",
                    "status": "pending",
                    "created_at": "2026-03-01T00:00:00Z",
                    "updated_at": "2026-03-01T00:00:00Z"
                }
            ]
        }
        save_feature_list(tmp_path, feature_list)
        
        # Execute & Verify
        with pytest.raises(ValueError, match="Invalid transition"):
            transition(
                tmp_path,
                "TASK-001",
                "completed",
                actor="reviewer"  # Even reviewer can't skip states
            )
    
    def test_reject_unknown_task_id(self, tmp_path):
        """Unknown task ID raises error"""
        # Setup
        feature_list = {"tasks": []}
        save_feature_list(tmp_path, feature_list)
        
        # Execute & Verify
        with pytest.raises(ValueError, match="Task not found"):
            transition(tmp_path, "NONEXISTENT", "in_progress")


class TestReviewerNotesValidation:
    """Tests for mandatory reviewer_notes on review_pending → completed."""

    def _setup_review_pending(self, tmp_path):
        feature_list = {
            "tasks": [{
                "id": "TASK-001", "name": "Test", "status": "review_pending",
                "created_at": "2026-03-01T00:00:00Z", "updated_at": "2026-03-01T00:00:00Z"
            }]
        }
        save_feature_list(tmp_path, feature_list)

    def test_reject_completed_without_notes(self, tmp_path):
        """review_pending → completed without reviewer_notes is rejected"""
        self._setup_review_pending(tmp_path)
        with pytest.raises(ValueError, match="reviewer_notes is required"):
            transition(tmp_path, "TASK-001", "completed", actor="reviewer")

    def test_reject_completed_with_empty_notes(self, tmp_path):
        """Empty reviewer_notes is rejected"""
        self._setup_review_pending(tmp_path)
        with pytest.raises(ValueError, match="reviewer_notes is required"):
            transition(tmp_path, "TASK-001", "completed", actor="reviewer",
                       reviewer_notes="   ")

    def test_reject_completed_with_short_notes(self, tmp_path):
        """Too-short reviewer_notes is rejected"""
        self._setup_review_pending(tmp_path)
        with pytest.raises(ValueError, match="too short"):
            transition(tmp_path, "TASK-001", "completed", actor="reviewer",
                       reviewer_notes="ok")

    def test_reject_completed_without_marker(self, tmp_path):
        """reviewer_notes without severity marker or LGTM is rejected"""
        self._setup_review_pending(tmp_path)
        with pytest.raises(ValueError, match="severity marker"):
            transition(tmp_path, "TASK-001", "completed", actor="reviewer",
                       reviewer_notes="This looks fine to me, no problems at all")

    def test_accept_lgtm_notes(self, tmp_path):
        """LGTM marker is accepted"""
        self._setup_review_pending(tmp_path)
        task = transition(tmp_path, "TASK-001", "completed", actor="reviewer",
                          reviewer_notes="LGTM: no issues found")
        assert task["status"] == "completed"

    def test_accept_severity_marker_notes(self, tmp_path):
        """[P3] severity marker is accepted"""
        self._setup_review_pending(tmp_path)
        task = transition(tmp_path, "TASK-001", "completed", actor="reviewer",
                          reviewer_notes="[P3] minor naming suggestion in utils.py")
        assert task["status"] == "completed"

    def test_reject_transition_still_allowed(self, tmp_path):
        """review_pending → rejected does NOT require reviewer_notes validation"""
        self._setup_review_pending(tmp_path)
        task = transition(tmp_path, "TASK-001", "rejected",
                          reviewer_notes="[P1] critical bug in auth flow")
        assert task["status"] == "rejected"


class TestTimestamps:
    """Tests for timestamp updates."""
    
    def test_timestamps_updated(self, tmp_path):
        """updated_at is updated on transition"""
        # Setup
        old_time = "2026-03-01T00:00:00Z"
        feature_list = {
            "tasks": [
                {
                    "id": "TASK-001",
                    "name": "Test Task",
                    "status": "pending",
                    "created_at": old_time,
                    "updated_at": old_time
                }
            ]
        }
        save_feature_list(tmp_path, feature_list)
        
        # Execute
        updated_task = transition(tmp_path, "TASK-001", "in_progress")
        
        # Verify
        assert updated_task["updated_at"] != old_time
        # Verify it's a valid ISO timestamp
        datetime.fromisoformat(updated_task["updated_at"])


class TestUtilityFunctions:
    """Tests for utility functions."""
    
    def test_get_project_root(self):
        """get_project_root returns valid path"""
        root = get_project_root()
        assert root.is_dir()
        assert (root / ".git").exists()
    
    def test_load_feature_list_nonexistent(self, tmp_path):
        """load_feature_list returns empty dict for nonexistent file"""
        data = load_feature_list(tmp_path)
        assert data == {"tasks": []}
    
    def test_find_task_existing(self, tmp_path):
        """find_task finds existing task"""
        feature_list = {
            "tasks": [
                {"id": "TASK-001", "name": "Task 1"},
                {"id": "TASK-002", "name": "Task 2"}
            ]
        }
        save_feature_list(tmp_path, feature_list)
        
        data = load_feature_list(tmp_path)
        task = find_task(data, "TASK-002")
        
        assert task is not None
        assert task["name"] == "Task 2"
    
    def test_find_task_nonexistent(self, tmp_path):
        """find_task returns None for nonexistent task"""
        feature_list = {"tasks": [{"id": "TASK-001", "name": "Task 1"}]}
        save_feature_list(tmp_path, feature_list)
        
        data = load_feature_list(tmp_path)
        task = find_task(data, "NONEXISTENT")
        
        assert task is None


class TestCreateTask:
    """Tests for create_task function."""
    
    def test_create_task_auto_id(self, tmp_path):
        """创建任务时自动生成递增ID"""
        # Create first task
        task1 = create_task(tmp_path, name="First Task")
        assert task1["id"] == "task-001"
        assert task1["name"] == "First Task"
        assert task1["status"] == "pending"
        
        # Create second task
        task2 = create_task(tmp_path, name="Second Task")
        assert task2["id"] == "task-002"
        
        # Verify saved
        data = load_feature_list(tmp_path)
        assert len(data["tasks"]) == 2
    
    def test_create_task_initializes_file(self, tmp_path):
        """如果文件不存在，自动初始化"""
        # Ensure file doesn't exist
        assert not (tmp_path / ".opencode" / "feature_list.json").exists()
        
        # Create task
        task = create_task(tmp_path, name="Test Task")
        
        # Verify file created
        assert (tmp_path / ".opencode" / "feature_list.json").exists()
        assert task["id"] == "task-001"
    
    def test_create_task_with_depends(self, tmp_path):
        """创建带依赖的任务"""
        # Create first task
        task1 = create_task(tmp_path, name="Base Task")
        
        # Create dependent task
        task2 = create_task(
            tmp_path,
            name="Dependent Task",
            description="Depends on task-001",
            priority="high",
            depends_on=["task-001"]
        )
        
        assert task2["depends_on"] == ["task-001"]
        assert task2["priority"] == "high"
        assert task2["description"] == "Depends on task-001"
    
    def test_create_task_with_all_fields(self, tmp_path):
        """创建包含所有字段的任务"""
        task = create_task(
            tmp_path,
            name="Full Task",
            description="Complete description",
            priority="high",
            depends_on=["task-001", "task-002"]
        )
        
        assert task["name"] == "Full Task"
        assert task["description"] == "Complete description"
        assert task["priority"] == "high"
        assert task["status"] == "pending"
        assert task["depends_on"] == ["task-001", "task-002"]
        assert "created_at" in task
        assert "updated_at" in task


class TestInitFeatureList:
    """Tests for init_feature_list function."""
    
    def test_init_creates_file(self, tmp_path):
        """初始化创建feature_list.json"""
        data = init_feature_list(tmp_path, "TestProject")
        
        assert data["project"] == "TestProject"
        assert data["tasks"] == []
        assert "created_at" in data
        
        # Verify file exists
        assert (tmp_path / ".opencode" / "feature_list.json").exists()


class TestAuditLog:
    """Tests for audit log on state transitions."""

    def test_audit_log_on_transition(self, tmp_path):
        """每次转换后 audit_log 有一条记录，包含 from/to/actor/timestamp"""
        task = create_task(tmp_path, name="Audit Task")
        transition(tmp_path, task["id"], "in_progress", actor="coder")

        data = load_feature_list(tmp_path)
        updated = find_task(data, task["id"])
        assert "audit_log" in updated
        assert len(updated["audit_log"]) == 1
        entry = updated["audit_log"][0]
        assert entry["from"] == "pending"
        assert entry["to"] == "in_progress"
        assert entry["actor"] == "coder"
        assert "timestamp" in entry
        datetime.fromisoformat(entry["timestamp"])  # valid ISO timestamp

    def test_audit_log_accumulates(self, tmp_path):
        """多次转换后 audit_log 有多条记录"""
        task = create_task(tmp_path, name="Audit Task")
        transition(tmp_path, task["id"], "in_progress")
        transition(tmp_path, task["id"], "review_pending")
        transition(tmp_path, task["id"], "completed", actor="reviewer",
                   reviewer_notes="LGTM: no issues found")

        data = load_feature_list(tmp_path)
        updated = find_task(data, task["id"])
        assert len(updated["audit_log"]) == 3
        assert updated["audit_log"][0]["from"] == "pending"
        assert updated["audit_log"][1]["from"] == "in_progress"
        assert updated["audit_log"][2]["from"] == "review_pending"

    def test_audit_log_not_on_idempotent(self, tmp_path):
        """幂等转换（same-state no-op）不追加审计记录"""
        task = create_task(tmp_path, name="Audit Task")
        transition(tmp_path, task["id"], "in_progress")
        # idempotent: no-op
        transition(tmp_path, task["id"], "in_progress")

        data = load_feature_list(tmp_path)
        updated = find_task(data, task["id"])
        # Only 1 real transition (pending→in_progress), idempotent not logged
        assert len(updated["audit_log"]) == 1

    def test_create_task_has_empty_audit_log(self, tmp_path):
        """create_task 初始化 audit_log 为空列表"""
        task = create_task(tmp_path, name="New Task")
        assert task["audit_log"] == []


class TestGetStatusSummary:
    """Tests for get_status_summary function."""
    
    def test_status_summary_empty(self, tmp_path):
        """空任务列表的统计"""
        summary = get_status_summary(tmp_path)
        
        assert summary["total"] == 0
        assert summary["pending"] == 0
        assert summary["completed"] == 0
        assert summary["current"] is None
        assert summary["has_active_session"] == False
        assert summary["has_pending"] == False
        assert summary["has_rejected"] == False
        assert summary["current_task"] is None
    
    def test_status_summary_with_tasks(self, tmp_path):
        """有任务时的统计"""
        # Create tasks
        create_task(tmp_path, name="Task 1", priority="high")
        task2 = create_task(tmp_path, name="Task 2")
        
        # Transition task2 to in_progress
        transition(tmp_path, "task-002", "in_progress")
        
        # Get summary
        summary = get_status_summary(tmp_path)
        
        assert summary["total"] == 2
        assert summary["pending"] == 1
        assert summary["in_progress"] == 1
        assert summary["current"] == "task-002 (in_progress)"
    
    def test_status_summary_all_statuses(self, tmp_path):
        """包含所有状态的统计"""
        # Create and transition tasks through various states
        t1 = create_task(tmp_path, name="Pending Task")
        t2 = create_task(tmp_path, name="In Progress Task")
        t3 = create_task(tmp_path, name="Review Pending Task")
        t4 = create_task(tmp_path, name="Completed Task")
        t5 = create_task(tmp_path, name="Rejected Task")
        t6 = create_task(tmp_path, name="Blocked Task")
        
        # Transition to different states
        transition(tmp_path, t2["id"], "in_progress")
        transition(tmp_path, t3["id"], "in_progress")
        transition(tmp_path, t3["id"], "review_pending")
        transition(tmp_path, t4["id"], "in_progress")
        transition(tmp_path, t4["id"], "review_pending")
        transition(tmp_path, t4["id"], "completed", actor="reviewer",
                   reviewer_notes="LGTM: no issues found")
        transition(tmp_path, t5["id"], "in_progress")
        transition(tmp_path, t5["id"], "review_pending")
        transition(tmp_path, t5["id"], "rejected")
        transition(tmp_path, t6["id"], "in_progress")
        transition(tmp_path, t6["id"], "blocked")
        
        # Get summary
        summary = get_status_summary(tmp_path)
        
        assert summary["total"] == 6
        assert summary["pending"] == 1
        assert summary["in_progress"] == 1
        assert summary["review_pending"] == 1
        assert summary["completed"] == 1
        assert summary["rejected"] == 1
        assert summary["blocked"] == 1
