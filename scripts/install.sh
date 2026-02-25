#!/bin/bash
################################################################################
# Evolving Programming Agent - 统一安装器
#
# 功能:
#   安装 evolving-agent 和 skill-manager 两个独立 skill
#   创建知识数据目录
#   支持 OpenCode / Claude Code (Cursor 自动共享)
#
# 使用方法:
#   ./install.sh --all                    # 安装所有 skill
#   ./install.sh --opencode             # 仅安装到 OpenCode
#   ./install.sh --claude-code          # 仅安装到 Claude Code (Cursor 也会使用)
#   ./install.sh --skills "skill1,skill2" # 指定要安装的 skill
#   ./install.sh --dry-run              # 预览模式
################################################################################

set -euo pipefail

################################################################################
# 配置常量
################################################################################

# 脚本所在目录和项目根目录
_SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${_SCRIPT_DIR}/.." && pwd)"
SCRIPT_NAME="$(basename "${BASH_SOURCE[0]}")"
VERSION="2.0.0"

# 技能列表 (新架构: 只有两个独立 skill)
declare -a ALL_SKILLS=(
    "evolving-agent"
    "skill-manager"
)

# 路径配置
OPENCODE_SKILLS_DIR="$HOME/.config/opencode/skills"
OPENCODE_COMMAND_DIR="$HOME/.config/opencode/command"
OPENCODE_KNOWLEDGE_DIR="$HOME/.config/opencode/knowledge"
OPENCODE_AGENTS_DIR="$HOME/.config/opencode/agents"   # OpenCode 原生 agent 目录
CLAUDE_CODE_SKILLS_DIR="$HOME/.claude/skills"
CLAUDE_CODE_KNOWLEDGE_DIR="$HOME/.claude/knowledge"
# Cursor 新版本会自动读取 ~/.claude/skills/，无需单独安装

# Agent 源目录（相对于 PROJECT_ROOT）
AGENTS_SRC_DIR="evolving-agent/agents"

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# sudo 确认状态（全局）
sudo_confirmed=false

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

# 检查是否需要 sudo 权限
needs_sudo() {
    local path="$1"
    
    # 如果路径不存在，检查父目录
    if [ ! -e "$path" ]; then
        local parent_dir=$(dirname "$path")
        if [ -d "$parent_dir" ] && [ ! -w "$parent_dir" ]; then
            return 0  # 需要 sudo
        fi
        return 1  # 不需要 sudo
    fi
    
    # 如果路径存在但不可写
    if [ ! -w "$path" ]; then
        return 0  # 需要 sudo
    fi
    
    # 检查目录内是否有不可写的文件
    if [ -d "$path" ]; then
        local non_writable=$(find "$path" -maxdepth 2 ! -writable 2>/dev/null | head -1)
        if [ -n "$non_writable" ]; then
            return 0  # 需要 sudo
        fi
    fi
    
    return 1  # 不需要 sudo
}

# 带 sudo 检测的命令执行
run_cmd() {
    local cmd="$1"
    local path="$2"
    
    if needs_sudo "$path"; then
        if [ "${sudo_confirmed:-false}" != "true" ]; then
            warn "检测到需要管理员权限来写入: $path"
            echo -e "${YELLOW}某些文件/目录需要 sudo 权限才能操作${NC}"
            read -p "是否使用 sudo 继续? [y/N]: " confirm
            if [[ "$confirm" =~ ^[Yy]$ ]]; then
                sudo_confirmed=true
                # 预先获取 sudo 权限
                sudo -v
            else
                error "用户取消，跳过需要 sudo 的操作"
                return 1
            fi
        fi
        eval "sudo $cmd"
    else
        eval "$cmd"
    fi
}

# 带 sudo 检测的目录创建
ensure_dir() {
    local dir="$1"
    if [ ! -d "$dir" ]; then
        run_cmd "mkdir -p '$dir'" "$dir"
    fi
}

# 带 sudo 检测的复制（使用 rsync 或 cp）
safe_copy() {
    local src="$1"
    local dst="$2"

    # 检查 rsync 是否可用
    if command -v rsync &> /dev/null; then
        # 使用 rsync（推荐，支持 --delete 清理旧文件）
        # 确保 src 以 / 结尾（rsync 要求）
        if [[ ! "$src" =~ /$ ]]; then
            src="${src}/"
        fi

        run_cmd "rsync -av --delete '$src' '$dst'" "$dst"
    else
        # Fallback: 使用 cp
        warn "rsync 不可用，使用 cp（可能无法完全清理旧文件）"

        # 先删除目标目录（如果有 sudo 权限）
        if [ -d "$dst" ]; then
            run_cmd "rm -rf '$dst'" "$dst"
        fi

        # 重新创建目标目录
        run_cmd "mkdir -p '$dst'" "$dst"

        # 复制源目录内容
        run_cmd "cp -r '$src'/* '$dst'/" "$dst"
    fi
}

################################################################################
# 安装函数
################################################################################

install_to_opencode() {
    local skill_name="$1"
    local src_dir="${PROJECT_ROOT}/${skill_name}"
    local dst_dir="${OPENCODE_SKILLS_DIR}/${skill_name}"

    if [ "${dry_run}" = true ]; then
        info "DRY-RUN: 将安装 ${skill_name} 到 OpenCode"
        return 0
    fi

    ensure_dir "${OPENCODE_SKILLS_DIR}" || return 1
    
    # 如果目标已存在，先删除
    if [ -e "${dst_dir}" ]; then
        run_cmd "rm -rf '$dst_dir'" "$dst_dir" || return 1
    fi
    
    safe_copy "${src_dir}" "${dst_dir}" || return 1
    success "已安装: ${skill_name} -> ${dst_dir}"
}

install_to_claude_code() {
    local skill_name="$1"
    local src_dir="${PROJECT_ROOT}/${skill_name}"
    local dst_dir="${CLAUDE_CODE_SKILLS_DIR}/${skill_name}"

    if [ "${dry_run}" = true ]; then
        info "DRY-RUN: 将安装 ${skill_name} 到 Claude Code"
        return 0
    fi

    ensure_dir "${CLAUDE_CODE_SKILLS_DIR}" || return 1
    
    # 如果目标已存在，先删除
    if [ -e "${dst_dir}" ]; then
        run_cmd "rm -rf '$dst_dir'" "$dst_dir" || return 1
    fi
    
    safe_copy "${src_dir}" "${dst_dir}" || return 1
    success "已安装: ${skill_name} -> ${dst_dir}"
}

# 安装 OpenCode 原生 Agent 文件
# OpenCode 支持 ~/.config/opencode/agents/ 目录，agent 文件直接放置于此
# Claude Code 无原生 agent 系统，agent 文件随 skill 一起复制，供 LLM 读取文档内容使用
install_opencode_agents() {
    local src_dir="${PROJECT_ROOT}/${AGENTS_SRC_DIR}"
    local dst_dir="${OPENCODE_AGENTS_DIR}"

    if [ "${dry_run}" = true ]; then
        info "DRY-RUN: 将安装 agent 文件到 OpenCode agents 目录: ${dst_dir}"
        if [ -d "${src_dir}" ]; then
            for agent_file in "${src_dir}"/*.md; do
                if [ -f "${agent_file}" ]; then
                    info "  DRY-RUN: ${agent_file} -> ${dst_dir}/$(basename "${agent_file}")"
                fi
            done
        fi
        return 0
    fi

    # 检查源目录是否存在
    if [ ! -d "${src_dir}" ]; then
        warn "Agent 目录不存在: ${src_dir}，跳过"
        return 0
    fi

    ensure_dir "${dst_dir}" || return 1

    local installed_count=0
    for agent_file in "${src_dir}"/*.md; do
        if [ -f "${agent_file}" ]; then
            local filename
            filename=$(basename "${agent_file}")
            run_cmd "cp '${agent_file}' '${dst_dir}/${filename}'" "${dst_dir}" || {
                warn "  复制 agent 文件失败: ${filename}"
                continue
            }
            success "  已安装 agent: ${filename} -> ${dst_dir}/"
            installed_count=$((installed_count + 1))
        fi
    done

    if [ "${installed_count}" -eq 0 ]; then
        warn "  未找到任何 agent 文件 (*.md) 在 ${src_dir}"
    else
        success "已安装 ${installed_count} 个 agent 文件到 OpenCode"
    fi
}

# 安装 OpenCode 命令文件
install_opencode_commands() {
    local src_dir="${PROJECT_ROOT}/evolving-agent/command"
    local dst_dir="${OPENCODE_COMMAND_DIR}"

    if [ "${dry_run}" = true ]; then
        info "DRY-RUN: 将安装命令文件到 ${dst_dir}"
        return 0
    fi

    # 检查源目录是否存在
    if [ ! -d "${src_dir}" ]; then
        warn "命令目录不存在: ${src_dir}"
        return 0
    fi

    ensure_dir "${dst_dir}" || return 1

    # 复制所有 .md 命令文件
    for cmd_file in "${src_dir}"/*.md; do
        if [ -f "${cmd_file}" ]; then
            local filename=$(basename "${cmd_file}")
            run_cmd "cp '${cmd_file}' '${dst_dir}/${filename}'" "${dst_dir}" || {
                warn "复制命令文件失败: ${filename}"
                continue
            }
            success "已安装命令: ${filename} -> ${dst_dir}/"
        fi
    done
}

# 创建知识数据目录
setup_knowledge_dir() {
    local knowledge_dir="$1"
    
    if [ "${dry_run}" = true ]; then
        info "DRY-RUN: 将创建知识库目录 ${knowledge_dir}"
        return 0
    fi
    
    ensure_dir "${knowledge_dir}" || return 1
    
    # 创建子目录结构
    local subdirs=("experiences" "tech-stacks" "scenarios" "problems" "testing" "patterns" "skills")
    for subdir in "${subdirs[@]}"; do
        ensure_dir "${knowledge_dir}/${subdir}" || return 1
    done
    
    # 创建空的 index.json
    local index_file="${knowledge_dir}/index.json"
    if [ ! -f "${index_file}" ]; then
        echo '{"version": "1.0", "last_updated": null, "entries": []}' > "${index_file}"
    fi
    
    success "知识库目录已创建: ${knowledge_dir}"
}

# 为 Python 脚本设置可执行权限
set_python_executable() {
    local skills_base_dir="$1"
    
    info "设置 Python 脚本可执行权限..."
    
    # 遍历所有已安装的 skill 目录
    for skill_name in "${ALL_SKILLS[@]}"; do
        local skill_dir="${skills_base_dir}/${skill_name}"
        
        if [ -d "${skill_dir}" ]; then
            # 查找所有 .py 文件并设置可执行权限
            local py_files=$(find "${skill_dir}" -name "*.py" -type f 2>/dev/null)
            if [ -n "${py_files}" ]; then
                while IFS= read -r py_file; do
                    run_cmd "chmod +x '${py_file}'" "${py_file}" || {
                        warn "  设置权限失败: ${py_file}"
                        continue
                    }
                done <<< "${py_files}"
                success "  ${skill_name}: Python 脚本已设置可执行权限"
            fi
        fi
    done
}

################################################################################
# Python 虚拟环境管理
# 注意：venv 只在 evolving-agent 目录创建
################################################################################

# 共享 venv 的 skill 名称
VENV_SKILL="evolving-agent"

# 设置共享的 Python 虚拟环境（只在 evolving-agent 目录创建）
setup_shared_venv() {
    local skills_base_dir="$1"
    local venv_dir="${skills_base_dir}/${VENV_SKILL}/.venv"
    
    info "设置共享 Python 虚拟环境: ${venv_dir}"
    
    # 检查 evolving-agent 目录是否存在
    if [ ! -d "${skills_base_dir}/${VENV_SKILL}" ]; then
        warn "  ${VENV_SKILL} 目录不存在，跳过 venv 设置"
        return 0
    fi
    
    # 创建虚拟环境（如果不存在）
    if [ ! -d "${venv_dir}" ]; then
        run_cmd "python3 -m venv '${venv_dir}'" "${venv_dir}" || {
            error "  创建虚拟环境失败"
            return 1
        }
        
        # 升级 pip 并安装依赖
        run_cmd "'${venv_dir}/bin/pip' install --upgrade pip -q" "${venv_dir}" || {
            warn "  pip 升级失败，继续安装依赖..."
        }
        
        run_cmd "'${venv_dir}/bin/pip' install 'PyYAML>=6.0,<7.0' -q" "${venv_dir}" || {
            error "  安装 PyYAML 失败"
            return 1
        }
    fi
    
    success "共享虚拟环境就绪: ${venv_dir}"
    return 0
}

################################################################################
# 主流程
################################################################################

show_help() {
    cat << EOF
Evolving Programming Agent - 统一安装器 v${VERSION}

用法:
    $SCRIPT_NAME [选项]

选项:
    --all                   安装所有 skill (推荐)
    --opencode              仅安装到 OpenCode
    --claude-code           仅安装到 Claude Code
    --skills <list>         指定要安装的 skill (逗号分隔)
    --dry-run               预览模式，不实际执行
    --help                  显示此帮助信息

示例:
    $SCRIPT_NAME --all
    $SCRIPT_NAME --opencode
    $SCRIPT_NAME --dry-run --all

安装路径:
    OpenCode Skills:     ${OPENCODE_SKILLS_DIR}
    OpenCode Commands:   ${OPENCODE_COMMAND_DIR}
    OpenCode Knowledge:  ${OPENCODE_KNOWLEDGE_DIR}
    OpenCode Agents:     ${OPENCODE_AGENTS_DIR}
    Claude Code Skills:  ${CLAUDE_CODE_SKILLS_DIR}
    Claude Knowledge:    ${CLAUDE_CODE_KNOWLEDGE_DIR}

说明:
    - Cursor 和 Claude Code 共享相同的 skills 目录 (~/.claude/skills/)
    - 安装到 Claude Code 后，Cursor 会自动识别这些 skills
    - OpenCode 安装时会同时安装命令文件 (如 /evolve) 和 agent 文件
    - Claude Code 无原生 agent 系统，agent 文件随 skill 一起复制供 LLM 读取
    - 知识数据存储在独立目录，与 skill 代码分离

架构说明 (v5.0):
    evolving-agent/         核心 skill，包含以下内部模块:
    ├── agents/              多 agent 角色定义 (orchestrator/coder/reviewer/evolver/retrieval)
    ├── modules/programming-assistant/    编程助手模块
    ├── modules/github-to-skills/        GitHub 学习模块
    ├── modules/knowledge-base/          知识库模块
    └── scripts/                         所有脚本
    
    skill-manager/          独立 skill，管理 skill 生命周期

多 Agent 模型配置:
    orchestrator: zai-coding-plan/glm-5    (任务调度)
    coder:        zai-coding-plan/glm-5    (代码执行)
    reviewer:     openrouter/anthropic/claude-sonnet-4.6  (代码审查)
    evolver:      zai-coding-plan/glm-5    (知识进化)
    retrieval:    zai-coding-plan/glm-5    (知识检索)

Python 虚拟环境:
    安装器会在 evolving-agent 目录创建共享的虚拟环境:
    - 虚拟环境位置: {skills_dir}/evolving-agent/.venv/
    - 自动安装依赖: PyYAML>=6.0,<7.0

更多信息: https://github.com/Khazix-Skills/evolving-programming-agent
EOF
}

main() {
    local install_opencode=false
    local install_claude_code=false
    local skills_to_install=("${ALL_SKILLS[@]}")
    local dry_run=false

    while [[ $# -gt 0 ]]; do
        case $1 in
            --all)
                install_opencode=true
                install_claude_code=true
                shift
                ;;
            --opencode)
                install_opencode=true
                shift
                ;;
            --claude-code)
                install_claude_code=true
                shift
                ;;
            --skills)
                shift
                IFS=',' read -ra skills_to_install <<< "$1"
                shift
                ;;
            --dry-run)
                dry_run=true
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
    if [ "$install_opencode" = false ] && [ "$install_claude_code" = false ]; then
        separator
        info "选择要安装的平台:"
        info "1) OpenCode"
        info "2) Claude Code (Cursor 也会自动使用这些 skills)"
        info "3) 全部安装"
        separator
        read -p "请选择 [1-3]: " choice
        case $choice in
            1) install_opencode=true ;;
            2) install_claude_code=true ;;
            3)
                install_opencode=true
                install_claude_code=true
                ;;
            *)
                error "无效选择"
                exit 1
                ;;
        esac
    fi

    if [ "${dry_run}" = true ]; then
        warn "DRY-RUN 模式：不会实际执行任何操作"
    fi

    separator
    info "开始安装 skill 组件..."
    info "架构: evolving-agent (核心) + skill-manager (独立)"
    separator

    # 遍历要安装的 skill
    for skill_name in "${skills_to_install[@]}"; do
        # Trim whitespace
        skill_name=$(echo "$skill_name" | xargs)

        info "处理: ${skill_name}"

        if [ ! -d "${PROJECT_ROOT}/${skill_name}" ]; then
            warn "跳过 ${skill_name} (目录不存在)"
            continue
        fi

        # 安装到各个平台
        if [ "$install_opencode" = true ]; then
            install_to_opencode "$skill_name"
        fi

        if [ "$install_claude_code" = true ]; then
            install_to_claude_code "$skill_name"
        fi
    done

    # 安装 OpenCode 命令文件
    if [ "$install_opencode" = true ]; then
        separator
        info "安装 OpenCode 命令文件..."
        install_opencode_commands
    fi

    # 安装 OpenCode Agent 文件（仅 OpenCode 支持原生 agent 系统）
    if [ "$install_opencode" = true ]; then
        separator
        info "安装 OpenCode Agent 文件..."
        info "  (Claude Code 无原生 agent 系统，agent 文件已随 skill 一起复制)"
        install_opencode_agents
    fi

    # 创建知识数据目录
    separator
    info "创建知识数据目录..."
    if [ "$install_opencode" = true ]; then
        setup_knowledge_dir "${OPENCODE_KNOWLEDGE_DIR}"
    fi
    if [ "$install_claude_code" = true ]; then
        setup_knowledge_dir "${CLAUDE_CODE_KNOWLEDGE_DIR}"
    fi

    # 设置共享虚拟环境
    if [ "${dry_run}" = true ]; then
        separator
        if [ "$install_opencode" = true ]; then
            info "DRY-RUN: 将在 ${OPENCODE_SKILLS_DIR}/${VENV_SKILL}/ 创建共享虚拟环境"
        fi
        if [ "$install_claude_code" = true ]; then
            info "DRY-RUN: 将在 ${CLAUDE_CODE_SKILLS_DIR}/${VENV_SKILL}/ 创建共享虚拟环境"
        fi
    else
        separator
        if [ "$install_opencode" = true ]; then
            setup_shared_venv "${OPENCODE_SKILLS_DIR}" || warn "OpenCode 虚拟环境设置失败"
        fi
        if [ "$install_claude_code" = true ]; then
            setup_shared_venv "${CLAUDE_CODE_SKILLS_DIR}" || warn "Claude Code 虚拟环境设置失败"
        fi
    fi

    # 设置 Python 脚本可执行权限
    if [ "${dry_run}" = true ]; then
        separator
        info "DRY-RUN: 将为 .py 文件设置可执行权限"
    else
        separator
        if [ "$install_opencode" = true ]; then
            set_python_executable "${OPENCODE_SKILLS_DIR}"
        fi
        if [ "$install_claude_code" = true ]; then
            set_python_executable "${CLAUDE_CODE_SKILLS_DIR}"
        fi
    fi

    separator
    success "安装完成！"
    separator

    if [ "$dry_run" = false ]; then
        info "建议重启相应的 IDE/CLI 以使更改生效"
        if [ "$install_opencode" = true ]; then
            info "  - OpenCode agent 文件已安装到: ${OPENCODE_AGENTS_DIR}/"
            info "    (orchestrator/coder/reviewer/evolver/retrieval)"
        fi
        if [ "$install_claude_code" = true ]; then
            info "  - Claude Code 和 Cursor 都会自动识别新安装的 skills"
            info "  - Claude Code 使用角色切换模拟多 agent 流程（agent 文件在 skill 目录内）"
        fi
        info "  - 共享虚拟环境位于: {skills_dir}/${VENV_SKILL}/.venv/"
        info "  - 知识数据目录: {platform_dir}/knowledge/"
    fi
}

# 执行主函数
main "$@"
