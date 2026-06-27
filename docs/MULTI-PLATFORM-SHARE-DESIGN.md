# 多平台共享机制设计

> 状态：已实施（P0–P2）  
> 关联：`scripts/install.sh`、`core/path_resolver.py`、`CODEGRAPH-KB-DESIGN.md`

---

## 一、问题

执行 `./scripts/install.sh --all` 时，OpenCode / Claude Code / Cursor / OpenClaw / Hermes **各装一份** evolving-agent，导致：

| 资源 | 当前行为 | 典型体积（单份） | 5 平台合计 |
|------|----------|------------------|------------|
| Skill 源码（SKILL.md、scripts/） | 每平台复制一份 | ~2–5 MB | ~10–25 MB（可接受） |
| **Python `.venv`** | 每平台 `setup_shared_venv` 独立创建 | **300 MB–1.5 GB**（含 sentence-transformers） | **1.5–7 GB** |
| **BGE 权重** | 预下载写入用户级 cache | ~100 MB | 理论共享，但无统一 `HF_HOME` 约束 |
| **全局 knowledge.db** | 设计为 `~/.config/opencode/codegraph/` | 数 MB–数百 MB | 已共享（若路径未漂移） |
| **项目 vectors** | `$PROJECT/.opencode/codegraph/vectors/` | 按项目 | 与平台无关（正确） |

用户感知：**装 3 个 IDE 就占 3 份 Python 环境与依赖**，空间浪费严重；知识库在文档与部分 fallback 路径下仍可能分裂。

---

## 二、设计目标

1. **一份运行时**：全平台共用 **单个 `.venv` + 单套 pip 依赖**。
2. **一份全局知识库**：全局 `knowledge.db` 与配置 **唯一权威路径**。
3. **一份模型缓存**：BGE / ModelScope 权重 **集中 cache 目录**，`prewarm` 只执行一次。
4. **平台 skill 仍独立**：各 IDE 必须从各自 skills 目录加载 SKILL.md / agents — **只共享重资源，不共享 skill 树**。
5. **向后兼容**：已有安装可 `--migrate-shared` 迁移，旧路径 symlink 保留 1–2 个版本周期。
6. **显式可覆盖**：`EVOLVING_AGENT_HOME` / `VENV_PYTHON` / `CODEGRAPH_DIR` 仍可手动指定。

---

## 三、目录布局（推荐）

采用 **XDG 风格用户数据根**，与 OpenCode 配置解耦，避免「只有装了 OpenCode 才有共享目录」：

```
${EVOLVING_AGENT_HOME}          # 默认 ~/.local/share/evolving-agent
├── runtime/
│   ├── .venv/                  # ★ 唯一 Python 虚拟环境
│   ├── python                  # → .venv/bin/python（便于脚本引用）
│   └── requirements.lock       # install 时写入，便于诊断
├── cache/
│   ├── huggingface/            # HF_HOME（BGE 权重）
│   └── modelscope/             # MODELSCOPE_CACHE
├── codegraph/
│   └── knowledge.db            # ★ 全局 KB（从 opencode/codegraph 迁入或 symlink）
├── config/
│   └── env                     # 原 evolving-agent.env 内容
└── install-manifest.json       # 已链接的平台列表 + 版本
```

**各平台 skill 目录**（仅文本 + 符号链接）：

```
~/.config/opencode/skills/evolving-agent/
~/.claude/skills/evolving-agent/
~/.agents/skills/evolving-agent/
~/.openclaw/skills/evolving-agent/
~/.hermes/skills/evolving-agent/
    ├── SKILL.md, agents/, scripts/ …   # 仍完整复制（IDE 要求）
    └── .venv → ${EVOLVING_AGENT_HOME}/runtime/.venv   # ★ 符号链接
```

**兼容旧路径**（迁移期 symlink，只读指向新位置）：

```
~/.config/opencode/codegraph/     → ~/.local/share/evolving-agent/codegraph/
~/.config/opencode/evolving-agent.env → config/env（或合并进 env 并由 run.py 读取）
```

---

## 四、环境变量契约

| 变量 | 默认值 | 用途 |
|------|--------|------|
| `EVOLVING_AGENT_HOME` | `$XDG_DATA_HOME/evolving-agent` 或 `~/.local/share/evolving-agent` | 共享根目录 |
| `EVOLVING_AGENT_VENV` | `$EVOLVING_AGENT_HOME/runtime/.venv` | 唯一 venv |
| `VENV_PYTHON` | `$EVOLVING_AGENT_HOME/runtime/python` | 写入 `.agent_config`，run.py 首选 |
| `CODEGRAPH_DIR` / `KNOWLEDGE_BASE_PATH` | `$EVOLVING_AGENT_HOME/codegraph` | 全局 KB |
| `HF_HOME` | `$EVOLVING_AGENT_HOME/cache/huggingface` | BGE 权重（install --china 设置） |
| `MODELSCOPE_CACHE` | `$EVOLVING_AGENT_HOME/cache/modelscope` | ModelScope 下载 |

加载顺序（与现有 run.py 一致，扩展一项）：

```
1. ~/.local/share/evolving-agent/config/env   # 新：共享全局配置
2. ~/.config/opencode/evolving-agent.env      # 旧：兼容
3. $PROJECT/.opencode/.agent_config           # 项目级（仅填充未设置项）
```

---

## 五、路径解析（单一权威）

扩展 `core/path_resolver.py`，所有模块禁止硬编码 `~/.config/opencode/codegraph` 或「按平台拼 venv」：

```python
def get_agent_home() -> Path:
    return Path(os.environ.get("EVOLVING_AGENT_HOME", _default_agent_home()))

def get_shared_venv_python() -> Path:
    explicit = os.environ.get("VENV_PYTHON") or os.environ.get("EVOLVING_AGENT_VENV")
    if explicit:
        p = Path(explicit)
        if p.is_dir():
            return p / "bin" / "python"
        return p
    return get_agent_home() / "runtime" / ".venv" / "bin" / "python"

def get_knowledge_base_dir() -> Path:
    env = os.environ.get("CODEGRAPH_DIR") or os.environ.get("KNOWLEDGE_BASE_PATH")
    if env:
        return Path(env)
    return get_agent_home() / "codegraph"
```

`run.py::get_python_executable()` 查找顺序调整为：

1. `VENV_PYTHON`（`.agent_config`）
2. `get_shared_venv_python()`（共享 venv）
3. `skill_root/.venv`（开发模式，源码仓库）
4. 各平台 `{skills}/evolving-agent/.venv`（**兼容**：若为 symlink 则命中共享 venv）
5. `sys.executable`

`toggle_mode.py::_find_venv_python()` 改为调用 `get_shared_venv_python()`，不再按平台顺序扫描多份 venv。

---

## 六、安装器改造

### 6.1 新函数（`scripts/lib/shared-runtime.sh`）

```bash
EVOLVING_AGENT_HOME="${EVOLVING_AGENT_HOME:-$HOME/.local/share/evolving-agent}"
SHARED_VENV="${EVOLVING_AGENT_HOME}/runtime/.venv"

ensure_shared_runtime() {
  # 1. 创建目录树
  # 2. 若 SHARED_VENV 不存在 → python3 -m venv + pip install 核心/可选依赖（仅一次）
  # 3. prewarm BGE（仅一次，HF_HOME 指向共享 cache）
  # 4. 写入 config/env + install-manifest.json
}

link_platform_venv() {
  local skills_base="$1"   # 如 ~/.agents/skills
  local link="${skills_base}/evolving-agent/.venv"
  # 若已是正确 symlink → 跳过
  # 若是实体目录 → 备份为 .venv.bak.<timestamp> 再 ln -s
  ln -snf "${SHARED_VENV}" "${link}"
}
```

### 6.2 `install.sh` 主流程变更

```
原：for each platform → setup_shared_venv($platform_skills_dir)
新：
  ensure_shared_runtime()                    # 一次
  for each platform:
      install_skill_copy(...)
      link_platform_venv($platform_skills_dir)
      set_python_executable(...)
```

`--all` 从「5 次 venv + 5 次 prewarm」变为 **「1 次 venv + 1 次 prewarm + 5 个 symlink」**。

### 6.3 迁移命令

```bash
./scripts/install.sh --migrate-shared          # 检测旧 venv，合并/删除冗余，建立 symlink
./scripts/install.sh --migrate-shared --dry-run
```

迁移策略：

1. 若多个平台各有 `.venv`，选 **最新 mtime 或 pip list 最完整** 的一份 move 到 `SHARED_VENV`。
2. 其余 `.venv` 改名为 `.venv.legacy.<platform>`（install 日志提示用户确认后删除）。
3. `~/.config/opencode/codegraph` 若已有数据 → move 或 symlink 到 `EVOLVING_AGENT_HOME/codegraph`。
4. 更新 `evolving-agent.env` → `config/env`。

### 6.4 卸载

`uninstall.sh --platform cursor`：**只删** `~/.agents/skills/evolving-agent/`，**不删** `EVOLVING_AGENT_HOME`（其他平台仍用）。

`uninstall.sh --all --purge-runtime`：额外删除 `EVOLVING_AGENT_HOME`（含 venv + 全局 KB + 模型 cache，需确认）。

---

## 七、知识库与向量

### 7.1 全局 KB（跨平台、跨 IDE）

- **唯一路径**：`$EVOLVING_AGENT_HOME/codegraph/knowledge.db`
- `codegraph/paths.py::get_global_knowledge_db_path()` 改为委托 `path_resolver.get_knowledge_base_dir()`
- 删除 `run.py` 中 `platform == 'claude'` → `~/.claude/knowledge` 的 fallback（迁移期可 warn + redirect）

### 7.2 项目 KB（按仓库，不变）

- 仍在 `$PROJECT/.opencode/codegraph/knowledge.db`
- 与平台无关，无需共享机制

### 7.3 向量索引

- **当前**：`vectors/index.json` 在项目目录（Phase 3 迁入 SQLite `entry_embedding`）
- **共享策略**：向量 **不放到 EVOLVING_AGENT_HOME**（按项目隔离正确）；共享的是 **embedder 模型权重** 与 **embed 运行时**，不是向量数据本身

---

## 八、install-manifest.json

```json
{
  "version": 1,
  "agent_home": "/Users/me/.local/share/evolving-agent",
  "shared_venv": "/Users/me/.local/share/evolving-agent/runtime/.venv",
  "skill_version": "abc1234",
  "platforms": {
    "opencode": {"skills_dir": "~/.config/opencode/skills/evolving-agent", "linked_at": "2026-06-23T..."},
    "cursor":   {"skills_dir": "~/.agents/skills/evolving-agent", "linked_at": "..."}
  },
  "cache": {
    "hf_home": ".../cache/huggingface",
    "modelscope": ".../cache/modelscope",
    "bge_model": "BAAI/bge-small-zh-v1.5",
    "prewarm_at": "..."
  }
}
```

用途：诊断、`install.sh --status`、CI 校验、避免重复 prewarm。

---

## 九、边界与风险

| 场景 | 处理 |
|------|------|
| Windows（Cursor） | symlink 需 Developer Mode 或 junction；fallback：`.venv/activate` 脚本写 `VENV_PYTHON` 绝对路径，不依赖 symlink |
| 多用户同机 | `EVOLVING_AGENT_HOME` 在用户 home 下，天然隔离 |
| 不同 Python 版本需求 | 共享 venv 锁定一个 minor 版本；install 前检查 `python3 --version` |
| 平台只装一个 | 仍走 `ensure_shared_runtime()`，无额外开销 |
| 开发模式（源码仓库） | 保留 `evolving-agent/.venv` 本地 venv，**不**链到共享（`EVOLVING_AGENT_DEV=1`） |
| IDE 打包（IDE-INTEGRATION） | 便携包自带 venv，不走用户级 `EVOLVING_AGENT_HOME` |

---

## 十、实施阶段

| 阶段 | 内容 | 风险 |
|------|------|------|
| **P0** | `path_resolver` 增加 `get_agent_home()` / `get_shared_venv_python()`；`run.py`、`toggle_mode`、`codegraph/paths.py` 统一引用 | 低 |
| **P1** | `shared-runtime.sh` + `install.sh` 单次 venv + 平台 symlink；`config/env` 写入 HF_HOME | 中（需测 symlink） |
| **P2** | `--migrate-shared` + `install.sh --status`；文档与 README 更新 | 低 |
| **P3** | `uninstall.sh --purge-runtime`；废弃 `setup_venv.sh` 多 venv 逻辑 | 低 |
| **P4** | 可选：`evolving-agent doctor` 子命令检查链接/manifest/磁盘占用 | 低 |

### P0 验收

- 仅安装 OpenCode + Cursor 后，`du -sh */evolving-agent/.venv` 显示 symlink，**总占用 ≈ 1 份 venv**
- 两平台各跑 `codegraph context`，命中同一 `knowledge.db` inode
- `prewarm` 日志只出现一次，BGE 在 `EVOLVING_AGENT_HOME/cache/huggingface`

### P1 验收

- `./scripts/install.sh --all --china` 完成后磁盘：共享 venv + 单份 HF cache < 旧方案 40%

---

## 十一、与 CodeGraph v3 的关系

- v3 设计已规定全局 KB 路径为 `~/.config/opencode/codegraph/` — 实施本方案时 **改为** `$EVOLVING_AGENT_HOME/codegraph/`，旧路径 symlink 兼容。
- `entry_embedding` 表（Phase 3）落在 **项目** `knowledge.db`，与共享机制无冲突。
- KnowledgePlane 只依赖 `get_knowledge_base_dir()`，换根目录对上层透明。

---

## 十二、用户可见变化（迁移后）

```bash
# 查看共享状态
./scripts/install.sh --status

# 预期输出
# EVOLVING_AGENT_HOME: ~/.local/share/evolving-agent
# Shared venv:         1.2 GB
# HF cache (BGE):      96 MB
# Global KB:           12 MB
# Linked platforms:    opencode, cursor, claude-code
# Legacy venv dirs:    none
```

安装提示由「每个 Skill 的虚拟环境位于 skill_dir/.venv/」改为「**运行时共享**：skill_dir/.venv → ~/.local/share/evolving-agent/runtime/.venv」。

---

## 十三、决策摘要

| 决策 | 选择 | 理由 |
|------|------|------|
| 共享根目录 | `~/.local/share/evolving-agent` | XDG 惯例，不绑定 OpenCode |
| venv 绑定方式 | symlink（Unix）/ env 绝对路径（Windows） | 对现有 `skill_dir/.venv` 探测逻辑侵入最小 |
| 全局 KB | 迁入 agent_home，旧路径 symlink | 单一 inode，避免 Claude fallback 分裂 |
| 模型 cache | 强制 HF_HOME 到 agent_home/cache | 避免预下载散落 ~/.cache |
| Skill 副本 | 仍每平台一份 | IDE 发现机制不可改 |
| 迁移 | 显式 `--migrate-shared` | 避免 install 误删用户 venv |
