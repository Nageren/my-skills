#!/bin/bash
# fix-machine-check.sh - 修复机器检查问题脚本 (Linux/macOS)
# 自动检测 CR 的机器检查结果，输出问题详情，供 Agent 分析修复
#
# 使用方法:
#   ./fix-machine-check.sh [CR编号] [最大重试次数]
#
# 示例:
#   ./fix-machine-check.sh                    # 自动检测 CR，默认重试 5 次
#   ./fix-machine-check.sh 120247220          # 指定 CR
#   ./fix-machine-check.sh 120247220 10       # 指定 CR 和最大重试次数

set -e

# 加载公共函数
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/common.sh"

# 获取机器检查结果
get_machine_check() {
    local change_number=$1
    "$ICODE_CLI" api get_machine_check --change-number "$change_number" -o json 2>/dev/null
}

# 检查是否有失败项
check_has_failures() {
    local result=$1
    local failed_count
    failed_count=$(echo "$result" | "$ICODE_CLI" jq '[.data.style.operations[]? | select(.status != "SUCCESS" or .score < 0)] | length' 2>/dev/null || echo "0")

    [[ "$failed_count" -gt 0 ]]
}

# 输出失败项详情
print_failures() {
    local result=$1

    echo ""
    log_warn "========== 机器检查失败项 =========="
    echo ""

    echo "$result" | "$ICODE_CLI" jq -r '
        .data.style.operations[]? |
        select(.status != "SUCCESS" or .score < 0) |
        "【检查项】\(.name)\n【状态】\(.status)\n【评分】\(.score)\n【说明】\(.comment)\n"
    ' 2>/dev/null

    local line_comments
    line_comments=$(echo "$result" | "$ICODE_CLI" jq -r '
        .data.style.operations[]? |
        select(.status != "SUCCESS" or .score < 0) |
        select(.lineComments != null and .lineComments != {}) |
        .lineComments | to_entries[] |
        "【文件】\(.key)\n" + (.value[]? | "  行 \(.line): \(.message // .comment // "无详细信息")")
    ' 2>/dev/null || true)

    if [[ -n "$line_comments" ]]; then
        echo ""
        log_warn "========== 行内评论 =========="
        echo "$line_comments"
    fi

    echo ""
    log_warn "=================================="
    echo ""
}

# ========== 主流程 ==========

# 初始化环境
init_toolkit_env

CHANGE_NUMBER=${1:-""}
MAX_RETRIES=${2:-5}

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
log_info "最大重试次数: $MAX_RETRIES"
echo ""

# 修复循环
RETRY_COUNT=0

while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
    RETRY_COUNT=$((RETRY_COUNT + 1))

    log_step "第 $RETRY_COUNT 次检查 (共 $MAX_RETRIES 次)..."

    RESULT=$(get_machine_check "$CHANGE_NUMBER")

    if [ -z "$RESULT" ]; then
        log_error "无法获取机器检查结果"
        exit 1
    fi

    if ! check_has_failures "$RESULT"; then
        echo ""
        log_info "=========================================="
        log_info "✓ 机器检查全部通过！"
        log_info "=========================================="
        exit 0
    fi

    print_failures "$RESULT"

    if [ $RETRY_COUNT -lt $MAX_RETRIES ]; then
        log_warn "请 Agent 分析上述问题并修复代码"
        log_warn "修复完成后："
        log_warn "  1. 使用 Edit 工具修复代码"
        log_warn "  2. 执行 submit-cr.sh 提交"
        log_warn "  3. 再次运行: $0 $CHANGE_NUMBER $MAX_RETRIES"
        exit 2
    fi
done

echo ""
log_error "=========================================="
log_error "✗ 修复失败，已达到最大重试次数 ($MAX_RETRIES)"
log_error "=========================================="
exit 1
