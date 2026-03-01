#!/usr/bin/env python3
"""
MVP 验收测试：验证所有 10 个任务是否完成
"""
import subprocess
from pathlib import Path


def test_t01_reviewer_model():
    """验收标准：reviewer 使用正确模型"""
    reviewer_path = Path.home() / ".config" / "opencode" / "skills" / "evolving-agent" / "agents" / "reviewer.md"
    content = reviewer_path.read_text()
    
    if "openrouter/anthropic/claude-sonnet-4.6" not in content:
        raise AssertionError("reviewer 模型配置不正确")
    
    print("✅ T01: reviewer 使用正确模型")


def test_t02_evolution_mode_path():
    """验收标准：进化模式路径正确"""
    run_py_path = Path.home() / ".config" / "opencode" / "skills" / "evolving-agent" / "scripts" / "run.py"
    content = run_py_path.read_text()
    
    if "rev-parse" not in content or "--show-toplevel" not in content:
        raise AssertionError("进化模式路径未使用 git root")
    
    print("✅ T02: 进化模式路径正确")


def test_t03_references_directory():
    """验收标准：references/ 目录完整"""
    references_dir = Path.home() / ".config" / "opencode" / "skills" / "evolving-agent" / "agents" / "references"
    
    if not references_dir.exists():
        raise AssertionError("references 目录不存在")
    
    required_files = [
        "solid-checklist.md",
        "security-checklist.md",
        "quality-checklist.md",
        "removal-plan.md"
    ]
    
    for file_name in required_files:
        file_path = references_dir / file_name
        if not file_path.exists():
            raise AssertionError(f"references 目录缺少文件: {file_name}")
    
    print("✅ T03-T06: references 目录完整（4 个文件）")


def test_t07_preflight_step():
    """验收标准：reviewer 流程包含 preflight"""
    reviewer_path = Path.home() / ".config" / "opencode" / "skills" / "evolving-agent" / "agents" / "reviewer.md"
    content = reviewer_path.read_text()
    
    if "Preflight" not in content:
        raise AssertionError("reviewer 缺少 preflight 步骤")
    
    print("✅ T07: reviewer 包含 preflight 步骤")


def test_t08_structured_process():
    """验收标准：reviewer 引用全部 4 个 checklist"""
    reviewer_path = Path.home() / ".config" / "opencode" / "skills" / "evolving-agent" / "agents" / "reviewer.md"
    content = reviewer_path.read_text()
    
    required_checklists = [
        "solid-checklist",
        "security-checklist",
        "quality-checklist",
        "removal-plan"
    ]
    
    for checklist in required_checklists:
        if checklist not in content:
            raise AssertionError(f"reviewer 未引用 {checklist}")
    
    print("✅ T08: reviewer 引用全部 4 个 checklist")


def test_t09_severity_levels():
    """验收标准：reviewer 使用 P0-P3 级别"""
    reviewer_path = Path.home() / ".config" / "opencode" / "skills" / "evolving-agent" / "agents" / "reviewer.md"
    content = reviewer_path.read_text()
    
    required_levels = ["P0", "P1", "P2", "P3"]
    
    for level in required_levels:
        if level not in content:
            raise AssertionError(f"reviewer 缺少严重级别 {level}")
    
    # 检查示例格式
    if "[P1]" not in content and "[P0]" not in content:
        raise AssertionError("reviewer 缺少 [Px] 格式示例")
    
    print("✅ T09: reviewer 使用 P0-P3 级别")


def test_t10_github_learn():
    """验收标准：github learn 命令可用"""
    run_py_path = Path.home() / ".config" / "opencode" / "skills" / "evolving-agent" / "scripts" / "run.py"
    
    result = subprocess.run(
        ['python', str(run_py_path), 'github', '--help'],
        capture_output=True,
        text=True
    )
    
    if 'learn' not in result.stdout:
        raise AssertionError("github learn 命令未注册")
    
    learn_script = Path.home() / ".config" / "opencode" / "skills" / "evolving-agent" / "scripts" / "github" / "learn.py"
    if not learn_script.exists():
        raise AssertionError("learn.py 脚本不存在")
    
    print("✅ T10: github learn 命令可用")


if __name__ == "__main__":
    print("=" * 60)
    print("MVP 验收测试")
    print("=" * 60)
    print()
    
    test_t01_reviewer_model()
    test_t02_evolution_mode_path()
    test_t03_references_directory()
    test_t07_preflight_step()
    test_t08_structured_process()
    test_t09_severity_levels()
    test_t10_github_learn()
    
    print()
    print("=" * 60)
    print("✅ 所有 MVP 任务验收通过！")
    print("=" * 60)
