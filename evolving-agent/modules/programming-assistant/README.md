# Programming Assistant

代码生成与问题修复的执行引擎。

## 核心原则

### 1. 状态文件驱动

> 通过 `feature_list.json` 和 `progress.txt` 跟踪任务状态，**不依赖会话历史**。
> 每次会话开始时读取这两个文件恢复上下文，每次任务完成后更新，节省 token。

### 2. ⚠️ 禁止中途停止（重要）

```
❌ 禁止行为:
- 完成一个任务后输出"总结报告"然后停止
- 看到 review/文档任务后停止
- 完成高优先级任务后等待用户确认
- 中途询问"是否继续"

✅ 正确行为:
- 完成任务后，立即检查 feature_list.json 是否还有 pending 任务
- 如有 pending 任务，继续执行下一个
- 循环执行直到所有任务 completed
```

## 状态文件（强制）

| 文件 | 用途 | 操作时机 |
|------|------|----------|
| `feature_list.json` | 任务清单和状态 | **会话开始读取，任务完成更新** |
| `progress.txt` | 进度日志和下一步 | **会话开始读取，每步更新** |
| `SOLUTION.md` | 架构设计 | Full Mode 初始化 |
| `TASK.md` | 实现计划 | Full Mode 初始化 |

### feature_list.json 模板（强制格式）

```json
{
  "project": "项目名称",
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-01T00:00:00Z",
  "features": [
    {
      "id": 1,
      "name": "任务名称",
      "description": "详细描述",
      "status": "pending|in_progress|completed|blocked",
      "priority": 1,
      "dependencies": [],
      "notes": ""
    }
  ]
}
```

### progress.txt 模板（强制格式）

```
# Progress Log - 项目名称
# 最后更新: 2024-01-01 10:00

## 当前任务
- [ ] 正在进行的任务描述

## 本次完成
- [x] 已完成任务1
- [x] 已完成任务2

## 下一步（具体可执行）
1. 下一个任务的具体步骤
2. 预期输出

## 遇到的问题
- 问题描述 → 解决方案

## 关键决策
- 决策点: 选择A而非B，因为...
```

## 强制工作流

### 1. 会话开始（必须执行）

```
步骤0: 知识检索（第一步，必须执行）
  SKILLS_DIR=$([ -d ~/.config/opencode/skills/evolving-agent ] && echo ~/.config/opencode/skills || echo ~/.claude/skills)
  python $SKILLS_DIR/evolving-agent/scripts/run.py knowledge trigger \
    --input "用户输入描述" --format context > .knowledge-context.md
  读取 .knowledge-context.md 获取相关历史经验

步骤1: 读取状态文件
  ├─ 存在 feature_list.json → 读取任务列表
  ├─ 存在 progress.txt → 读取进度和下一步
  └─ 不存在 → 执行初始化流程

步骤2: 确定当前任务
  ├─ 从 progress.txt 的"下一步"继续
  └─ 或从 feature_list.json 选择第一个 pending 任务
```

**重要**: 步骤0的知识检索可以帮助利用历史经验，避免重复劳动。

### 2. 任务执行前（必须执行）

```bash
# 更新 feature_list.json: 将当前任务状态改为 in_progress
# 更新 progress.txt: 记录"当前任务"
```

### 3. 任务完成后（必须执行）

```bash
# 更新 feature_list.json: 将任务状态改为 completed
# 更新 progress.txt: 
#   - 移动到"本次完成"
#   - 写入"下一步"
#   - 记录遇到的问题和决策
```

## 模式选择

| 场景 | 关键词 | 模式 | 加载 |
|------|--------|------|------|
| 新建/功能 | 创建、实现、添加、开发 | Full Mode | `@load workflows/full-mode.md` |
| 修复/重构 | 修复、fix、bug、重构、优化、review | Simple Mode | `@load workflows/simple-mode.md` |
| 咨询 | 怎么、为什么、解释 | Direct Answer | 直接回答 |

## 核心流程

```
会话开始 → 读取状态文件 → WHILE 有 pending 任务:
    确定任务 → 更新(in_progress) → 执行 → 更新(completed) → 检查剩余任务
→ 所有任务完成 → 进化检查
```

**注意**: 这是一个循环，不是单次执行！必须完成所有 pending 任务。

## 任务拆解原则

**必须**先用 `sequential-thinking` 分析，再写入 `feature_list.json`。

每个任务：
- 非常小（< 30分钟）
- 可测试验证
- 专注单一问题
- 按依赖顺序排列

## 执行规范

1. **状态优先**: 先读状态文件，再开始工作
2. **理解优先**: 先读代码，再修改
3. **最小改动**: 选择破坏性最小的方案
4. **状态透明**: 每步完成后立即更新状态文件
5. **经验积累**: 循环结束后执行进化检查

## 强制操作：进化检查（循环结束后必须执行）

> **重要**: 每个编程循环结束后，必须调用进化检查以提取经验和积累知识。

```
步骤1: 加载进化检查流程
  @load workflows/evolution-check.md

步骤2: 检查进化模式状态
  python $SKILLS_DIR/evolving-agent/scripts/run.py mode --status

步骤3: 判断是否需要提取经验
  ├─ 进化模式激活 → 主动提取
  ├─ 遇到复杂问题(尝试>1次) → 提取
  ├─ 发现更优方案 → 提取
  ├─ 用户说"记住" → 提取
  └─ 简单修改 → 跳过

步骤4: 执行知识归纳（如需要）
  echo "{经验内容}" | python $SKILLS_DIR/evolving-agent/scripts/run.py knowledge summarize --auto-store
```

**必须提取的场景**:
| 场景 | 提取 |
|------|------|
| 修复失败2次后成功 | ✅ |
| 发现隐蔽的 bug 根因 | ✅ |
| 环境特定的 workaround | ✅ |
| 总结出可复用模式 | ✅ |
| 用户说"记住这个" | ✅ |
| 简单修改一行代码 | ❌ |

## 常用命令

```bash
# 设置路径变量
SKILLS_DIR=$([ -d ~/.config/opencode/skills/evolving-agent ] && echo ~/.config/opencode/skills || echo ~/.claude/skills)

python $SKILLS_DIR/evolving-agent/scripts/run.py project detect .      # 检测技术栈
python $SKILLS_DIR/evolving-agent/scripts/run.py knowledge trigger --input "..." # 检索知识
python $SKILLS_DIR/evolving-agent/scripts/run.py mode --status         # 进化模式状态
```
