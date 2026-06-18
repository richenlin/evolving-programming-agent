# Knowledge Base

知识存储、查询、归纳系统。

## 知识分类

| 分类 | 说明 | 触发场景 |
|------|------|----------|
| experience | 经验条目 | 优化、重构、最佳实践 |
| tech-stack | 技术栈 | 框架相关 |
| scenario | 场景 | 创建、实现功能 |
| problem | 问题 | 修复、调试、报错 |
| testing | 测试 | 测试相关 |
| pattern | 模式 | 架构、设计模式 |
| skill | 技能 | 通用技巧 |

> 所有分类均存储在 CodeGraph SQLite（`knowledge.db`），不再使用 JSON 文件目录。

## 核心命令

```bash
# 设置路径变量（优先使用项目本地脚本）
PROJECT_ROOT=$(git rev-parse --show-toplevel 2>/dev/null || pwd)
if [ -f "$PROJECT_ROOT/.opencode/scripts/run.py" ]; then RUN_PY="$PROJECT_ROOT/.opencode/scripts/run.py"; elif [ -d ~/.config/opencode/skills/evolving-agent ]; then RUN_PY=~/.config/opencode/skills/evolving-agent/scripts/run.py; elif [ -d ~/.hermes/skills/evolving-agent ]; then RUN_PY=~/.hermes/skills/evolving-agent/scripts/run.py; elif [ -d ~/.agents/skills/evolving-agent ]; then RUN_PY=~/.agents/skills/evolving-agent/scripts/run.py; else RUN_PY=~/.claude/skills/evolving-agent/scripts/run.py; fi

# 查询
python $RUN_PY knowledge query --stats           # 统计
python $RUN_PY knowledge query --trigger "react,hooks"  # 按触发词
python $RUN_PY knowledge query --category problem       # 按分类
python $RUN_PY knowledge query --search "跨域"          # 全文搜索

# 触发检测
python $RUN_PY knowledge trigger --input "修复CORS问题"
python $RUN_PY knowledge trigger --input "..." --project .

# 归纳存储
echo "内容" | python $RUN_PY knowledge summarize --auto-store

# 存储
python $RUN_PY knowledge store --category experience --name "xxx"
```

## 工作流程

> **CodeGraph 集成**：推荐使用 `codegraph scan`（编程开始）+ `codegraph context`（任务开始）+ `codegraph extract`（编程完成）。详见 `references/codegraph.md`。

### 检索流程（任务开始时）

推荐：CodeGraph 合并上下文（项目结构 + 向量经验 + 知识库）：

```bash
python $RUN_PY codegraph context \
  --input "..." --project "$PROJECT_ROOT" --format context \
  > "$PROJECT_ROOT/.opencode/.knowledge-context.md"
```

备选：仅知识库检索：

```bash
python $RUN_PY knowledge trigger \
  --input "..." --format context --mode hybrid \
  --merge "$PROJECT_ROOT/.opencode/.knowledge-context.md" \
  > "$PROJECT_ROOT/.opencode/.knowledge-context.md"
```

> `--merge` 保留文件中的"项目经验"部分，全局知识库检索结果每次刷新。

### 归纳流程（任务结束后）

进化模式激活时，执行统一提取：

```bash
python $RUN_PY codegraph extract --project "$PROJECT_ROOT"
# 或: python $RUN_PY evolve --project "$PROJECT_ROOT"
```

检查 `.opencode/.evolution_mode_active`，存在则执行上述命令。

1. **全局知识库**（跨项目复用）：
```bash
echo "问题：xxx → 解决：yyy" | python $RUN_PY knowledge summarize --auto-store
```

2. **项目知识上下文**（项目专属，追加）：
```bash
echo -e "\n### $(date +%Y-%m-%d) 问题：xxx → 解决：yyy" >> "$PROJECT_ROOT/.opencode/.knowledge-context.md"
```

## 知识条目 Schema（全局知识库）

```json
{
  "id": "category-name-hash",
  "category": "experience|tech-stack|scenario|problem|testing|pattern|skill",
  "name": "名称",
  "triggers": ["触发词"],
  "content": {},
  "sources": ["来源"],
  "created_at": "ISO-8601",
  "effectiveness": 0.5
}
```

## 数据位置

| 类型 | 路径 | 说明 |
|------|------|------|
| 全局知识库 | `~/.config/opencode/codegraph/knowledge.db` | SQLite + FTS5，跨平台跨项目共享 |
| 项目知识库 | `$PROJECT_ROOT/.opencode/codegraph/knowledge.db` | 项目级 SQLite 条目 |
| 项目知识上下文 | `$PROJECT_ROOT/.opencode/.knowledge-context.md` | Markdown，项目专属，跨会话持久化 |

> 导入/导出使用 JSON **bundle**（`knowledge export` / `import`），不是 per-file JSON KB。

### .knowledge-context.md 文件格式

```markdown
## 相关知识（每次检索刷新）
### [problem] CORS跨域问题
**解决方案**: ...

## 可能相关（每次检索刷新）
### [experience] React性能优化
**最佳实践**: ...

## 项目经验（跨会话持久化）
### 2026-03-13 问题：MinIO签名过期 → 解决：设置 presigned URL 有效期为 7 天
### 2026-03-12 决策：选择 Gin 而非 Echo → 原因：团队更熟悉 Gin 中间件体系
```

## 知识进化

| 命令 | 用途 |
|------|------|
| `codegraph extract` | 统一经验归纳（脚本） |
| `evolve` | 同上，别名 |

> 知识检索与归纳均为 orchestrator 直接执行的 CodeGraph 脚本。
