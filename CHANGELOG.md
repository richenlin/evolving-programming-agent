# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## Release Categories（分类规范）

每个版本变更按以下分类记录，便于 IDE 集成方判断升级影响：

- **Skill changes**：影响 SKILL.md / agents/ / workflows/ / references/ 的内容变更
  - IDE 跟进：仅需 IDE build 时拉取新版资源即可，**IDE 代码不变**
- **CLI changes**：run.py 子命令、参数、输出格式的兼容性变更（增字段、新子命令）
  - IDE 跟进：可选更新 mapActionToCli 以使用新功能，但**旧调用仍工作**
- **Breaking changes**：破坏 cli_protocol 兼容性的变更
  - IDE 跟进：必须 bump cli_protocol.version 并适配 IDE 代码
- **Bug fixes**（可选，仅 patch 版本使用）：build 工具、内部脚本等不属于上述三栏的修复
  - IDE 跟进：通常仅需重新拉取资源（`npm run skill:prepare`），无 IDE 代码变更

## [Unreleased]

### Skill changes
- _none_

### CLI changes
- _none_

### Breaking changes
- _none_

## [1.1.1] - 2026-05-13

### Bug fixes
- `scripts/pack_for_ide.py`: `shutil.copytree` calls now pass
  `symlinks=True` so that the relative symlinks shipped by
  python-build-standalone (e.g. `bin/python3 → python3.11`,
  `bin/2to3 → 2to3-3.11`) are preserved instead of being
  dereferenced into absolute paths. Without this, downstream
  consumers using `fs.cpSync(... { recursive: true })` could hit
  EINVAL on re-runs because already-extracted symlink targets
  appeared as the source's own subdirectories.
- New post-pack sanity check warns if portable Python's expected
  symlinks (python3 / 2to3 / pip3) appear as regular files,
  surfacing dereference bugs early.

### Skill changes
- _none_

### CLI changes
- _none_

### Breaking changes
- _none_

## [1.1.0] - 2026-05-13

### Skill changes
- New `evolving-agent/SKILL.ide.md` — IDE single-model adapter variant of SKILL.md.
  Rewrites `调度 @agent` multi-agent dispatch syntax into `evolving_agent` tool
  calls suitable for single-conversation IDE integrations. Core workflow
  (state machine / intent detection / knowledge retrieval / commit flow)
  preserved verbatim.

### CLI changes
- `run.py meta` accepts new `--mode {default,ide}` argument. Default behaviour
  unchanged. `--mode ide` returns SKILL.ide.md as `skill_md`; falls back to
  default with a stderr warning if SKILL.ide.md is missing. Response JSON
  gains a `mode` field so callers can detect fallback.

### Breaking changes
- _none_ (cli_protocol stays at v1; --mode is additive)

### Notes for IDE integrators
- Prefer `run.py meta --skill-content --mode ide` over implementing custom
  adapter layers on your side.
- Bump skill min_ide_version requirement check to 1.1.0 only if you start
  consuming the `mode` field; older callers continue to work as before.

## [1.0.0] - 2026-05-12

### Skill changes
- _none_ (initial release)

### CLI changes
- 新增 `run.py version` 子命令：输出 skill_version / cli_protocol / min_ide_version
- 新增 `run.py meta [--skill-content]` 子命令：导出 runtime.json 或 skill 文档树
- 新增 `run.py verify` 子命令：校验 manifest.json 完整性

### Breaking changes
- _none_

### Infrastructure
- 新增 `runtime.json`：声明 skill 版本、便携 Python 下载源、依赖、cli_protocol
- 新增 `scripts/bootstrap.py`：纯 stdlib detect-only Python 解析器
- 新增 `scripts/pack_for_ide.py`：IDE build 期一键打包工具
- 新增 `.github/workflows/release.yml`：5 平台预构建 release pipeline
- `evolving-agent/scripts/core/task_manager.py:get_project_root()`：增加 runtime.json fallback 解析（向前兼容，git 路径不变）
- ⚠️ Known limitation: `runtime.json` Python checksums are placeholders. Until checksums are populated, release archives are built with `--skip-checksum` and `manifest.python_runtime.checksum_verified = false`. IDE integrators should track this for supply-chain hardening.
