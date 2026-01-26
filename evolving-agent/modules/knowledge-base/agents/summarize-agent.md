# Knowledge Summarize Agent

异步分析会话提取知识，不阻塞主任务。

## ⚠️ 重要：长会话需要先压缩

对于复杂任务（多轮会话、大量步骤），在归纳经验前**建议先使用 `/compact` 压缩会话**：
- 会话轮数 > 50 → 建议压缩
- 任务数量 > 10 → 建议压缩
- 压缩后归纳更快，token 消耗更少

## 输入

- `session_content`: 会话内容
- `session_id`: 会话标识符

## 执行

### 推荐：从 progress.txt 提取

`progress.txt` 已经包含结构化的经验，直接提取最高效：

```bash
SKILLS_DIR=$([ -d ~/.config/opencode/skills/evolving-agent ] && echo ~/.config/opencode/skills || echo ~/.claude/skills)

# 方式1: 提取问题部分（最简单，推荐）
if [ -f progress.txt ]; then
  sed -n '/## 遇到的问题/,/^$/p' progress.txt | \
    python $SKILLS_DIR/evolving-agent/scripts/run.py knowledge summarize --auto-store
fi

# 方式2: 同时提取问题和决策
if [ -f progress.txt ]; then
  grep -A 20 "## 遇到的问题\|## 关键决策" progress.txt | \
    python $SKILLS_DIR/evolving-agent/scripts/run.py knowledge summarize --auto-store
fi

# 方式3: 只提取特定问题（最精准）
if [ -f progress.txt ]; then
  echo "bcrypt 编译失败 → 改用 @node-rs/bcrypt" | \
    python $SKILLS_DIR/evolving-agent/scripts/run.py knowledge summarize --auto-store
fi
```

**progress.txt 示例格式**：
```
## 遇到的问题
- bcrypt 编译失败 → 改用 @node-rs/bcrypt
- CORS 跨域报错 → Vite配置 server.proxy

## 关键决策
- JWT secret 存储在环境变量
- 使用 httpOnly cookie 提高安全性
```

### 其他方式

```bash
# 方式4: 从压缩后的摘要归纳
echo "{/compact 后的摘要}" | \
  python $SKILLS_DIR/evolving-agent/scripts/run.py knowledge summarize --auto-store

# 方式5: 手动输入关键经验
echo "问题：跨域报错 → 解决：Vite配置proxy" | \
  python $SKILLS_DIR/evolving-agent/scripts/run.py knowledge summarize --auto-store

# 方式6: 从文件读取
cat experience.txt | \
  python $SKILLS_DIR/evolving-agent/scripts/run.py knowledge summarize --auto-store --session-id "session-123"
```

**建议优先级**:
1. 从 `progress.txt` 提取（已经是结构化的经验）
2. 使用 `/compact` 后的摘要
3. 手动总结关键点

## 知识类型映射

| 内容 | 分类 |
|------|------|
| 问题-解决方案 | problem |
| 最佳实践 | experience |
| 注意事项/坑 | experience |
| 技术模式 | pattern/tech-stack |

## 输出

写入 `.knowledge-summary.md`:

```markdown
## 提取的知识
| 分类 | 名称 | ID |
|------|------|-----|
| problem | CORS问题 | problem-cors-xxx |

## 统计
- 提取条目: 3
- 已存储: 3
```

## 调用方式

```python
Task(
  subagent_type="general",
  description="Knowledge summarization",
  prompt="分析会话并归纳知识"
)
```

## 触发时机

1. **自动**: 进化模式激活时
2. **手动**: 用户说"记住"、"/evolve"

## 约束

- 异步执行
- 不询问用户
- 自动去重
