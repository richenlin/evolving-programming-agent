---
name: evolving-agent
description: AI 编程系统协调器。触发词："开发"、"实现"、"创建"、"添加"、"修复"、"报错"、"重构"、"优化"、"review"、"评审"、"继续"、"实现"、"为什么"、"记住"、"保存经验"、"复盘"、"分析"、"学习"、"参考"、"模仿"、"/evolve"
---

# Evolving Agent - 协调器

你现在扮演"主进程监督员"的角色，负责管理任务的完整生命周期。

> **渐进披露原则**: 本文件只定义主进程逻辑，详细实现委托给各模块（子进程）。

---

## 核心流程（强制执行）

```
步骤1: 环境初始化
  1.1 设置路径变量：
      SKILLS_DIR=$([ -d ~/.config/opencode/skills/evolving-agent ] && echo ~/.config/opencode/skills || echo ~/.claude/skills)
      > 后续所有命令使用 `$SKILLS_DIR` 变量

  1.2 激活进化模式（幂等，重复调用安全）：
      python $SKILLS_DIR/evolving-agent/scripts/run.py mode --init
      > 确保 `.opencode/.evolution_mode_active` 存在，步骤6验证时需要此标记。
      > 无论由 /evolve 命令还是触发词自动进入，此步骤保证初始化一致。

步骤2: 意图识别
  2.1 上下文优先检查（优先于关键词匹配）：
      首先执行 `python $SKILLS_DIR/evolving-agent/scripts/run.py task status --json`
      ├─ 命令失败或输出 "No active task session"
      │   → 无活跃会话，进入 2.2 关键词匹配
      ├─ has_active_session=true 且 (has_pending=true 或 has_rejected=true)
      │   → 编程意图（继续未完成/被拒绝的任务），跳过 2.2
      └─ has_active_session=true 且全部 completed
          → 进入 2.2 关键词匹配（当前会话已结束）

  2.2 关键词匹配：
      必须使用 `sequential-thinking` 工具进行深度分析和调度，识别用户意图: 编程 / 归纳 / 学习

      | 意图 | 触发词 |
      |------|--------|
      | 编程 | 开发、实现、创建、添加、修复、重构、优化、完成、review、怎么、为什么、报错、解释 |
      | 归纳 | 记住、保存、复盘、提取 |
      | 学习 | 学习、分析、参考、模仿 |

      > 编程意图包含咨询类问题（怎么/为什么/报错），由 programming-assistant 内部路由到 Consult Mode。

步骤3: 任务拆解与分发（加载对应模块）
  ├─ 编程意图 → 读取 $SKILLS_DIR/evolving-agent/modules/programming-assistant/guide.md
  │             [OpenCode] 通知 @orchestrator 接管，传入任务描述
  │             [Claude Code] 当前 agent 扮演 orchestrator，通过 Task tool 调度 subagent 执行
  ├─ 归纳意图 → 读取 $SKILLS_DIR/evolving-agent/modules/knowledge-base/guide.md
  └─ 学习意图 → 读取 $SKILLS_DIR/evolving-agent/modules/github-to-knowledge/guide.md

步骤4: 子进程按照模块文档执行任务
  执行模块中定义的完整流程
  > 重要: 识别到意图后立即加载模块执行，不要停止或等待确认！
  > 编程任务必须经过 reviewer 审查后才能标记 completed，结束前必须调用 evolver

步骤5: 健康检查与监控
  在子进程运行期间，如果任务支持分步，定期检查中间产物：
  ├─ 检查 .opencode/progress.txt 的执行进度
  ├─ 检查 .opencode/feature_list.json 的任务状态
  └─ 如发现执行结果偏离预期（代码不符合规范、测试失败等），中断并重新调整

步骤6: 结果验证
  子进程完成后，主进程必须对产出进行最终审计：
  ├─ 检查所有任务状态是否为 completed
  ├─ 检查 .opencode/.evolution_mode_active，是否成功完成经验提取
  └─ 确保任务闭环，向用户反馈执行结果
```

---

## 调度规则

| 意图 | 加载模块 | 核心流程 |
|------|----------|----------|
| **编程** | `modules/programming-assistant/guide.md` | 知识检索 → 状态恢复 → 开发循环 → 审查门控 → 进化检查 |
| **归纳** | `modules/knowledge-base/guide.md` | 提取经验 → 分类 → 存储到知识库 |
| **学习** | `modules/github-to-knowledge/guide.md` | fetch → extract → store |

> **评审→修复 衔接规则**：评审（review/评审）走 Simple Mode 步骤A，完成后会将问题写入
> `feature_list.json`（status=pending）。用户后续发出修复指令时，步骤1 读取该文件自动
> 恢复上下文，进入修复循环（步骤4），**必须经过 reviewer 审查门控**。

---

## 多 Agent 调度（编程意图）

编程任务采用 **调度-执行-审查-进化** 四段式闭环，平台差异如下：

### OpenCode（原生多 agent）

```
evolving-agent
    ↓
@orchestrator (GLM-5)     ← 任务调度，只读+Task权限
    ├─ @retrieval (GLM-5) ← 知识预取，并行执行
    ├─ @coder (GLM-5)     ← 代码执行，全权限
    ├─ @reviewer (claude-sonnet-4.6) ← 代码审查，只读+git
    └─ @evolver (GLM-5)   ← 知识归纳，强制执行
```

**步骤3（编程意图）升级为**：
1. 读取 `$SKILLS_DIR/evolving-agent/modules/programming-assistant/guide.md`
2. 通知 @orchestrator 接管，传入任务描述
3. orchestrator 负责后续的调度-执行-审查-进化全流程

### Claude Code（Task tool 调度）

当前 agent 扮演 orchestrator 角色，通过 Task tool spawn 独立 subagent：

```
当前 agent (orchestrator)
    ├─ Task(prompt="知识检索: ...")       → retrieval subagent
    ├─ Task(prompt="编码任务: ...")       → coder subagent（可并行多个）
    ├─ Task(prompt="代码审查: ...")       → reviewer subagent（独立上下文）
    └─ Task(prompt="经验提取: ...")       → evolver subagent（独立上下文）
```

1. 读取 `$SKILLS_DIR/evolving-agent/modules/programming-assistant/guide.md`
2. 按 full-mode.md / simple-mode.md 执行，当前 agent 负责任务拆解和调度
3. 审查时：Task tool spawn reviewer subagent（加载 `agents/reviewer.md` 作为 prompt）
4. 进化时：Task tool spawn evolver subagent（加载 `agents/evolver.md` 作为 prompt）

> **与 OpenCode 的差异**：OpenCode 用 `@agent` 语法 spawn 命名 agent 并可指定模型，
> Claude Code 用 `Task(subagent_type, prompt)` spawn 匿名 subagent，默认继承 parent 模型。
> 两者的 Task tool 语义一致：subagent 有独立上下文窗口，完成后返回结果给 parent。

---

## 模块职责（详细实现委托给子进程）

| 模块 | 职责 | 文档位置 |
|------|------|----------|
| **programming-assistant** | 代码生成、修复、重构 | `modules/programming-assistant/` |
| **knowledge-base** | 知识存储、查询、归纳 | `modules/knowledge-base/` |
| **github-to-knowledge** | 仓库学习、知识提取 | `modules/github-to-knowledge/` |

## Agent 角色（详细定义见 agents/ 目录）

| Agent | 模型 | 职责 | 文件位置 |
|-------|------|------|----------|
| **orchestrator** | `zai-coding-plan/glm-5` | 任务调度、DAG 排序、并行分发 | `agents/orchestrator.md` |
| **coder** | `zai-coding-plan/glm-5` | 代码执行、测试验证 | `agents/coder.md` |
| **reviewer** | `openrouter/anthropic/claude-sonnet-4.6` | 代码审查、质量把关 | `agents/reviewer.md` |
| **evolver** | `zai-coding-plan/glm-5` | 知识提取、经验归纳 | `agents/evolver.md` |
| **retrieval** | `zai-coding-plan/glm-5` | 知识检索、上下文预取 | `agents/retrieval.md` |

---

## 进化模式

标记文件: `.opencode/.evolution_mode_active`

- **激活时**: 已经触发自动提取经验
- **未激活时**: 未触发自动提取，需用户手动提取

> 命令速查、健康检查清单、结果验证清单见 `references/commands.md`
