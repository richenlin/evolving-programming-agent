---
name: evolve
description: Start the Evolving Agent coordinator. Supports mode initialization/switching and enters the orchestrator-driven "dispatch + review + evolution" closed loop.
metadata:
  command: /evolve
  usage: "/evolve [subcommand]"
---

# Evolve Command

`/evolve` 是 Evolving Programming Agent 的手动入口命令。

> **核心原则**：`/evolve` 与触发词自动激活走**同一条执行路径**（SKILL.md 步骤 1~6）。
> `/evolve` 的唯一额外作用是：当用户没有附带具体任务时，输出简短状态摘要。

## 1. 无参数 — 启动协调器

```bash
/evolve
```

**执行流程**：

1. 执行 SKILL.md **步骤 1（环境初始化）**：设置路径 + `mode --init`
2. 执行 SKILL.md **步骤 2（意图识别）**：
   - 2.1 上下文检查 `run.py task status --json`
   - 如有活跃任务 → 直接进入步骤 3 继续执行（不暂停）
   - 如无活跃任务且用户未附带具体任务 → 输出状态摘要后等待下一条消息
3. 后续消息由 SKILL.md 触发词自动匹配，走相同的步骤 1~6

**状态摘要格式**（仅在无活跃任务且无具体任务时输出）：
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
| `/evolve on` | `run.py mode --on` | 仅开启进化模式 |
| `/evolve off` | `run.py mode --off` | 关闭进化模式 |
| `/evolve status` | `run.py mode --status` | 查看进化模式状态 |
| `/evolve init` | `run.py mode --init` | 强制重新初始化 |

> 执行前需设置 `SKILLS_DIR` 变量：
> ```bash
> SKILLS_DIR=$([ -d ~/.config/opencode/skills/evolving-agent ] && echo ~/.config/opencode/skills || echo ~/.claude/skills)
> ```

## 3. `/evolve` vs 自然语言

| | `/evolve` | 自然语言（如"开发一个功能"） |
|---|---|---|
| 入口 | command/evolve.md | SKILL.md triggers 匹配 |
| 执行路径 | SKILL.md 步骤 1~6 | SKILL.md 步骤 1~6 |
| 初始化 | 步骤 1.2 `mode --init` | 步骤 1.2 `mode --init` |
| 意图识别 | 步骤 2（可能无意图 → 输出摘要） | 步骤 2（从用户消息识别意图） |
| 差异 | 用户可能未附带任务 | 用户消息中包含任务 |

两者**共享同一条执行路径**，唯一区别是 `/evolve` 不附带任务时多输出一次状态摘要。
