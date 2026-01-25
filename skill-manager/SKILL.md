---
name: skill-manager
description: AI 系统的技能生命周期管理器。触发词："列出skill"、"查看skill"、"skill列表"、"有哪些skill"、"检查skill"、"更新skill"、"删除skill"、"启用skill"、"禁用skill"、"skill状态"、"健康检查"、"list skills"、"check skills"
license: MIT
metadata:
  triggers: ["列出skill", "查看skill", "skill列表", "有哪些skill", "检查skill", "更新skill", "删除skill", "启用skill", "禁用skill", "skill状态", "健康检查", "list skills", "check skills", "update skill", "delete skill", "enable skill", "disable skill", "scan skills"]
---

# Skill Manager
 
AI 编程系统的**技能生命周期管理器**，负责维护系统中所有已安装 Skill 的状态、更新和健康状况。

## 1. 核心定位

此 Skill 是 `evolving-agent` 架构中的**运维工具**。

- **上游**: `evolving-agent` (负责调度管理指令)
- **职责**: 确保 skills 目录下的 Skill 保持健康、最新且有序。
  - OpenCode: `~/.config/opencode/skills/`
  - Claude Code / Cursor: `~/.claude/skills/`

## 2. 调度协议 (Interface)

### 输入 (Commands)
由用户指令触发，经 `evolving-agent` 调度：
- **检查**: `check skills`, `scan skills`
- **列表**: `list skills`
- **管理**: `enable/disable <skill>`, `delete <skill>`
- **健康**: `health check`, `status`

### 输出 (Report)
- **状态报告**: JSON/Table 格式的技能状态清单
- **操作反馈**: 操作成功与否的确认信息

## 3. 核心能力 (Capabilities)

> **路径约定**: 执行命令前先设置 `SKILLS_DIR` 变量：
> ```bash
> SKILLS_DIR=$([ -d ~/.config/opencode/skills/evolving-agent ] && echo ~/.config/opencode/skills || echo ~/.claude/skills)
> ```

### 3.1 列表管理 (List)
列出所有已安装的 Skill 及其基本信息。

```bash
$SKILLS_DIR/evolving-agent/.venv/bin/python $SKILLS_DIR/skill-manager/scripts/list_skills.py
```
**输出**:
- Skill 名称
- 版本 (如有)
- 状态 (Enabled/Disabled)
- 来源 (System/User/GitHub)

### 3.2 扫描与更新检查 (Scan & Check)
扫描本地 Skill，并对比 GitHub 远程仓库检查更新。

```bash
$SKILLS_DIR/evolving-agent/.venv/bin/python $SKILLS_DIR/skill-manager/scripts/scan_and_check.py
```
**检查项**:
- 解析 `SKILL.md` 的 `github_hash`
- 调用 `git ls-remote` 获取远程 HEAD
- 报告 `Outdated` (有新提交) 或 `Current` (最新)

### 3.3 启用与禁用 (Toggle)
不删除文件，仅通过移动目录实现软停用。

```bash
# 禁用 (移动到 .disabled/ 目录)
$SKILLS_DIR/evolving-agent/.venv/bin/python $SKILLS_DIR/skill-manager/scripts/toggle_skill.py --disable <skill_name>

# 启用 (移回主目录)
$SKILLS_DIR/evolving-agent/.venv/bin/python $SKILLS_DIR/skill-manager/scripts/toggle_skill.py --enable <skill_name>
```

### 3.4 健康检查 (Health Check)
深度检查 Skill 的完整性和有效性。

```bash
$SKILLS_DIR/evolving-agent/.venv/bin/python $SKILLS_DIR/skill-manager/scripts/health_check.py
```
**检查标准**:
- ✅ **Healthy**: `SKILL.md` 存在且格式正确
- ⚠️ **Outdated**: GitHub 有新版本
- ❌ **Invalid**: 缺少必要文件或 YAML 格式错误

### 3.5 删除 (Delete)
永久移除 Skill。

```bash
$SKILLS_DIR/evolving-agent/.venv/bin/python $SKILLS_DIR/skill-manager/scripts/delete_skill.py <skill_name>
```

## 4. 工作流示例 (Workflows)

### 场景 1: 每日巡检
1. 用户输入: "检查一下所有 skill 的状态"
2. Agent 执行: `$SKILLS_DIR/evolving-agent/.venv/bin/python $SKILLS_DIR/skill-manager/scripts/health_check.py`
3. 反馈:
   ```
   [Status Report]
   ✅ programming-assistant (v3.0.0) - Healthy
   ✅ github-to-skills - Healthy
   ⚠️ some-old-skill - Outdated (Behind 5 commits)
   ```

### 场景 2: 更新 Skill
1. 发现 `some-old-skill` 过期
2. 用户输入: "更新 some-old-skill"
3. Agent 执行:
   - 读取远程 README
   - 生成新的 `SKILL.md`
   - 更新 `github_hash`

### 场景 3: 临时停用
1. 某 Skill 干扰了正常工作
2. 用户输入: "暂时禁用 auto-completer"
3. Agent 执行: `$SKILLS_DIR/evolving-agent/.venv/bin/python $SKILLS_DIR/skill-manager/scripts/toggle_skill.py --disable auto-completer`
4. 结果: 目录被移至 `.disabled/auto-completer`，不再被系统加载。

## 5. 脚本清单 (Scripts)

| 脚本 | 用途 |
|------|------|
| `scripts/list_skills.py` | 列出所有 Skill |
| `scripts/scan_and_check.py` | 扫描版本并检查 GitHub 更新 |
| `scripts/health_check.py` | 综合健康状态检查 |
| `scripts/toggle_skill.py` | 启用/禁用 (目录移动) |
| `scripts/delete_skill.py` | 删除 Skill |
| `scripts/utils/frontmatter_parser.py` | YAML Frontmatter 解析工具 |

## 6. 元数据规范 (Metadata Standard)

本管理器依赖 `SKILL.md` 中的标准元数据进行管理：

```yaml
metadata:
  github_url: "https://github.com/user/repo"  # 来源仓库
  github_hash: "a1b2c3d..."                   # 当前安装版本的 Commit Hash
  version: "1.0.0"                            # 语义化版本 (可选)
  status: "active"                            # 状态 (active/deprecated)
```
