# 平台差异 — 唯一定义

其他文件通过"见 `references/platform.md`"引用本文件，不各自重复。

---

## Agent 调度方式

| 平台 | 调度语法 | 说明 |
|------|---------|------|
| **OpenCode** | `@agent_name` | 原生多 agent，可指定模型，独立上下文 |
| **Claude Code** | `Task(subagent_type, prompt)` | Task tool spawn 匿名 subagent，继承 parent 模型 |

两者语义一致：subagent 有独立上下文窗口，完成后返回结果给 parent。

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

## 多 Agent 编排（Full Mode）

### OpenCode

```
@orchestrator (调度)
    ├─ @retrieval  ← 知识预取，并行
    ├─ @coder      ← 代码执行，可并行多个
    ├─ @reviewer   ← 代码审查
    └─ @evolver    ← 知识归纳
```

### Claude Code

当前 agent 扮演 orchestrator，通过 Task tool 调度：

```
当前 agent
    ├─ Task("知识检索: ...")   → retrieval
    ├─ Task("编码任务: ...")   → coder（可并行多个）
    ├─ Task("代码审查: ...")   → reviewer（独立上下文）
    └─ Task("经验提取: ...")   → evolver（独立上下文）
```

---

## Agent 文件位置

| Agent | 模型 | 文件 |
|-------|------|------|
| orchestrator | `zai-coding-plan/glm-5` | `agents/orchestrator.md` |
| coder | `zai-coding-plan/glm-5` | `agents/coder.md` |
| reviewer | `openrouter/anthropic/claude-sonnet-4.6` | `agents/reviewer.md` |
| evolver | `zai-coding-plan/glm-5` | `agents/evolver.md` |
| retrieval | `zai-coding-plan/glm-5` | `agents/retrieval.md` |
