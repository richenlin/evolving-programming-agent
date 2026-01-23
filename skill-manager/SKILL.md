---
name: skill-manager
description: Lifecycle manager for GitHub-based skills. Use this to batch scan your skills directory, check for updates on GitHub, and perform guided upgrades of your skill wrappers.
license: MIT
---

# Skill Lifecycle Manager

This skill helps you maintain your library of GitHub-wrapped skills by automating the detection of updates and assisting in the refactoring process.

## Core Capabilities

1.  **Audit**: Scans your local skills folder for skills with `github_url` metadata.
2.  **Check**: Queries GitHub (via `git ls-remote`) to compare local commit hashes against the latest remote HEAD.
3.  **Report**: Generates a status report identifying which skills are "Stale" or "Current".
4.  **Update Workflow**: Provides a structured process for the Agent to upgrade a skill.
5.  **Inventory Management**: Lists all local skills and provides deletion capabilities.
6.  **Health Check**: Monitors skill health status, detects outdated and invalid skills.
7.  **Enable/Disable**: Temporarily enable or disable skills without deletion.

## Usage

**Existing Triggers**:
- `/skill-manager check` or "Scan my skills for updates"
- `/skill-manager list` or "List my skills"
- `/skill-manager delete <skill_name>` or "Delete skill <skill_name>"

**New Triggers**:
- `/skill-manager enable <skill_name>` or "Enable skill <skill_name>"
- `/skill-manager disable <skill_name>` or "Disable skill <skill_name>"
- `/skill-manager status` or "Check skill status"
- `/skill-manager health` or "Run health check"

### Workflow 1: Check for Updates

1.  **Run Scanner**: The agent runs `scripts/scan_and_check.py` to analyze all skills.
2.  **Review Report**: The script outputs a JSON summary. The Agent presents this to the user.
    *   Example: "Found 3 outdated skills: `yt-dlp` (behind 50 commits), `ffmpeg-tool` (behind 2 commits)..."

### Workflow 2: Update a Skill

**Trigger**: "Update [Skill Name]" (after a check)

1.  **Fetch New Context**: The agent fetches the *new* README from the remote repo.
2.  **Diff Analysis**:
    *   The agent compares the new README with the old `SKILL.md`.
    *   Identifies new features, deprecated flags, or usage changes.
3.  **Refactor**:
    *   The agent rewrites `SKILL.md` to reflect the new capabilities.
    *   The agent updates the `github_hash` in the frontmatter.
    *   The agent (optionally) attempts to update the `wrapper.py` if CLI args have changed.
4.  **Verify**: Runs a quick validation (if available).

### Workflow 3: Enable/Disable a Skill

**Trigger**: `/skill-manager enable <skill_name>` or `/skill-manager disable <skill_name>`

1.  **Disable**: Move skill directory to `.disabled/` subdirectory.
2.  **Enable**: Move skill directory from `.disabled/` back to main directory.
3.  The skill is not loaded while in `.disabled/` but can be re-enabled later.

### Workflow 4: Health Check

**Trigger**: `/skill-manager health` or "Run health check"

1.  **Run Scanner**: The agent runs `scripts/health_check.py` to analyze all skills.
2.  **Review Report**: The script outputs a table summary showing:
    *   ✅ Healthy skills (valid SKILL.md, up to date)
    *   ⚠️ Outdated skills (new commits available on GitHub)
    *   ❌ Invalid skills (missing SKILL.md)
3.  **Action**: Based on report, user can update or clean up problematic skills.

## Scripts

- `scripts/scan_and_check.py`: Scans directories, parses Frontmatter, fetches remote tags, returns status.
- `scripts/update_helper.py`: Helper to backup files before update.
- `scripts/list_skills.py`: Lists all installed skills with type and version.
- `scripts/delete_skill.py`: Permanently removes a skill folder.
- `scripts/health_check.py`: Health checker that validates skills and checks for updates.
- `scripts/toggle_skill.py`: Enable/disable skills by moving to/from `.disabled/` directory.
- `scripts/utils/frontmatter_parser.py`: Reusable utility for parsing YAML frontmatter.

## Metadata Requirements

This manager relies on the `github-to-skills` metadata standard:
- `github_url`: Source of truth.
- `github_hash`: State of truth.
