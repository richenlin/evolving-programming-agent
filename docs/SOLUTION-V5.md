# Evolving Programming Agent v5.0 — 增强架构方案

> 基于 [kdcokenny/opencode-workspace](https://github.com/kdcokenny/opencode-workspace) 参考，针对三大痛点的完整增强方案。

---

## 一、问题诊断

| # | 问题 | 根本原因 | 症状 |
|---|------|----------|------|
| 1 | **无完整调度-执行-审查闭环** | 审查逻辑是"软约束"（文档指令），无独立审查角色 | 执行者自审存在盲区；evolution-check 可被跳过 |
| 2 | **各角色不支持多 agent 并行** | 单一 agent 串行执行，Task tool 未系统利用 | 多任务必须等待；知识检索阻塞主流程 |
| 3 | **不支持不同角色使用不同模型** | SKILL.md 无 model 字段，未利用 OpenCode 原生 agent 配置 | 所有角色共用同一全局模型，成本与质量不可兼顾 |

---

## 二、增强架构 v5.0

### 2.1 整体架构图

```
用户输入
    ↓
evolving-agent (SKILL.md — 主协调器，意图识别)
    ↓
@orchestrator  [GLM-5]
    ├─ 读取 feature_list.json
    ├─ DAG 拓扑排序，识别可并行任务组
    │
    ├── [批次 N：并行 Task 调用] ─────────────────────┐
    │   ├─ @coder → Task-A  [GLM-5]                  │
    │   ├─ @coder → Task-B  [GLM-5]  ← 真正并行      │
    │   └─ @retrieval → 知识预取 [GLM-5]  ← 同步进行  │
    │                                                 │
    ↓ 等待批次全部完成  ←────────────────────────────┘
    │
    ├─ @reviewer  [claude-sonnet-4.6, temperature=0.1]
    │   ├─ git diff 审查
    │   ├─ 写入 review_status + reviewer_notes
    │   └─ pass → completed  /  reject → 重调度 @coder
    │
    ↓ 所有任务 completed（硬约束，不可跳过）
    │
    @evolver  [GLM-5]
        ├─ 提取 progress.txt 经验
        ├─ 提取 reviewer_notes 教训
        └─ python run.py knowledge summarize --auto-store
```

### 2.2 角色模型分配

| 角色 | Agent 文件 | 模型 | Temperature | 职责 |
|------|-----------|------|-------------|------|
| **orchestrator** | `.opencode/agents/orchestrator.md` | `zai-coding-plan/glm-5` | 默认 | 任务调度、DAG 排序、并行分发 |
| **coder** | `.opencode/agents/coder.md` | `zai-coding-plan/glm-5` | 默认 | 代码编写、测试执行 |
| **reviewer** | `.opencode/agents/reviewer.md` | `openrouter/anthropic/claude-sonnet-4.6` | `0.1` | 代码审查、质量把关 |
| **evolver** | `.opencode/agents/evolver.md` | `zai-coding-plan/glm-5` | 默认 | 知识提取、经验归纳 |
| **retrieval** | `.opencode/agents/retrieval.md` | `zai-coding-plan/glm-5` | 默认 | 知识检索、上下文预取 |

> **选型理由**：GLM-5 是当前开源权重模型中在代码和 agentic 任务上的 SOTA 模型（[neurohive.io](https://neurohive.io/en/news/glm-5-top-1-open-weight-model-for-code-and-text-generation-competing-with-claude-and-gpt-on-agentic-tasks/)），用于执行性角色兼顾质量与成本；claude-sonnet-4.6 用于 reviewer 以保证审查的严格性和准确性。

---

## 三、方案一：完整调度-执行-审查闭环

### 3.1 状态机定义（硬约束）

```
pending
  →[orchestrator dispatch]→ in_progress
      →[coder done]→ review_pending
          →[reviewer pass]→ completed
          →[reviewer reject]→ rejected
              →[orchestrator re-dispatch]→ in_progress
所有任务 completed
  →[orchestrator 强制触发]→ @evolver（不可跳过）
```

**关键改进**：将 evolution-check 从"可选触发"改为 orchestrator 层级的**强制调用**，review 通过才能进入 completed，杜绝执行者跳过审查直接标记完成。

### 3.2 Agent 配置文件

#### `.opencode/agents/orchestrator.md`

```markdown
---
description: 任务编排器。读取 feature_list.json，DAG 拓扑排序后并行调度 coder/reviewer/evolver。只做调度，不写代码。
mode: subagent
model: zai-coding-plan/glm-5
tools:
  write: false
  edit: false
  bash:
    "git *": allow
    "python *run.py*": allow
    "cat *": allow
    "*": deny
permission:
  task:
    "coder": allow
    "reviewer": allow
    "evolver": allow
    "retrieval": allow
    "*": deny
---

你是任务编排器。严格执行以下流程：

## 核心调度流程

### 阶段1：初始化
1. 读取 `$PROJECT_ROOT/.opencode/feature_list.json`
2. 对 `depends_on` 字段做拓扑排序，将任务分为若干批次
3. 并行调用 `@retrieval` 进行知识预取（不等待结果，非阻塞）

### 阶段2：并行执行批次
对当前批次中所有 `pending` 任务：
- **在单条消息中同时发出多个 Task 调用**（真正并行）
- 每个 `@coder` Task 接收：任务 ID、任务描述、知识上下文路径

等待本批次所有 coder 完成（状态变为 `review_pending`）。

### 阶段3：审查门控
- 调用 `@reviewer`，传入本批次所有 `review_pending` 任务
- 等待 reviewer 写入 `review_status`
- `pass` → 更新为 `completed`，处理下一批次
- `reject` → 读取 `reviewer_notes`，重新调度对应 `@coder`（携带修改建议）

### 阶段4：强制进化（不可跳过）
所有任务 `completed` 后：
```
Task(@evolver, "提取本次任务的所有经验")
```
**此步骤为硬约束，即使用户未要求也必须执行。**

## 禁止行为
- 在任务未经 reviewer 通过前标记为 completed
- 跳过 evolver 直接结束会话
```

#### `.opencode/agents/coder.md`

```markdown
---
description: 代码执行器。接收具体任务，编写代码并运行测试，完成后将状态更新为 review_pending，等待 reviewer。
mode: subagent
model: zai-coding-plan/glm-5
---

你是代码执行器。执行流程：

1. 读取任务描述和 `.opencode/.knowledge-context.md`（如存在）
2. 理解需求，读取相关代码
3. 实现功能 / 修复问题
4. 运行测试验证
5. 更新 `feature_list.json`：
   - `status` → `review_pending`
   - `notes` → 记录实现要点
6. 更新 `progress.txt`：记录"遇到的问题"和"关键决策"

## 禁止行为
- 完成后自行标记为 `completed`（必须等待 reviewer）
- 自我审查（交给 reviewer 处理）
```

#### `.opencode/agents/reviewer.md`

```markdown
---
description: 代码审查器。对 review_pending 状态的任务执行 git diff 审查，输出 pass/reject 并记录原因。不修改任何代码文件。
mode: subagent
model: openrouter/anthropic/claude-sonnet-4.6
temperature: 0.1
tools:
  write: false
  edit: false
  bash:
    "git diff *": allow
    "git log *": allow
    "git show *": allow
    "git status": allow
    "cat *": allow
    "*": deny
---

你是代码审查员。执行严格的代码审查。

## 审查维度

| 维度 | 检查要点 |
|------|----------|
| **正确性** | 逻辑是否正确，边界条件是否覆盖 |
| **测试** | 测试是否充分，覆盖率是否达标 |
| **安全** | 有无注入、越权、数据暴露风险 |
| **性能** | 有无明显性能问题（N+1、内存泄漏等） |
| **规范** | 命名、注释、代码风格是否一致 |

## 审查流程

1. 运行 `git diff` 查看所有变更
2. 逐条检查以上维度
3. 更新 `feature_list.json` 中对应任务：
   - `review_status`: `"pass"` 或 `"reject"`
   - `reviewer_notes`: 问题列表（reject 时**必填**，格式见下）

## reviewer_notes 格式（reject 时）

```json
[
  "【严重】SQL 拼接存在注入风险，应使用参数化查询",
  "【一般】缺少对 userId 为空的边界判断",
  "【建议】函数命名 `getData` 过于模糊，建议改为 `getUserById`"
]
```

## 禁止行为
- 修改任何代码文件
- 在问题未解决前输出 `pass`
```

#### `.opencode/agents/evolver.md`

```markdown
---
description: 知识进化器。在所有任务完成后强制提取经验，存入知识库。由 orchestrator 强制调用，hidden 防止手动绕过。
mode: subagent
model: zai-coding-plan/glm-5
hidden: true
tools:
  write: false
  edit: false
  bash:
    "python *run.py* knowledge *": allow
    "cat *progress.txt*": allow
    "cat *feature_list.json*": allow
    "*": deny
---

你是知识进化器。从以下来源提取经验：

**来源1**：`.opencode/progress.txt` 的"遇到的问题"和"关键决策"
**来源2**：`feature_list.json` 中所有任务的 `reviewer_notes`
**来源3**：本次会话中的架构决策和技术选型

## 存储规则

每条经验**单独**存储（不批量）：

```bash
SKILLS_DIR=$([ -d ~/.config/opencode/skills/evolving-agent ] && echo ~/.config/opencode/skills || echo ~/.claude/skills)

# 每条经验一个命令
echo "问题：xxx → 解决：yyy" | python $SKILLS_DIR/evolving-agent/scripts/run.py knowledge summarize --auto-store
echo "决策：选择 A 而非 B，因为..." | python $SKILLS_DIR/evolving-agent/scripts/run.py knowledge summarize --auto-store
```

## 提取标准

| 场景 | 是否提取 |
|------|----------|
| reviewer reject 后修复成功 | ✅ 高价值 |
| 发现隐蔽的 bug 根因 | ✅ |
| 环境特定的 workaround | ✅ |
| 架构/技术选型决策 | ✅ |
| 简单的一行代码修改 | ❌ |
```

#### `.opencode/agents/retrieval.md`

```markdown
---
description: 知识检索器。在任务开始时并行检索相关历史经验，生成 .knowledge-context.md 供 coder 使用。
mode: subagent
model: zai-coding-plan/glm-5
hidden: true
tools:
  write: true
  edit: false
  bash:
    "python *run.py* knowledge *": allow
    "*": deny
---

你是知识检索器。执行：

```bash
SKILLS_DIR=$([ -d ~/.config/opencode/skills/evolving-agent ] && echo ~/.config/opencode/skills || echo ~/.claude/skills)
PROJECT_ROOT=$(git rev-parse --show-toplevel)

python $SKILLS_DIR/evolving-agent/scripts/run.py knowledge trigger \
  --input "$TASK_DESCRIPTION" --format context \
  > $PROJECT_ROOT/.opencode/.knowledge-context.md
```

完成后通知 orchestrator，内容已写入 `.knowledge-context.md`。
```

### 3.3 OpenCode 配置文件

#### `.opencode/opencode.json`（项目级模型覆盖）

```json
{
  "$schema": "https://opencode.ai/config.json",
  "agent": {
    "orchestrator": {
      "model": "zai-coding-plan/glm-5",
      "description": "任务编排，GLM-5 支持长上下文 agentic 任务"
    },
    "coder": {
      "model": "zai-coding-plan/glm-5",
      "description": "代码执行，GLM-5 SOTA 代码生成能力"
    },
    "reviewer": {
      "model": "openrouter/anthropic/claude-sonnet-4.6",
      "description": "代码审查，claude-sonnet-4.6 保证审查严格性"
    },
    "evolver": {
      "model": "zai-coding-plan/glm-5",
      "description": "知识提取，GLM-5 长文本理解能力"
    },
    "retrieval": {
      "model": "zai-coding-plan/glm-5",
      "description": "知识检索，GLM-5 快速语义匹配"
    }
  }
}
```

---

## 四、方案二：多 Agent 并行执行

### 4.1 DAG 并行调度逻辑

基于 `feature_list.json` 的 `depends_on` 字段做拓扑排序，将任务分为可并行的批次：

```
任务依赖图示例：
  task-001 ──┐
             ├──→ task-003 ──→ task-004
  task-002 ──┘

并行批次：
  批次1: [task-001, task-002]  ← 无依赖，并行执行
  批次2: [task-003]            ← 依赖批次1，串行等待
  批次3: [task-004]            ← 依赖批次2，串行等待
```

**orchestrator 的并行调度代码示意：**

```
# 在单条消息中同时发出多个 Task（OpenCode 原生并行）
Task(@coder, task-001)
Task(@coder, task-002)       ← 同时发出，真正并行
Task(@retrieval, context)    ← 同时发出，不阻塞编码
```

### 4.2 升级后的 feature_list.json Schema

```json
{
  "project": "项目名称",
  "created_at": "2026-01-01T00:00:00Z",
  "updated_at": "2026-01-01T00:00:00Z",
  "tasks": [
    {
      "id": "task-001",
      "name": "实现 UserService",
      "description": "...",
      "status": "pending",
      "review_status": null,
      "reviewer_notes": [],
      "priority": "high",
      "depends_on": [],
      "assignee": null,
      "created_at": "2026-01-01T00:00:00Z",
      "updated_at": "2026-01-01T00:00:00Z",
      "completed_at": null
    },
    {
      "id": "task-002",
      "name": "实现 ProductService",
      "description": "...",
      "status": "pending",
      "review_status": null,
      "reviewer_notes": [],
      "priority": "high",
      "depends_on": [],
      "assignee": null,
      "created_at": "2026-01-01T00:00:00Z",
      "updated_at": "2026-01-01T00:00:00Z",
      "completed_at": null
    },
    {
      "id": "task-003",
      "name": "实现 API routes",
      "description": "...",
      "status": "pending",
      "review_status": null,
      "reviewer_notes": [],
      "priority": "medium",
      "depends_on": ["task-001", "task-002"],
      "assignee": null,
      "created_at": "2026-01-01T00:00:00Z",
      "updated_at": "2026-01-01T00:00:00Z",
      "completed_at": null
    }
  ]
}
```

**新增字段说明：**

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | `string` | 任务唯一标识（原为数字，改为字符串以支持引用） |
| `review_status` | `null \| "pass" \| "reject"` | reviewer 的审查结论 |
| `reviewer_notes` | `string[]` | 审查问题列表（reject 时必填） |
| `depends_on` | `string[]` | 前置任务 ID 列表，支持 DAG 排序 |
| `assignee` | `string \| null` | 当前执行的 agent 标识 |
| `completed_at` | `string \| null` | 完成时间戳 |

---

## 五、方案三：多模型配置

### 5.1 模型选型依据

| 角色 | 模型 | 选型理由 |
|------|------|----------|
| orchestrator | `zai-coding-plan/glm-5` | 调度逻辑需要 agentic 长上下文理解，GLM-5 在 agentic 任务 SOTA |
| coder | `zai-coding-plan/glm-5` | GLM-5 在代码生成 LMArena Code Top-1，SWE-bench 领先 |
| reviewer | `openrouter/anthropic/claude-sonnet-4.6` | claude-sonnet 在代码审查细节把控上更严格准确 |
| evolver | `zai-coding-plan/glm-5` | 文本理解提取，GLM-5 200K 上下文窗口满足需求 |
| retrieval | `zai-coding-plan/glm-5` | 简单语义检索任务，GLM-5 足够且成本低 |

### 5.2 配置层级

```
优先级（低 → 高）：
  全局默认模型
    ↓
  ~/.config/opencode/opencode.json（全局 agent 配置）
    ↓
  .opencode/opencode.json（项目级覆盖）
    ↓
  agent markdown frontmatter 中的 model 字段（最高优先级，已内置）
```

### 5.3 快速配置

**方式1：使用模板（推荐）**

```bash
cp opencode.json.template ~/.config/opencode/opencode.json
# 编辑文件，填入 API key
```

**方式2：仅依赖 agent frontmatter 默认值**

Agent 文件中已内置模型配置，只需确保 OpenCode 全局配置中有对应 provider 的 API key：

```bash
# 设置环境变量
export OPENROUTER_API_KEY="sk-or-v1-xxxxx"
export ZHIPUAI_API_KEY="xxxxx.xxxxx"

# 或在 ~/.config/opencode/opencode.json 中配置 provider
{
  "provider": {
    "openrouter": { "apiKey": "..." },
    "zhipuai": { "apiKey": "..." }
  }
}
```

详细配置指南见：[docs/MODEL-CONFIG.md](MODEL-CONFIG.md)

---

## 六、需要修改的现有文件

### 6.1 `evolving-agent/SKILL.md` — 更新调度规则

在步骤3（任务分发）中，编程意图的分发改为：

```
编程意图 →
  1. @orchestrator 接管（而非直接调用 programming-assistant）
  2. orchestrator 内部调度 @coder / @reviewer / @evolver
```

### 6.2 `evolving-agent/modules/programming-assistant/workflows/full-mode.md` — 引入审查步骤

在步骤3（编程循环）中，3.4 完成后状态改为 `review_pending`，新增 3.5 等待审查：

```
3.4 编码完成 → status: review_pending（不再直接 completed）
3.5 等待 @reviewer 审查结果
    ├─ pass  → status: completed → 回到 3.1
    └─ reject → 读取 reviewer_notes → 修复 → 回到 3.3
```

### 6.3 `evolving-agent/modules/programming-assistant/workflows/evolution-check.md` — 强制调用

将"激活进化模式条件"中的可选逻辑改为强制：

```
❌ 旧逻辑（可选）：满足条件才激活
✅ 新逻辑（强制）：orchestrator 层级强制调用 @evolver，本文件只负责 evolver 内部逻辑
```

### 6.4 `evolving-agent/modules/programming-assistant/template/feature_list.json` — 升级 Schema

按第四节的新 Schema 更新模板文件。

---

## 七、实施路线图

```
阶段1（高优先级）：完整闭环
  □ 创建 .opencode/agents/reviewer.md
  □ 创建 .opencode/agents/evolver.md
  □ 更新 feature_list.json template（review_status, reviewer_notes, depends_on）
  □ 更新 evolving-agent/SKILL.md（调度规则加入 reviewer/evolver 强制调用）
  □ 更新 full-mode.md（加入 review_pending 状态和等待审查步骤）
  □ 强化 evolution-check.md（改为 orchestrator 强制触发）

阶段2（中优先级）：多模型配置
  □ 创建 .opencode/agents/orchestrator.md（含 GLM-5 model 配置）
  □ 创建 .opencode/agents/coder.md（含 GLM-5 model 配置）
  □ 创建 .opencode/agents/retrieval.md（含 GLM-5 model 配置）
  □ 创建 .opencode/opencode.json（项目级模型配置）

阶段3（低优先级）：并行调度
  □ 在 orchestrator.md 完善 DAG 并行逻辑
  □ 更新 feature_list.json schema（depends_on 字段文档化）
  □ 可选：新增 evolving-agent/scripts/core/dag_scheduler.py 辅助脚本
```

---

## 八、与 kdcokenny/opencode-workspace 的对比

| 特性 | kdcokenny | 本项目 v5.0 |
|------|-----------|------------|
| 知识积累 | ❌ | ✅ 核心差异化 |
| 自我进化 | ❌ | ✅ evolver 强制执行 |
| GitHub 学习 | ❌ | ✅ github-to-skills |
| 审查闭环 | ✅ reviewer agent | ✅ reviewer + 状态机硬约束 |
| 并行调度 | ✅ background-agents 插件 | ✅ 原生 Task tool + DAG |
| 多模型 | ✅ JSON config | ✅ Agent markdown + JSON |
| 权限边界 | ✅ 细粒度 permission | ✅ 复用 OpenCode permission |
| worktree 隔离 | ✅ worktree 插件 | 可选（轻量方案：任务分区） |

---

## 九、核心设计原则

1. **硬约束优于软约束**：状态机转换由 orchestrator 控制，执行者无法跳过 review 和 evolver
2. **角色分离**：coder 不做自审，reviewer 不写代码，evolver 不执行任务，职责边界清晰
3. **并行最大化**：无依赖的任务组在单条消息中同时发出 Task，不串行等待
4. **知识进化是一等公民**：evolver 与 reviewer 同级，由 orchestrator 强制触发，非可选步骤
5. **模型匹配任务**：高精度任务（审查）用 claude-sonnet；高吞吐任务（编码、调度、检索）用 GLM-5
