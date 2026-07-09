#!/bin/bash
# merge-cr.sh - 合入代码评审脚本 (Linux/macOS)
# 尝试打分 +2 并合入，通过打分结果判断是否有合入权限
#
# 使用方法:
#   ./merge-cr.sh [CR编号]
#
# 示例:
#   ./merge-cr.sh                    # 自动检测 CR
#   ./merge-cr.sh 120247220          # 指定 CR

set -e

# 加载公共函数
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/common.sh"

# 打分 +2
set_score() {
    local repo_name=$1
    local change_number=$2

    local result
    result=$("$ICODE_CLI" api set_review_score --repo "$repo_name" --change-number "$change_number" --score 2 -o json 2>/dev/null || echo '{"status":"FAIL"}')

    local status
    status=$(echo "$result" | "$ICODE_CLI" jq -r '.status' 2>/dev/null || echo "FAIL")

    [ "$status" = "OK" ]
}

# 合入 CR
submit_cr() {
    local repo_name=$1
    local change_number=$2

    local result
    result=$("$ICODE_CLI" api submit_review --repo "$repo_name" --change-number "$change_number" -o json 2>/dev/null)

    local status
    status=$(echo "$result" | "$ICODE_CLI" jq -r '.status' 2>/dev/null || echo "FAIL")

    local message
    message=$(echo "$result" | "$ICODE_CLI" jq -r '.message' 2>/dev/null || echo "未知错误")

    if [ "$status" = "OK" ]; then
        return 0
    else
        echo "$message"
        return 1
    fi
}

# ========== 主流程 ==========

# 初始化环境
init_toolkit_env

CHANGE_NUMBER=${1:-""}

# 如果没有指定 CR 编号，自动检测
if [ -z "$CHANGE_NUMBER" ]; then
    log_step "检测当前 CR..."
    CHANGE_NUMBER=$(get_current_cr "$ICODE_CLI" "$REPO_NAME" "$USERNAME")

    if [ -z "$CHANGE_NUMBER" ]; then
        log_error "未找到当前 commit 对应的 CR"
        log_warn "请先执行 submit-cr.sh 提交 CR，或手动指定 CR 编号"
        exit 1
    fi
fi

log_info "CR 编号: $CHANGE_NUMBER"
echo ""

# 尝试打分 +2（同时检测权限）
log_step "尝试打分 +2..."
if set_score "$REPO_NAME" "$CHANGE_NUMBER"; then
    log_info "打分成功，有合入权限"
    echo ""

    log_step "尝试合入 CR..."
    MERGE_ERROR=""
    if MERGE_ERROR=$(submit_cr "$REPO_NAME" "$CHANGE_NUMBER"); then
        echo ""
        log_success "=========================================="
        log_success "✓ CR #$CHANGE_NUMBER 合入成功！"
        log_success "=========================================="
        exit 0
    else
        echo ""
        log_error "=========================================="
        log_error "✗ CR 合入失败"
        log_error "=========================================="
        log_warn "失败原因: $MERGE_ERROR"
        exit 1
    fi
else
    echo ""
    log_error "=========================================="
    log_error "✗ 打分失败，无合入权限"
    log_error "=========================================="
    log_warn "请联系仓库管理员添加权限，或找有权限的评审人帮忙合入"
    exit 1
fi
