# Evolution Check - 进化检查

**必须**在每个开发/修复循环结束后执行。

## ⚠️ 重要：长会话需要先压缩

对于复杂任务（多轮会话、大量步骤），在归纳经验前**必须先使用 `/compact` 压缩会话历史**：

**触发条件**：
- `.opencode/feature_list.json` 中任务数 > 10，或
- 会话轮数 > 50

**压缩流程**：
```
1. 检测任务数或会话轮数 → 触发压缩
2. 执行 /compact 压缩会话历史（保留关键信息）
3. 基于压缩后的内容 + .opencode/progress.txt 归纳经验
```

**重要**: `.opencode/progress.txt` 只保存当前任务的详细情况，不包含历史任务信息。对于多任务项目，需要结合会话历史（压缩后）进行经验提取。

## 执行时机

- Full Mode: 开发循环完成后
- Simple Mode: 修复循环完成后
- 会话结束前

## 检查流程

```
步骤1: 检测任务复杂度
    读取 .opencode/feature_list.json 检查任务数
    ├─ 任务数 > 10 或 会话轮数 > 50 → 需要压缩
    └─ 简单任务 → 直接归纳

步骤2: 会话压缩（如需要）
    执行 /compact 命令压缩会话历史
    保留关键决策、问题解决方案、技术栈选择等

步骤3: 检查进化模式
    检查 .opencode/.evolution_mode_active
        ├─ 存在 → 进化模式激活 → 主动提取
        └─ 不存在 → 被动检查
                    ├─ 复杂问题(尝试>1次) → 提取
                    ├─ 用户说"记住" → 提取
                    └─ 否则 → 正常结束

步骤4: 知识归纳
    基于以下内容提取经验：
    - 压缩后的会话历史（或完整历史，如果未压缩）
    - .opencode/progress.txt 的"遇到的问题"和"关键决策"
    注意：不要只依赖 progress.txt，因为它只包含当前任务信息
```

## 触发条件

| 场景 | 触发 |
|------|------|
| 修复失败2次后成功 | 是 |
| 用户说"记住这个" | 是 |
| 发现更优方案 | 是 |
| 特定环境 workaround | 是 |
| 简单修改一行代码 | 否 |
| 用户说"很好"、"ok" | 否 |

## 执行命令

```bash
# 设置路径变量
SKILLS_DIR=$([ -d ~/.config/opencode/skills/evolving-agent ] && echo ~/.config/opencode/skills || echo ~/.claude/skills)

# 检查任务复杂度
TASK_COUNT=0
if [ -f .opencode/feature_list.json ]; then
  TASK_COUNT=$(jq '.features | length' .opencode/feature_list.json 2>/dev/null || echo 0)
fi

# 判断是否需要压缩（任务数 > 10 或会话轮数 > 50）
# 注意：会话轮数需要根据实际情况判断，这里先检查任务数
if [ "$TASK_COUNT" -gt 10 ]; then
  echo "检测到任务数 > 10，建议先执行 /compact 压缩会话历史，然后再归纳总结"
  # 用户需要手动执行 /compact
fi

# 方式1: 提取 progress.txt 的问题和决策（适用于简单任务）
if [ -f .opencode/progress.txt ]; then
  {
    echo "## 经验总结"
    sed -n '/## 遇到的问题/,/^$/p' .opencode/progress.txt
    sed -n '/## 关键决策/,/^$/p' .opencode/progress.txt
  } | python $SKILLS_DIR/evolving-agent/scripts/run.py knowledge summarize --auto-store
fi

# ===== 其他方式 =====

# 方式4: 检查进化模式状态
python $SKILLS_DIR/evolving-agent/scripts/run.py mode --status

# 方式5: 手动输入关键经验
echo "问题：跨域报错 → 解决：Vite配置proxy" | \
  python $SKILLS_DIR/evolving-agent/scripts/run.py knowledge summarize --auto-store

# 方式6: 快速存储偏好
python $SKILLS_DIR/evolving-agent/scripts/run.py project store --preference "使用pnpm"
```

**推荐顺序**:
1. **检查任务复杂度**（任务数 > 10 或会话轮数 > 50）
2. **如需要，先执行 `/compact`**（压缩会话历史，保留关键信息）
3. **结合多种来源提取经验**：
   - 压缩后的会话历史（包含所有任务的上下文）
   - `.opencode/progress.txt` 的"遇到的问题"和"关键决策"（仅当前任务）
4. **简单任务直接从 progress.txt 提取**

## 快速存储

```bash
# 存储偏好
python $SKILLS_DIR/evolving-agent/scripts/run.py project store --preference "内容"

# 存储修复方案
python $SKILLS_DIR/evolving-agent/scripts/run.py project store --fix "方案描述"

# 存储技术栈模式
python $SKILLS_DIR/evolving-agent/scripts/run.py project store --tech react --pattern "模式内容"
```

## 示例

### 示例1: 简单任务（从 progress.txt 提取）

假设 `.opencode/progress.txt` 内容：
```
# Progress Log - 登录功能

## 当前任务
- [ ] 添加 JWT 中间件

## 本次完成
- [x] 实现密码哈希
- [x] 创建登录 API

## 下一步
1. 添加 JWT 中间件

## 遇到的问题
- bcrypt 编译报错 → 使用 @node-rs/bcrypt 替代
- JWT 过期时间设置 → 采用 7天 + refresh token 方案

## 关键决策
- 选择 bcrypt 而非 argon2，因为 bcrypt 更成熟
- JWT secret 存储在环境变量，不提交到 git
```

任务数少（< 10），直接提取：
```bash
{
  sed -n '/## 遇到的问题/,/^$/p' .opencode/progress.txt
  sed -n '/## 关键决策/,/^$/p' .opencode/progress.txt
} | python $SKILLS_DIR/evolving-agent/scripts/run.py knowledge summarize --auto-store
```

结果：自动存储2条经验到知识库
- `problem`: bcrypt 编译报错使用 @node-rs/bcrypt
- `experience`: JWT secret 安全存储最佳实践

---

### 示例2: 简单修复（手动总结）
```
用户: 修复跨域问题
尝试1: 修改 headers - 失败
尝试2: 配置 proxy - 成功

进化检查（手动总结）:
echo "问题：Vite项目跨域报错 → 解决：配置 server.proxy" | \
  python $SKILLS_DIR/evolving-agent/scripts/run.py knowledge summarize --auto-store
```

---

### 示例3: 复杂任务（先压缩）
```
用户: 实现完整的用户认证系统

检查 .opencode/feature_list.json：
{
  "features": [ /* 15个任务 */ ]
}

进化检查:
1. 任务数 = 15 > 10 → 需要压缩
2. 执行 /compact 压缩会话历史（保留关键决策和问题）
3. 基于压缩后的摘要 + .opencode/progress.txt 归纳总结
4. 注意：不要只读 progress.txt，因为它只包含当前任务信息

手动总结示例：
echo "经验总结：
- 问题1：bcrypt 编译报错 → 使用 @node-rs/bcrypt
- 问题2：JWT 中间件顺序 → 需要在路由之前注册
- 决策1：选择 bcrypt，因为更成熟
- 决策2：JWT 过期时间 7天 + refresh token
" | python $SKILLS_DIR/evolving-agent/scripts/run.py knowledge summarize --auto-store
```

---

### 示例4: 快速存储偏好
```
用户: 记住以后都用 pnpm

进化检查（直接存储）:
echo "以后Node.js项目都使用pnpm install" | \
  python $SKILLS_DIR/evolving-agent/scripts/run.py knowledge summarize --auto-store
```

## 注意事项

- **复杂度检测**: 
  - 任务数 > 10：检查 `.opencode/feature_list.json` 中的 `features` 数组长度
  - 会话轮数 > 50：根据实际会话交互次数判断
- **压缩时机**: 满足任一条件即需先执行 `/compact`，然后再归纳总结
- **提取来源**: 
  - 简单任务（任务数 ≤ 10）：从 `.opencode/progress.txt` 提取
  - 复杂任务（任务数 > 10）：结合压缩后的会话历史 + `.opencode/progress.txt`
  - **重要**：不要只读 `progress.txt`，它只保存当前任务信息
- **异步执行**: 对于非关键的知识归纳，可使用 Task 工具异步执行
- **静默模式**: 只在存储成功后简短通知，不阻塞主流程
- **去重机制**: 知识库会自动去重相似条目
