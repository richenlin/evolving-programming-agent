#!/bin/bash
################################################################################
# Evolving Programming Agent - 一键安装（无需 git clone）
#
# 功能:
#   从 GitHub 下载源码包 → 调用 install.sh 安装 → 自动清理临时目录
#
# 使用方法:
#   ./onekey.sh --cursor --china              # Cursor + 国内镜像
#   ./onekey.sh --all --china                 # 全部平台
#   ./onekey.sh --version v1.1.1 --cursor     # 指定 release tag
#   ./onekey.sh --ref main --cursor           # 指定分支
#
# 远程一行命令（无需克隆仓库）:
#   curl -fsSL https://raw.githubusercontent.com/richenlin/evolving-programming-agent/main/scripts/onekey.sh | bash -s -- --cursor --china
#
# install.sh 支持的参数均可透传（--all / --opencode / --china / --dry-run 等）
################################################################################

set -euo pipefail

_SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SCRIPT_NAME="$(basename "${BASH_SOURCE[0]}")"
VERSION="1.0.0"

DEFAULT_REPO="richenlin/evolving-programming-agent"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

info() { echo -e "${BLUE}[INFO]${NC} $*" >&2; }
success() { echo -e "${GREEN}[SUCCESS]${NC} $*" >&2; }
warn() { echo -e "${YELLOW}[WARN]${NC} $*" >&2; }
error() { echo -e "${RED}[ERROR]${NC} $*" >&2; }
separator() { echo "========================================================================" >&2; }

repo="${DEFAULT_REPO}"
tag=""
ref=""
keep=false
use_local=false
workdir=""
project_root=""
install_args=()

show_help() {
    cat << EOF
Evolving Programming Agent - 一键安装器 v${VERSION}

用法:
    ${SCRIPT_NAME} [onekey 选项] [install.sh 选项]

onekey 选项:
    --version <tag>         下载指定 release tag（如 v1.1.1）
    --ref <branch>          下载指定分支（如 main），与 --version 互斥
    --repo <owner/name>     GitHub 仓库（默认: ${DEFAULT_REPO}）
    --local                 跳过下载，使用本脚本所在仓库（开发用）
    --keep                  安装后保留临时目录（调试用）
    --help, -h              显示此帮助

install.sh 选项（透传）:
    --all                   安装到全部平台
    --opencode              仅 OpenCode
    --claude-code           仅 Claude Code
    --cursor                仅 Cursor (~/.agents/skills/)
    --openclaw              仅 OpenClaw
    --hermes                仅 Hermes Agent
    --skills <list>         指定 skill（逗号分隔）
    --china                 国内镜像（PyPI + HF + BGE 预下载）
    --mirror <url>          自定义 PyPI 镜像
    --dry-run               预览，不实际安装
    --status                显示共享运行时状态
    --migrate-shared        迁移/链接共享运行时
    更多选项见: install.sh --help

示例:
    ${SCRIPT_NAME} --cursor --china
    ${SCRIPT_NAME} --version v1.1.1 --all --china
    ${SCRIPT_NAME} --ref main --cursor --dry-run

远程安装:
    curl -fsSL https://raw.githubusercontent.com/${DEFAULT_REPO}/main/scripts/onekey.sh | bash -s -- --cursor --china
EOF
}

parse_args() {
    while [[ $# -gt 0 ]]; do
        case $1 in
            --version)
                shift
                if [ -z "${1:-}" ]; then
                    error "请提供 --version 的 tag，例如: --version v1.1.1"
                    exit 1
                fi
                tag="$1"
                shift
                ;;
            --ref)
                shift
                if [ -z "${1:-}" ]; then
                    error "请提供 --ref 的分支名，例如: --ref main"
                    exit 1
                fi
                ref="$1"
                shift
                ;;
            --repo)
                shift
                if [ -z "${1:-}" ]; then
                    error "请提供 --repo，例如: --repo owner/name"
                    exit 1
                fi
                repo="$1"
                shift
                ;;
            --local)
                use_local=true
                shift
                ;;
            --keep)
                keep=true
                shift
                ;;
            --help|-h)
                show_help
                exit 0
                ;;
            *)
                install_args+=("$1")
                shift
                ;;
        esac
    done

    if [ -n "$tag" ] && [ -n "$ref" ]; then
        error "--version 与 --ref 不能同时使用"
        exit 1
    fi
}

fetch_latest_tag() {
  local from_gh="" fetched=""

    if command -v gh >/dev/null 2>&1; then
        from_gh=$(gh release view -R "${repo}" --json tagName -q .tagName 2>/dev/null || true)
        if [ -n "${from_gh}" ]; then
            echo "${from_gh}"
            return 0
        fi
    fi

    fetched=$(curl -fsSL "https://api.github.com/repos/${repo}/releases/latest" 2>/dev/null \
        | sed -n 's/.*"tag_name"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/p' | head -1 || true)
    if [ -n "${fetched}" ]; then
        echo "${fetched}"
        return 0
    fi

    return 1
}

resolve_download_url() {
    if [ -n "$ref" ]; then
        echo "https://github.com/${repo}/archive/refs/heads/${ref}.tar.gz"
        return 0
    fi

    local resolved_tag="${tag}"
    if [ -z "${resolved_tag}" ]; then
        resolved_tag=$(fetch_latest_tag) || {
            error "无法获取最新 release tag，请显式指定 --version <tag> 或 --ref <branch>"
            exit 1
        }
        info "使用最新 release: ${resolved_tag}"
    fi

    echo "https://github.com/${repo}/archive/refs/tags/${resolved_tag}.tar.gz"
}

cleanup_workdir() {
    if [ "${keep}" = true ]; then
        if [ -n "${workdir}" ] && [ -d "${workdir}" ]; then
            info "保留临时目录: ${workdir}"
        fi
        trap - EXIT
        return 0
    fi

    if [ -n "${workdir}" ] && [ -d "${workdir}" ]; then
        rm -rf "${workdir}"
    fi
}

find_extracted_root() {
    local base="$1"
    local count
    count=$(find "${base}" -mindepth 1 -maxdepth 1 -type d 2>/dev/null | wc -l | tr -d ' ')
    if [ "${count}" -ne 1 ]; then
        error "解压后未找到单一根目录（${base}）"
        exit 1
    fi
    find "${base}" -mindepth 1 -maxdepth 1 -type d | head -1
}

download_source() {
    local url extracted_root
    url=$(resolve_download_url)

    workdir=$(mktemp -d "${TMPDIR:-/tmp}/evolving-agent-onekey.XXXXXX")

    separator
    info "下载源码包..."
    info "  URL: ${url}"
    info "  临时目录: ${workdir}"
    separator

    if ! curl -fsSL "${url}" | tar -xz -C "${workdir}"; then
        error "下载或解压失败"
        exit 1
    fi

    extracted_root=$(find_extracted_root "${workdir}")
    project_root="${extracted_root}"
    success "源码包已就绪: ${project_root}"
}

resolve_project_root() {
    if [ "${use_local}" = true ]; then
        project_root="$(cd "${_SCRIPT_DIR}/.." && pwd)"
        if [ ! -f "${project_root}/scripts/install.sh" ] || [ ! -d "${project_root}/evolving-agent" ]; then
            error "--local 需要在本仓库内运行（缺少 scripts/install.sh 或 evolving-agent/）"
            exit 1
        fi
        info "使用本地仓库: ${project_root}"
        return 0
    fi

    download_source
}

main() {
    parse_args "$@"

    if [ "${use_local}" = false ]; then
        trap cleanup_workdir EXIT
    fi

    resolve_project_root

    local install_sh="${project_root}/scripts/install.sh"
    if [ ! -x "${install_sh}" ] && [ ! -f "${install_sh}" ]; then
        error "未找到 install.sh: ${install_sh}"
        exit 1
    fi

    separator
    info "执行安装..."
    separator

  # shellcheck disable=SC2068
    bash "${install_sh}" "${install_args[@]}"
    install_status=$?

    if [ "${install_status}" -ne 0 ]; then
        error "install.sh 退出码: ${install_status}"
        exit "${install_status}"
    fi

    separator
    success "一键安装完成"
    if [ "${use_local}" = false ]; then
        info "即将清理临时目录..."
    fi
    separator
}

main "$@"
