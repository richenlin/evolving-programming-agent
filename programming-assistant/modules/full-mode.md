# 完整模式 (Full Mode)

适用于新建项目和功能开发场景。

## 状态文件

| 文件 | 用途 |
|------|------|
| `SOLUTION.md` | 架构设计、技术选型 |
| `TASK.md` | 任务拆解、实现步骤 |
| `feature_list.json` | 功能状态跟踪 |
| `progress.txt` | 会话进度日志 |

## 工作流程

### 1. 状态检查（每次会话必须首先执行）

**目的**: 了解上一步完成情况和遗留问题

```
检查 progress.txt 和 feature_list.json 是否存在
    ├─ 存在 → 执行状态检查
    └─ 不存在 → 进入初始化流程
```

**检查内容**:
```bash
# 读取进度日志 - 了解上次完成了什么、遗留什么问题
cat progress.txt

# 读取功能列表 - 了解哪些功能待开发、哪些进行中
cat feature_list.json
```

**检查后行动**:
- 从 `progress.txt` 的"下一步"继续
- 优先处理"遇到的问题"中的遗留项
- 选择 `feature_list.json` 中优先级最高的 `pending` 任务

### 2. 初始化（新项目首次）

```
分析需求 → 生成 SOLUTION.md
         → 生成 TASK.md
         → 创建 feature_list.json + progress.txt
         → 目录结构 + git init + 首次 commit
```

### 3. 开发循环

```
状态检查 → 选择任务(优先级最高的pending)
         → 实现功能(参考TASK.md)
         → 验证测试(失败则修复，3次失败则回退)
         → 状态更新
         → git commit
         → 继续下一任务或结束
```

### 4. 状态更新（每个步骤完成后必须执行）

**目的**: 给下一步做指引

**progress.txt 更新内容**:
```
## 本次完成
- [x] 具体完成的任务描述

## 当前状态
- 项目整体进度
- 已完成的功能列表

## 下一步
- 下个会话应该做什么（具体、可执行）
- 优先级最高的待办事项

## 遇到的问题
- 问题描述 + 临时方案或待解决标记
```

**feature_list.json 更新内容**:
- 完成的功能: `status` → `"completed"`, 填写 `completed_at`
- 进行中的功能: `status` → `"in_progress"`
- 被阻塞的功能: `status` → `"blocked"`, 在 `notes` 说明原因

## feature_list.json 格式

```json
{
  "project": "项目名称",
  "features": [
    {"id": "F001", "name": "功能名", "priority": 1, "status": "pending", "completed_at": null, "notes": ""}
  ]
}
```

## 代码实现规范

**实现前**: 阅读现有代码，确认技术方案
**实现中**: 遵循现有风格，一次只改一个功能点
**实现后**: 运行测试验证，检查回归

## 错误处理

1. 分析失败原因
2. 尝试不同方案（最多3次）
3. 连续失败：回退 + 记录到 progress.txt + 报告用户
