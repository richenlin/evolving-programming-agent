#!/usr/bin/env python3
"""Pre-download BGE embedding model (install.sh --china / setup_venv.sh --china)."""

from __future__ import annotations

import os
import sys


def _use_china_mirror() -> bool:
    if os.environ.get("EVOLVE_USE_CN_MIRROR") == "1":
        return True
    endpoint = os.environ.get("HF_ENDPOINT", "")
    return "hf-mirror" in endpoint


def _apply_hf_mirror_compat() -> None:
    """Avoid cas-bridge.xethub.hf.co redirects; stay on HF mirror HTTP."""
    os.environ.setdefault("HF_HUB_DISABLE_XET", "1")
    os.environ.setdefault("HF_HUB_DOWNLOAD_TIMEOUT", "600")


def _download_via_modelscope(model_id: str) -> str | None:
    try:
        from modelscope import snapshot_download
    except ImportError:
        return None

    print("  使用 ModelScope 下载（国内 CDN）...")
    return snapshot_download(model_id)


def prewarm(model_id: str = "BAAI/bge-small-zh-v1.5") -> int:
    try:
        from sentence_transformers import SentenceTransformer
    except ImportError:
        return 2

    china = _use_china_mirror()
    if china:
        _apply_hf_mirror_compat()
        endpoint = os.environ.get("HF_ENDPOINT", "(default huggingface.co)")
        print(f"  HF_ENDPOINT={endpoint}")
        print(f"  HF_HUB_DISABLE_XET={os.environ.get('HF_HUB_DISABLE_XET')}")

    local_path: str | None = None
    if china:
        try:
            local_path = _download_via_modelscope(model_id)
        except Exception as exc:
            print(f"  ModelScope 失败 ({exc})，回退 HF 镜像...")

    load_path = local_path or model_id
    print(f"  下载/校验模型: {load_path} ...")
    SentenceTransformer(load_path)
    print("  模型就绪")
    return 0


if __name__ == "__main__":
    mid = sys.argv[1] if len(sys.argv) > 1 else "BAAI/bge-small-zh-v1.5"
    raise SystemExit(prewarm(mid))
