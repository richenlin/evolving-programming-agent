# CodeGraph

项目代码图谱 + **统一知识归纳**（`codegraph extract` 脚本）。

## 知识归纳

| 能力 | 实现 |
|------|------|
| 读 progress / feature_list / git diff | `extractor._build_session_context()` |
| 全局 vs 项目 KB 路由 | `classify_scope()` |
| 质量过滤 | `should_extract()` |
| FTS5 + 向量持久化 | `db.py` + `embedder.py` |

进化模式激活时 orchestrator 直接运行：

```bash
python $RUN_PY codegraph extract --project "$PROJECT_ROOT"
# 别名: python $RUN_PY evolve --project "$PROJECT_ROOT"
```

## 存储结构

```
$PROJECT_ROOT/.opencode/codegraph/
├── graph.json          # 项目代码图谱（文件、符号、依赖、调用边）
├── knowledge.db        # SQLite + FTS5（符号索引 + 经验全文检索）
├── index-state.json    # 增量扫描状态（mtime + hash）
└── vectors/
    └── index.json      # 经验向量索引（语义检索）

~/.config/opencode/codegraph/
└── knowledge.db        # 全局经验 FTS5 索引
```

知识条目**仅**存于上述 SQLite；旧版 JSON 目录（`~/.config/opencode/knowledge/`、`$PROJECT/.opencode/knowledge/`）已移除，无迁移兼容层。

## 索引层

| 层 | 技术 | 用途 |
|----|------|------|
| AST 扫描 | tree-sitter（可选）→ regex 回退 | 符号、import、call 边 |
| 符号检索 | SQLite FTS5 `symbols_fts` | 任务开始时匹配代码结构 |
| 经验检索 | FTS5 `entries_fts` + 向量 cosine | 混合关键词 + 语义 |

## 生命周期

| 阶段 | 命令 | 说明 |
|------|------|------|
| 编程开始 | `codegraph scan` | 扫描项目代码，生成/更新 graph.json |
| 任务开始 | `codegraph context` | 合并 CodeGraph + 知识库，输出 `.knowledge-context.md` |
| 编程完成 | `codegraph extract` | 自动提取会话经验，嵌入向量并持久化 |

## 命令

```bash
RUN_PY="$PROJECT_ROOT/.opencode/scripts/run.py"

# 扫描项目（增量，默认）
python $RUN_PY codegraph scan --project "$PROJECT_ROOT"

# 全量重扫
python $RUN_PY codegraph scan --project "$PROJECT_ROOT" --full

# 任务上下文（CodeGraph + 知识库）
python $RUN_PY codegraph context \
  --input "修复 CORS 跨域问题" --project "$PROJECT_ROOT" --format context

# 仅 CodeGraph 查询
python $RUN_PY codegraph query --input "User 模型" --project "$PROJECT_ROOT" --format context

# 会话结束后自动提取
python $RUN_PY codegraph extract --project "$PROJECT_ROOT"
```

可选依赖（`requirements-optional.txt`）：

```bash
pip install -r requirements-optional.txt
```

| 包 | 作用 |
|----|------|
| jieba | 中文分词（知识检索） |
| sentence-transformers | 本地 BGE 向量（默认 `BAAI/bge-small-zh-v1.5`） |
| tree-sitter + 语言包 | AST 精确符号提取 |

`install.sh` 会自动安装可选依赖，并写入 `~/.config/opencode/evolving-agent.env`。

无 tree-sitter 时自动降级为 regex；SQLite FTS5 使用 Python 内置 sqlite3，零额外依赖。

向量后端优先级（自动选择）：

1. OpenAI 兼容 API — 设置 `OPENAI_API_KEY`（或 `CODEGRAPH_EMBED_API_KEY`）时优先
2. 本地 sentence-transformers — 默认 `BAAI/bge-small-zh-v1.5`（install 后生效）
3. hash-trick 回退 — 无 ST 时使用，语义匹配较弱

| 变量 | 说明 |
|------|------|
| `CODEGRAPH_EMBED_MODEL` | OpenAI embedding 模型名 |
| `CODEGRAPH_EMBED_BASE_URL` | OpenAI 兼容 API 地址 |
| `CODEGRAPH_LOCAL_EMBED_MODEL` | 本地 ST 模型（默认 `BAAI/bge-small-zh-v1.5`） |

## extract() 输入来源

- `.opencode/progress.txt` — 问题、决策、完成项
- `.opencode/feature_list.json` — 任务意图、reviewer_notes
- `git diff` — 最终代码变更

输出：结构化知识条目 + 向量索引，供下次 `codegraph context` 检索。
