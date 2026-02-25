# Full Mode - 完整开发

适用于新建项目和功能开发。

> **核心原则**: 通过状态文件跟踪进度，不依赖会话历史，节省 token。

---

## ⚠️ 重要约束

```
❌ 禁止行为:
- 完成编码后自行将任务标记为 completed（必须经过 reviewer）
- 看到 review/文档任务后停止执行
- 完成高优先级任务后等待用户确认
- 中途询问"是否继续"

✅ 正确行为:
- 编码完成后将状态更新为 review_pending，等待 reviewer
- reviewer pass 后才标记为 completed
- 所有任务 completed 后，强制调用 @evolver 提取经验
- 循环执行直到没有 pending 任务
```

---

## 平台差异

| 平台 | 多 Agent 方式 | orchestrator/reviewer/evolver |
|------|--------------|-------------------------------|
| **OpenCode** | 通过 `@orchestrator` 调度，原生 Task tool 并行 | 使用 `evolving-agent/agents/` 中的 agent 文件 |
| **Claude Code** | 通过当前 agent 模拟 orchestrator 逻辑，串行执行 | 通过 `Read` 加载对应 agent 文档中的指令执行 |

---

## 核心流程

```
步骤0: 环境准备（必须执行）
  # 设置路径变量
  SKILLS_DIR=$([ -d ~/.config/opencode/skills/evolving-agent ] && echo ~/.config/opencode/skills || echo ~/.claude/skills)
  
  # 获取项目根目录
  PROJECT_ROOT=$(git rev-parse --show-toplevel 2>/dev/null || pwd)
  
  # 知识检索（与任务初始化并行，不阻塞）
  python $SKILLS_DIR/evolving-agent/scripts/run.py knowledge trigger \
    --input "用户输入描述" --format context > $PROJECT_ROOT/.opencode/.knowledge-context.md &
  读取 $PROJECT_ROOT/.opencode/.knowledge-context.md 获取相关历史经验

步骤1: 状态恢复与任务分析
  使用 `sequential-thinking` 工具进行深度分析
  ├─ 存在 $PROJECT_ROOT/.opencode/feature_list.json → 读取任务列表，恢复上下文
  │   └─ 存在 $PROJECT_ROOT/.opencode/progress.txt → 读取当前进度和"下一步"
  └─ 不存在 → 执行初始化（步骤2）

步骤2: 任务拆解与初始化
  使用 `sequential-thinking` 生成 todos
  ├─ 在项目根目录创建 $PROJECT_ROOT/.opencode/feature_list.json（模板: ../template/feature_list.json）
  ├─ 将 todos 写入 feature_list.json（包含 id、depends_on 字段，支持 DAG 并行）
  └─ 选取第一个 pending 任务，写入 $PROJECT_ROOT/.opencode/progress.txt
  
步骤3: 编程循环 [WHILE 有 pending/rejected 任务]
  3.1 确定当前任务
      ├─ 从 feature_list.json 选择第一个 pending 任务（考虑 depends_on 依赖）
      └─ 或从 progress.txt 的"下一步"继续
  
  3.2 更新状态为 in_progress
      ├─ 修改 feature_list.json 中对应任务的 status → "in_progress"
      └─ 更新 progress.txt 的"当前任务"
  
  3.3 执行开发
      ├─ 读取历史经验（.knowledge-context.md）
      ├─ 如有 reviewer_notes（上次被 reject），优先针对性修复
      ├─ 编写代码
      ├─ 编写单元测试
      └─ 运行测试验证
  
  3.4 编码完成，更新状态为 review_pending（不是 completed）
      ├─ 修改 feature_list.json: status → "review_pending"
      ├─ 更新 progress.txt: 记录"遇到的问题"和"关键决策"
      └─ 不要自我审查，等待 reviewer
  
  3.5 审查门控（硬约束）
      ├─ [OpenCode] 调用 @reviewer 执行代码审查
      ├─ [Claude Code] 加载 $SKILLS_DIR/evolving-agent/agents/reviewer.md 中的指令，
      │               切换角色执行审查，将结论写入 feature_list.json
      │
      ├─ reviewer_status = "pass"  → status → "completed" → 回到 3.1
      └─ reviewer_status = "reject" → status → "rejected"
                                     → 读取 reviewer_notes
                                     → 回到 3.3（携带修改建议）

步骤4: 结果验证（主进程协调点）
  ├─ 确认所有任务状态为 completed（无 pending/rejected/review_pending）
  └─ 输出最终执行摘要

步骤5: 强制知识归纳（不可跳过）
  按照 ./evolution-check.md 执行进化检查
  > ⚠️ 此步骤强制执行，不因任务简单而跳过
```

---

## 任务拆解原则

每个任务必须满足：
- **< 30分钟**可完成
- **可独立测试**验证
- **单一职责**，专注一个问题
- **按依赖顺序**排列（使用 `depends_on` 字段）
- **并行友好**：无依赖关系的任务使用相同空 `depends_on: []`，orchestrator 可并行调度

---

## 错误处理

```
错误发生 → 分析原因 → 尝试方案（最多3次）
├─ 成功 → 继续执行，记录到 progress.txt "遇到的问题"
└─ 连续失败 3 次 → 标记 blocked + 记录详情 + 报告用户
```

---

## 状态文件说明

| 文件 | 用途 | 模板 |
|------|------|------|
| `$PROJECT_ROOT/.opencode/feature_list.json` | 任务清单和状态 | `../template/feature_list.json` |
| `$PROJECT_ROOT/.opencode/progress.txt` | 当前任务进度 | `../template/progress.txt` |
| `$PROJECT_ROOT/.opencode/.knowledge-context.md` | 知识检索结果 | 自动生成 |

> **注意**: `progress.txt` 只保存当前任务详情，历史任务查看 `feature_list.json`
