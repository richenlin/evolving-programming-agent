# Simple Mode - 快速修复

适用于问题修复、代码重构、代码审查。

> **核心原则**: 通过状态文件跟踪进度，不依赖会话历史，节省 token。

## ⚠️ 重要约束：禁止中途停止

```
❌ 禁止行为:
- 完成一个修复后输出"总结报告"然后停止
- 中途询问"是否继续"
- 完成主要修复后忽略后续验证步骤

✅ 正确行为:
- 完成修复后，检查 .opencode/feature_list.json（如有）是否还有 pending 任务
- 如有 pending 任务，继续执行下一个
- 完成所有修复和验证
```

## 强制操作：会话开始

**每次会话必须先执行**：

```
步骤1: 检查状态文件
  cat .opencode/progress.txt        # 读取当前任务进度和下一步
  cat .opencode/feature_list.json   # 如果存在，读取任务列表

步骤2: 确定当前任务
  ├─ 从 .opencode/progress.txt "下一步" 继续
  └─ 或根据用户描述创建新任务

步骤3: 更新状态
  # 更新 .opencode/progress.txt 的"当前任务"
  # 如有 .opencode/feature_list.json，更新对应任务为 in_progress
```

## 强制操作：修复完成后

**每次修复完成必须执行**：

```
步骤1: 更新 .opencode/progress.txt
  - 将修复内容移到"本次完成"
  - 清空"当前任务"（如果还有pending任务），写入新的"当前任务"
  - 写入具体的"下一步"（如有后续工作）
  - 记录问题根因和解决方案
  - 记录关键发现

步骤2: 更新 .opencode/feature_list.json（如存在）
  将 status 改为 "completed"

步骤3: git commit
```

## 状态文件模板

### progress.txt（必须创建/更新）

```
# Progress Log - 修复记录
# 最后更新: 2024-01-01 10:00

## 当前任务
- [ ] 修复登录接口 500 错误

## 本次完成
- [x] 定位问题：数据库连接池耗尽
- [x] 修复：增加连接池大小 10 → 50
- [x] 验证：登录接口恢复正常

## 下一步（如有后续）
1. 添加连接池监控日志
2. 设置连接池告警阈值

## 问题根因
- 现象：登录接口随机 500 错误
- 根因：高并发下数据库连接池耗尽
- 方案：增加连接池大小，添加重试机制

## 关键发现
- 连接泄漏来自未关闭的事务
- 需要添加 finally 块确保连接释放
```

### feature_list.json（复杂修复时创建）

```json
{
  "project": "登录问题修复",
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-01T00:00:00Z",
  "features": [
    {
      "id": 1,
      "name": "复现问题",
      "status": "completed",
      "notes": "使用 ab -n 1000 -c 100 复现"
    },
    {
      "id": 2,
      "name": "定位根因",
      "status": "completed",
      "notes": "连接池耗尽"
    },
    {
      "id": 3,
      "name": "修复代码",
      "status": "completed",
      "notes": "增加连接池大小"
    },
    {
      "id": 4,
      "name": "添加监控",
      "status": "pending",
      "notes": ""
    }
  ]
}
```

## 何时创建 feature_list.json

- 涉及多个文件
- 修复范围较大
- 根因不明确需要多步排查
- 预计需要多个会话完成

## 修复循环（必须循环执行直到所有任务完成）

```
WHILE 存在未完成的修复任务:
    1. 确定当前修复任务
    2. 理解问题 → 复现 → 分析根因
    3. 最小化修改
    4. 验证修复
    5. 更新 .opencode/progress.txt（记录完成、问题、决策）
    6. 更新 .opencode/feature_list.json（如有，状态改为 completed）
    7. git commit
    8. 检查是否还有 pending 任务 → 如有，继续循环

END WHILE → 所有修复完成 → 执行进化检查
```

**关键**: 不要在循环中途停止！完成所有修复任务后才能结束。

## 任务拆解示例

```
❌ "修复登录失败"
✓ 1. 复现问题 - 记录错误日志和请求参数
  2. 检查前端请求 - 确认请求格式正确
  3. 检查后端响应 - 查看具体错误信息
  4. 定位失败点 - 确定是哪个环节出错
  5. 修复代码 - 最小化改动
  6. 验证修复 - 确认问题解决且无回归
```

## 验证方法

| 类型 | 方法 |
|------|------|
| 编译 | 运行构建 |
| 单测 | 运行测试 |
| 功能 | curl/手动 |
| 回归 | 确认无破坏 |

## 错误处理

1. 分析失败原因
2. 尝试不同方案（最多3次）
3. 连续失败: 回退 + **记录到 .opencode/progress.txt** + 报告用户

## 强制操作：进化检查（循环结束后必须执行）

> **重要**: 每个修复循环结束后，必须执行进化检查以提取经验和积累知识。

```
步骤1: 加载进化检查流程
  @load workflows/evolution-check.md

步骤2: 检查进化模式状态
  SKILLS_DIR=$([ -d ~/.config/opencode/skills/evolving-agent ] && echo ~/.config/opencode/skills || echo ~/.claude/skills)
  python $SKILLS_DIR/evolving-agent/scripts/run.py mode --status

步骤3: 判断是否需要提取经验
  ├─ 进化模式激活 → 主动提取
  ├─ 遇到复杂问题(尝试>1次) → 提取
  ├─ 发现问题根因有价值 → 提取
  ├─ 用户说"记住" → 提取
  └─ 简单修改 → 跳过

步骤4: 执行知识归纳（如需要）
  echo "{问题根因 + 解决方案}" | python $SKILLS_DIR/evolving-agent/scripts/run.py knowledge summarize --auto-store
```

**必须提取的场景**:
- 修复失败2次后成功
- 发现隐蔽的 bug 根因
- 环境特定的 workaround
- 用户明确要求记住
