# 模型配置指南

Evolving Programming Agent v5.0 使用多个专用模型执行不同角色任务。

---

## 配置方式

### 优先级（从低到高）

```
全局默认模型
  ↓
~/.config/opencode/opencode.json（全局配置）
  ↓
.opencode/opencode.json（项目级配置）
  ↓
agent markdown frontmatter（最高优先级，已内置）
```

**默认情况**：agent 文件中已内置模型配置（frontmatter 的 `model:` 字段），安装后即可使用。

**覆盖配置**：如需更改模型，在 `opencode.json` 中配置即可覆盖默认值。

---

## 角色与模型分配

| 角色 | 默认模型 | 用途 | 理由 |
|------|----------|------|------|
| orchestrator | `zai-coding-plan/glm-5` | 任务调度、DAG 排序 | agentic 任务 SOTA，长上下文支持 |
| coder | `zai-coding-plan/glm-5` | 代码生成、测试执行 | LMArena Code Top-1 |
| reviewer | `openrouter/anthropic/claude-sonnet-4.6` | 代码审查（temperature=0.1） | 细节把控严格，减少随机性 |
| evolver | `zai-coding-plan/glm-5` | 知识提取、经验归纳 | 200K 上下文窗口 |
| retrieval | `zai-coding-plan/glm-5` | 知识检索 | 快速语义匹配 |

---

## 配置步骤

### 1. 使用模板配置（推荐）

```bash
# 全局配置（影响所有项目）
cp opencode.json.template ~/.config/opencode/opencode.json

# 或项目级配置（仅影响当前项目）
mkdir -p .opencode
cp opencode.json.template .opencode/opencode.json
```

### 2. 配置 API Key

编辑 `opencode.json`，填入对应 provider 的 API key：

```json
{
  "$schema": "https://opencode.ai/config.json",
  "provider": {
    "openrouter": {
      "apiKey": "sk-or-v1-xxxxx"
    },
    "zhipuai": {
      "apiKey": "xxxxx.xxxxx"
    }
  }
}
```

### 3. 获取 API Key

**OpenRouter（用于 claude-sonnet-4.6）：**
- 访问 https://openrouter.ai/keys
- 创建 API key
- 模型标识：`openrouter/anthropic/claude-sonnet-4.6`

**智谱 AI（用于 GLM-5）：**
- 访问 https://open.bigmodel.cn/usercenter/apikeys
- 创建 API key
- 模型标识：`zai-coding-plan/glm-5`

---

## 验证配置

安装完成后，执行以下命令验证：

```bash
# OpenCode 查看当前模型配置
opencode config

# 或查看 agent 配置
opencode agent list
```

---

## 覆盖单个 Agent 模型

如果只想更改某个 agent 的模型，在 `opencode.json` 中单独配置：

```json
{
  "agent": {
    "reviewer": {
      "model": "anthropic/claude-opus-4-20250514",
      "temperature": 0.05,
      "comment": "使用更强的 opus 模型审查"
    }
  }
}
```

---

## 使用其他模型

### 替换为纯 Claude 方案

```json
{
  "agent": {
    "orchestrator": {
      "model": "anthropic/claude-haiku-4-20250514"
    },
    "coder": {
      "model": "anthropic/claude-sonnet-4-20250514"
    },
    "reviewer": {
      "model": "anthropic/claude-sonnet-4-20250514",
      "temperature": 0.1
    },
    "evolver": {
      "model": "anthropic/claude-haiku-4-20250514"
    },
    "retrieval": {
      "model": "anthropic/claude-haiku-4-20250514"
    }
  },
  "provider": {
    "anthropic": {
      "apiKey": "sk-ant-xxxxx"
    }
  }
}
```

### 替换为纯 OpenAI 方案

```json
{
  "agent": {
    "orchestrator": {
      "model": "openai/gpt-4o-mini"
    },
    "coder": {
      "model": "openai/gpt-4o"
    },
    "reviewer": {
      "model": "openai/gpt-4o",
      "temperature": 0.1
    },
    "evolver": {
      "model": "openai/gpt-4o-mini"
    },
    "retrieval": {
      "model": "openai/gpt-4o-mini"
    }
  },
  "provider": {
    "openai": {
      "apiKey": "sk-xxxxx"
    }
  }
}
```

---

## 常见问题

### Q: 不配置 opencode.json 能用吗？

**A**: 可以，但需要确保：
1. OpenCode 全局配置中有可用的默认模型
2. 该默认模型的 provider 已配置 API key

Agent 文件中已内置 `model:` 字段，但如果对应 provider 未配置 key，会报错。

### Q: Claude Code 如何配置？

**A**: Claude Code 无原生 agent 系统，使用角色切换模拟。模型配置方式：
1. 通过 Claude Code 的全局设置配置默认模型
2. 在 `.claude/skills/evolving-agent/agents/*.md` 中的 frontmatter 字段仅供文档参考，不会被 Claude Code 解析

### Q: 如何降低成本？

**A**: 所有角色都使用免费/便宜的模型：

```json
{
  "agent": {
    "orchestrator": { "model": "openai/gpt-4o-mini" },
    "coder": { "model": "openai/gpt-4o-mini" },
    "reviewer": { "model": "openai/gpt-4o-mini", "temperature": 0.1 },
    "evolver": { "model": "openai/gpt-4o-mini" },
    "retrieval": { "model": "openai/gpt-4o-mini" }
  }
}
```

或使用本地模型：

```json
{
  "agent": {
    "orchestrator": { "model": "ollama/qwen2.5-coder:14b" },
    "coder": { "model": "ollama/qwen2.5-coder:32b" },
    "reviewer": { "model": "ollama/qwen2.5-coder:32b" },
    "evolver": { "model": "ollama/qwen2.5-coder:14b" },
    "retrieval": { "model": "ollama/qwen2.5-coder:7b" }
  }
}
```
