# Full Mode - 完整开发

适用于新建项目和功能开发。

## 状态文件

| 文件 | 用途 |
|------|------|
| `SOLUTION.md` | 架构设计、技术选型 |
| `TASK.md` | 任务拆解、实现步骤 |
| `feature_list.json` | 功能状态跟踪 |
| `progress.txt` | 会话进度日志 |

## 工作流程

### 1. 任务拆解（新任务必须）

```
用户需求 → sequential-thinking 分析 → 拆解为原子任务 → 写入 feature_list.json
```

**拆解原则**:
- 每个任务 < 30分钟
- 可测试验证
- 按依赖顺序排列

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

### 2. 状态检查（每次会话必须）

```bash
cat progress.txt        # 了解上次进度
cat feature_list.json   # 查看待办任务
```

**检查后行动**:
- 从"下一步"继续
- 选择第一个 `pending` 任务

### 3. 初始化（新项目首次）

```
分析需求 → SOLUTION.md → TASK.md → feature_list.json → progress.txt → git init
```

### 4. 开发循环

```
选择任务 → 实现 → 验证测试 → 状态更新 → git commit → 进化检查
```

### 5. 状态更新（每步必须）

**progress.txt**:
```
## 本次完成
- [x] 具体任务

## 下一步
- 下个任务（具体可执行）

## 遇到的问题
- 问题 + 方案
```

**feature_list.json**:
- 完成: `status → "completed"`
- 进行中: `status → "in_progress"`

## 错误处理

1. 分析失败原因
2. 尝试不同方案（最多3次）
3. 连续失败: 回退 + 记录 + 报告用户

## 进化检查（循环结束后必须）

`@load workflows/evolution-check.md`
