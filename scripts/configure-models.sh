#!/bin/bash
################################################################################
# Evolving Programming Agent - 子 Agent 模型配置器
#
# 修改已安装的 evolving-agent 中各子 agent 使用的模型。
# 仅修改已安装的副本，不修改源码仓库。
#
# 使用方法:
#   ./configure-models.sh                          # 交互式配置
#   ./configure-models.sh --all <model>            # 所有 agent 统一使用同一模型
#   ./configure-models.sh --agent coder <model>    # 仅修改指定 agent
#   ./configure-models.sh --agent reviewer <model> # 仅修改 reviewer
#   ./configure-models.sh --list                   # 查看当前各 agent 模型配置
#   ./configure-models.sh --help                   # 帮助
#
# 示例:
#   ./configure-models.sh --all anthropic/claude-sonnet-4-20250514
#   ./configure-models.sh --agent reviewer openrouter/anthropic/claude-sonnet-4
#   ./configure-models.sh --agent coder opencode/gpt-5.1-codex
################################################################################

set -euo pipefail

_SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
BOLD='\033[1m'
DIM='\033[2m'
NC='\033[0m'

AGENTS=("coder" "reviewer" "evolver" "retrieval")

OPENCODE_AGENTS_DIR="$HOME/.config/opencode/agents"
OPENCODE_SKILLS_DIR="$HOME/.config/opencode/skills/evolving-agent/agents"
CLAUDE_CODE_SKILLS_DIR="$HOME/.claude/skills/evolving-agent/agents"
CURSOR_SKILLS_DIR="$HOME/.agents/skills/evolving-agent/agents"
OPENCLAW_SKILLS_DIR="$HOME/.openclaw/skills/evolving-agent/agents"

info()    { echo -e "${BLUE}[INFO]${NC} $*"; }
success() { echo -e "${GREEN}[OK]${NC} $*"; }
warn()    { echo -e "${YELLOW}[WARN]${NC} $*"; }
error()   { echo -e "${RED}[ERROR]${NC} $*"; }

separator() { echo "════════════════════════════════════════════════════════════════════════"; }

read_model_from_file() {
    local file="$1"
    if [ -f "$file" ]; then
        # Extract model value from YAML frontmatter
        sed -n '/^---$/,/^---$/p' "$file" | grep '^model:' | head -1 | sed 's/^model:[[:space:]]*//'
    fi
}

update_model_in_file() {
    local file="$1"
    local new_model="$2"

    if [ ! -f "$file" ]; then
        return 1
    fi

    local old_model
    old_model=$(read_model_from_file "$file")

    if [ -z "$old_model" ]; then
        warn "  无法解析 model 字段: $file"
        return 1
    fi

    if [ "$old_model" = "$new_model" ]; then
        echo -e "  ${DIM}未变更${NC} $file ${DIM}(已是 $new_model)${NC}"
        return 0
    fi

    # Replace the model line in frontmatter
    if [[ "$(uname)" == "Darwin" ]]; then
        sed -i '' "s|^model:.*|model: ${new_model}|" "$file"
    else
        sed -i "s|^model:.*|model: ${new_model}|" "$file"
    fi

    echo -e "  ${GREEN}✓${NC} $file  ${DIM}${old_model}${NC} → ${CYAN}${new_model}${NC}"
    return 0
}

update_agent_model() {
    local agent_name="$1"
    local new_model="$2"
    local updated=0

    echo ""
    echo -e "${BOLD}  [$agent_name]${NC} → ${CYAN}${new_model}${NC}"

    # OpenCode native agents dir
    local oc_file="${OPENCODE_AGENTS_DIR}/${agent_name}.md"
    if [ -f "$oc_file" ]; then
        update_model_in_file "$oc_file" "$new_model" && ((updated++)) || true
    fi

    # All skills directories (OpenCode skills / Claude Code / Cursor / OpenClaw)
    local dirs=("$OPENCODE_SKILLS_DIR" "$CLAUDE_CODE_SKILLS_DIR" "$CURSOR_SKILLS_DIR" "$OPENCLAW_SKILLS_DIR")
    for dir in "${dirs[@]}"; do
        local skill_file="${dir}/${agent_name}.md"
        if [ -f "$skill_file" ]; then
            update_model_in_file "$skill_file" "$new_model" && ((updated++)) || true
        fi
    done

    if [ "$updated" -eq 0 ]; then
        warn "  未找到任何已安装的 ${agent_name}.md 文件（请先运行 install.sh）"
    fi
}

show_current_config() {
    separator
    echo -e "${BOLD}  当前子 Agent 模型配置（已安装）${NC}"
    separator
    echo ""

    printf "  ${BOLD}%-12s${NC}" "Agent"
    printf "  ${DIM}%-35s${NC}" "OpenCode agents/"
    printf "  ${DIM}%-35s${NC}" "OpenCode skills/"
    printf "  ${DIM}%-35s${NC}" "Claude Code"
    printf "  ${DIM}%-35s${NC}" "Cursor"
    printf "  ${DIM}%-35s${NC}" "OpenClaw"
    echo ""
    echo "  $(printf '─%.0s' {1..185})"

    for agent in "${AGENTS[@]}"; do
        printf "  ${BOLD}%-12s${NC}" "$agent"

        # OpenCode agents
        local oc="${OPENCODE_AGENTS_DIR}/${agent}.md"
        local m; m=$(read_model_from_file "$oc" 2>/dev/null || echo "—")
        printf "  %-35s" "$m"

        # OpenCode skills
        local os="${OPENCODE_SKILLS_DIR}/${agent}.md"
        m=$(read_model_from_file "$os" 2>/dev/null || echo "—")
        printf "  %-35s" "$m"

        # Claude Code
        local cc="${CLAUDE_CODE_SKILLS_DIR}/${agent}.md"
        m=$(read_model_from_file "$cc" 2>/dev/null || echo "—")
        printf "  %-35s" "$m"

        # Cursor
        local cu="${CURSOR_SKILLS_DIR}/${agent}.md"
        m=$(read_model_from_file "$cu" 2>/dev/null || echo "—")
        printf "  %-35s" "$m"

        # OpenClaw
        local cl="${OPENCLAW_SKILLS_DIR}/${agent}.md"
        m=$(read_model_from_file "$cl" 2>/dev/null || echo "—")
        printf "  %-35s" "$m"

        echo ""
    done
    echo ""
}

read_model_first_installed() {
    local agent="$1"
    local dirs=("$OPENCODE_AGENTS_DIR" "$OPENCODE_SKILLS_DIR" "$CLAUDE_CODE_SKILLS_DIR" "$CURSOR_SKILLS_DIR" "$OPENCLAW_SKILLS_DIR")
    for dir in "${dirs[@]}"; do
        local f="${dir}/${agent}.md"
        if [ -f "$f" ]; then
            read_model_from_file "$f"
            return
        fi
    done
    echo "未安装"
}

show_compact_config() {
    separator
    echo -e "${BOLD}  当前子 Agent 模型配置${NC}"
    separator
    echo ""

    for agent in "${AGENTS[@]}"; do
        local m; m=$(read_model_first_installed "$agent")
        printf "  ${BOLD}%-12s${NC} %s\n" "$agent" "$m"
    done

    echo ""
    echo -e "  ${DIM}（显示首个已安装位置的值，--list 查看所有平台详情）${NC}"
    echo ""
}

interactive_mode() {
    separator
    echo -e "${BOLD}  Evolving Agent — 子 Agent 模型配置${NC}"
    separator

    show_compact_config

    echo -e "  ${BOLD}选择操作:${NC}"
    echo "  1) 统一修改所有 agent 的模型"
    echo "  2) 逐个配置每个 agent 的模型"
    echo "  3) 修改单个 agent 的模型"
    echo "  4) 查看详细配置"
    echo "  5) 退出"
    separator
    read -p "  请选择 [1-5]: " choice

    case "$choice" in
        1)
            echo ""
            echo -e "  ${DIM}模型格式: provider/model-name (例: anthropic/claude-sonnet-4-20250514)${NC}"
            read -p "  输入模型名称: " model
            if [ -z "$model" ]; then
                error "模型名称不能为空"
                exit 1
            fi
            echo ""
            separator
            echo -e "${BOLD}  正在更新所有 agent → ${CYAN}${model}${NC}"
            separator
            for agent in "${AGENTS[@]}"; do
                update_agent_model "$agent" "$model"
            done
            ;;
        2)
            echo ""
            echo -e "  ${DIM}模型格式: provider/model-name (直接回车保持不变)${NC}"
            echo ""
            for agent in "${AGENTS[@]}"; do
                local current
                current=$(read_model_first_installed "$agent")
                read -p "  ${agent} [当前: ${current}]: " model
                if [ -n "$model" ]; then
                    update_agent_model "$agent" "$model"
                else
                    echo -e "  ${DIM}  跳过 ${agent}${NC}"
                fi
            done
            ;;
        3)
            echo ""
            echo -e "  可用 agent: ${BOLD}${AGENTS[*]}${NC}"
            read -p "  输入 agent 名称: " agent_name
            if [[ ! " ${AGENTS[*]} " =~ " ${agent_name} " ]]; then
                error "未知 agent: $agent_name (可选: ${AGENTS[*]})"
                exit 1
            fi
            local current
            current=$(read_model_first_installed "$agent_name")
            echo -e "  ${DIM}当前模型: ${current}${NC}"
            read -p "  输入新模型: " model
            if [ -z "$model" ]; then
                error "模型名称不能为空"
                exit 1
            fi
            separator
            echo -e "${BOLD}  正在更新${NC}"
            separator
            update_agent_model "$agent_name" "$model"
            ;;
        4)
            show_current_config
            exit 0
            ;;
        5)
            exit 0
            ;;
        *)
            error "无效选择"
            exit 1
            ;;
    esac

    echo ""
    separator
    success "配置完成！"
    separator
    show_compact_config

    echo -e "  ${DIM}提示: 如果使用 OpenCode，确保对应 provider 已在 opencode.json 中配置 API key。${NC}"
    echo -e "  ${DIM}      运行 opencode models 可查看当前可用模型列表。${NC}"
    echo ""
}

show_help() {
    cat << 'EOF'
Evolving Agent — 子 Agent 模型配置器

用法:
    configure-models.sh [选项]

选项:
    (无参数)                         交互式配置
    --all <model>                   所有 agent 统一使用指定模型
    --agent <name> <model>          修改指定 agent 的模型
    --list                          查看当前各 agent 模型配置（详细）
    --list-compact                  查看当前各 agent 模型配置（紧凑）
    --help                          显示帮助

Agent 名称:
    coder       代码执行器
    reviewer    代码审查器
    evolver     知识进化器
    retrieval   知识检索器

示例:
    # 所有 agent 使用同一模型
    ./configure-models.sh --all anthropic/claude-sonnet-4-20250514

    # reviewer 使用不同模型（更严格的审查）
    ./configure-models.sh --agent reviewer openrouter/anthropic/claude-sonnet-4

    # coder 使用快速模型
    ./configure-models.sh --agent coder opencode/gpt-5.1-codex

    # 查看配置
    ./configure-models.sh --list

更新范围:
    脚本修改所有已安装位置的 agent 文件（不修改源码仓库）:
    - OpenCode:      ~/.config/opencode/agents/*.md
    - OpenCode:      ~/.config/opencode/skills/evolving-agent/agents/*.md
    - Claude Code:   ~/.claude/skills/evolving-agent/agents/*.md
    - Cursor:        ~/.agents/skills/evolving-agent/agents/*.md
    - OpenClaw:      ~/.openclaw/skills/evolving-agent/agents/*.md

注意:
    - 修改后需确保对应 provider 的 API key 已配置
    - OpenCode: 在 opencode.json 中配置 provider，或通过 /connect 连接
    - Cursor/Claude Code: 模型由平台控制，agent 文件中的 model 字段仅供参考
EOF
}

main() {
    if [ $# -eq 0 ]; then
        interactive_mode
        exit 0
    fi

    case "$1" in
        --help|-h)
            show_help
            ;;
        --list)
            show_current_config
            ;;
        --list-compact)
            show_compact_config
            ;;
        --all)
            if [ -z "${2:-}" ]; then
                error "请指定模型: --all <model>"
                exit 1
            fi
            local model="$2"
            separator
            echo -e "${BOLD}  统一修改所有 agent → ${CYAN}${model}${NC}"
            separator
            for agent in "${AGENTS[@]}"; do
                update_agent_model "$agent" "$model"
            done
            echo ""
            separator
            success "配置完成！"
            separator
            show_compact_config
            ;;
        --agent)
            if [ -z "${2:-}" ] || [ -z "${3:-}" ]; then
                error "用法: --agent <name> <model>"
                exit 1
            fi
            local agent_name="$2"
            local model="$3"
            if [[ ! " ${AGENTS[*]} " =~ " ${agent_name} " ]]; then
                error "未知 agent: $agent_name (可选: ${AGENTS[*]})"
                exit 1
            fi
            separator
            echo -e "${BOLD}  修改 ${agent_name} 模型${NC}"
            separator
            update_agent_model "$agent_name" "$model"
            echo ""
            separator
            success "配置完成！"
            separator
            show_compact_config
            ;;
        *)
            error "未知选项: $1"
            echo ""
            show_help
            exit 1
            ;;
    esac
}

main "$@"
