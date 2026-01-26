# Evolution Check - 进化检查

**必须**在每个开发/修复循环结束后执行。

## ⚠️ 重要：长会话需要先压缩

对于复杂任务（多轮会话、大量步骤），在归纳经验前**必须先使用 `/compact` 压缩会话历史**：

```
1. 检测会话长度 > 50轮 → 先执行 /compact
2. 压缩后的摘要会保留关键信息
3. 再基于压缩后的内容进行知识归纳
```

**原因**: 直接归纳长会话会耗费大量时间和 token。

## 执行时机

- Full Mode: 开发循环完成后
- Simple Mode: 修复循环完成后
- 会话结束前

## 检查流程

```
步骤1: 检测会话复杂度
    ├─ 会话轮数 > 50 或 任务数量 > 10 → 需要压缩
    └─ 简单会话 → 直接归纳

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
    基于压缩后的内容（或原始内容）进行知识提取和存储
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

# progress.txt 已经包含结构化的"遇到的问题"和"关键决策"

# 方式1: 提取"遇到的问题"部分
if [ -f progress.txt ]; then
  sed -n '/## 遇到的问题/,/## /p' progress.txt | \
    python $SKILLS_DIR/evolving-agent/scripts/run.py knowledge summarize --auto-store
fi

# 方式2: 提取"关键决策"部分
if [ -f progress.txt ]; then
  sed -n '/## 关键决策/,/## /p' progress.txt | \
    python $SKILLS_DIR/evolving-agent/scripts/run.py knowledge summarize --auto-store
fi

# 方式3: 提取所有问题和决策（推荐）
if [ -f progress.txt ]; then
  {
    echo "## 经验总结"
    sed -n '/## 遇到的问题/,/^$/p' progress.txt
    sed -n '/## 关键决策/,/^$/p' progress.txt
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
1. **从 progress.txt 提取**（最佳，已经是结构化经验）
2. 手动总结关键点（适合简单任务）
3. 使用 `/compact` 后的摘要（适合超长会话）

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

### 示例1: 从 progress.txt 提取（推荐）

假设 `progress.txt` 内容：
```
# Progress Log - 登录功能

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

执行归纳：
```bash
# 提取问题和决策部分
{
  sed -n '/## 遇到的问题/,/^$/p' progress.txt
  sed -n '/## 关键决策/,/^$/p' progress.txt
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
用户: 实现完整的用户认证系统（涉及50+步骤）

进化检查:
1. 任务数量 > 10 → 需要优化
2. 检查 progress.txt 是否完整记录了关键问题
3. 如果 progress.txt 记录完整 → 直接提取
4. 如果 progress.txt 不完整 → 执行 /compact，然后手动总结
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

- **长会话优化**: 超过50轮的会话先执行 `/compact` 压缩，节省时间和 token
- **提取来源**: 可以从 `progress.txt` 的"遇到的问题"和"关键决策"部分提取经验
- **异步执行**: 对于非关键的知识归纳，可使用 Task 工具异步执行
- **静默模式**: 只在存储成功后简短通知，不阻塞主流程
- **去重机制**: 知识库会自动去重相似条目
