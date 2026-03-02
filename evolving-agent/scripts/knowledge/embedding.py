#!/usr/bin/env python3
"""
Semantic Search via Embeddings.

Provides optional embedding-based semantic search for the knowledge base.
Falls back gracefully when sentence-transformers is not installed.
"""

import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# Optional dependency: sentence-transformers + numpy
try:
    from sentence_transformers import SentenceTransformer
    import numpy as np
    HAS_EMBEDDING = True
except ImportError:
    HAS_EMBEDDING = False

# Category to directory mapping
CATEGORY_DIRS = {
    'experience': 'experiences',
    'tech-stack': 'tech-stacks',
    'scenario': 'scenarios',
    'problem': 'problems',
    'testing': 'testing',
    'pattern': 'patterns',
    'skill': 'skills'
}

# Model singleton
_model = None


def get_model():
    """
    Lazily load and cache the sentence-transformers model.

    Returns:
        SentenceTransformer model instance

    Raises:
        ImportError: If sentence-transformers is not installed
    """
    global _model
    if not HAS_EMBEDDING:
        raise ImportError(
            "sentence-transformers is required for semantic search. "
            "Install with: pip install sentence-transformers"
        )
    if _model is None:
        _model = SentenceTransformer('all-MiniLM-L6-v2')
    return _model


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


def encode(texts: List[str]):
    """
    Batch-encode texts into vectors.

    Args:
        texts: List of text strings

    Returns:
        numpy ndarray of shape (len(texts), embedding_dim)
    """
    model = get_model()
    return model.encode(texts, show_progress_bar=False, convert_to_numpy=True)


def build_index(kb_root: Path) -> Tuple[Any, List[str], List[Dict[str, Any]]]:
    """
    Build an embedding index from all knowledge entries.

    Args:
        kb_root: Knowledge base root path

    Returns:
        (vectors, entry_ids, entries) — vectors is a numpy array,
        entry_ids is a list of IDs, entries is a list of full dicts
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
            except (json.JSONDecodeError, IOError):
                continue
            if not entry:
                continue

            text = _entry_to_text(entry)
            if text.strip():
                entries.append(entry)
                entry_ids.append(entry.get('id', entry_file.stem))
                texts.append(text)

    if not texts:
        return None, [], []

    vectors = encode(texts)
    return vectors, entry_ids, entries


def _load_cache(kb_root: Path):
    """Try loading cached index. Returns (vectors, ids) or None."""
    cache_path = kb_root / '.embedding_cache.npz'
    ids_path = kb_root / '.embedding_ids.json'
    if not cache_path.exists() or not ids_path.exists():
        return None

    import numpy as np
    try:
        data = np.load(str(cache_path))
        vectors = data['vectors']
        with open(ids_path, 'r', encoding='utf-8') as f:
            ids = json.load(f)
        return vectors, ids
    except Exception:
        return None


def _save_cache(kb_root: Path, vectors, ids: List[str]):
    """Save index cache."""
    import numpy as np
    cache_path = kb_root / '.embedding_cache.npz'
    ids_path = kb_root / '.embedding_ids.json'
    try:
        np.savez(str(cache_path), vectors=vectors)
        with open(ids_path, 'w', encoding='utf-8') as f:
            json.dump(ids, f)
    except Exception:
        pass


def search(
    query: str,
    kb_root: Path,
    top_k: int = 10,
) -> List[Tuple[str, float]]:
    """
    Semantic search over the knowledge base.

    Args:
        query: Search query text
        kb_root: Knowledge base root
        top_k: Number of top results

    Returns:
        List of (entry_id, similarity_score) tuples, sorted by score descending
    """
    if not HAS_EMBEDDING:
        return []

    vectors, entry_ids, entries = build_index(kb_root)
    if vectors is None or len(entry_ids) == 0:
        return []

    import numpy as np

    # Encode query
    query_vec = encode([query])[0]

    # Cosine similarity
    norms = np.linalg.norm(vectors, axis=1, keepdims=True)
    norms[norms == 0] = 1  # avoid division by zero
    normed = vectors / norms
    query_norm = query_vec / (np.linalg.norm(query_vec) or 1)
    scores = normed @ query_norm

    # Top-k
    top_indices = np.argsort(scores)[::-1][:top_k]
    results = [(entry_ids[i], float(scores[i])) for i in top_indices if scores[i] > 0]

    return results
