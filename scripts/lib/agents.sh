#!/bin/bash
# Shared OpenCode agent file lists for install/uninstall.
# Keep in sync with evolving-agent/agents/

# Currently shipped sub-agents
OPENCODE_AGENT_FILES=(
    "coder.md"
    "reviewer.md"
)

# Deprecated basenames removed on install upgrade / uninstall (pre-CodeGraph agents)
DEPRECATED_OPENCODE_AGENT_FILES=(
    "orchestrator.md"
    "evolver.md"
    "retrieval.md"
)

# All agent basenames this project may have placed under ~/.config/opencode/agents/
opencode_agent_cleanup_list() {
    local -n _out=$1
    _out=("${OPENCODE_AGENT_FILES[@]}" "${DEPRECATED_OPENCODE_AGENT_FILES[@]}")
}

# Remove deprecated agent files from older installs. Prints count removed to stdout.
purge_deprecated_opencode_agents() {
    local agents_dir="$1"
    local dry_run="${2:-false}"
    local removed=0

    for agent_file in "${DEPRECATED_OPENCODE_AGENT_FILES[@]}"; do
        local target="${agents_dir}/${agent_file}"
        if [ ! -f "${target}" ]; then
            continue
        fi
        if [ "${dry_run}" = true ]; then
            removed=$((removed + 1))
        else
            rm -f "${target}"
            removed=$((removed + 1))
        fi
    done

    echo "${removed}"
}
