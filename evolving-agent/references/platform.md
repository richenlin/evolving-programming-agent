# 平台差异 — 唯一定义

其他文件通过"见 `$SKILLS_DIR/evolving-agent/references/platform.md`"引用本文件，不各自重复。

---

## Agent 调度方式

| 平台 | 调度语法 | 说明 |
|------|---------|------|
| **OpenCode** | `@agent_name` | 原生多 agent，可指定模型，独立上下文 |
| **Claude Code** | `Task(subagent_type, prompt)` | Task tool spawn 匿名 subagent，继承 parent 模型 |
| **Cursor** | `Task(subagent_type, prompt)` | 同 Claude Code，通过 Task tool 调度子 agent |

三者语义一致：subagent 有独立上下文窗口，完成后返回结果给 parent。
SKILL.md 中标注 `[Claude Code/Cursor]` 的语法适用于 Claude Code 和 Cursor 两个平台。

---

## 审查门控

```
编码完成 → status: review_pending

[OpenCode]    调用 @reviewer 执行代码审查
[Claude Code] Task tool spawn reviewer subagent
              （加载 $SKILLS_DIR/evolving-agent/agents/reviewer.md 作为 prompt）

pass   → python run.py task transition --task-id $TASK_ID --status completed --actor reviewer
reject → python run.py task transition --task-id $TASK_ID --status rejected
         读取 reviewer_notes → 针对性修复 → 重新提交
```

---

## 知识归纳

```
所有任务 completed 后：

[OpenCode]    调用 @evolver 提取经验
[Claude Code] Task tool spawn evolver subagent
              （加载 $SKILLS_DIR/evolving-agent/agents/evolver.md 作为 prompt）
```

---

## 多 Agent 编排

主进程（SKILL.md）即 orchestrator，直接调度子 agent：

### OpenCode

```
主进程 = orchestrator（SKILL.md）
    ├─ @retrieval  ← 知识预取，完成后再调度 @coder
    ├─ @coder      ← 代码执行，可并行多个
    ├─ @reviewer   ← 代码审查，独立上下文
    └─ @evolver    ← 知识归纳
```

### Claude Code / Cursor

```
主进程 = orchestrator（SKILL.md）
    ├─ Task(retrieval, "...")   ← 知识预取，完成后再调度 coder
    ├─ Task(coder, "...")       ← 代码执行，可并行多个
    ├─ Task(reviewer, "...")    ← 代码审查，独立上下文
    └─ Task(evolver, "...")     ← 知识归纳
```

---

## Agent 文件位置

| Agent | 模型 | 文件 |
|-------|------|------|
| coder | `zai-coding-plan/glm-5` | `$SKILLS_DIR/evolving-agent/agents/coder.md` |
| reviewer | `opencode/claude-sonnet-4-6` | `$SKILLS_DIR/evolving-agent/agents/reviewer.md` |
| evolver | `zai-coding-plan/glm-5` | `$SKILLS_DIR/evolving-agent/agents/evolver.md` |
| retrieval | `zai-coding-plan/glm-5` | `$SKILLS_DIR/evolving-agent/agents/retrieval.md` |

> orchestrator 由主进程（SKILL.md）承担，不需要单独的 agent 文件。
