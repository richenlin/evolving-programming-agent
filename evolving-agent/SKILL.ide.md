---
name: evolving-agent
description: "Programming workflow orchestrator (IDE Mode) — MUST be loaded for ANY coding task in single-model IDE environments. Handles: development, bug fixing, refactoring, code review, consulting, knowledge capture, and repo learning. Uses evolving_agent tool for sub-agent semantics in single-process environment. Python-enforced state machine. Knowledge retrieval runs as a direct script call (<1s). Load this skill FIRST before starting any programming work."
---

# Evolving Agent — IDE Mode（单模型适配版）

> 本文件是 evolving-agent skill 的 **IDE 单模型适配版本**。
> - 默认上下文（OpenCode / Claude Code）请用 `SKILL.md`
> - IDE 集成方读取本文件：`run.py meta --skill-content --mode ide`
> - 两份内容保持核心逻辑（状态机/知识库/工作流）一致，仅调度语法不同

<EVOLVING_AGENT_IDE_MODE>
你处在单模型 IDE 环境。**没有** Task tool / 多模型 sub-agent 调度能力。
所有 sub-agent 语义通过 `evolving_agent` tool 实现：

- `action="task_status"` / `"task_create"` / `"task_transition"` — 任务状态机
- `action="knowledge_query"` / `"knowledge_store"` — 知识库
- `action="request_review"` — IDE 主进程会用同模型新开 conversation 执行 reviewer，独立 context，返回审查结果
- `action="request_evolver"` — 同理，独立 conversation 执行 evolver

⚠️ MANDATORY：所有编程任务必须先 evolving_agent(task_create) + transition 到 in_progress，
否则 write_file / apply_patch / multi_replace_in_file 等编辑工具会被 IDE 拒绝执行。
</EVOLVING_AGENT_IDE_MODE>

你是 orchestrator（主进程）。负责 **初始化 → 意图识别 → 角色扮演 + 状态机驱动 → 最终验证**。
不写代码——编码在 [CODER] 角色中执行，审查通过 `evolving_agent(action="request_review")` 委托独立 conversation，归纳通过 `evolving_agent(action="request_evolver")` 委托独立 conversation。知识检索直接执行脚本（无需 sub-agent）。

**角色边界**：你可以阅读任意文件、执行 `run.py` 命令、切换 [CODER] 角色编码、调用 evolving_agent tool 触发审查/归纳。禁止在 orchestrator 角色中编辑项目源码和配置文件——如果你已想到具体改法，将其写入任务描述，进入 [CODER] 角色后再编码。

---

## 步骤 1：初始化

直接执行：

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
> `completed` 状态只能由 reviewer 写入（通过 `evolving_agent(action="request_review")` 返回 pass 时自动完成）。
> 强制清理旧会话请使用 `task cleanup --force`。

---

## 步骤 2：意图识别

使用 `sequential-thinking` 分析用户输入，识别意图并制定执行计划。

| 意图 | 触发词 | 进入 |
|------|--------|------|
| 编程-新建 | 创建、实现、添加、开发、继续、完成 | 步骤 3（工作流: `$PROJECT_ROOT/.opencode/workflows/full-mode.md`） |
| 编程-修复 | 修复、fix、bug、报错 | 步骤 3（工作流: `$PROJECT_ROOT/.opencode/workflows/simple-mode.md`） |
| 编程-重构 | 重构、优化 | 步骤 3（工作流: 按规模判断，见下方说明） |
| 编程-评审 | review、评审、审查 | 步骤 3a（直接调用 evolving_agent request_review） |
| 编程-咨询 | 怎么、为什么、解释 | 读取 `$PROJECT_ROOT/.opencode/workflows/consult-mode.md` 直接执行 |
| 归纳 | 记住、保存、复盘、提取 | 读取 `$PROJECT_ROOT/.opencode/references/knowledge-base.md` 执行 |
| 学习 | 学习、分析、参考、模仿 | 读取 `$PROJECT_ROOT/.opencode/references/github-learning.md` 执行 |

**编程-重构 工作流选择规则**：用 `sequential-thinking` 分析变更范围后决定：
- 涉及 **1-2 个文件、单一职责调整** → `simple-mode.md`
- 涉及 **3+ 个文件、模块拆分、架构调整、需要拆分为多任务** → `full-mode.md`

识别意图后，创建 TodoWrite checklist（编程/评审意图的模板见下方对应章节；归纳/学习等单步意图可省略 checklist）。

---

## 步骤 3a：评审流程（仅"编程-评审"意图）

直接调用 evolving_agent request_review 审查指定代码，不需要进入 [CODER] 角色。

### Checklist

```
TodoWrite:
- [ ] 调用 evolving_agent(action="request_review") 审查
- [ ] 输出评审报告
- [ ] 知识归纳（如有发现）
```

### 流程

1. 调用 `evolving_agent(action="request_review", args={scope: "<用户指定的文件/目录>", mode: "user_initiated"})`：
   - IDE 主进程会用同模型新开 conversation，以 `agents/reviewer.md` 作为 system prompt
   - 审查用户指定的文件/目录，不依赖 git diff
   - 等待 tool 返回结果

2. 读取审查结论，输出评审报告给用户
   如发现问题 → 写入 feature_list.json（status=pending）

3. 知识归纳（如有高价值发现）
   检查 `.evolution_mode_active` → 激活则调用 `evolving_agent(action="request_evolver")`

→ 完成后进入步骤 4 最终验证。

---

## 步骤 3：编程调度闭环

你负责分析、拆解和角色切换。[CODER] 角色负责编码，reviewer 在独立 conversation 中审查，evolver 在独立 conversation 中归纳。

### Checklist

```
TodoWrite:
- [ ] 任务分析 + 拆解（你执行）
- [ ] 知识检索（直接执行脚本，完成后再进入 [CODER] 角色）
- [ ] 编码（[CODER] 角色按工作流执行）
- [ ] 审查（evolving_agent request_review，独立上下文）
- [ ] 结果验证
- [ ] 知识归纳（evolving_agent request_evolver）
```

### 3.1 任务分析 + 拆解（你执行）

确定工作流文件：

| 意图 | 工作流文件（[CODER] 角色使用） |
|------|------------------------------|
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

⚠️ **单进程串行执行**——一次只能扮演一个 [CODER] 角色，多任务按拓扑顺序逐个处理。

对每个任务：

1. 调用 `evolving_agent(action="task_transition", args={task_id: "<TASK_ID>", status: "in_progress"})`
2. **进入 [CODER] 角色**：
   - 读取 `{工作流文件}` 作为工作指南
   - 读取 `$PROJECT_ROOT/.opencode/.knowledge-context.md`（如存在）获取知识上下文
   - 读取 reviewer_notes（如上次被 reject）
   - 执行任务：阅读代码 → 分析 → 编码 → 测试
3. 编码完成后，调用 `evolving_agent(action="task_transition", args={task_id: "<TASK_ID>", status: "review_pending"})`

更新 `$PROJECT_ROOT/.opencode/progress.txt`：
- 记录"遇到的问题"
- 记录"关键决策"

### 3.4 审查门控

所有任务都 `review_pending` 后，一次性审查全部：

调用 `evolving_agent(action="request_review", args={scope: "all_review_pending"})`：
- IDE 主进程会在独立 conversation 中执行 reviewer，以 `agents/reviewer.md` 作为 system prompt
- 审查所有 review_pending 状态的任务
- **不要自己扮演 reviewer**——审查必须由独立 context 完成

根据审查结果（tool 返回）：
- **pass** → 任务自动 transition 到 completed（reviewer 工具内完成）→ 执行单步提交：
  ```bash
  TASK_ID=<通过的任务 id>
  TASK_DESC=<任务描述>
  git add -A && git commit -m "task(${TASK_ID}): ${TASK_DESC}"
  ```
  提交完成后回到 3.3 处理下一批次
- **reject** → 读取 reviewer_notes → 重新进入 [CODER] 角色，携带修改建议修复

### 3.5 知识归纳（所有任务 completed 后）

```bash
test -f $PROJECT_ROOT/.opencode/.evolution_mode_active && echo "ACTIVE" || echo "INACTIVE"
```

- **ACTIVE** → 调用 `evolving_agent(action="request_evolver", args={project_root: "$PROJECT_ROOT"})`：
  - IDE 主进程会在独立 conversation 中执行 evolver，以 `agents/evolver.md` 作为 system prompt
  - 从 `.opencode/` 中提取经验并存入知识库
  - **不要自己扮演 evolver**
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

- Agent 角色定义：`$PROJECT_ROOT/.opencode/agents/` 目录（coder.md, reviewer.md, evolver.md）
  - reviewer.md / evolver.md 由 evolving_agent tool 内部使用，作为 fresh conversation 的 system prompt
- 工作流：`$PROJECT_ROOT/.opencode/workflows/full-mode.md` / `simple-mode.md` / `consult-mode.md`
  - 适用，但调度部分以本文件为准（workflow 文档中如提到"调度 @agent"等 multi-agent 语法，请忽略，按本文件的 evolving_agent tool 调用方式执行）
- 命令速查：`$PROJECT_ROOT/.opencode/references/commands.md`
- 进化模式标记：`.opencode/.evolution_mode_active`
