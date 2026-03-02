# Simple Mode - 快速修复

适用于问题修复、代码重构、代码审查。

> **核心原则**: 通过状态文件跟踪进度，不依赖会话历史，节省 token。

---

> 公共步骤（环境准备、审查门控、结果验证、知识归纳、错误处理）见 [_base.md](./_base.md)。本文件只记录 simple-mode 特有逻辑。

---

## ⚠️ 重要约束

```
❌ 禁止行为:
- 完成修复后自行将任务标记为 completed（必须经过 reviewer）
- 中途询问"是否继续"
- 完成主要修复后忽略后续验证步骤
- 评审后用户要求修复时，跳过本流程直接改代码

✅ 正确行为:
- 修复完成后将状态更新为 review_pending，等待 reviewer
- reviewer pass 后才标记为 completed
- 完成所有修复和验证后强制执行知识归纳
- 评审后用户要求修复时，从已生成的 feature_list.json 恢复状态，走完整修复循环
```

---

## 平台差异

| 平台 | 多 Agent 方式 | reviewer/evolver |
|------|--------------|-----------------|
| **OpenCode** | 通过 `@reviewer` 独立 agent 审查 | 使用 `evolving-agent/agents/` 中的 agent 文件 |
| **Claude Code** | Task tool spawn reviewer subagent（独立上下文） | Task tool spawn 对应 agent subagent |

---

## 核心流程

```
步骤0: 环境准备（必须执行）
  # 设置路径变量
  SKILLS_DIR=$([ -d ~/.config/opencode/skills/evolving-agent ] && echo ~/.config/opencode/skills || echo ~/.claude/skills)
  
  # 获取项目根目录
  PROJECT_ROOT=$(git rev-parse --show-toplevel 2>/dev/null || pwd)
  
  # 知识检索
  python $SKILLS_DIR/evolving-agent/scripts/run.py knowledge trigger \
    --input "用户问题描述" --format context > $PROJECT_ROOT/.opencode/.knowledge-context.md
  读取 $PROJECT_ROOT/.opencode/.knowledge-context.md 获取相关历史经验
  > 利用历史经验，快速定位类似问题

步骤1: 状态恢复与问题分析
  使用 `sequential-thinking` 工具进行深度分析
  ├─ 存在 $PROJECT_ROOT/.opencode/feature_list.json → 读取任务列表，恢复上下文
  │   └─ 存在 $PROJECT_ROOT/.opencode/progress.txt → 读取当前进度和"下一步"
  │   └─ 如有 pending 任务 → 跳到步骤4（修复循环）
  └─ 不存在 → 判断场景类型（步骤1.5）
  
步骤1.5: 场景分支
  ├─ 修复/重构场景（用户描述了具体问题） → 步骤2（问题理解）
  └─ 评审场景（用户要求 review/评审代码）  → 步骤A（评审流程）

步骤A: 评审流程（触发词: review、评审、审查）
  A.1 分析代码，输出评审报告
  A.2 将评审发现的问题写入 feature_list.json（status=pending）
      ├─ 每个问题对应一个 task，包含 id、name、description、severity
      ├─ status 统一设为 "pending"
      └─ 写入 progress.txt，记录"评审已完成，待用户确认修复"
  A.3 向用户输出评审报告
      > 评审报告末尾附带提示: "问题已写入 feature_list.json，
      > 如需修复请告知，将自动进入修复流程"
  A.4 结束（等待用户下一步指令）
      > 用户说"修复" → 步骤1 读取 feature_list.json → 步骤4 修复循环

步骤2: 问题理解（修复前必须）
  ├─ 复现问题 - 确认能稳定复现
  ├─ 分析根因 - 定位问题源头
  └─ 制定方案 - 选择最小化修改

步骤3: 任务拆解与初始化
  使用 `sequential-thinking` 生成 todos
  ├─ 在项目根目录创建 $PROJECT_ROOT/.opencode/feature_list.json（模板: ../template/feature_list.json）
  ├─ 将 todos 写入 feature_list.json（包含 id、depends_on 字段）
  └─ 选取第一个 pending 任务，写入 $PROJECT_ROOT/.opencode/progress.txt

步骤4: 修复循环 [WHILE 有 pending/rejected 任务]
  4.1 确定当前任务
      ├─ 从 progress.txt 的"下一步"继续
      └─ 或从 feature_list.json 选择第一个 pending 任务
  
  4.2 更新状态为 in_progress
      ├─ 更新 progress.txt 的"当前任务"
      └─ python $SKILLS_DIR/evolving-agent/scripts/run.py task transition \
             --task-id $TASK_ID --status in_progress
  
  4.3 执行修复
      ├─ 如有 reviewer_notes（上次被 reject），优先针对性修复
      ├─ 最小化修改代码
      ├─ 运行测试验证
      └─ 确认无回归
  
  4.4 修复完成，更新状态为 review_pending（不是 completed）
      ├─ python $SKILLS_DIR/evolving-agent/scripts/run.py task transition \
      │       --task-id $TASK_ID --status review_pending
      ├─ 更新 progress.txt: 记录"问题根因"和"关键发现"
      └─ 不要自我审查，等待 reviewer
  
  4.5 审查门控（硬约束）
      ├─ [OpenCode] 调用 @reviewer 执行代码审查
      ├─ [Claude Code] Task tool spawn reviewer subagent
      │               （加载 $SKILLS_DIR/evolving-agent/agents/reviewer.md 作为 prompt，独立上下文）
      │
      ├─ reviewer_status = "pass"  → status → "completed" → git commit → 回到 4.1
      └─ reviewer_status = "reject" → status → "rejected"
                                     → 读取 reviewer_notes
                                     → 回到 4.3（携带修改建议）

步骤5: 结果验证（主进程协调点）
  ├─ 确认所有修复任务状态为 completed
  ├─ 运行完整测试确认无回归
  └─ 输出修复摘要

步骤6: 强制知识归纳（不可跳过）
  按照 ./evolution-check.md 执行进化检查
  > ⚠️ 此步骤强制执行，不因修复简单而跳过
```

---

## 何时创建 feature_list.json

| 场景 | 是否创建 |
|------|----------|
| 涉及多个文件 | ✅ |
| 修复范围较大 | ✅ |
| 根因不明确需多步排查 | ✅ |
| 预计需要多个会话完成 | ✅ |
| 单文件简单修复 | ❌ |

---

## 任务拆解原则

```
❌ 模糊: "修复登录失败"

✅ 清晰:
  task-001: 复现问题 - 记录错误日志和请求参数 (depends_on: [])
  task-002: 检查前端请求 - 确认请求格式正确 (depends_on: ["task-001"])
  task-003: 检查后端响应 - 查看具体错误信息 (depends_on: ["task-001"])
  task-004: 定位失败点 - 确定是哪个环节出错 (depends_on: ["task-002", "task-003"])
  task-005: 修复代码 - 最小化改动 (depends_on: ["task-004"])
  task-006: 验证修复 - 确认问题解决且无回归 (depends_on: ["task-005"])
```

---

## 验证方法

| 类型 | 方法 | 时机 |
|------|------|------|
| 编译 | 运行构建命令 | 每次修改后 |
| 单测 | 运行相关测试 | 修复完成后 |
| 功能 | curl/手动测试 | 验证修复 |
| 回归 | 运行完整测试 | 最终验证 |

---

> 错误处理、状态文件说明、平台差异见 [_base.md](./_base.md)。
