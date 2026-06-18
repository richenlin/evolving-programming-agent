#!/usr/bin/env python3
"""
CodeGraph Embedder — generate and persist text vectors.

Backends (first available wins):
  1. OpenAI-compatible API  (OPENAI_API_KEY + optional OPENAI_BASE_URL)
  2. sentence-transformers  (optional pip install; default BAAI/bge-small-zh-v1.5)
  3. hash-trick fallback    (stdlib only, deterministic)
"""

from __future__ import annotations

import json
import math
import os
import re
import urllib.error
import urllib.request
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from codegraph.paths import get_vectors_path

try:
    from core.config import DEFAULT_LOCAL_EMBED_MODEL
except ImportError:
    DEFAULT_LOCAL_EMBED_MODEL = "BAAI/bge-small-zh-v1.5"

DEFAULT_DIM = 384
DEFAULT_MODEL = "hash-trick-v1"

_ST_MODEL_CACHE: Dict[str, Any] = {}


def _tokenize(text: str) -> List[str]:
    return re.findall(r"[\u4e00-\u9fff]+|[a-zA-Z0-9]+", text.lower())


def hash_embed(text: str, dim: int = DEFAULT_DIM) -> List[float]:
    """Deterministic feature-hashing embedding (L2-normalized)."""
    vec = [0.0] * dim
    for token in _tokenize(text):
        h = hash(token) % dim
        vec[h] += 1.0
        h2 = hash(token + ":2") % dim
        vec[h2] += 0.5
    norm = math.sqrt(sum(v * v for v in vec))
    if norm > 0:
        vec = [v / norm for v in vec]
    return vec


def _openai_embed(texts: List[str], model: str) -> Optional[List[List[float]]]:
    api_key = os.environ.get("OPENAI_API_KEY") or os.environ.get("CODEGRAPH_EMBED_API_KEY")
    if not api_key:
        return None
    base = (os.environ.get("OPENAI_BASE_URL")
            or os.environ.get("CODEGRAPH_EMBED_BASE_URL")
            or "https://api.openai.com/v1")
    url = base.rstrip("/") + "/embeddings"
    payload = json.dumps({"input": texts, "model": model}).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=payload,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            data = json.load(resp)
        items = sorted(data["data"], key=lambda x: x["index"])
        return [item["embedding"] for item in items]
    except (urllib.error.URLError, KeyError, json.JSONDecodeError, OSError):
        return None


def _local_embed(texts: List[str], model: str) -> Optional[List[List[float]]]:
    try:
        from sentence_transformers import SentenceTransformer  # type: ignore
    except ImportError:
        return None
    try:
        if model not in _ST_MODEL_CACHE:
            _ST_MODEL_CACHE[model] = SentenceTransformer(model)
        st_model = _ST_MODEL_CACHE[model]
        vectors = st_model.encode(texts, normalize_embeddings=True)
        return [v.tolist() for v in vectors]
    except Exception:
        return None


def get_embed_backend() -> Tuple[str, str]:
    """Return (backend_name, model_id)."""
    if os.environ.get("OPENAI_API_KEY") or os.environ.get("CODEGRAPH_EMBED_API_KEY"):
        model = os.environ.get("CODEGRAPH_EMBED_MODEL", "text-embedding-3-small")
        return "openai", model
    local_model = os.environ.get("CODEGRAPH_LOCAL_EMBED_MODEL", DEFAULT_LOCAL_EMBED_MODEL)
    try:
        import sentence_transformers  # noqa: F401
        return "local", local_model
    except ImportError:
        pass
    return "hash", DEFAULT_MODEL


def embed_texts(texts: List[str]) -> Tuple[List[List[float]], str, str]:
    """
    Embed a batch of texts.

    Returns:
        (vectors, backend, model)
    """
    if not texts:
        return [], "none", "none"

    backend, model = get_embed_backend()
    if backend == "openai":
        vecs = _openai_embed(texts, model)
        if vecs:
            return vecs, backend, model
        backend = "hash"
        model = DEFAULT_MODEL

    if backend == "local":
        vecs = _local_embed(texts, model)
        if vecs:
            return vecs, backend, model
        backend = "hash"
        model = DEFAULT_MODEL

    return [hash_embed(t) for t in texts], backend, model


def embed_text(text: str) -> Tuple[List[float], str, str]:
    vecs, backend, model = embed_texts([text])
    return vecs[0] if vecs else [], backend, model


def cosine_similarity(a: List[float], b: List[float]) -> float:
    if not a or not b or len(a) != len(b):
        return 0.0
    dot = sum(x * y for x, y in zip(a, b))
    return max(0.0, min(1.0, dot))


def _load_vector_index(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {"version": 1, "model": None, "backend": None, "dim": DEFAULT_DIM, "entries": {}}
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return {"version": 1, "model": None, "backend": None, "dim": DEFAULT_DIM, "entries": {}}


def _save_vector_index(path: Path, data: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    tmp.replace(path)


def persist_vectors(
    project_root: str | Path,
    items: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """
    Embed and persist vector records for knowledge entries.

    Each item: { entry_id, text, type?, sources? }
    """
    if not items:
        return {"stored": 0}

    texts = [it["text"] for it in items]
    vectors, backend, model = embed_texts(texts)
    path = get_vectors_path(project_root)
    index = _load_vector_index(path)

    index["backend"] = backend
    index["model"] = model
    index["dim"] = len(vectors[0]) if vectors else DEFAULT_DIM
    index["updated_at"] = datetime.now().isoformat()

    entries = index.setdefault("entries", {})
    for item, vec in zip(items, vectors):
        eid = item["entry_id"]
        entries[eid] = {
            "entry_id": eid,
            "text": item["text"][:2000],
            "type": item.get("type", "solution"),
            "vector": vec,
            "sources": item.get("sources", []),
            "embedded_at": datetime.now().isoformat(),
        }

    _save_vector_index(path, index)
    return {"stored": len(items), "backend": backend, "model": model, "path": str(path)}


def search_vectors(
    project_root: str | Path,
    query: str,
    top_k: int = 5,
    threshold: float = 0.35,
) -> List[Dict[str, Any]]:
    """Cosine search over persisted vectors."""
    path = get_vectors_path(project_root)
    index = _load_vector_index(path)
    entries: Dict[str, Any] = index.get("entries", {})
    if not entries:
        return []

    q_vec, _, _ = embed_text(query)
    results: List[Dict[str, Any]] = []
    for eid, rec in entries.items():
        score = cosine_similarity(q_vec, rec.get("vector", []))
        if score >= threshold:
            results.append({
                "entry_id": eid,
                "score": round(score, 4),
                "type": rec.get("type"),
                "text": rec.get("text", ""),
                "sources": rec.get("sources", []),
            })

    results.sort(key=lambda x: x["score"], reverse=True)
    return results[:top_k]
