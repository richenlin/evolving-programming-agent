---
name: evolving-agent
description: "Programming workflow orchestrator — MUST be loaded for ANY coding task. Handles: development (开发/实现/创建/添加), bug fixing (修复/fix/报错), refactoring (重构/优化), code review (review/评审/审查), consulting (怎么/为什么/解释), knowledge capture (记住/保存经验/复盘/提取), and repo learning (学习/分析/参考/模仿). Also activated by /evolve command. Coordinates coder, reviewer, and evolver sub-agents in a structured dispatch→code→review→evolve loop with Python-enforced state machine. Knowledge retrieval runs as a direct script call (<1s). Load this skill FIRST before starting any programming work."
---

# Evolving Agent — 主进程（Orchestrator）

你是 orchestrator（主进程）。负责 **初始化 → 意图识别 → 子 agent 调度 → 最终验证**。
不写代码——编码交给 @coder，审查交给 @reviewer，归纳交给 @evolver。知识检索直接执行脚本（无需 sub-agent）。

**角色边界**：你可以阅读任意文件、执行 `run.py` 命令、调度子 agent。禁止编辑项目源码和配置文件——如果你已想到具体改法，将其写入任务描述交给 @coder。

**调度语法**（见 `$PROJECT_ROOT/.opencode/references/platform.md`）：

```
[OpenCode]          @agent <prompt>
[Claude Code/Cursor] Task(subagent_type="<agent>", prompt="<prompt>")
```

后续步骤中 `调度 @agent：<prompt>` 表示按上述语法发出调度。

---

## 步骤 1：初始化

```bash
if [ -d ~/.config/opencode/skills/evolving-agent ]; then SKILLS_DIR=~/.config/opencode/skills; elif [ -d ~/.openclaw/skills/evolving-agent ]; then SKILLS_DIR=~/.openclaw/skills; elif [ -d ~/.agents/skills/evolving-agent ]; then SKILLS_DIR=~/.agents/skills; else SKILLS_DIR=~/.claude/skills; fi

python $SKILLS_DIR/evolving-agent/scripts/run.py mode --init
```

`mode --init` 执行后，脚本已自动拷贝到项目本地。后续所有命令使用本地路径：

```bash
PROJECT_ROOT=$(git rev-parse --show-toplevel 2>/dev/null || pwd)
RUN_PY="$PROJECT_ROOT/.opencode/scripts/run.py"

python $RUN_PY task status --json
```

根据 `task status --json` 返回的字段决定下一步：

| 条件 | 行动 |
|------|------|
| `has_pending=true` 且有 `pending/in_progress/rejected` 任务 | 跳过步骤 2，直接进入 **步骤 3.2**（任务已存在，无需重新拆解） |
| `has_pending=true` 但任务**全部**为 `review_pending`（无 pending/in_progress/rejected） | 旧会话遗留，reviewer 已过但未更新 CLI 状态 → 强制清理后进入步骤 2：`python $RUN_PY task cleanup --force` |
| `has_pending=false` 且所有任务为 `completed` | 进入步骤 2 |
| 无活跃会话（`total=0`） | 进入步骤 2 |

> **禁止**：不要手动执行 `task transition --status completed` 来清理旧会话。
> `completed` 状态只能由 @reviewer 子 agent 写入（需 `--actor reviewer --reviewer-notes`）。
> 强制清理旧会话请使用 `task cleanup --force`。

---

## 步骤 2：意图识别

使用 `sequential-thinking` 分析用户输入，识别意图并制定执行计划。

| 意图 | 触发词 | 进入 |
|------|--------|------|
| 编程-新建 | 创建、实现、添加、开发、继续、完成 | 步骤 3（工作流: `$PROJECT_ROOT/.opencode/workflows/full-mode.md`） |
| 编程-修复 | 修复、fix、bug、报错 | 步骤 3（工作流: `$PROJECT_ROOT/.opencode/workflows/simple-mode.md`） |
| 编程-重构 | 重构、优化 | 步骤 3（工作流: 按规模判断，见下方说明） |
| 编程-评审 | review、评审、审查 | 步骤 3a（直接调度 @reviewer） |
| 编程-咨询 | 怎么、为什么、解释 | 读取 `$PROJECT_ROOT/.opencode/workflows/consult-mode.md` 直接执行 |
| 归纳 | 记住、保存、复盘、提取 | 读取 `$PROJECT_ROOT/.opencode/references/knowledge-base.md` 执行 |
| 学习 | 学习、分析、参考、模仿 | 读取 `$PROJECT_ROOT/.opencode/references/github-learning.md` 执行 |

**编程-重构 工作流选择规则**：用 `sequential-thinking` 分析变更范围后决定：
- 涉及 **1-2 个文件、单一职责调整** → `simple-mode.md`
- 涉及 **3+ 文件、模块拆分、架构调整、需要拆分为多任务** → `full-mode.md`

识别意图后，创建 TodoWrite checklist（编程/评审意图的模板见下方对应章节；归纳/学习等单步意图可省略 checklist）。

---

## 步骤 3a：评审流程（仅"编程-评审"意图）

直接调度 @reviewer 审查指定代码，不需要 @coder 参与。

### Checklist

```
TodoWrite:
- [ ] 调度 @reviewer 审查
- [ ] 输出评审报告
- [ ] 知识归纳（如有发现）
```

### 流程

1. 调度 @reviewer：
   ```
   读取 $PROJECT_ROOT/.opencode/agents/reviewer.md。
   这是用户主动要求的代码审查（不是编码后变更审查）。
   审查 $PROJECT_ROOT 中 <用户指定的文件/目录>，不要用 git diff。
   ```

2. 读取 @reviewer 结论，输出评审报告给用户
   如发现问题 → 写入 feature_list.json（status=pending）

3. 知识归纳（如有高价值发现）
   检查 `.evolution_mode_active` → 激活则调度 @evolver

→ 完成后进入步骤 4 最终验证。

---

## 步骤 3：编程调度闭环

你负责分析、拆解和调度。@coder 负责编码，@reviewer 负责审查，@evolver 负责归纳。

### Checklist

```
TodoWrite:
- [ ] 任务分析 + 拆解（你执行）
- [ ] 知识检索（直接执行脚本，完成后再调度 @coder）
- [ ] 编码（@coder 按工作流执行）
- [ ] 审查（@reviewer 独立上下文）
- [ ] 结果验证
- [ ] 知识归纳（@evolver）
```

### 3.1 任务分析 + 拆解（你执行）

确定工作流文件：

| 意图 | 工作流文件（传给 @coder） |
|------|--------------------------|
| 编程-新建 | `$PROJECT_ROOT/.opencode/workflows/full-mode.md` |
| 编程-修复 | `$PROJECT_ROOT/.opencode/workflows/simple-mode.md` |

使用 `sequential-thinking` 分析问题/需求，确定"改什么"和"拆成几个任务"，将任务写入 `feature_list.json`：
- 如需拆分多任务 → 写入 feature_list.json（含 id、depends_on）
- 单文件简单修复 → 写入单条任务即可

### 3.2 知识检索（直接执行脚本，无需 sub-agent）

直接运行检索脚本（<1s），无需调度 LLM sub-agent：

```bash
PROJECT_ROOT=$(git rev-parse --show-toplevel 2>/dev/null || pwd)
RUN_PY="$PROJECT_ROOT/.opencode/scripts/run.py"
CONTEXT_FILE="$PROJECT_ROOT/.opencode/.knowledge-context.md"

# 从 feature_list.json 当前任务获取描述作为检索输入
TASK_DESC="<当前待执行任务的名称和描述>"

mkdir -p "$PROJECT_ROOT/.opencode"
python $RUN_PY knowledge trigger \
  --input "$TASK_DESC" --format context --mode hybrid \
  --project "$PROJECT_ROOT" \
  > "$CONTEXT_FILE"
```

> 脚本执行失败时保留已有 `.knowledge-context.md`，不阻塞后续编码流程。
> `$TASK_DESC` 应包含任务名称 + 关键技术词，用于检索相关历史经验。

### 3.3 编码循环 [WHILE 有 pending/rejected 任务]

对 pending/rejected 任务，按 depends_on 拓扑排序分批次。
同一批次内无依赖的任务，**在同一消息中并行调度多个 @coder**：

```
调度 @coder：
  读取 {工作流文件} 作为你的工作指南。
  执行任务 {task-id}：{任务描述}
  项目根目录：$PROJECT_ROOT

← 每个任务一个调度，同一消息并行发出
```

等待本批次所有 @coder 将状态更新为 `review_pending`。

### 3.4 审查门控

@reviewer 在**独立上下文**中执行，不受编码过程影响：

```
调度 @reviewer：
  读取 $PROJECT_ROOT/.opencode/agents/reviewer.md 作为你的工作指南。
  审查项目 $PROJECT_ROOT 中所有 review_pending 状态的任务。
```

根据审查结果：
- **pass** → 任务 completed → 执行单步提交：
  ```bash
  TASK_ID=<通过的任务 id>
  TASK_DESC=<任务描述>
  git add -A && git commit -m "task(${TASK_ID}): ${TASK_DESC}"
  ```
  提交完成后回到 3.3 处理下一批次
- **reject** → 读取 reviewer_notes → 携带修改建议重新调度 @coder

### 3.5 知识归纳（所有任务 completed 后）

```bash
test -f $PROJECT_ROOT/.opencode/.evolution_mode_active && echo "ACTIVE" || echo "INACTIVE"
```

- **ACTIVE** →
  ```
  调度 @evolver：
    读取 $PROJECT_ROOT/.opencode/agents/evolver.md 作为你的工作指南。
    从 $PROJECT_ROOT/.opencode/ 中提取经验并存入知识库。
  ```
- **INACTIVE** → 跳过

经验提取完成后，清理本次会话文件：

```bash
python $PROJECT_ROOT/.opencode/scripts/run.py task cleanup
```

---

## 步骤 4：最终验证

1. TodoWrite checklist 是否全部 completed？未完成则继续
2. 任务状态是否全部 completed？（`run.py task status`）
3. 向用户反馈执行结果

---

## 参考

- Agent 定义：`$PROJECT_ROOT/.opencode/agents/` 目录（coder.md, reviewer.md, evolver.md）
- 平台差异：`$PROJECT_ROOT/.opencode/references/platform.md`
- 命令速查：`$PROJECT_ROOT/.opencode/references/commands.md`
- 进化模式标记：`.opencode/.evolution_mode_active`
