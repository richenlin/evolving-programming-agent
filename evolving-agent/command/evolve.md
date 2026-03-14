---
name: evolve
description: Start the Evolving Agent coordinator. Supports mode initialization/switching and enters the orchestrator-driven "dispatch + review + evolution" closed loop.
metadata:
  command: /evolve
  usage: "/evolve [subcommand]"
---

# Evolve Command

`/evolve` 是 Evolving Programming Agent 的手动入口命令。

> `/evolve` 与触发词自动激活走**同一条执行路径**（SKILL.md 步骤 1→2→3→4）。
> 唯一额外作用：用户没有附带具体任务时，输出简短状态摘要。

## 1. 无参数 — 启动协调器

```bash
/evolve
```

1. 执行 SKILL.md **步骤 1（初始化）**：`mode --init` + `task status`
2. 根据任务状态分支：
   - 有 pending/rejected 任务 → 跳过步骤 2，直接进入**步骤 3.2** 编码调度
   - 无活跃任务且用户未附带具体任务 → 输出状态摘要后等待
   - 否则 → 执行 SKILL.md **步骤 2（意图识别）**

**状态摘要格式**（仅在无任务时输出）：
```
Evolution Mode: ACTIVE
Knowledge Base: N entries
Active Tasks: none
Ready — 描述你的编程任务、知识归纳或仓库学习需求。
```

## 2. 子命令

环境管理快捷指令，不经过 SKILL.md 流程：

| 子命令 | 行为 | 说明 |
|--------|------|------|
| `/evolve on` | `run.py mode --on` | 开启进化模式 |
| `/evolve off` | `run.py mode --off` | 关闭进化模式 |
| `/evolve status` | `run.py mode --status` | 查看进化模式状态 |
| `/evolve init` | `run.py mode --init` | 强制重新初始化 |

> 执行前需设置 `SKILLS_DIR` 变量：
> ```bash
> SKILLS_DIR=$([ -d ~/.config/opencode/skills/evolving-agent ] && echo ~/.config/opencode/skills || echo ~/.claude/skills)
> ```

## 3. `/evolve` vs 自然语言

| | `/evolve` | 自然语言 |
|---|---|---|
| 入口 | command/evolve.md | SKILL.md triggers |
| 执行路径 | SKILL.md 步骤 1→2→3→4 | SKILL.md 步骤 1→2→3→4 |
| 差异 | 可能无意图 → 输出摘要 | 用户消息中包含任务 |

两者共享同一执行路径。
