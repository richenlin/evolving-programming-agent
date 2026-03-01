#!/usr/bin/env python3
"""
T02 单元测试：验证进化模式路径修复正确

测试策略：
1. 验证 run.py 源码包含正确的 git rev-parse 逻辑
2. 验证函数签名和行为符合预期
"""
import subprocess
import tempfile
from pathlib import Path


def test_run_py_has_git_rev_parse():
    """验证 run.py 源码包含 git rev-parse --show-toplevel"""
    run_py_path = Path.home() / ".config" / "opencode" / "skills" / "evolving-agent" / "scripts" / "run.py"
    
    if not run_py_path.exists():
        raise AssertionError(f"run.py 文件不存在: {run_py_path}")
    
    content = run_py_path.read_text()
    
    if "rev-parse" not in content:
        raise AssertionError("run.py 未包含 'rev-parse'")
    
    if "--show-toplevel" not in content:
        raise AssertionError("run.py 未包含 '--show-toplevel'")
    
    print("✅ T02 测试通过: run.py 包含 git rev-parse --show-toplevel")


def test_evolution_mode_function_exists():
    """验证 get_evolution_mode_status 函数存在且签名正确"""
    run_py_path = Path.home() / ".config" / "opencode" / "skills" / "evolving-agent" / "scripts" / "run.py"
    content = run_py_path.read_text()
    
    if "def get_evolution_mode_status" not in content:
        raise AssertionError("run.py 未定义 get_evolution_mode_status 函数")
    
    if "subprocess.run" not in content:
        raise AssertionError("get_evolution_mode_status 未使用 subprocess.run")
    
    print("✅ T02 测试通过: get_evolution_mode_status 函数存在且使用 subprocess")


def test_evolution_mode_in_real_git_repo():
    """在真实 git 仓库中验证进化模式检测"""
    run_py_path = Path.home() / ".config" / "opencode" / "skills" / "evolving-agent" / "scripts" / "run.py"
    
    with tempfile.TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)
        
        subprocess.run(['git', 'init'], cwd=tmppath, capture_output=True, check=True)
        subprocess.run(['git', 'config', 'user.email', 'test@test.com'], cwd=tmppath, capture_output=True, check=True)
        subprocess.run(['git', 'config', 'user.name', 'Test'], cwd=tmppath, capture_output=True, check=True)
        
        opencode_dir = tmppath / '.opencode'
        opencode_dir.mkdir()
        marker_file = opencode_dir / '.evolution_mode_active'
        marker_file.touch()
        
        subdir = tmppath / 'subdir'
        subdir.mkdir()
        
        result = subprocess.run(
            ['python', str(run_py_path), 'info'],
            cwd=subdir,
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            raise AssertionError(f"run.py info 执行失败: {result.stderr}")
        
        if "Evolution Mode:  ACTIVE" not in result.stdout:
            raise AssertionError(
                f"从子目录未能检测到进化模式\n"
                f"期望输出包含: 'Evolution Mode:  ACTIVE'\n"
                f"实际输出:\n{result.stdout}"
            )
    
    print("✅ T02 测试通过: 从子目录能正确检测进化模式标记文件")


if __name__ == "__main__":
    test_run_py_has_git_rev_parse()
    test_evolution_mode_function_exists()
    test_evolution_mode_in_real_git_repo()
    print("\n✅ 所有 T02 测试通过")
