# 实现文档：轻量级语义搜索替代 sentence-transformers

## 1. 背景与目标

### 1.1 问题

当前 `embedding.py` 使用 `sentence-transformers`（依赖 PyTorch ~2GB + transformers + numpy）提供语义搜索。对于一个 AI Coding Agent 的 skill 来说，这个依赖过于沉重。

### 1.2 目标

用零依赖的 BM25 算法替代 sentence-transformers 作为默认语义搜索实现：

- **零新增依赖**：仅使用 Python 标准库 + 项目已有的可选依赖 jieba
- **API 兼容**：对外接口签名不变，调用方（`query.py`、`trigger.py`、`run.py`、`retrieval.md`）无需修改
- **质量提升**：BM25 比当前 keyword fallback（纯词频 + match_score 计数）有显著提升
- **彻底移除 sentence-transformers**：从 `requirements-optional.txt` 和 `install.sh` 中删除

### 1.3 不做什么

- 不实现 ONNX Runtime 可选升级路径（未来可加，本次不做）
- 不修改 `query.py` 中 keyword 四级检索逻辑（`query_by_triggers` 等）
- 不修改知识库存储格式

---

## 2. 改动范围

| 文件 | 操作 | 说明 |
|------|------|------|
| `evolving-agent/scripts/knowledge/embedding.py` | **重写** | 删除 sentence-transformers 代码，实现 BM25 搜索引擎 |
| `evolving-agent/scripts/knowledge/query.py` | **小改** | `query_semantic()` 适配新模块；`SYNONYM_MAP` 扩展 |
| `tests/test_knowledge_embedding.py` | **重写** | 适配新接口，所有测试无需 skip |
| `requirements-optional.txt` | **修改** | 移除 sentence-transformers 行 |
| `scripts/install.sh` | **修改** | 移除 `--optional full` 相关的 sentence-transformers 提示 |
| `README.md` | **小改** | 更新可选依赖说明 |
| `docs/SOLUTION.md` | **小改** | 更新四级检索描述 |

---

## 3. 详细实现规格

### 3.1 重写 `embedding.py` — BM25 搜索引擎

**文件**：`evolving-agent/scripts/knowledge/embedding.py`

**完整重写**，删除所有 sentence-transformers / numpy 代码，替换为纯 Python BM25 实现。

#### 3.1.1 模块级常量与导入

```python
#!/usr/bin/env python3
"""
Lightweight Semantic Search via BM25.

Provides BM25-based search for the knowledge base.
Zero external dependencies — uses only Python stdlib + optional jieba.
"""

import json
import math
import re
from pathlib import Path
from typing import Any, Dict, List, Tuple

# 复用 query.py 已有的分词器和同义词扩展
try:
    from query import tokenize, expand_with_synonyms
except ImportError:
    # Fallback：如果直接运行本模块（不通过 query.py）
    # 提供最小化的 tokenize 实现
    def tokenize(text: str) -> List[str]:
        return re.findall(r'[\u4e00-\u9fff]+|[a-zA-Z0-9]+', text.lower())
    def expand_with_synonyms(tokens, max_expansions=3):
        return tokens

try:
    from core.config import CATEGORY_DIRS
except ImportError:
    CATEGORY_DIRS = {
        'experience': 'experiences', 'tech-stack': 'tech-stacks',
        'scenario': 'scenarios', 'problem': 'problems',
        'testing': 'testing', 'pattern': 'patterns', 'skill': 'skills',
    }

# BM25 参数
BM25_K1 = 1.5   # 词频饱和参数
BM25_B = 0.75   # 文档长度归一化参数

# 向后兼容标志：始终为 True（BM25 无需外部依赖）
HAS_EMBEDDING = True
```

**要点**：
- `HAS_EMBEDDING = True` 始终为真（BM25 是纯 Python），保持向后兼容
- 从 `query.py` 导入 `tokenize` 和 `expand_with_synonyms`，避免重复代码
- 提供 fallback 版本以防直接运行本模块

#### 3.1.2 `_entry_to_text()` — 保持不变

```python
def _entry_to_text(entry: Dict[str, Any]) -> str:
    """Convert a knowledge entry to a searchable text representation."""
    parts = []
    if entry.get('name'):
        parts.append(entry['name'])
    content = entry.get('content', {})
    if isinstance(content, dict):
        desc = content.get('description', '')
        if desc:
            parts.append(desc)
    triggers = entry.get('triggers', [])
    if triggers:
        parts.append(' '.join(triggers))
    return ' '.join(parts)
```

此函数逻辑不变，与原版完全一致。

#### 3.1.3 `BM25Index` 类

```python
class BM25Index:
    """
    Pure-Python BM25 index for small document collections.

    Designed for knowledge bases with <10,000 entries.
    Supports Chinese + English mixed tokenization via query.tokenize().
    """

    def __init__(self, documents: List[str], doc_ids: List[str]):
        """
        Build index from documents.

        Args:
            documents: List of document text strings
            doc_ids: Parallel list of document IDs
        """
        self.doc_ids = doc_ids
        self.doc_count = len(documents)
        self.avgdl = 0.0
        self.doc_lens: List[int] = []
        self.doc_freqs: List[Dict[str, int]] = []  # per-doc term frequencies
        self.idf: Dict[str, float] = {}             # inverse document frequency
        self._build(documents)

    def _build(self, documents: List[str]) -> None:
        df: Dict[str, int] = {}  # document frequency: how many docs contain term
        total_len = 0

        for doc_text in documents:
            tokens = tokenize(doc_text)
            self.doc_lens.append(len(tokens))
            total_len += len(tokens)

            # Term frequency for this document
            tf: Dict[str, int] = {}
            seen_terms: set = set()
            for token in tokens:
                t = token.lower()
                tf[t] = tf.get(t, 0) + 1
                seen_terms.add(t)
            self.doc_freqs.append(tf)

            # Update document frequency
            for term in seen_terms:
                df[term] = df.get(term, 0) + 1

        self.avgdl = total_len / max(self.doc_count, 1)

        # IDF with smoothing: log((N - df + 0.5) / (df + 0.5) + 1)
        for term, freq in df.items():
            self.idf[term] = math.log(
                (self.doc_count - freq + 0.5) / (freq + 0.5) + 1.0
            )

    def score(self, query_tokens: List[str]) -> List[float]:
        """
        Compute BM25 scores for all documents against query tokens.

        Args:
            query_tokens: Tokenized and synonym-expanded query

        Returns:
            List of float scores, parallel to self.doc_ids
        """
        scores = [0.0] * self.doc_count

        for token in query_tokens:
            t = token.lower()
            if t not in self.idf:
                continue
            idf = self.idf[t]

            for i in range(self.doc_count):
                tf = self.doc_freqs[i].get(t, 0)
                if tf == 0:
                    continue
                dl = self.doc_lens[i]
                # BM25 formula
                numerator = tf * (BM25_K1 + 1)
                denominator = tf + BM25_K1 * (1 - BM25_B + BM25_B * dl / self.avgdl)
                scores[i] += idf * numerator / denominator

        return scores

    def search(self, query_tokens: List[str], top_k: int = 10) -> List[Tuple[str, float]]:
        """
        Search for top-k documents matching query.

        Args:
            query_tokens: Tokenized and synonym-expanded query
            top_k: Number of results

        Returns:
            List of (doc_id, score) sorted by score descending
        """
        scores = self.score(query_tokens)

        # Argsort descending without numpy
        indexed = [(score, i) for i, score in enumerate(scores) if score > 0]
        indexed.sort(key=lambda x: x[0], reverse=True)

        return [
            (self.doc_ids[i], score)
            for score, i in indexed[:top_k]
        ]
```

#### 3.1.4 模块级索引缓存

```python
# Module-level cache (avoids rebuilding per query within same process)
_cached_index: Dict[str, Any] = {}


def _get_or_build_index(kb_root: Path) -> Tuple[BM25Index, List[str], List[Dict[str, Any]]]:
    """
    Get cached index or build new one.

    Returns:
        (bm25_index, entry_ids, entries)
    """
    cache_key = str(kb_root)

    if cache_key in _cached_index:
        cached = _cached_index[cache_key]
        return cached['index'], cached['entry_ids'], cached['entries']

    entries, entry_ids, texts = _load_entries(kb_root)
    if not texts:
        return None, [], []

    index = BM25Index(texts, entry_ids)
    _cached_index[cache_key] = {
        'index': index,
        'entry_ids': entry_ids,
        'entries': entries,
    }
    return index, entry_ids, entries


def invalidate_cache(kb_root: Path = None) -> None:
    """
    Invalidate BM25 index cache.

    Args:
        kb_root: Specific root to invalidate, or None to clear all
    """
    if kb_root is None:
        _cached_index.clear()
    else:
        _cached_index.pop(str(kb_root), None)
```

#### 3.1.5 `_load_entries()` — 提取公共加载逻辑

```python
def _load_entries(kb_root: Path) -> Tuple[List[Dict[str, Any]], List[str], List[str]]:
    """
    Load all knowledge entries from kb_root.

    Returns:
        (entries, entry_ids, texts)
    """
    entries: List[Dict[str, Any]] = []
    entry_ids: List[str] = []
    texts: List[str] = []

    for cat_dir in CATEGORY_DIRS.values():
        cat_path = kb_root / cat_dir
        if not cat_path.exists():
            continue
        for entry_file in cat_path.glob('*.json'):
            if entry_file.name == 'index.json':
                continue
            try:
                with open(entry_file, 'r', encoding='utf-8') as f:
                    entry = json.load(f)
            except (json.JSONDecodeError, IOError, UnicodeDecodeError):
                continue
            if not entry:
                continue

            text = _entry_to_text(entry)
            if text.strip():
                entries.append(entry)
                entry_ids.append(entry.get('id', entry_file.stem))
                texts.append(text)

    return entries, entry_ids, texts
```

#### 3.1.6 `build_index()` — 保持签名兼容

```python
def build_index(kb_root: Path) -> Tuple[Any, List[str], List[Dict[str, Any]]]:
    """
    Build a BM25 index from all knowledge entries.

    Signature matches the old embedding.py for backward compatibility.

    Args:
        kb_root: Knowledge base root path

    Returns:
        (bm25_index, entry_ids, entries)
    """
    return _get_or_build_index(kb_root)
```

#### 3.1.7 `search()` — 公开搜索接口（签名兼容）

```python
def search(
    query: str,
    kb_root: Path,
    top_k: int = 10,
) -> List[Tuple[str, float]]:
    """
    BM25 search over the knowledge base.

    API-compatible with the old embedding-based search().

    Args:
        query: Search query text
        kb_root: Knowledge base root
        top_k: Number of top results

    Returns:
        List of (entry_id, score) tuples, sorted by score descending.
        Scores are BM25 scores (not normalized to 0-1).
    """
    index, entry_ids, entries = _get_or_build_index(kb_root)
    if index is None:
        return []

    # Tokenize and expand query with synonyms
    query_tokens = tokenize(query)
    expanded_tokens = expand_with_synonyms(query_tokens, max_expansions=3)

    return index.search(expanded_tokens, top_k=top_k)
```

#### 3.1.8 删除的函数

以下函数从旧 `embedding.py` 中**删除**，不再需要：

- `get_model()` — 无模型可加载
- `encode()` — 无向量编码
- `_load_cache()` / `_save_cache()` — 不再使用 `.npz` 缓存（BM25 索引构建足够快）

#### 3.1.9 清理旧缓存文件

在 `_load_entries()` 或模块加载时，可选择清理旧的 embedding 缓存文件：

```python
def _cleanup_old_cache(kb_root: Path) -> None:
    """Remove old sentence-transformers cache files if present."""
    for name in ['.embedding_cache.npz', '.embedding_ids.json']:
        old_file = kb_root / name
        if old_file.exists():
            try:
                old_file.unlink()
            except OSError:
                pass
```

在 `_get_or_build_index()` 首次构建时调用一次 `_cleanup_old_cache(kb_root)`。

---

### 3.2 修改 `query.py`

**文件**：`evolving-agent/scripts/knowledge/query.py`

#### 3.2.1 修改 `query_semantic()`

**原代码**（第 598-633 行）：

```python
def query_semantic(query_text: str, limit: int = TOP_K_RESULTS) -> List[Dict[str, Any]]:
    try:
        from embedding import HAS_EMBEDDING, search as semantic_search
    except ImportError:
        HAS_EMBEDDING = False

    if not HAS_EMBEDDING:
        print("Warning: sentence-transformers not installed, falling back to keyword search",
              file=sys.stderr)
        tokens = query_text.replace(',', ' ').split()
        return query_by_triggers(tokens, limit=limit)

    kb_root = get_kb_root()
    hits = semantic_search(query_text, kb_root, top_k=limit)

    results: List[Dict[str, Any]] = []
    for entry_id, score in hits:
        entry = get_entry(entry_id)
        if entry:
            entry['_relevance_score'] = score
            entry['_match_type'] = 'semantic'
            results.append(entry)

    return results
```

**替换为**：

```python
def query_semantic(query_text: str, limit: int = TOP_K_RESULTS) -> List[Dict[str, Any]]:
    """
    Semantic search using BM25.

    Args:
        query_text: Natural language query
        limit: Max results

    Returns:
        Matched knowledge entries with _relevance_score
    """
    try:
        from embedding import search as bm25_search
    except ImportError:
        tokens = query_text.replace(',', ' ').split()
        return query_by_triggers(tokens, limit=limit)

    kb_root = get_kb_root()
    hits = bm25_search(query_text, kb_root, top_k=limit)

    results: List[Dict[str, Any]] = []
    for entry_id, score in hits:
        entry = get_entry(entry_id)
        if entry:
            entry['_relevance_score'] = score
            entry['_match_type'] = 'semantic'
            results.append(entry)

    return results
```

**改动要点**：
- 移除 `HAS_EMBEDDING` 检查（BM25 始终可用）
- 移除 fallback 警告（不再需要）
- `semantic_search` 重命名为 `bm25_search` 使语义更清晰
- 签名和返回格式完全不变

#### 3.2.2 扩展 `SYNONYM_MAP`

在 `query.py` 的 `SYNONYM_MAP` 字典中，**追加**以下新映射组（在现有条目之后添加，不修改已有条目）：

```python
    # --- 以下为新增同义词组 ---

    # request / response / HTTP
    '请求': ['request', 'http', 'fetch', 'ajax', 'xhr'],
    'request': ['请求', 'http', 'fetch', 'ajax'],
    '响应': ['response', 'reply', '返回'],
    'response': ['响应', 'reply', '返回'],
    '接口': ['api', 'endpoint', 'interface', 'rest'],
    'api': ['接口', 'endpoint', 'rest', 'restful'],

    # proxy / middleware
    '代理': ['proxy', 'middleware', 'gateway'],
    'proxy': ['代理', 'middleware', 'gateway'],

    # container / docker
    '容器': ['container', 'docker', 'k8s', 'kubernetes', 'pod'],
    'container': ['容器', 'docker', 'pod'],
    'docker': ['容器', 'container', 'image', 'dockerfile'],

    # CI/CD / pipeline
    'pipeline': ['ci', 'cd', 'workflow', '流水线', 'github-actions'],
    '流水线': ['pipeline', 'ci', 'cd', 'workflow'],

    # data structure
    '数组': ['array', 'list', 'slice'],
    'array': ['数组', 'list', 'slice'],
    '字典': ['dict', 'map', 'object', 'hashmap'],
    'dict': ['字典', 'map', 'object', 'hashmap'],
    'map': ['字典', 'dict', 'object', 'hashmap'],

    # config / settings
    '配置': ['config', 'configuration', 'settings', 'env'],
    'config': ['配置', 'configuration', 'settings'],

    # route / navigation
    '路由': ['route', 'router', 'navigation', 'routing'],
    'route': ['路由', 'router', 'navigation', 'routing'],

    # dependency / package
    '依赖': ['dependency', 'package', 'module', 'npm', 'pip'],
    'dependency': ['依赖', 'package', 'module'],
    'package': ['依赖', 'dependency', 'module', 'library'],

    # log / monitoring
    '日志': ['log', 'logging', 'logger', 'monitor'],
    'log': ['日志', 'logging', 'logger'],

    # concurrency
    '并发': ['concurrent', 'parallel', 'thread', 'multiprocess', '多线程'],
    'concurrent': ['并发', 'parallel', 'thread', '多线程'],
    'parallel': ['并发', 'concurrent', '多线程'],

    # validation / form
    '校验': ['validate', 'validation', 'check', 'verify', '验证'],
    'validate': ['校验', 'validation', 'verify', '验证'],
    '表单': ['form', 'input', 'field'],
    'form': ['表单', 'input', 'field'],

    # pagination / scroll
    '分页': ['pagination', 'paging', 'page', 'infinite-scroll'],
    'pagination': ['分页', 'paging', 'infinite-scroll'],

    # WebSocket / real-time
    'websocket': ['ws', 'socket', 'realtime', '实时'],
    '实时': ['realtime', 'websocket', 'socket', 'sse'],

    # file / upload
    '上传': ['upload', 'file', 'multipart'],
    'upload': ['上传', 'file', 'multipart'],

    # permission / role
    '权限': ['permission', 'role', 'rbac', 'acl', '授权'],
    'permission': ['权限', 'role', 'rbac', 'acl'],
```

---

### 3.3 重写 `tests/test_knowledge_embedding.py`

**文件**：`tests/test_knowledge_embedding.py`

**完整重写**。所有测试现在可以无条件运行（无需 skip），因为 BM25 是纯 Python 实现。

```python
#!/usr/bin/env python3
"""Tests for BM25-based search (replacement for embedding-based semantic search)."""

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / 'evolving-agent' / 'scripts' / 'knowledge'))

from embedding import HAS_EMBEDDING, BM25Index, search, build_index, invalidate_cache


def _make_kb(tmp_path, entries):
    """Helper: create a mini knowledge base with given entries."""
    kb_root = tmp_path / 'knowledge'
    exp_dir = kb_root / 'experiences'
    exp_dir.mkdir(parents=True)

    index_triggers = {}
    for entry in entries:
        entry_id = entry['id']
        with open(exp_dir / f"{entry_id}.json", 'w') as f:
            json.dump(entry, f)
        for trigger in entry.get('triggers', []):
            index_triggers.setdefault(trigger, []).append(entry_id)

    with open(kb_root / 'index.json', 'w') as f:
        json.dump({'trigger_index': index_triggers}, f)

    return kb_root


class TestHasEmbedding:
    """BM25 is always available."""

    def test_has_embedding_always_true(self):
        assert HAS_EMBEDDING is True


class TestBM25Index:
    """Unit tests for the BM25Index class."""

    def test_empty_corpus(self):
        index = BM25Index([], [])
        assert index.doc_count == 0
        results = index.search(['test'], top_k=5)
        assert results == []

    def test_single_document(self):
        index = BM25Index(['hello world'], ['doc-1'])
        results = index.search(['hello'], top_k=5)
        assert len(results) == 1
        assert results[0][0] == 'doc-1'
        assert results[0][1] > 0

    def test_multiple_documents_ranking(self):
        docs = [
            'react hooks state management guide',
            'python flask web framework tutorial',
            'react component lifecycle hooks performance',
        ]
        ids = ['doc-react-1', 'doc-python', 'doc-react-2']
        index = BM25Index(docs, ids)

        results = index.search(['react', 'hooks'], top_k=3)
        assert len(results) >= 2
        result_ids = [r[0] for r in results]
        # Both react docs should rank above python doc
        assert 'doc-react-1' in result_ids[:2]
        assert 'doc-react-2' in result_ids[:2]

    def test_no_match_returns_empty(self):
        index = BM25Index(['hello world'], ['doc-1'])
        results = index.search(['nonexistent'], top_k=5)
        assert results == []

    def test_chinese_tokenization(self):
        docs = ['修复跨域请求问题', '优化数据库查询性能']
        ids = ['doc-cors', 'doc-db']
        index = BM25Index(docs, ids)
        results = index.search(['跨域'], top_k=5)
        assert len(results) >= 1
        assert results[0][0] == 'doc-cors'

    def test_score_is_positive(self):
        index = BM25Index(['test document'], ['doc-1'])
        results = index.search(['test'], top_k=1)
        assert results[0][1] > 0


class TestSearch:
    """Integration tests for the search() function."""

    def test_search_basic(self, tmp_path):
        invalidate_cache()
        kb_root = _make_kb(tmp_path, [
            {
                'id': 'experience-cors-001',
                'name': 'CORS proxy solution',
                'triggers': ['cors', 'proxy'],
                'content': {'description': 'Fix cross-origin resource sharing issues'},
                'effectiveness': 0.8,
            }
        ])
        results = search('cors proxy cross origin', kb_root, top_k=5)
        assert isinstance(results, list)
        assert len(results) >= 1
        assert results[0][0] == 'experience-cors-001'
        assert isinstance(results[0][1], float)
        assert results[0][1] > 0

    def test_search_empty_kb(self, tmp_path):
        invalidate_cache()
        kb_root = tmp_path / 'knowledge'
        kb_root.mkdir(parents=True)
        results = search('anything', kb_root, top_k=5)
        assert results == []

    def test_search_multiple_entries(self, tmp_path):
        invalidate_cache()
        kb_root = _make_kb(tmp_path, [
            {
                'id': 'experience-react-001',
                'name': 'React Hooks Guide',
                'triggers': ['react', 'hooks'],
                'content': {'description': 'Guide to React hooks and state management'},
            },
            {
                'id': 'experience-vue-001',
                'name': 'Vue Composition API',
                'triggers': ['vue', 'composition'],
                'content': {'description': 'Vue 3 composition API patterns'},
            },
        ])

        results = search('react hooks state', kb_root, top_k=5)
        assert len(results) >= 1
        assert results[0][0] == 'experience-react-001'

    def test_search_synonym_expansion(self, tmp_path):
        """Synonym expansion should help match related terms."""
        invalidate_cache()
        kb_root = _make_kb(tmp_path, [
            {
                'id': 'experience-perf-001',
                'name': 'Performance optimization',
                'triggers': ['optimize', 'performance'],
                'content': {'description': 'Web app performance optimization techniques'},
            },
        ])
        # '优化' should expand to 'optimize', 'performance' etc via SYNONYM_MAP
        results = search('优化', kb_root, top_k=5)
        assert len(results) >= 1


class TestBuildIndex:
    """Tests for build_index()."""

    def test_build_index_returns_tuple(self, tmp_path):
        invalidate_cache()
        kb_root = _make_kb(tmp_path, [
            {
                'id': 'experience-test-001',
                'name': 'Test entry',
                'triggers': ['test'],
                'content': {'description': 'A test entry'},
            },
        ])
        index, ids, entries = build_index(kb_root)
        assert index is not None
        assert isinstance(index, BM25Index)
        assert len(ids) == 1
        assert ids[0] == 'experience-test-001'
        assert len(entries) == 1

    def test_build_index_empty(self, tmp_path):
        invalidate_cache()
        kb_root = tmp_path / 'knowledge'
        kb_root.mkdir()
        index, ids, entries = build_index(kb_root)
        assert index is None
        assert ids == []
        assert entries == []


class TestCache:
    """Tests for index cache behavior."""

    def test_cache_invalidation(self, tmp_path):
        invalidate_cache()
        kb_root = _make_kb(tmp_path, [
            {'id': 'exp-1', 'name': 'Entry 1', 'triggers': ['a'],
             'content': {'description': 'First'}},
        ])
        r1 = search('a', kb_root, top_k=5)
        assert len(r1) == 1

        invalidate_cache(kb_root)

        # After invalidation, should rebuild
        r2 = search('a', kb_root, top_k=5)
        assert len(r2) == 1
```

**测试要点**：
- 每个 test 方法开头调用 `invalidate_cache()` 确保隔离
- 不需要任何 `skipif` — BM25 始终可用
- 覆盖：空语料库、单文档、多文档排序、中文分词、同义词扩展、缓存失效
- 使用 `_make_kb()` helper 创建临时知识库

---

### 3.4 修改 `requirements-optional.txt`

**文件**：`requirements-optional.txt`

**原内容**：
```
# Optional Dependencies for Evolving Programming Agent
# These enhance functionality but are NOT required.
# Install with: pip install -r requirements-optional.txt

# Chinese tokenization (improves knowledge retrieval for Chinese text)
# Without: falls back to regex-based character splitting
jieba>=0.42,<1.0

# Semantic search via embeddings (improves knowledge retrieval precision)
# Without: falls back to keyword-based search
sentence-transformers>=2.2
```

**替换为**：
```
# Optional Dependencies for Evolving Programming Agent
# These enhance functionality but are NOT required.
# Install with: pip install -r requirements-optional.txt

# Chinese tokenization (improves knowledge retrieval for Chinese text)
# Without: falls back to regex-based character splitting
jieba>=0.42,<1.0
```

即：**删除 `sentence-transformers>=2.2` 及其注释行**。

---

### 3.5 修改 `scripts/install.sh`

**文件**：`scripts/install.sh`

#### 改动 1：简化可选依赖安装逻辑（约第 424-439 行）

**原代码**：
```bash
        # 安装可选依赖（失败不中断）
        # 默认仅装轻量可选 jieba；--optional full 时装 sentence-transformers（耗时长，见 docs/INSTALL_OPTIONAL.md）
        local optional_req
        if [ "${OPTIONAL_DEPS:-light}" = "full" ]; then
            optional_req="${PROJECT_ROOT}/requirements-optional.txt"
            info "  安装完整可选依赖（jieba + sentence-transformers，可能较慢）..."
        else
            optional_req="${PROJECT_ROOT}/requirements-optional-light.txt"
            [ ! -f "${optional_req}" ] && optional_req="${PROJECT_ROOT}/requirements-optional.txt"
            info "  安装轻量可选依赖（jieba）..."
        fi
        if [ -f "${optional_req}" ]; then
            run_cmd "${pip_install_prefix} -r '${optional_req}' -q" "${venv_dir}" || {
                warn "  部分可选依赖安装失败，核心功能不受影响"
            }
        fi
```

**替换为**：
```bash
        # 安装可选依赖（失败不中断）
        local optional_req="${PROJECT_ROOT}/requirements-optional.txt"
        if [ -f "${optional_req}" ]; then
            info "  安装可选依赖（jieba 中文分词）..."
            run_cmd "${pip_install_prefix} -r '${optional_req}' -q" "${venv_dir}" || {
                warn "  可选依赖安装失败，核心功能不受影响"
            }
        fi
```

#### 改动 2：help 文本中移除 `--optional full`（约第 464 行）

删除这一行：
```
    --optional full         安装完整可选依赖（含 sentence-transformers，耗时长）
```

#### 改动 3：info 文本中更新说明（约第 512 行）

**原**：
```
    - 可选依赖默认仅安装 jieba（轻量）；--optional full 可安装 sentence-transformers（较慢，见 docs/INSTALL_OPTIONAL.md）
```

**替换为**：
```
    - 可选依赖：jieba（中文分词，提升知识检索精度）
```

#### 改动 4：第 17 行 usage 注释

**原**：
```bash
#   ./install.sh --optional full         # 安装完整可选依赖（含 sentence-transformers，较慢）
```

**删除此行。**

#### 改动 5：移除 `--optional` 参数解析

搜索脚本中解析 `--optional` 参数的 case 分支，**删除**该分支。具体位置在 `parse_args()` 函数或主循环 `while` 中的 `--optional)` case。

---

### 3.6 修改 `README.md`

搜索 README.md 中提到 `sentence-transformers` 的位置，更新说明。

**原**（大意）：
> 四级检索：精确匹配 → 部分匹配 → 模糊匹配（可选 jieba）→ 语义搜索（可选 embedding）

**替换为**：
> 四级检索：精确匹配 → 部分匹配 → 模糊匹配（可选 jieba）→ BM25 语义搜索

如有提到 `sentence-transformers` 作为可选依赖的地方，替换为说明 BM25 是内置的零依赖方案。

---

### 3.7 修改 `docs/SOLUTION.md`

同 README.md，搜索所有 `sentence-transformers` / `embedding 语义搜索` 提及，更新为 BM25。

**原**（第 74 行附近）：
> 四级检索 + jieba 中文分词 + embedding 语义搜索 + 相关性排序

**替换为**：
> 四级检索 + jieba 中文分词 + BM25 语义搜索 + 相关性排序

**原**（第 462 行附近）：
> 可选依赖优雅降级：jieba、sentence-transformers 不安装也能正常运行，功能退化但不报错

**替换为**：
> 可选依赖优雅降级：jieba 不安装也能正常运行（回退到正则分词），BM25 搜索为内置零依赖实现

---

## 4. query_hybrid() 的阈值调整

`trigger.py` 第 221 行有阈值判断：

```python
high_threshold = 0.45 if mode in ('semantic', 'hybrid') else 3
```

旧版 embedding search 返回的是余弦相似度分数（0-1 范围），而 BM25 分数范围不固定，通常在 0-20+ 之间。

**改动**：在 `trigger.py` 中，将 semantic/hybrid 模式的阈值调整为 BM25 适配值：

```python
high_threshold = 2.0 if mode in ('semantic', 'hybrid') else 3
```

选 `2.0` 的理由：BM25 中一个精确匹配的 IDF 加权通常在 1.0-3.0 之间，`2.0` 作为"高相关"的阈值合理。如需微调，可后续根据实际数据校准。

**或者**，更好的方案是在 `embedding.py` 的 `search()` 中对 BM25 分数做归一化：

```python
def search(...) -> List[Tuple[str, float]]:
    ...
    raw_results = index.search(expanded_tokens, top_k=top_k)
    if not raw_results:
        return []

    # Normalize scores to 0-1 range
    max_score = raw_results[0][1]  # Already sorted descending
    if max_score > 0:
        return [(doc_id, score / max_score) for doc_id, score in raw_results]
    return raw_results
```

**推荐使用归一化方案**，这样 `trigger.py` 的阈值 `0.45` 可以保持不变，对所有调用方透明。

---

## 5. 不需要修改的文件（确认）

以下文件**不需要改动**：

| 文件 | 原因 |
|------|------|
| `evolving-agent/scripts/knowledge/trigger.py` | 通过 `query.py` 间接调用，如采用归一化方案则阈值无需改 |
| `evolving-agent/scripts/knowledge/query.py` 的 `query_by_triggers()` | keyword 四级检索逻辑不变 |
| `evolving-agent/scripts/knowledge/query.py` 的 `query_hybrid()` | 组合逻辑不变 |
| `evolving-agent/scripts/run.py` | 通过 subprocess 调用 `query.py` / `trigger.py`，无直接依赖 |
| `evolving-agent/agents/retrieval.md` | agent 描述中已注明"自动回退"，无需改 |
| `evolving-agent/scripts/core/config.py` | 无 embedding 相关配置 |
| `evolving-agent/scripts/knowledge/store.py` | 知识存储不涉及搜索 |

---

## 6. 验收标准

### 6.1 测试通过

```bash
cd /home/richen/Workspace/python/evolving-programming-agent
python -m pytest tests/test_knowledge_embedding.py -v
```

**预期**：所有测试 pass，无 skip。

### 6.2 全量回归

```bash
python -m pytest tests/ -v
```

**预期**：不引入新的 failure。现有测试（~148 个）中与 embedding 相关的不应再有 skip。

### 6.3 功能验证

```bash
cd evolving-agent/scripts
python run.py knowledge query --trigger "react,hooks" --mode semantic
python run.py knowledge query --trigger "优化,性能" --mode hybrid
python run.py knowledge trigger --input "修复 CORS 跨域问题" --mode hybrid --format context
```

**预期**：三条命令均正常输出，不报 ImportError，不输出 "sentence-transformers not installed" 警告。

### 6.4 依赖验证

```bash
pip uninstall sentence-transformers torch numpy -y 2>/dev/null
python -c "from embedding import HAS_EMBEDDING; print(HAS_EMBEDDING)"
# 预期输出: True
```

### 6.5 同义词验证

```bash
python run.py knowledge query --trigger "请求" --mode semantic
# 预期：能匹配到包含 request/http/fetch/api 等触发词的条目
```

---

## 7. 实现顺序

建议按以下顺序执行，每步可独立验证：

1. **重写 `embedding.py`** — 核心改动
2. **修改 `query.py`** — 适配新模块 + 扩展同义词
3. **重写测试文件** — 验证核心功能
4. **修改 `requirements-optional.txt`** — 移除旧依赖
5. **修改 `install.sh`** — 清理安装逻辑
6. **修改文档** — README.md + SOLUTION.md

---

## 8. 技术备注

### 8.1 BM25 vs sentence-transformers 在本场景的权衡

| 维度 | BM25 | sentence-transformers |
|------|------|-----------------------|
| 安装体积 | 0 | ~2.5GB |
| 首次查询延迟 | <10ms | ~3-5s（模型加载） |
| 词汇外泛化 | 靠同义词表 | 靠神经网络 |
| 中英跨语言 | 靠同义词表 | 内置（多语言模型） |
| 适合规模 | <10K 条目 | 任意规模 |

**对于本项目**：知识库通常 <1000 条目，同义词表已覆盖 ~60 组中英映射，BM25 + 同义词在实际使用中效果接近，而安装成本降低 99.9%+。

### 8.2 为何不用 `rank_bm25` 库

- `rank_bm25` 依赖 numpy，而本方案目标是零外部依赖
- 我们的知识库规模小，纯 Python 实现性能足够
- 自行实现可以深度集成 `tokenize()` 和 `expand_with_synonyms()`

### 8.3 缓存策略

- BM25 索引构建对 <1000 条目来说 <50ms，无需持久化缓存
- 使用 module-level dict 缓存避免同一进程内重复构建
- 提供 `invalidate_cache()` 供 store 操作后调用（当前版本可选，未来可集成）
