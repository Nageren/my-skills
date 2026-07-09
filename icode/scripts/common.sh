#!/bin/bash
# common.sh - icode 公共函数库
# 被其他脚本 source 引用

# ========== 颜色定义 ==========
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# ========== 日志函数 ==========
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_step() {
    echo -e "${BLUE}[STEP]${NC} $1"
}

log_phase() {
    echo -e "${CYAN}[PHASE]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

# ========== icode-cli 检测 ==========
get_icode_cli() {
    if command -v icode-cli &> /dev/null; then
        echo "icode-cli"
    elif [ -x "$HOME/.icode/bin/icode-cli" ]; then
        echo "$HOME/.icode/bin/icode-cli"
    else
        log_error "icode-cli 未找到，请先安装"
        log_error "安装命令: curl -fsSL http://icode-cli.bj.bcebos.com/install.sh | bash -s -- --no-skills"
        exit 1
    fi
}

# ========== Git 仓库检测 ==========
check_git_repo() {
    if ! git rev-parse --is-inside-work-tree &> /dev/null; then
        log_error "当前目录不是 git 仓库"
        exit 1
    fi
}

# ========== 登录状态检测 ==========
# 返回用户名，失败则退出
check_login() {
    local cli=$1
    log_step "检查登录状态..."

    local login_output
    login_output=$("$cli" login 2>&1)

    if echo "$login_output" | grep -q "Not logged in"; then
        log_error "未登录，请先完成认证"
        echo "$login_output"
        exit 1
    fi

    local username
    # 匹配 "Already logged in as: username (method)" 或 "Logged in as: username (method)" 格式
    username=$(echo "$login_output" | grep -oE 'logged in as: [^ ]+' | sed 's/logged in as: //')

    if [ -z "$username" ]; then
        log_error "无法获取用户名"
        exit 1
    fi

    log_info "当前用户: $username"
    echo "$username"
}

# ========== 获取仓库名 ==========
get_repo_name() {
    local remote_url
    remote_url=$(git remote get-url origin 2>/dev/null)

    if [ -z "$remote_url" ]; then
        log_error "无法获取 origin 远程地址"
        exit 1
    fi

    local repo_name=""
    if [[ "$remote_url" == ssh://* ]]; then
        repo_name=$(echo "$remote_url" | sed -E 's|ssh://[^/]+/||')
    elif [[ "$remote_url" == git@* ]]; then
        repo_name=$(echo "$remote_url" | sed -E 's|git@[^:]+:||')
    elif [[ "$remote_url" == http* ]]; then
        repo_name=$(echo "$remote_url" | sed -E 's|https?://[^/]+/||')
    else
        log_error "无法解析远程 URL: $remote_url"
        exit 1
    fi

    echo "${repo_name%.git}"
}

# ========== 获取当前 CR ==========
# 参数: $1=cli路径 $2=仓库名 $3=用户名
get_current_cr() {
    local cli=$1
    local repo_name=$2
    local username=$3
    local local_commit
    local_commit=$(git rev-parse HEAD)

    local cr_list
    cr_list=$("$cli" api get_repo_reviews --repo "$repo_name" --status NEW -o json 2>/dev/null || echo '{"data":{"changes":[]}}')

    echo "$cr_list" | "$cli" jq -r ".data.changes[] | select(.owner.username == \"$username\" and .current_revision == \"$local_commit\") | ._number" 2>/dev/null | head -1 || true
}

# ========== 初始化环境 ==========
# 执行常见的初始化检查，返回 ICODE_CLI, USERNAME, REPO_NAME
init_toolkit_env() {
    check_git_repo

    ICODE_CLI=$(get_icode_cli)
    export ICODE_CLI

    # 获取用户名（check_login 会输出日志，我们只要最后一行的用户名）
    local login_result
    login_result=$(check_login "$ICODE_CLI")
    USERNAME=$(echo "$login_result" | tail -1)
    export USERNAME

    log_step "获取仓库信息..."
    REPO_NAME=$(get_repo_name)
    export REPO_NAME
    log_info "仓库: $REPO_NAME"
}
