# Simple Mode — 快速修复

适用于 bug 修复、代码重构、代码评审。自包含——按本文件从头执行到尾。

---

## Checklist

进入本模式时创建 TodoWrite：

```
- [ ] 知识检索
- [ ] 问题分析（sequential-thinking）
- [ ] 编码修复 + 测试
- [ ] 审查（reviewer）
- [ ] 结果验证
- [ ] 知识归纳（evolution-check）
```

完成每步后立即标记 completed。

---

## 流程

```
步骤 1: 环境准备 + 知识检索
  SKILLS_DIR=$([ -d ~/.config/opencode/skills/evolving-agent ] && echo ~/.config/opencode/skills || echo ~/.claude/skills)
  PROJECT_ROOT=$(git rev-parse --show-toplevel 2>/dev/null || pwd)

  python $SKILLS_DIR/evolving-agent/scripts/run.py knowledge trigger \
    --input "用户问题描述" --format context
  读取输出，获取相关历史经验

步骤 2: 状态恢复 + 问题分析
  使用 sequential-thinking 深度分析
  ├─ 存在 $PROJECT_ROOT/.opencode/feature_list.json
  │   → 读取任务列表恢复上下文
  │   → 如有 pending 任务 → 跳到步骤 4
  └─ 不存在 → 判断场景：
      ├─ 修复/重构 → 步骤 3
      └─ 评审 → 步骤 A

步骤 A: 评审流程（仅评审场景）
  A.1 分析代码，输出评审报告
  A.2 将发现的问题写入 feature_list.json（status=pending）
  A.3 向用户输出评审报告
  A.4 结束，等待用户指令
      > 用户说"修复" → 步骤 2 读取 feature_list.json → 步骤 4

步骤 3: 问题理解 + 任务拆解
  ├─ 分析根因，定位问题源头
  ├─ 制定方案，选择最小化修改
  └─ 如需拆分多任务 → 写入 feature_list.json（含 id、depends_on）
     单文件简单修复不需要 feature_list.json

步骤 4: 修复循环 [WHILE 有 pending/rejected 任务]
  4.1 确定当前任务
  4.2 更新状态为 in_progress
      python $SKILLS_DIR/evolving-agent/scripts/run.py task transition \
        --task-id $TASK_ID --status in_progress
  4.3 执行修复
      ├─ 如有 reviewer_notes（上次被 reject），针对性修复
      ├─ 最小化修改代码
      └─ 运行测试验证
  4.4 修复完成，更新状态为 review_pending（不是 completed）
      python $SKILLS_DIR/evolving-agent/scripts/run.py task transition \
        --task-id $TASK_ID --status review_pending
      更新 progress.txt: 记录"问题根因"和"关键发现"

步骤 5: 审查
  调用 reviewer 执行代码审查（平台差异见 references/platform.md）
  ├─ pass  → status: completed → 回到 4.1 处理下一个任务
  └─ reject → status: rejected → 读取 reviewer_notes → 回到 4.3

步骤 6: 结果验证
  ├─ 确认所有任务状态为 completed
  └─ 运行完整测试确认无回归

步骤 7: 知识归纳
  按照 ./evolution-check.md 执行
  检查进化模式标记（.opencode/.evolution_mode_active）
  ├─ 激活 → 提取经验存入知识库
  └─ 未激活 → 跳过
```

---

## 何时创建 feature_list.json

| 场景 | 创建 |
|------|------|
| 涉及多个文件 | 是 |
| 根因不明确需多步排查 | 是 |
| 预计需要多个会话 | 是 |
| 单文件简单修复 | 否 |

---

## 状态文件

| 文件 | 用途 |
|------|------|
| `$PROJECT_ROOT/.opencode/feature_list.json` | 任务清单和状态（CLI 管理） |
| `$PROJECT_ROOT/.opencode/progress.txt` | 当前任务进度（手动维护） |

> `.opencode` 必须在项目根目录（git 仓库根），不是当前工作目录。

---

## 错误处理

```
错误发生 → 分析原因 → 尝试方案（最多 3 次）
├─ 成功 → 继续，记录到 progress.txt
└─ 连续失败 3 次 → 标记 blocked + 报告用户
    python $SKILLS_DIR/evolving-agent/scripts/run.py task transition \
      --task-id $TASK_ID --status blocked
```
