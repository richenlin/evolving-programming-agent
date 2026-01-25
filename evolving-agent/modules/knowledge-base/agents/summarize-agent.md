# Knowledge Summarize Agent

异步分析会话提取知识，不阻塞主任务。

## 输入

- `session_content`: 会话内容
- `session_id`: 会话标识符

## 执行

```bash
cat {session_file} | python scripts/run.py knowledge summarize \
  --auto-store \
  --session-id "{session_id}"
```

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
