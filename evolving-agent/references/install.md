# Evolving Agent — 安装与更新

## 仓库位置

```
/Volumes/ExternalSSD/Users/richen/Workspace/evolving-programming-agent/
```

## 安装 (全新)

```bash
git clone https://github.com/richenlin/evolving-programming-agent.git \
  /Volumes/ExternalSSD/Users/richen/Workspace/evolving-programming-agent
cd /Volumes/ExternalSSD/Users/richen/Workspace/evolving-programming-agent
./scripts/install.sh --all
```

## 更新 (已安装)

```bash
cd /Volumes/ExternalSSD/Users/richen/Workspace/evolving-programming-agent
git pull
./scripts/install.sh --all
```

## 已知问题

### `--china` 标志导致 PyYAML 安装失败

`install.sh` 的 `--china` 标志在构造 pip 镜像 URL 时引入了多余的引号，导致 pip 无法解析索引 URL。

**症状**：
```
WARNING: The index url "'https://pypi.tuna.tsinghua.edu.cn/simple'" seems invalid
ERROR: Could not find a version that satisfies the requirement PyYAML
```

**修复**：已在 install.sh 中修复 `pip_extra_index()` 函数的引号问题。

**临时修复**（旧版本安装后手动补装 venv）：
```bash
cd ~/.config/opencode/skills/evolving-agent
python3 -m venv .venv
.venv/bin/pip install PyYAML -i https://pypi.tuna.tsinghua.edu.cn/simple
```

## 安装目标平台

| 平台 | 路径 |
|------|------|
| OpenCode | `~/.config/opencode/skills/evolving-agent/` |
| OpenCode Agents | `~/.config/opencode/agents/` |
| OpenCode Commands | `~/.config/opencode/command/evolve.md` |
| Claude Code | `~/.claude/skills/evolving-agent/` |
| Cursor | `~/.agents/skills/evolving-agent/` |
| OpenClaw | `~/.openclaw/skills/evolving-agent/` |
| Hermes Agent | `~/.hermes/skills/evolving-agent/` |
