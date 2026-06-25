# CodeGraph 知识库 v3 设计方案

> 状态：设计完成，分阶段实施中。

---

## 一、痛点 ↔ 根因映射

| 痛点 | 当前根因 | CodeGraph 的解 |
|------|----------|-------------------|
| 检索与任务相关性弱 | 经验条目是扁平 FTS + trigger 打分，**与代码结构无关联**；`codegraph context` 两段检索（graph + KB）各自独立合并 | 统一 `node/edge/entry` 存储；检索时 **1-hop 图扩展** + zero-gate 相关性门控 |
| MD 跨任务 token 膨胀 | `.knowledge-context.md` 是**全文 dump**；无 tier/budget 控制；条目 content 整块注入 | **按需切片**（字段级/摘要级）；KnowledgePlane 按 token 预算 merge；JIT 工具按需拉取 |
| 任务从零开始 | `codegraph scan` 在 SKILL 里写了，但 graph 与经验**未形成项目认知快照**；无架构蒸馏 | 启动即 index + distill；prompt 注入「项目地图」摘要（模块/框架/模式） |

---

## 二、目标架构：统一 CodeGraph v3

核心原则：**一个 SQLite 文件 = 代码图谱 + 经验知识 + 向量索引**，MD 只做 ephemeral 注入层，不做持久存储。

```
┌─────────────────────────────────────────────────────────────────┐
│                     KnowledgePlane (路由层)                      │
│  AdaptiveRouter → 并行 Provider → Merger (token budget)         │
└────────────┬──────────────────────┬─────────────────────────────┘
             │                      │
    ExperienceProvider      GraphProvider
             │                      │
             └──────────┬───────────┘
                        ▼
              knowledge.db (SQLite v3)
         ┌──────────────┼──────────────┐
         │ file         │ node         │ edge
         │ entry        │ entry_embed  │
         │ node_fts     │ entry_fts    │
         └──────────────┴──────────────┘
                        ▲
         scan → extract → resolve → distill
```

### 存储分层（保留现有路径习惯）

| 层 | 路径 | 内容 |
|----|------|------|
| 全局 | `~/.config/opencode/codegraph/knowledge.db` | 种子概念、跨项目经验、通用 pattern |
| 项目 | `$PROJECT/.opencode/codegraph/knowledge.db` | AST 符号、调用/导入边、项目经验、架构推断 |

**废弃**：`graph.json` 作为查询源（保留为 export/debug 快照即可）；`vectors/index.json` 迁入 SQLite `entry_embedding` 表。

---

## 三、数据模型（Schema v3）

在现有 `symbols` + `entries` 基础上，对齐 tiantacode 的 **node/edge 统一图**：

```sql
-- 新增/替换
CREATE TABLE file (
    path TEXT PRIMARY KEY,
    lang TEXT, size INTEGER, mtime REAL,
    hash TEXT, indexed_at TEXT
);

CREATE TABLE node (
    id TEXT PRIMARY KEY,          -- sha1(scope, kind, name, file?, line?)[:16]
    kind TEXT NOT NULL,           -- symbol|module|pattern|framework|architecture|concept|language
    name TEXT NOT NULL,
    file TEXT, line INTEGER, end_line INTEGER,
    signature TEXT, summary TEXT,  -- summary 由 Distiller/LLM 填充
    body TEXT,                    -- 截断 2000 字符
    scope TEXT DEFAULT 'project', -- global|project
    provenance TEXT,              -- parsed|heuristic|distilled|curated|llm|extracted
    meta_json TEXT,
    effectiveness REAL DEFAULT 0.5,
    usage_count INTEGER DEFAULT 0,
    created_at TEXT, updated_at TEXT
);

CREATE TABLE edge (
    src TEXT NOT NULL, dst TEXT NOT NULL, kind TEXT NOT NULL,
    provenance TEXT,
    PRIMARY KEY (src, dst, kind)
);

-- entry 保留，增加图关联
CREATE TABLE entry (
    id TEXT PRIMARY KEY,
    category TEXT NOT NULL,
    name TEXT NOT NULL,
    triggers_json TEXT,
    content_json TEXT NOT NULL,
    scope TEXT DEFAULT 'project',
    -- 新增：与代码图的锚点
    anchor_node_ids_json TEXT,    -- ["sym-abc", "mod-xyz"]
    anchor_files_json TEXT,       -- ["src/auth/user.py"]
    codegraph_type TEXT,
    effectiveness REAL, usage_count INTEGER,
    search_text TEXT,
    created_at TEXT, updated_at TEXT
);

CREATE TABLE entry_embedding (
    entry_id TEXT PRIMARY KEY,
    model TEXT, dim INTEGER,
    vector BLOB                    -- float32 序列化
);

-- FTS5
CREATE VIRTUAL TABLE node_fts USING fts5(...);
CREATE VIRTUAL TABLE entry_fts USING fts5(...);
```

### 节点/边类型（与 tiantacode 对齐）

**Node kinds**

| kind | 来源 | 用途 |
|------|------|------|
| `symbol` | tree-sitter | 函数/类/方法，检索入口 |
| `module` | 每文件一个 | import 边、模块级上下文 |
| `pattern` | Distiller + seeds | Repository、MVC 等架构模式 |
| `framework` | import 分析 + seeds | React、FastAPI 等 |
| `architecture` | seeds + 人工 | 分层架构描述 |
| `concept` | extract 关联 | 业务概念节点 |

**Edge kinds（分阶段实现）**

| 阶段 | kind | 生产者 |
|------|------|--------|
| P0 | `imports`, `calls` | Resolver（启发式） |
| P1 | `uses`, `is-a` | Distiller |
| P2 | `references`, `similar-to` | extract 时 LLM/规则关联经验↔符号 |
| P3 | `extends`, `implements` | tree-sitter 增强 |

**Provenance** 贯穿所有节点/边，便于信任分级和刷新策略。

---

## 四、索引流水线（解决「任务从零开始」）

```
codegraph scan [--full]
    │
    ├─ 1. Extractor   tree-sitter → symbol/module nodes + file 表
    ├─ 2. Resolver    imports 边 + calls 边（token 匹配，上限 5000）
    ├─ 3. Distiller   目录模式 → pattern；import → framework
    ├─ 4. SeedSync    全局 seeds 镜像到项目 store（首次）
    └─ 5. Snapshot    生成 project-map.json（轻量摘要，非查询源）
```

### Distiller 规则（Python 版，参考 tiantacode `Distiller.ts`）

| 信号 | 输出 |
|------|------|
| `services/`, `components/`, `controllers/` 等目录 | `pattern` node + `is-a` 边 |
| `import react`, `from fastapi` 等 | `framework` node + `uses` 边 |
| 入口文件 `main.py`, `index.ts` | `architecture` 摘要节点 |

### 增量更新

- 保留现有 `index-state.json`（mtime + hash）
- 文件变更 → 仅 `deleteNodesByFile` + 重 extract 该文件 → 全量 resolve edges
- 可选：`codegraph watch`（inotify/fsevents，2s debounce）供长期会话

### 任务开始时的「项目认知快照」

scan 完成后自动生成 **Project Map**（~300–500 tokens），写入 context 首部：

```markdown
## 项目地图
- 语言: Python 3.11 | 框架: FastAPI, SQLAlchemy
- 模块: auth(12 sym) | api(8 sym) | models(5 sym)
- 架构模式: Repository Pattern, Layered Architecture
- 热点符号: UserService.authenticate, get_db_session
- 项目经验: 23 条 (problem×8, pattern×5, ...)
```

---

## 五、检索流水线（解决「相关性弱 + token 膨胀」）

### 5.1 KnowledgePlane（`codegraph/plane.py`）

统一入口：

```python
def query(
    input: str,
    project_root: Path,
    *,
    tier: Literal["tiny","small","medium","large"] = "medium",
    budget_tokens: int = 1500,
    sources: list[str] | None = None,  # experience|graph|both
) -> KnowledgeResult:
    ...
```

**AdaptiveRouter 分 tier 策略**（借鉴 tiantacode）：

| tier | 经验条数 | 图节点 | 邻居扩展 | 典型场景 |
|------|---------|--------|---------|---------|
| tiny | 1 | 0 | 0 | 简单 fix |
| small | 2 | 0 | 0 | 单文件修改 |
| medium | 4 | 2 symbol | 1-hop | 常规模块开发 |
| large | 5 | 3 symbol | 1-hop + pattern | 架构级任务 |

### 5.2 三阶段检索（提升相关性）

```
Phase A: Intent Parse
  输入 → 关键词 + 场景(problem/scenario) + 技术栈 + 可能模块名

Phase B: Parallel Retrieve (带 timeout)
  GraphProvider:
    1. node_fts 搜 symbol/module
    2. 命中 symbol → neighbors(calls|imports) 最多 3 个
    3. medium+ → 扩展 pattern/framework 概念节点
  ExperienceProvider:
    1. trigger 精确匹配
    2. entry_fts + entry_embedding hybrid
    3. anchor_node_ids 与 Phase B graph 命中取交集 → 加权

Phase C: Merge + Budget
  KnowledgeMerger:
    - 按 relevance 排序
    - zero-gate: 无 trigger 重叠且 semantic < 0.35 → 丢弃
    - 按 budget_tokens 截断（graph 30–60%，experience 其余）
    - 条目只注入 content 的摘要字段，非全文
```

**相关性公式**（保留现有，增加图锚点）：

```
relevance = trigger·0.30 + effectiveness·0.25 + recency·0.15 + usage·0.10
          + graph_anchor·0.20   # 新增：经验锚定到命中 symbol 则 +0.2
```

### 5.3 上下文输出：结构化 JSON → 预算 MD

```bash
python run.py codegraph context \
  --input "$TASK_DESC" \
  --project "$PROJECT_ROOT" \
  --tier medium \
  --budget 1200 \
  --format context
```

**MD 不再是知识存储，只是 Merger 的输出视图**。每次任务重新生成，不累积历史全文。

### 5.4 JIT 检索工具（Phase 2）

```bash
python run.py knowledge search \
  --kind graph|experience \
  --query "UserService authenticate" \
  --limit 5 \
  --expand-neighbors
```

---

## 六、经验提取与图关联（解决「知识不成体系」）

### 6.1 `codegraph extract` 增强

```
progress.txt + feature_list + git diff
    │
    ├─ 1. SessionParser（regex 保留作 fast path）
    ├─ 2. AnchorResolver
    │      git diff 变更文件 → module nodes
    │      符号名 regex → symbol nodes
    ├─ 3. ScopeClassifier（global vs project，保留）
    ├─ 4. QualityGate（保留 should_extract）
    ├─ 5. store entry + anchor_node_ids + embed
    └─ 6. 可选：创建 concept node + references 边（经验 → 符号）
```

**示例 entry**：

```json
{
  "id": "problem-cors-fix-a1b2",
  "category": "problem",
  "name": "FastAPI CORS 预检失败",
  "content": {
    "symptoms": ["OPTIONS 404"],
    "solution": "CORSMiddleware 需在路由注册前 mount",
    "summary": "CORS 中间件顺序问题"
  },
  "anchor_node_ids": ["mod-main-py", "sym-add_middleware"],
  "anchor_files": ["src/main.py"],
  "triggers": ["CORS", "跨域", "FastAPI", "OPTIONS"]
}
```

### 6.2 全局 KB 也向量化

全局 KB 改为 **entry_embedding 双写**（global + project 各自 HNSW/线性回退）。

### 6.3 生命周期

| 机制 | 规则 |
|------|------|
| usage_count | 每次 retrieve 命中 +1 |
| effectiveness decay | 90 天未用 ×0.95 |
| gc | effectiveness < 0.1 删除 |
| dream/distill | 7 天合并重复经验；30 天 LLM 蒸馏 symbol summary |

---

## 七、与 SKILL 工作流集成

```bash
# 扫描 + 架构推断
python $RUN_PY codegraph scan --project "$PROJECT_ROOT"
python $RUN_PY codegraph distill --project "$PROJECT_ROOT"

# 设计阶段 vs 编码阶段
python $RUN_PY codegraph context --input "..." --tier large --budget 2000 --format context   # 3.1a
python $RUN_PY codegraph context --input "..." --tier medium --budget 1200 --format context  # 3.2

# 归纳
python $RUN_PY codegraph extract --project "$PROJECT_ROOT"
```

| 阶段 | tier | budget | 侧重 |
|------|------|--------|------|
| 3.1a 设计 | large | 2000 | 全局经验 + 架构 pattern + 模块概览 |
| 3.2 编码 | medium | 1200 | 命中 symbol + 邻居 + 锚定经验 |

---

## 八、迁移路径（v2 → v3）

| 步骤 | 动作 | 风险 |
|------|------|------|
| M1 | `db.py` 增 node/edge/file 表；migration v2→v3 | 低 |
| M2 | `indexer.py` 写 node 表，停止写 symbols 表；graph.json 改 export-only | 中 |
| M3 | 新增 `resolver.py`, `distiller.py`, `seeds.py` | 低 |
| M4 | 新增 `plane.py`, `merger.py`, `providers/` | 中 |
| M5 | `extractor.py` 增 anchor 解析；向量迁入 SQLite | 中 |
| M6 | 全局 KB 向量索引；废弃 `vectors/index.json` | 低 |
| M7 | 更新 SKILL.md / codegraph.md 文档 | 低 |

**兼容**：v3 migration 读取旧 `symbols` → 导入 `node(kind=symbol)`；旧 `entries` → `entry`。

---

## 九、实施分期

### Phase 0（1–2 天）：止血
- [x] KnowledgeMerger token budget
- [x] `format_for_context` 只输出 summary 字段
- [x] `context.py` 检索诊断 meta 文件

### Phase 1（3–5 天）：统一图存储
- [x] Schema v3 + migration
- [x] Extractor/Resolver 写 node/edge
- [x] scan 后输出 Project Map

### Phase 2（3–5 天）：KnowledgePlane
- [x] AdaptiveRouter + GraphProvider + ExperienceProvider
- [ ] 图锚点加权 + 1-hop 扩展（extract anchor 待 Phase 3）
- [x] tier/budget CLI 参数
- [x] knowledge 命令向后兼容 + 全场景测试 (`tests/test_knowledge_commands_compat.py`)

### Phase 3（2–3 天）：Extract 增强
- [ ] git diff → anchor 关联
- [ ] 全局向量索引
- [ ] `knowledge search` JIT 命令

### Phase 4（可选）：Distiller + Dream
- [ ] 架构 pattern 推断
- [ ] 周期性经验合并 / symbol LLM 摘要

---

## 十、与 CodeGraph 的差异（有意保留）

| 维度 | CodeGraph | evolving-agent 适配 |
|------|---------------|---------------------|
| 运行时 | VS Code 扩展 | Python CLI + Cursor Task 调度 |
| 注入方式 | system prompt eager + tool | `.design-context.md` / `.knowledge-context.md` + 可选 CLI tool |
| 向量 | HNSW (hnswlib-node) | Python: hnswlib 或 numpy 线性回退 |
| LLM distill | medium/large tier 可选 | extract 阶段可选 `--llm` |
| Memory | FileSystemMemoryStore 独立 | 不引入，统一进 entry 表 |

---

## 参考

- CodeGraph: `docs/SOLUTION.md` §6, `services/knowledge-store/`, `services/knowledge-graph/`
- 本项目现状: `evolving-agent/references/codegraph.md`, `evolving-agent/scripts/codegraph/`
