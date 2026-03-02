# Base Workflow — 公共基底

> 本文件提取 full-mode.md 和 simple-mode.md 的公共部分，避免重复维护。
> **full-mode** 和 **simple-mode** 通过引用本文件中的章节获取公共步骤。

---

## 环境准备

```bash
# 设置路径变量（每个会话执行一次）
SKILLS_DIR=$([ -d ~/.config/opencode/skills/evolving-agent ] && echo ~/.config/opencode/skills || echo ~/.claude/skills)

# 获取项目根目录
PROJECT_ROOT=$(git rev-parse --show-toplevel 2>/dev/null || pwd)
```

---

## 知识检索

```bash
# 知识检索（与任务初始化并行，不阻塞主流程）
python $SKILLS_DIR/evolving-agent/scripts/run.py knowledge trigger \
  --input "用户输入描述" --format context > $PROJECT_ROOT/.opencode/.knowledge-context.md

# 读取历史经验
cat $PROJECT_ROOT/.opencode/.knowledge-context.md
```

> 利用历史经验，快速定位类似问题和已有解决方案。

---

## 审查门控（硬约束）

所有任务编码完成后，**必须**经过以下审查流程：

```
├─ [OpenCode]    调用 @reviewer 执行代码审查
├─ [Claude Code] Task tool spawn reviewer subagent
│               （加载 $SKILLS_DIR/evolving-agent/agents/reviewer.md 作为 prompt，独立上下文）

审查通过（reviewer pass）：
  python $SKILLS_DIR/evolving-agent/scripts/run.py task transition \
    --task-id $TASK_ID --status completed --actor reviewer
  → 继续下一个任务

审查拒绝（reviewer reject）：
  python $SKILLS_DIR/evolving-agent/scripts/run.py task transition \
    --task-id $TASK_ID --status rejected
  → 读取 reviewer_notes → 针对性修复 → 重新提交审查
```

> ⚠️ **禁止跳过审查直接标记 completed**，状态机会强制拒绝此操作。

---

## 结果验证

```bash
# 查看当前所有任务状态
python $SKILLS_DIR/evolving-agent/scripts/run.py task status

# 确认所有任务已 completed（无 pending/rejected/review_pending）
python $SKILLS_DIR/evolving-agent/scripts/run.py task list --json
```

验证通过条件：
- 所有任务 `status = completed`
- 无 `review_pending` 或 `rejected` 状态残留

---

## 强制知识归纳（不可跳过）

按照 `./evolution-check.md` 执行进化检查。

> ⚠️ 此步骤**强制执行**，不因任务简单而跳过。
> 即使只修复了一个小 bug，也必须提取经验存入知识库。

```bash
# [OpenCode]    调用 @evolver 提取经验
# [Claude Code] Task tool spawn evolver subagent
#               （加载 $SKILLS_DIR/evolving-agent/agents/evolver.md 作为 prompt，独立上下文）
```

---

## 错误处理

```
错误发生 → 分析原因 → 尝试方案（最多 3 次）
├─ 成功 → 继续执行，记录到 progress.txt "遇到的问题"
└─ 连续失败 3 次 → 标记 blocked + 记录详情 + 报告用户

标记 blocked：
  python $SKILLS_DIR/evolving-agent/scripts/run.py task transition \
    --task-id $TASK_ID --status blocked
```

---

## 状态文件说明

| 文件 | 用途 | 模板 |
|------|------|------|
| `$PROJECT_ROOT/.opencode/feature_list.json` | 任务清单和状态（由 CLI 管理） | `../template/feature_list.json` |
| `$PROJECT_ROOT/.opencode/progress.txt` | 当前任务进度（手动维护） | `../template/progress.txt` |
| `$PROJECT_ROOT/.opencode/.knowledge-context.md` | 知识检索结果（自动生成） | — |

> **注意**: `progress.txt` 只保存当前任务详情，历史任务查看 `feature_list.json`。

---

## 平台差异

| 平台 | 多 Agent 方式 | reviewer/evolver |
|------|--------------|-----------------|
| **OpenCode** | 通过 `@orchestrator` 原生调度，并行执行 | 使用 `evolving-agent/agents/` 中的 agent 文件 |
| **Claude Code** | 当前 agent 扮演 orchestrator，通过 Task tool 调度 | Task tool spawn reviewer/evolver subagent（独立上下文） |
