#!/usr/bin/env python3
"""
Path Resolver - 统一路径解析模块

为 Evolving Programming Agent 提供跨平台的路径解析能力。
支持 OpenCode、Claude Code、Cursor 等多个平台。

使用方式：
    from path_resolver import get_agent_home, get_shared_venv_python, get_knowledge_base_dir

平台支持：
    - OpenCode: ~/.config/opencode/skills/
    - Claude Code: ~/.claude/skills/
    - Cursor: ~/.agents/skills/
    - OpenClaw: ~/.openclaw/skills/
    - Hermes: ~/.hermes/skills/
"""

import os
import sys
from pathlib import Path
from typing import List, Optional, Tuple


# 平台 skills 目录（按优先级）
PLATFORM_SKILL_DIRS: List[Tuple[str, Path, int]] = [
    ("opencode", Path.home() / ".config" / "opencode" / "skills", 1),
    ("cursor", Path.home() / ".agents" / "skills", 2),
    ("claude", Path.home() / ".claude" / "skills", 3),
    ("openclaw", Path.home() / ".openclaw" / "skills", 4),
    ("hermes", Path.home() / ".hermes" / "skills", 5),
]

# 兼容旧接口
PLATFORM_CONFIGS = {
    "opencode": {
        "skills_dir": Path.home() / ".config" / "opencode" / "skills",
        "priority": 1,
    },
    "claude": {
        "skills_dir": Path.home() / ".claude" / "skills",
        "priority": 2,
    },
}

VENV_SKILL = "evolving-agent"


def _legacy_shared_knowledge_dir() -> Path:
    return Path.home() / ".config" / "opencode" / "codegraph"


def _default_agent_home() -> Path:
    xdg = os.environ.get("XDG_DATA_HOME")
    if xdg:
        return Path(xdg) / "evolving-agent"
    return Path.home() / ".local" / "share" / "evolving-agent"


def get_agent_home() -> Path:
    """Shared runtime root (~/.local/share/evolving-agent by default)."""
    env = os.environ.get("EVOLVING_AGENT_HOME")
    if env:
        return Path(env)
    return _default_agent_home()


def get_shared_venv_dir() -> Path:
    explicit = os.environ.get("EVOLVING_AGENT_VENV")
    if explicit:
        return Path(explicit)
    return get_agent_home() / "runtime" / ".venv"


def get_shared_venv_python() -> Path:
    """Single shared venv python (multi-platform)."""
    venv_python = os.environ.get("VENV_PYTHON", "")
    if venv_python:
        p = Path(venv_python)
        if p.is_dir():
            return p / "bin" / "python"
        return p
    return get_shared_venv_dir() / "bin" / "python"


def detect_platform() -> str:
    """
    自动检测当前运行的平台。

    Returns:
        平台名称: 'opencode' 或 'claude'（兼容旧 API）
    """
    env_platform = os.environ.get("SKILLS_PLATFORM", "").lower()
    if env_platform in PLATFORM_CONFIGS:
        return env_platform

    for name, skills_dir, _prio in PLATFORM_SKILL_DIRS:
        venv = skills_dir / VENV_SKILL / ".venv"
        if venv.exists():
            if name in ("claude",):
                return "claude"
            return "opencode"

    for _name, skills_dir, _prio in PLATFORM_SKILL_DIRS:
        if skills_dir.exists():
            if _name == "claude":
                return "claude"
            return "opencode"

    return "opencode"


def get_skills_dir(platform: Optional[str] = None) -> Path:
    """获取 skills 基础目录（当前 IDE 平台）。"""
    env_dir = os.environ.get("SKILLS_BASE_DIR")
    if env_dir:
        return Path(env_dir)

    if platform is None:
        # 检测第一个已安装 evolving-agent 的平台
        for _name, skills_dir, _prio in PLATFORM_SKILL_DIRS:
            if (skills_dir / VENV_SKILL).exists():
                return skills_dir
        platform = detect_platform()

    if platform in PLATFORM_CONFIGS:
        return PLATFORM_CONFIGS[platform]["skills_dir"]

    for name, skills_dir, _prio in PLATFORM_SKILL_DIRS:
        if name == platform or (platform == "claude-code" and name == "claude"):
            return skills_dir

    return PLATFORM_CONFIGS["opencode"]["skills_dir"]


def get_venv_python(platform: Optional[str] = None) -> Path:
    """Prefer shared venv; fall back to platform-local symlink target."""
    shared = get_shared_venv_python()
    if shared.is_file():
        return shared
    skills_dir = get_skills_dir(platform)
    local = skills_dir / VENV_SKILL / ".venv" / "bin" / "python"
    if local.is_file():
        return local
    return shared


def get_knowledge_base_dir(platform: Optional[str] = None) -> Path:
    """Global CodeGraph directory (shared across all platforms)."""
    env_path = os.environ.get("CODEGRAPH_DIR") or os.environ.get("KNOWLEDGE_BASE_PATH")
    if env_path:
        kb_path = Path(env_path)
        kb_path.mkdir(parents=True, exist_ok=True)
        return kb_path

    kb_path = get_agent_home() / "codegraph"
    legacy = _legacy_shared_knowledge_dir()
    if kb_path.exists() or not legacy.exists():
        kb_path.mkdir(parents=True, exist_ok=True)
        return kb_path

    # Legacy path still a real directory — use until install migrates
    if legacy.is_dir() and not legacy.is_symlink():
        legacy.mkdir(parents=True, exist_ok=True)
        return legacy

    kb_path.mkdir(parents=True, exist_ok=True)
    return kb_path


# 兼容旧常量名（运行时解析，非 import 时固定）
def _shared_knowledge_dir_compat() -> Path:
    return get_agent_home() / "codegraph"


def get_script_path(skill_name: str, script_name: str, platform: Optional[str] = None) -> Path:
    skills_dir = get_skills_dir(platform)
    return skills_dir / skill_name / "scripts" / script_name


def get_run_command(skill_name: str, script_name: str, *args, platform: Optional[str] = None) -> str:
    python_path = get_venv_python(platform)
    script_path = get_script_path(skill_name, script_name, platform)
    cmd_parts = [str(python_path), str(script_path)]
    cmd_parts.extend(str(arg) for arg in args)
    return " ".join(cmd_parts)


def print_paths(platform: Optional[str] = None):
    if platform is None:
        platform = detect_platform()
    print(f"Platform: {platform}")
    print(f"Agent Home: {get_agent_home()}")
    print(f"Skills Directory: {get_skills_dir(platform)}")
    print(f"Shared Venv Python: {get_shared_venv_python()}")
    print(f"Knowledge Base: {get_knowledge_base_dir(platform)}")
    print()
    print("Script paths:")
    print(f"  toggle_mode.py: {get_script_path('evolving-agent', 'toggle_mode.py', platform)}")
    print(f"  knowledge_query.py: {get_script_path('knowledge-base', 'knowledge_query.py', platform)}")


def get_project_kb_root(project_root: str | Path) -> Path:
    project_root = Path(project_root)
    cg_path = project_root / ".opencode" / "codegraph"
    cg_path.mkdir(parents=True, exist_ok=True)
    return cg_path


def get_global_kb_root() -> Path:
    return get_knowledge_base_dir()


def get_kb_root() -> Path:
    return get_knowledge_base_dir()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Path Resolver - 路径解析工具")
    parser.add_argument("--platform", "-p", choices=["opencode", "claude"],
                        help="指定平台")
    parser.add_argument("--skills-dir", action="store_true", help="输出 skills 目录")
    parser.add_argument("--venv-python", action="store_true", help="输出 venv Python 路径")
    parser.add_argument("--agent-home", action="store_true", help="输出共享 agent home")
    parser.add_argument("--knowledge-base", action="store_true", help="输出知识库目录")
    parser.add_argument("--script", nargs=2, metavar=("SKILL", "SCRIPT"), help="输出指定脚本路径")
    parser.add_argument("--run-cmd", nargs="+", metavar="ARG", help="输出运行命令")
    parser.add_argument("--all", "-a", action="store_true", help="输出所有路径信息")

    args = parser.parse_args()

    if args.all:
        print_paths(args.platform)
    elif args.agent_home:
        print(get_agent_home())
    elif args.skills_dir:
        print(get_skills_dir(args.platform))
    elif args.venv_python:
        print(get_venv_python(args.platform))
    elif args.knowledge_base:
        print(get_knowledge_base_dir(args.platform))
    elif args.script:
        print(get_script_path(args.script[0], args.script[1], args.platform))
    elif args.run_cmd and len(args.run_cmd) >= 2:
        skill, script = args.run_cmd[0], args.run_cmd[1]
        extra_args = args.run_cmd[2:] if len(args.run_cmd) > 2 else []
        print(get_run_command(skill, script, *extra_args, platform=args.platform))
    else:
        print(f"Detected platform: {detect_platform()}")
        print(f"Agent home: {get_agent_home()}")
        print(f"Skills directory: {get_skills_dir()}")
