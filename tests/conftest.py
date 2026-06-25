"""
Pytest configuration and fixtures.
"""

import importlib
import sys
from pathlib import Path

import pytest

# Add all scripts directories to Python path
scripts_dirs = [
    Path(__file__).parent,
    Path(__file__).parent.parent / 'evolving-agent' / 'scripts',
    Path(__file__).parent.parent / 'evolving-agent' / 'scripts' / 'knowledge',
]

for scripts_dir in scripts_dirs:
    if str(scripts_dir) not in sys.path:
        sys.path.insert(0, str(scripts_dir))


def _load_kb_modules():
    """Load knowledge modules (may exist as top-level or knowledge.*)."""
    names = ("backend", "lifecycle", "query", "dashboard", "knowledge_io", "store", "trigger", "quality")
    mods = []
    seen = set()
    for name in names:
        for mod_name in (name, f"knowledge.{name}"):
            try:
                mod = importlib.import_module(mod_name)
            except ImportError:
                continue
            if id(mod) not in seen:
                seen.add(id(mod))
                mods.append(mod)
    return mods


def patch_get_db(monkeypatch, get_db_fn):
    """Patch get_db on every knowledge module alias."""
    for mod in _load_kb_modules():
        if hasattr(mod, "get_db"):
            monkeypatch.setattr(mod, "get_db", get_db_fn, raising=False)


@pytest.fixture
def kb_db(tmp_path, monkeypatch):
    """Isolated CodeGraph SQLite DB for knowledge tests."""
    from codegraph.db import CodeGraphDB

    db = CodeGraphDB(tmp_path / "knowledge.db")

    def _get_db(project_path=None):
        if project_path:
            return CodeGraphDB(
                Path(project_path) / ".opencode" / "codegraph" / "knowledge.db"
            )
        return db

    patch_get_db(monkeypatch, _get_db)
    return db


@pytest.fixture
def scripts_dir():
    return Path(__file__).parent.parent / "evolving-agent" / "scripts"


REPO_ROOT = Path(__file__).resolve().parent.parent
EVOLVING_AGENT_DIR = REPO_ROOT / "evolving-agent"
REVIEWER_MODEL = "opencode-go/minimax-m3"


def resolve_evolving_agent_path(*parts: str) -> Path:
    """Prefer repo copy; fall back to installed ~/.config/opencode/skills/evolving-agent."""
    repo_path = EVOLVING_AGENT_DIR.joinpath(*parts)
    if repo_path.exists():
        return repo_path
    installed = Path.home() / ".config" / "opencode" / "skills" / "evolving-agent"
    installed_path = installed.joinpath(*parts)
    if installed_path.exists():
        return installed_path
    raise FileNotFoundError(
        f"Cannot find evolving-agent/{'/'.join(parts)} in repo or {installed}"
    )


@pytest.fixture
def reviewer_md_path():
    return resolve_evolving_agent_path("agents", "reviewer.md")


@pytest.fixture
def sample_project(tmp_path):
    """Minimal Python project with OpenCode session artifacts for pipeline tests."""
    import json

    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "user.py").write_text(
        "class UserModel:\n    pass\n\ndef get_user():\n    return UserModel()\n",
        encoding="utf-8",
    )
    (tmp_path / "src" / "auth.py").write_text(
        "from user import get_user\n\ndef authenticate():\n    return get_user()\n",
        encoding="utf-8",
    )
    opencode = tmp_path / ".opencode"
    opencode.mkdir()
    (opencode / "progress.txt").write_text(
        """## 本次完成
- [x] 创建 User 模型

## 遇到的问题
- Prisma 初始化报错 → 需要先运行 npx prisma generate

## 关键决策
- 选择 bcrypt 而非 argon2 → 原因：bcrypt 更成熟
""",
        encoding="utf-8",
    )
    (opencode / "feature_list.json").write_text(
        json.dumps({
            "project": "pipeline-test",
            "tasks": [{
                "id": "task-001",
                "name": "创建 User 模型",
                "description": "User 数据模型与 password 哈希",
                "status": "completed",
                "reviewer_notes": ["缺少 password 字段校验"],
            }],
        }),
        encoding="utf-8",
    )
    return tmp_path


@pytest.fixture
def project_db(sample_project):
    """Project-scoped CodeGraphDB (created on first use)."""
    from codegraph.db import CodeGraphDB

    db_path = sample_project / ".opencode" / "codegraph" / "knowledge.db"
    return CodeGraphDB(db_path)
