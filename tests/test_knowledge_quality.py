#!/usr/bin/env python3
"""Tests for knowledge entry quality gates."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "evolving-agent" / "scripts" / "knowledge"))

from quality import (
    is_low_value_entry,
    filter_entries_for_display,
)


class TestIsLowValueEntry:
    def test_rejects_review_placeholder(self):
        entry = {
            "name": "review发现",
            "category": "problem",
            "content": {
                "description": "review发现",
                "solution": "缺少 password 字段校验",
                "symptoms": ["review发现"],
            },
        }
        assert is_low_value_entry(entry) is True

    def test_rejects_meta_jargon(self):
        entry = {
            "name": "builder 经验检索用回调注入",
            "category": "experience",
            "content": {
                "description": "BuildOpts experience 回调",
                "solution": "extension.ts 注入 storeOf hybrid retriever",
            },
        }
        assert is_low_value_entry(entry) is True

    def test_rejects_generic_pytest_fixture(self):
        entry = {
            "name": "Pytest Best Practices",
            "category": "testing",
            "content": {
                "best_practices": ["Use fixtures", "Parametrize tests"],
            },
        }
        assert is_low_value_entry(entry) is True

    def test_accepts_real_problem(self):
        entry = {
            "name": "CORS 跨域 blocked by browser",
            "category": "problem",
            "content": {
                "description": "前端 localhost 调用 API 被浏览器拦截",
                "solution": "开发环境配置 vite proxy 转发 /api",
                "symptoms": ["Access-Control-Allow-Origin missing"],
            },
        }
        assert is_low_value_entry(entry) is False


class TestFilterEntriesForDisplay:
    def test_dedupes_same_content_different_ids(self):
        base = {
            "name": "JWT 过期导致 401",
            "category": "experience",
            "content": {
                "description": "长时间操作后登录态失效",
                "solution": "access token 15m + refresh 轮换",
            },
        }
        entries = [
            {**base, "id": "exp-1", "_relevance_score": 0.8},
            {**base, "id": "exp-2", "_relevance_score": 0.75},
        ]
        out = filter_entries_for_display(
            entries, mode="hybrid", min_relevance=0.35, max_items=5,
        )
        assert len(out) == 1
        assert out[0]["id"] == "exp-1"

    def test_keeps_one_good_entry(self):
        good = {
            "id": "exp-1",
            "name": "JWT 过期导致 401",
            "category": "experience",
            "content": {
                "description": "登录态在长时间操作后失效",
                "solution": "access token 15m + refresh token 轮换",
            },
            "_relevance_score": 0.72,
        }
        out = filter_entries_for_display(
            [good], mode="hybrid", min_relevance=0.35, max_items=5,
        )
        assert len(out) == 1
