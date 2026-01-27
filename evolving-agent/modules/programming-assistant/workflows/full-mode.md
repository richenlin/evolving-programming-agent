# Full Mode - 完整开发

适用于新建项目和功能开发。

> **核心原则**: 通过状态文件跟踪进度，不依赖会话历史，节省 token。

## ⚠️ 重要约束：禁止中途停止

```
❌ 禁止行为:
- 完成一个任务后输出"总结报告"然后停止
- 看到 review 文档后停止执行
- 完成高优先级任务后等待用户确认
- 中途询问"是否继续"

✅ 正确行为:
- 完成一个任务后，立即检查 .opencode/feature_list.json 是否还有 pending 任务
- 如有 pending 任务，继续执行下一个
- 只有当所有任务状态都是 completed 时，才输出最终总结
- 循环执行直到 .opencode/feature_list.json 中没有 pending 任务
```

## 强制操作：会话开始

**每次会话必须先执行以下步骤**：

```
步骤1: 检查状态文件
  cat .opencode/feature_list.json   # 读取任务列表
  cat .opencode/progress.txt        # 读取当前任务进度和下一步

步骤2: 确定当前任务
  ├─ 从 .opencode/progress.txt "下一步" 继续
  └─ 或从 .opencode/feature_list.json 选择第一个 pending 任务

步骤3: 更新状态为 in_progress
  # 修改 .opencode/feature_list.json 中对应任务的 status
  # 更新 .opencode/progress.txt 的"当前任务"
```

## 强制操作：任务完成后

**每个任务完成必须执行**：

```
步骤1: 更新 .opencode/feature_list.json
  将 status 从 "in_progress" 改为 "completed"
  更新 updated_at 时间戳

步骤2: 更新 .opencode/progress.txt
  - 将任务移到"本次完成"
  - 清空"当前任务"（如果还有pending任务），写入新的"当前任务"
  - 写入具体的"下一步"
  - 记录遇到的问题和解决方案
  - 记录关键决策

步骤3: git commit
```

## 状态文件模板

### feature_list.json（必须创建）

```json
{
  "project": "项目名称",
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-01T00:00:00Z",
  "features": [
    {
      "id": 1,
      "name": "创建 User 模型",
      "status": "completed",
      "notes": "使用 Prisma ORM"
    },
    {
      "id": 2,
      "name": "实现密码哈希",
      "status": "in_progress",
      "notes": ""
    },
    {
      "id": 3,
      "name": "创建注册 API",
      "status": "pending",
      "dependencies": [1, 2],
      "notes": ""
    }
  ]
}
```

### progress.txt（必须创建）

```
# Progress Log - 项目名称
# 最后更新: 2024-01-01 10:00

## 当前任务
- [ ] 实现密码哈希 (feature_list.json #2)

## 本次完成
- [x] 创建 User 模型 - 使用 Prisma，包含 id/email/password/createdAt 字段

## 下一步（具体可执行）
1. 安装 bcrypt 依赖: npm install bcrypt @types/bcrypt
2. 创建 src/utils/password.ts
3. 实现 hashPassword() 和 verifyPassword() 函数
4. 编写单元测试

## 遇到的问题
- Prisma 初始化报错 → 需要先运行 npx prisma generate

## 关键决策
- 选择 bcrypt 而非 argon2，因为 bcrypt 更成熟且无需 native 编译
```

## 初始化流程（新项目）

```
1. 分析需求 (sequential-thinking)
2. 创建 SOLUTION.md (架构设计)
3. 创建 TASK.md (实现计划)
4. 创建 .opencode/ 目录（如不存在）
5. 创建 .opencode/feature_list.json (任务列表，所有状态为 pending)
6. 创建 .opencode/progress.txt (初始进度，写入第一个"下一步")
7. git init && git add . && git commit -m "Initial setup"
```

## 开发循环（必须循环执行直到所有任务完成）

```
WHILE .opencode/feature_list.json 中存在 status="pending" 的任务:
    1. 选择下一个 pending 任务（按优先级/依赖顺序）
    2. 更新 .opencode/feature_list.json 状态为 in_progress
    3. 更新 .opencode/progress.txt 当前任务
    4. 实现任务
    5. 验证测试
    6. 更新 .opencode/feature_list.json 状态为 completed
    7. 更新 .opencode/progress.txt（移到本次完成，记录问题和决策）
    8. git commit
    9. 检查是否还有 pending 任务 → 如有，继续循环

END WHILE → 所有任务完成 → 执行进化检查 → 输出最终总结
```

**关键**: 不要在循环中途停止！只有当所有任务都 completed 后才能结束。

## 任务拆解原则

**示例**:
```
❌ "实现用户认证系统"
✓ 1. 创建 User 模型
  2. 实现密码哈希
  3. 创建注册 API
  4. 创建登录 API
  5. 实现 JWT 生成
  6. 添加认证中间件
```

每个任务:
- < 30分钟可完成
- 可独立测试验证
- 按依赖顺序排列

## 错误处理

1. 分析失败原因
2. 尝试不同方案（最多3次）
3. 连续失败: 回退 + **记录到 .opencode/progress.txt** + 报告用户

## 强制操作：进化检查（循环结束后必须执行）

> **重要**: 每个开发循环结束后，必须执行进化检查以提取经验和积累知识。

```
步骤1: 加载进化检查流程
  @load workflows/evolution-check.md

步骤2: 检查进化模式状态
  SKILLS_DIR=$([ -d ~/.config/opencode/skills/evolving-agent ] && echo ~/.config/opencode/skills || echo ~/.claude/skills)
  python $SKILLS_DIR/evolving-agent/scripts/run.py mode --status

步骤3: 判断是否需要提取经验
  ├─ 进化模式激活 → 主动提取
  ├─ 遇到复杂问题(尝试>1次) → 提取
  ├─ 发现更优方案 → 提取
  ├─ 用户说"记住" → 提取
  └─ 简单修改 → 跳过

步骤4: 执行知识归纳（如需要）
  echo "{问题描述 + 解决方案}" | python $SKILLS_DIR/evolving-agent/scripts/run.py knowledge summarize --auto-store
```

**必须提取的场景**:
- 修复失败2次后成功
- 发现环境特定的 workaround
- 总结出可复用的模式
- 用户明确要求记住
