#!/usr/bin/env python3
"""
T10 单元测试：验证 github learn 一键命令
"""
import subprocess
import sys
from pathlib import Path


def test_learn_script_exists():
    """验证 learn.py 脚本存在"""
    learn_script_path = Path.home() / ".config" / "opencode" / "skills" / "evolving-agent" / "scripts" / "github" / "learn.py"
    
    if not learn_script_path.exists():
        raise AssertionError(f"learn.py 脚本不存在: {learn_script_path}")
    
    print(f"✅ learn.py 脚本存在")


def test_learn_command_registered():
    """验证 learn 命令已注册"""
    run_py_path = Path.home() / ".config" / "opencode" / "skills" / "evolving-agent" / "scripts" / "run.py"
    
    result = subprocess.run(
        ['python', str(run_py_path), 'github', '--help'],
        capture_output=True,
        text=True
    )
    
    if result.returncode != 0:
        raise AssertionError(f"运行 run.py github --help 失败: {result.stderr}")
    
    if 'learn' not in result.stdout:
        raise AssertionError("learn 命令未在帮助信息中注册")
    
    print(f"✅ learn 命令已注册")


def test_learn_script_syntax():
    """验证 learn.py 脚本语法正确"""
    learn_script_path = Path.home() / ".config" / "opencode" / "skills" / "evolving-agent" / "scripts" / "github" / "learn.py"
    
    # 使用 Python 编译检查语法
    result = subprocess.run(
        ['python', '-m', 'py_compile', str(learn_script_path)],
        capture_output=True,
        text=True
    )
    
    if result.returncode != 0:
        raise AssertionError(f"learn.py 语法错误: {result.stderr}")
    
    print(f"✅ learn.py 脚本语法正确")


def test_run_py_has_learn_mapping():
    """验证 run.py 包含 learn 映射"""
    run_py_path = Path.home() / ".config" / "opencode" / "skills" / "evolving-agent" / "scripts" / "run.py"
    content = run_py_path.read_text()
    
    # 检查 mapping 中是否包含 learn
    if '"learn"' not in content:
        raise AssertionError("run.py 的 mapping 中未包含 learn")
    
    # 检查是否包含 ("github", "learn")
    if '("github", "learn")' not in content and '("github","learn")' not in content:
        raise AssertionError("run.py 的 mapping 中 learn 映射不正确")
    
    print(f"✅ run.py 包含 learn 映射")


if __name__ == "__main__":
    test_learn_script_exists()
    test_learn_command_registered()
    test_learn_script_syntax()
    test_run_py_has_learn_mapping()
    print("\n✅ 所有 T10 测试通过")
