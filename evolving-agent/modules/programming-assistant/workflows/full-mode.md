# Full Mode — 完整开发

适用于新建项目和功能开发。自包含——按本文件从头执行到尾。

---

## Checklist

进入本模式时创建 TodoWrite：

```
- [ ] 知识检索
- [ ] 需求分析（sequential-thinking）
- [ ] 任务拆解（feature_list.json + DAG）
- [ ] 编码循环（每个任务一轮）
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
    --input "用户输入描述" --format context
  读取输出，获取相关历史经验

步骤 2: 状态恢复 + 需求分析
  使用 sequential-thinking 深度分析
  ├─ 存在 $PROJECT_ROOT/.opencode/feature_list.json
  │   → 读取任务列表恢复上下文
  │   → 如有 pending 任务 → 跳到步骤 4
  └─ 不存在 → 步骤 3

步骤 3: 任务拆解
  使用 sequential-thinking 生成 todos
  ├─ 创建 $PROJECT_ROOT/.opencode/feature_list.json（模板: ../template/feature_list.json）
  ├─ 写入任务（含 id、depends_on，支持 DAG 并行）
  └─ 选取第一个 pending 任务，写入 progress.txt

  拆解原则：
  - < 30 分钟可完成
  - 可独立测试验证
  - 单一职责
  - 无依赖关系的任务使用 depends_on: []，可并行

步骤 4: 编码循环 [WHILE 有 pending/rejected 任务]
  4.1 确定当前任务（考虑 depends_on 依赖）
  4.2 更新状态为 in_progress
      python $SKILLS_DIR/evolving-agent/scripts/run.py task transition \
        --task-id $TASK_ID --status in_progress
  4.3 执行开发
      ├─ 读取历史经验
      ├─ 如有 reviewer_notes（上次被 reject），针对性修复
      ├─ 编写代码 + 单元测试
      └─ 运行测试验证
  4.4 编码完成，更新状态为 review_pending（不是 completed）
      python $SKILLS_DIR/evolving-agent/scripts/run.py task transition \
        --task-id $TASK_ID --status review_pending
      更新 progress.txt: 记录"遇到的问题"和"关键决策"

步骤 5: 审查
  调用 reviewer 执行代码审查（平台差异见 references/platform.md）
  ├─ pass  → status: completed → 回到 4.1 处理下一个任务
  └─ reject → status: rejected → 读取 reviewer_notes → 回到 4.3

步骤 6: 结果验证
  ├─ 确认所有任务状态为 completed（无 pending/rejected/review_pending）
  └─ 输出执行摘要

步骤 7: 知识归纳
  按照 ./evolution-check.md 执行
  检查进化模式标记（.opencode/.evolution_mode_active）
  ├─ 激活 → 提取经验存入知识库
  └─ 未激活 → 跳过
```

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
