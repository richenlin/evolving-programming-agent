#!/bin/bash
################################################################################
# Evolving Programming Agent - 卸载器
#
# 功能:
#   卸载 skill 组件
#   可选: 删除知识数据
#
# 使用方法:
#   ./uninstall.sh --all                    # 从所有平台卸载
#   ./uninstall.sh --opencode             # 仅从 OpenCode 卸载
#   ./uninstall.sh --claude-code          # 仅从 Claude Code 卸载
#   ./uninstall.sh --with-data            # 同时删除知识数据
#   ./uninstall.sh --dry-run              # 预览模式
################################################################################

set -euo pipefail

################################################################################
# 配置常量
################################################################################

SCRIPT_NAME="$(basename "${BASH_SOURCE[0]}")"
VERSION="2.0.0"

# 技能列表
declare -a ALL_SKILLS=(
    "evolving-agent"
)

# 共享 venv 所在的 skill
VENV_SKILL="evolving-agent"

# 路径配置
OPENCODE_SKILLS_DIR="$HOME/.config/opencode/skills"
OPENCODE_COMMAND_DIR="$HOME/.config/opencode/command"
OPENCODE_KNOWLEDGE_DIR="$HOME/.config/opencode/knowledge"
OPENCODE_AGENTS_DIR="$HOME/.config/opencode/agents"   # OpenCode 原生 agent 目录
CLAUDE_CODE_SKILLS_DIR="$HOME/.claude/skills"
CLAUDE_CODE_KNOWLEDGE_DIR="$HOME/.claude/knowledge"

# 本项目安装的 agent 文件列表（与 evolving-agent/agents/ 保持同步）
declare -a AGENT_FILES=(
    "orchestrator.md"
    "coder.md"
    "reviewer.md"
    "evolver.md"
    "retrieval.md"
)

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

################################################################################
# 辅助函数
################################################################################

info() {
    echo -e "${BLUE}[INFO]${NC} $*"
}

success() {
    echo -e "${GREEN}[SUCCESS]${NC} $*"
}

warn() {
    echo -e "${YELLOW}[WARN]${NC} $*"
}

error() {
    echo -e "${RED}[ERROR]${NC} $*"
}

separator() {
    echo "========================================================================"
}

################################################################################
# 卸载函数
################################################################################

uninstall_from_opencode() {
    local skill_name="$1"
    local skill_dir="${OPENCODE_SKILLS_DIR}/${skill_name}"

    if [ ! -d "${skill_dir}" ]; then
        info "OpenCode: ${skill_name} 未安装，跳过"
        return 0
    fi

    if [ "${DRY_RUN}" = true ]; then
        info "DRY-RUN: 将从 OpenCode 卸载 ${skill_name}"
        if [ "${skill_name}" = "${VENV_SKILL}" ] && [ -d "${skill_dir}/.venv" ]; then
            info "DRY-RUN:   将清理共享虚拟环境: ${skill_dir}/.venv"
        fi
        return 0
    fi

    if [ "${skill_name}" = "${VENV_SKILL}" ] && [ -d "${skill_dir}/.venv" ]; then
        info "  清理共享虚拟环境: ${skill_dir}/.venv"
    fi

    rm -rf "${skill_dir}"
    success "已卸载 (OpenCode): ${skill_name}"
}

uninstall_from_claude_code() {
    local skill_name="$1"
    local skill_dir="${CLAUDE_CODE_SKILLS_DIR}/${skill_name}"

    if [ ! -d "${skill_dir}" ]; then
        info "Claude Code: ${skill_name} 未安装，跳过"
        return 0
    fi

    if [ "${DRY_RUN}" = true ]; then
        info "DRY-RUN: 将从 Claude Code 卸载 ${skill_name}"
        if [ "${skill_name}" = "${VENV_SKILL}" ] && [ -d "${skill_dir}/.venv" ]; then
            info "DRY-RUN:   将清理共享虚拟环境: ${skill_dir}/.venv"
        fi
        return 0
    fi

    if [ "${skill_name}" = "${VENV_SKILL}" ] && [ -d "${skill_dir}/.venv" ]; then
        info "  清理共享虚拟环境: ${skill_dir}/.venv"
    fi

    rm -rf "${skill_dir}"
    success "已卸载 (Claude Code): ${skill_name}"
}

uninstall_opencode_agents() {
    local agents_dir="${OPENCODE_AGENTS_DIR}"

    if [ "${DRY_RUN}" = true ]; then
        for agent_file in "${AGENT_FILES[@]}"; do
            if [ -f "${agents_dir}/${agent_file}" ]; then
                info "DRY-RUN: 将删除 agent 文件 ${agents_dir}/${agent_file}"
            fi
        done
        return 0
    fi

    local removed_count=0
    for agent_file in "${AGENT_FILES[@]}"; do
        local target="${agents_dir}/${agent_file}"
        if [ -f "${target}" ]; then
            rm -f "${target}"
            success "  已删除 agent: ${agent_file}"
            removed_count=$((removed_count + 1))
        fi
    done

    if [ "${removed_count}" -eq 0 ]; then
        info "OpenCode agent 文件未安装，跳过"
    else
        success "已删除 ${removed_count} 个 OpenCode agent 文件"
    fi
}

uninstall_opencode_commands() {
    local cmd_dir="${OPENCODE_COMMAND_DIR}"

    if [ "${DRY_RUN}" = true ]; then
        if [ -f "${cmd_dir}/evolve.md" ]; then
            info "DRY-RUN: 将删除命令文件 ${cmd_dir}/evolve.md"
        fi
        return 0
    fi

    if [ -f "${cmd_dir}/evolve.md" ]; then
        rm -f "${cmd_dir}/evolve.md"
        success "已删除命令: evolve.md"
    fi
}

delete_knowledge_data() {
    local knowledge_dir="$1"
    local platform="$2"

    if [ ! -d "${knowledge_dir}" ]; then
        info "${platform} 知识数据目录不存在，跳过"
        return 0
    fi

    if [ "${DRY_RUN}" = true ]; then
        info "DRY-RUN: 将删除 ${platform} 知识数据: ${knowledge_dir}"
        return 0
    fi

    warn "即将删除 ${platform} 知识数据: ${knowledge_dir}"
    read -p "确认删除? [y/N]: " confirm
    if [[ "$confirm" =~ ^[Yy]$ ]]; then
        rm -rf "${knowledge_dir}"
        success "已删除: ${knowledge_dir}"
    else
        info "跳过删除知识数据"
    fi
}

################################################################################
# 主流程
################################################################################

show_help() {
    cat << EOF
Evolving Programming Agent - 卸载器 v${VERSION}

用法:
    $SCRIPT_NAME [选项]

选项:
    --all                   从所有平台卸载
    --opencode              仅从 OpenCode 卸载
    --claude-code           仅从 Claude Code 卸载
    --with-data             同时删除知识数据 (需确认)
    --dry-run               预览模式，不实际执行
    --help                  显示此帮助信息

示例:
    $SCRIPT_NAME --all
    $SCRIPT_NAME --opencode --with-data
    $SCRIPT_NAME --dry-run --all

卸载路径:
    OpenCode Skills:    ${OPENCODE_SKILLS_DIR}
    OpenCode Commands:  ${OPENCODE_COMMAND_DIR}
    OpenCode Agents:    ${OPENCODE_AGENTS_DIR}
    Claude Code Skills: ${CLAUDE_CODE_SKILLS_DIR}

知识数据路径:
    OpenCode:    ${OPENCODE_KNOWLEDGE_DIR}
    Claude Code: ${CLAUDE_CODE_KNOWLEDGE_DIR}

说明:
    - 卸载时会删除 skill 目录
    - 默认不删除知识数据，使用 --with-data 可同时删除

更多信息: https://github.com/Khazix-Skills/evolving-programming-agent
EOF
}

main() {
    local uninstall_opencode=false
    local uninstall_claude_code=false
    local with_data=false
    local DRY_RUN=false

    while [[ $# -gt 0 ]]; do
        case $1 in
            --all)
                uninstall_opencode=true
                uninstall_claude_code=true
                shift
                ;;
            --opencode)
                uninstall_opencode=true
                shift
                ;;
            --claude-code)
                uninstall_claude_code=true
                shift
                ;;
            --with-data)
                with_data=true
                shift
                ;;
            --dry-run)
                DRY_RUN=true
                shift
                ;;
            --help|-h)
                show_help
                exit 0
                ;;
            *)
                error "未知选项: $1"
                show_help
                exit 1
                ;;
        esac
    done

    # 如果没有指定平台，询问用户
    if [ "$uninstall_opencode" = false ] && [ "$uninstall_claude_code" = false ]; then
        separator
        info "选择要卸载的平台:"
        info "1) OpenCode"
        info "2) Claude Code"
        info "3) 全部卸载"
        separator
        read -p "请选择 [1-3]: " choice
        case $choice in
            1) uninstall_opencode=true ;;
            2) uninstall_claude_code=true ;;
            3)
                uninstall_opencode=true
                uninstall_claude_code=true
                ;;
            *)
                error "无效选择"
                exit 1
                ;;
        esac
    fi

    if [ "${DRY_RUN}" = true ]; then
        warn "DRY-RUN 模式：不会实际执行任何操作"
    fi

    separator
    info "开始卸载 skill 组件..."
    separator

    # 遍历要卸载的 skill
    for skill_name in "${ALL_SKILLS[@]}"; do
        info "处理: ${skill_name}"

        if [ "$uninstall_opencode" = true ]; then
            uninstall_from_opencode "$skill_name"
        fi

        if [ "$uninstall_claude_code" = true ]; then
            uninstall_from_claude_code "$skill_name"
        fi
    done

    # 卸载 OpenCode 命令文件
    if [ "$uninstall_opencode" = true ]; then
        separator
        info "卸载 OpenCode 命令文件..."
        uninstall_opencode_commands
    fi

    # 卸载 OpenCode Agent 文件
    if [ "$uninstall_opencode" = true ]; then
        separator
        info "卸载 OpenCode Agent 文件..."
        uninstall_opencode_agents
    fi

    # 删除知识数据
    if [ "$with_data" = true ]; then
        separator
        warn "正在删除知识数据..."
        if [ "$uninstall_opencode" = true ]; then
            delete_knowledge_data "${OPENCODE_KNOWLEDGE_DIR}" "OpenCode"
        fi
        if [ "$uninstall_claude_code" = true ]; then
            delete_knowledge_data "${CLAUDE_CODE_KNOWLEDGE_DIR}" "Claude Code"
        fi
    fi

    separator
    success "卸载完成！"
    separator

    if [ "${DRY_RUN}" = false ] && [ "$with_data" = false ]; then
        info "知识数据已保留，如需删除请使用 --with-data 选项"
    fi
}

# 执行主函数
main "$@"
