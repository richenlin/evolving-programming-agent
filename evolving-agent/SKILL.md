---
name: evolving-agent
description: AI 编程系统协调器。触发词："开发"、"实现"、"创建"、"添加"、"修复"、"报错"、"重构"、"优化"、"review"、"评审"、"继续"、"为什么"、"记住"、"保存经验"、"复盘"、"分析"、"学习"、"参考"、"模仿"、"/evolve"
---

# Evolving Agent — 入口协调器

只做三件事：**初始化 → 意图路由 → 最终验证**。

具体执行逻辑委托给各模式文件（自包含，读一个文件就能从头执行到尾）。

---

## 步骤 1：初始化

```bash
SKILLS_DIR=$([ -d ~/.config/opencode/skills/evolving-agent ] && echo ~/.config/opencode/skills || echo ~/.claude/skills)

# 激活进化模式（幂等）
python $SKILLS_DIR/evolving-agent/scripts/run.py mode --init

# 检查是否有未完成任务
python $SKILLS_DIR/evolving-agent/scripts/run.py task status --json
```

- 有未完成/被拒绝任务 → 直接进入对应模式文件的编码循环
- 无活跃会话 → 进入步骤 2

---

## 步骤 2：意图识别 + 路由

使用 `sequential-thinking` 分析用户输入，识别意图并制定执行计划。

然后按意图创建 TodoWrite checklist 并加载对应文件：

| 意图 | 触发词 | 加载文件 |
|------|--------|---------|
| 编程-新建 | 创建、实现、添加、开发、继续、完成 | `modules/programming-assistant/full-mode.md` |
| 编程-修复 | 修复、fix、bug、重构、优化、报错 | `modules/programming-assistant/simple-mode.md` |
| 编程-评审 | review、评审、审查 | `modules/programming-assistant/simple-mode.md`（步骤 A 入口） |
| 编程-咨询 | 怎么、为什么、解释 | `modules/programming-assistant/consult-mode.md` |
| 归纳 | 记住、保存、复盘、提取 | `modules/knowledge-base/guide.md` |
| 学习 | 学习、分析、参考、模仿 | `modules/github-to-knowledge/guide.md` |

> 「报错」默认走修复（simple-mode）。sequential-thinking 可根据上下文调整：
> 如用户只是询问原因而不需要改代码，可路由到 consult-mode。

TodoWrite checklist 从对应模式文件的"Checklist"章节获取。
加载文件后立即执行，不停顿。

---

## 步骤 3：最终验证

模式文件执行完毕后，回到这里做收尾检查：

1. TodoWrite checklist 是否全部 completed？未完成则继续执行
2. 任务状态是否全部 completed？（`run.py task status`）
3. 向用户反馈执行结果

---

## 进化模式

标记文件：`.opencode/.evolution_mode_active`

- **激活时**：编程完成后自动调用 evolver 提取经验
- **未激活时**：跳过自动归纳，需用户通过"记住"/"复盘"手动触发

> 命令速查见 `references/commands.md`
> 平台差异（OpenCode vs Claude Code agent 调度）见 `references/platform.md`
