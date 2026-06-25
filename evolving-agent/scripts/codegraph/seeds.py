#!/usr/bin/env python3
"""Curated global knowledge seeds — pattern, framework, architecture nodes."""

from __future__ import annotations

from typing import Any, Dict, List

SEEDS: List[Dict[str, Any]] = [
    {
        "kind": "pattern",
        "name": "Repository Pattern",
        "summary": "数据访问抽象层，隔离持久化与业务逻辑",
        "provenance": "curated",
    },
    {
        "kind": "pattern",
        "name": "Layered Architecture",
        "summary": "表现层 / 业务层 / 数据层分层",
        "provenance": "curated",
    },
    {
        "kind": "pattern",
        "name": "Component-Based",
        "summary": "UI 组件化，组合优于继承",
        "provenance": "curated",
    },
    {
        "kind": "pattern",
        "name": "MVC",
        "summary": "Model-View-Controller 分离",
        "provenance": "curated",
    },
    {
        "kind": "framework",
        "name": "React",
        "summary": "声明式 UI 库，组件 + hooks",
        "provenance": "curated",
    },
    {
        "kind": "framework",
        "name": "Vue",
        "summary": "渐进式前端框架",
        "provenance": "curated",
    },
    {
        "kind": "framework",
        "name": "FastAPI",
        "summary": "Python 异步 Web API 框架",
        "provenance": "curated",
    },
    {
        "kind": "framework",
        "name": "Express",
        "summary": "Node.js 极简 HTTP 框架",
        "provenance": "curated",
    },
    {
        "kind": "framework",
        "name": "Django",
        "summary": "Python 全栈 Web 框架",
        "provenance": "curated",
    },
    {
        "kind": "framework",
        "name": "Flask",
        "summary": "Python 轻量 Web 框架",
        "provenance": "curated",
    },
    {
        "kind": "language",
        "name": "Python",
        "summary": "通用脚本与后端语言",
        "provenance": "curated",
    },
    {
        "kind": "language",
        "name": "TypeScript",
        "summary": "带类型的 JavaScript 超集",
        "provenance": "curated",
    },
    {
        "kind": "architecture",
        "name": "REST API",
        "summary": "资源导向 HTTP API 风格",
        "provenance": "curated",
    },
    {
        "kind": "architecture",
        "name": "Microservices",
        "summary": "服务拆分，独立部署与扩展",
        "provenance": "curated",
    },
]

DIRECTORY_PATTERNS: Dict[str, str] = {
    "services": "Service Layer",
    "service": "Service Layer",
    "controllers": "Controller Layer",
    "controller": "Controller Layer",
    "models": "Domain Model Layer",
    "model": "Domain Model Layer",
    "repositories": "Repository Pattern",
    "repository": "Repository Pattern",
    "components": "Component-Based",
    "component": "Component-Based",
    "views": "MVC",
    "handlers": "Handler Pattern",
    "middleware": "Middleware Pattern",
    "routes": "Routing Layer",
    "api": "REST API",
    "utils": "Utility Layer",
    "lib": "Shared Library",
    "core": "Core Domain",
}

FRAMEWORK_IMPORTS: Dict[str, str] = {
    "react": "React",
    "react-dom": "React",
    "vue": "Vue",
    "fastapi": "FastAPI",
    "express": "Express",
    "django": "Django",
    "flask": "Flask",
    "sqlalchemy": "SQLAlchemy",
    "prisma": "Prisma",
    "next": "Next.js",
    "next/server": "Next.js",
    "@nestjs/core": "NestJS",
    "springframework": "Spring",
}
