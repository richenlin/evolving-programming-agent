---
name: github-to-skills
description: Automated factory for converting GitHub repositories into specialized AI skills. Use this skill when the user provides a GitHub URL and wants to "package", "wrap", or "create a skill" from it. It automatically fetches repository details, latest commit hashes, and generates a standardized skill structure with enhanced metadata suitable for lifecycle management.
license: MIT
---

# GitHub to Skills Factory

This skill automates the conversion of GitHub repositories into fully functional AI skills.

## Core Functionality

1. **Analysis**: Fetches repository metadata (Description, README, Latest Commit Hash, File Tree).
2. **Scaffolding**: Creates a standardized skill directory structure.
3. **Metadata Injection**: Generates `SKILL.md` with extended frontmatter (tracking source, version, hash) for future automated management.
4. **Wrapper Generation**: Creates a `scripts/wrapper.py` (or similar) to interface with the tool.
5. **Pattern Extraction** [NEW]: Analyzes code structure and README to extract programming patterns and best practices.

## Usage

**Tool Mode Trigger**:
- `/github-to-skills <url>` - Wrap as a callable tool
- "Package this repo into a skill"
- "Create a skill from this repository"

**Learning Mode Trigger** [NEW]:
- `/learn <url>` - Learn programming patterns and best practices
- "学习这个仓库的最佳实践"
- "从这个项目中提取代码规范"
- "Extract patterns from this repository"

### Required Metadata Schema

Every skill created by this factory MUST include the following extended YAML frontmatter in its `SKILL.md`. This is critical for the `skill-manager` to function later.

```yaml
---
name: <kebab-case-repo-name>
description: <concise-description-for-agent-triggering>
# EXTENDED METADATA (MANDATORY)
github_url: <original-repo-url>
github_hash: <latest-commit-hash-at-time-of-creation>
version: <tag-or-0.1.0>
created_at: <ISO-8601-date>
entry_point: scripts/wrapper.py # or main script
dependencies: # List main dependencies if known, e.g., ["yt-dlp", "ffmpeg"]
---
```

## Workflow

### Tool Mode

1. **Fetch Info**: The agent runs `scripts/fetch_github_info.py` to get the raw data from the repo.
2. **Plan**: The agent analyzes the README to understand how to invoke the tool (CLI args, Python API, etc.).
3. **Generate**: The agent uses the `skill-creator` patterns to write the `SKILL.md` and wrapper scripts, ensuring the **extended metadata** is present.
4. **Verify**: Checks if the commit hash was correctly captured.

### Learning Mode [NEW]

**Two output modes available:**

#### A) Legacy Markdown Output
```bash
python scripts/fetch_github_info.py <url> | python scripts/extract_patterns.py --markdown
```
Creates a Markdown addon file for manual attachment to `programming-assistant`.

#### B) Progressive Knowledge Storage (Recommended)
```bash
# Direct storage to knowledge base
python scripts/fetch_github_info.py <url> | python scripts/extract_patterns.py --store

# Or two-step with JSON intermediate
python scripts/fetch_github_info.py <url> | python scripts/extract_patterns.py --json > extracted.json
cat extracted.json | python scripts/store_knowledge.py --from-json --source <url>
```

The `--store` mode automatically:
1. Extracts patterns, conventions, tech stack, and best practices
2. Stores framework-specific knowledge in `knowledge/frameworks/<framework>.json`
3. Stores architecture patterns in `knowledge/patterns/<pattern>.json`
4. Stores best practices in `knowledge/practices/<practice>.json`
5. Updates `knowledge/index.json` with metadata

#### Query Learned Knowledge
```bash
# Query by framework
python scripts/query_knowledge.py --framework react
python scripts/query_knowledge.py --framework gin

# Query by pattern
python scripts/query_knowledge.py --pattern "Feature-Based Architecture"

# Auto-detect project and load relevant knowledge
python scripts/query_knowledge.py --project /path/to/your-project
```

## Resources

- `scripts/fetch_github_info.py`: Utility to scrape/API fetch repo details (README, Hash, Tags).
- `scripts/create_github_skill.py`: Orchestrator to scaffold the folder and write the initial files.
- `scripts/extract_patterns.py`: Pattern extraction with `--markdown`, `--json`, or `--store` modes.
- `scripts/store_knowledge.py`: Store extracted knowledge to progressive knowledge base.
- `scripts/query_knowledge.py`: Query knowledge by framework, pattern, or auto-detected project.

## Knowledge Base Structure

```
knowledge/
├── index.json              # Index of all learned knowledge
├── frameworks/             # Framework-specific knowledge
│   ├── react.json
│   ├── gin.json
│   └── spring-boot.json
├── patterns/               # Architecture patterns
│   └── feature-based-architecture.json
└── practices/              # Best practices
    └── automated-testing.json
```

The progressive storage enables:
- **Minimal token usage**: Only load knowledge relevant to current project
- **Incremental learning**: Knowledge accumulates from multiple repositories
- **Cross-reference**: Link patterns to applicable frameworks

## Best Practices for Generated Skills

- **Isolation**: The generated skill should install its own dependencies (e.g., in a venv or via `uv`/`pip`) if possible, or clearly state them.
- **Progressive Disclosure**: Do not dump the entire repo into the skill. Only include the necessary wrapper code and reference the original repo for deep dives.
- **Idempotency**: The `github_hash` field allows the future `skill-manager` to check `if remote_hash != local_hash` to trigger updates.
