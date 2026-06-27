#!/bin/bash
################################################################################
# 为所有已安装平台的 evolving-agent 链接共享 Python 运行时
#
# 用法:
#   ./scripts/setup_venv.sh
#   ./scripts/setup_venv.sh --china
#   EVOLVE_USE_CN_MIRROR=1 ./scripts/setup_venv.sh
################################################################################

set -euo pipefail

_SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${_SCRIPT_DIR}/.." && pwd)"
# shellcheck source=lib/mirrors.sh
source "${_SCRIPT_DIR}/lib/mirrors.sh"
# shellcheck source=lib/shared-runtime.sh
source "${_SCRIPT_DIR}/lib/shared-runtime.sh"

DEFAULT_LOCAL_EMBED_MODEL="${DEFAULT_LOCAL_EMBED_MODEL:-BAAI/bge-small-zh-v1.5}"
dry_run=false

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

info() { echo -e "${BLUE}[INFO]${NC} $*"; }
success() { echo -e "${GREEN}[SUCCESS]${NC} $*"; }
warn() { echo -e "${YELLOW}[WARN]${NC} $*"; }
error() { echo -e "${RED}[ERROR]${NC} $*"; }

separator() { echo "========================================================================"; }

main() {
    if [ "${EVOLVE_USE_CN_MIRROR:-}" = "1" ]; then
        apply_china_mirrors
    fi

    while [[ $# -gt 0 ]]; do
        case $1 in
            --china) apply_china_mirrors; shift ;;
            --mirror)
                shift
                PIP_INDEX_URL="${1:?}"
                export PIP_INDEX_URL
                shift
                ;;
            --dry-run) dry_run=true; shift ;;
            --help|-h)
                echo "用法: $0 [--china] [--dry-run]"
                exit 0
                ;;
            *) error "未知选项: $1"; exit 1 ;;
        esac
    done

    export_mirror_env
    separator
    info "链接共享 Python 运行时（多平台）"
    separator

    ensure_shared_runtime || { error "共享运行时设置失败"; exit 1; }
    link_all_installed_platform_venvs
    cleanup_old_resources

    separator
    success "完成！各平台 .venv 已指向 ${SHARED_VENV}"
    show_shared_runtime_status
}

main "$@"
