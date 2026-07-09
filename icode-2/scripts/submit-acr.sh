#!/bin/bash
# submit-acr.sh - AI 代码评审脚本 (Linux/macOS)
# 自动执行 AI 代码评审 + 问题修复的循环流程
#
# 使用方法:
#   ./submit-acr.sh [CR编号] [最大循环次数] [AI评审超时秒数] [严重度阈值]
#
# 示例:
#   ./submit-acr.sh                        # 自动检测 CR，使用默认参数
#   ./submit-acr.sh 120247220              # 指定 CR
#   ./submit-acr.sh 120247220 10 1200 5    # 完整参数

set -e

# 加载公共函数
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/common.sh"

# 触发 AI 评审
trigger_ai_review() {
    local change_number=$1

    local result
    local stderr_output
    local exit_code
    stderr_output=$(mktemp)

    # 临时禁用 set -e，避免命令失败时脚本退出
    set +e
    result=$("$ICODE_CLI" api start_ai_review --change-number "$change_number" -o json 2>"$stderr_output")
    exit_code=$?
    set -e

    if [ $exit_code -ne 0 ]; then
        # 检查是否有 API 错误信息
        if grep -q "API_REQUEST_FAILED\|BAD_REQUEST" "$stderr_output" 2>/dev/null; then
            local api_error
            api_error=$(grep -oE '"message":"[^"]*"' "$stderr_output" | head -1 | sed 's/"message":"//;s/"$//')
            log_error "API 调用失败: $api_error" >&2
        else
            log_error "触发 AI 评审失败" >&2
            cat "$stderr_output" >&2
        fi
        rm -f "$stderr_output"
        return 1
    fi
    rm -f "$stderr_output"

    if [ -z "$result" ]; then
        log_error "触发 AI 评审失败: 无返回结果" >&2
        return 1
    fi

    local status
    status=$(echo "$result" | "$ICODE_CLI" jq -r '.status' 2>/dev/null)

    if [ "$status" != "OK" ]; then
        local message
        message=$(echo "$result" | "$ICODE_CLI" jq -r '.message' 2>/dev/null)
        log_error "触发 AI 评审失败: $message" >&2
        return 1
    fi

    echo "$result" | "$ICODE_CLI" jq -r '.conversationId' 2>/dev/null
}

# 获取 AI 评审结果
get_ai_review_result() {
    local conversation_id=$1
    "$ICODE_CLI" api get_ai_review --conversation-id "$conversation_id" -o json 2>/dev/null
}

# 检查 AI 评审状态
check_ai_review_status() {
    local result=$1
    echo "$result" | "$ICODE_CLI" jq -r '.data.crStatus' 2>/dev/null
}

# 统计需要修复的问题数量
count_ai_issues() {
    local result=$1
    local severity_threshold=$2
    echo "$result" | "$ICODE_CLI" jq "
        [.data.results[] |
         select(.messageType == \"INTERLINEAR_COMMENT\") |
         .processedContent |
         select(.severityScore >= $severity_threshold)] | length
    " 2>/dev/null || echo "0"
}

# 输出 AI 评审问题详情
print_ai_issues() {
    local result=$1
    local severity_threshold=$2

    echo ""
    log_warn "========== AI 评审问题 (severityScore >= $severity_threshold) =========="
    echo ""

    echo "$result" | "$ICODE_CLI" jq -r "
        .data.results[] |
        select(.messageType == \"INTERLINEAR_COMMENT\") |
        .processedContent |
        select(.severityScore >= $severity_threshold) |
        \"【文件】\\(.fileName)\\n【行号】\\(.startLine)-\\(.endLine)\\n【严重度】\\(.severityScore)\\n【问题】\\(.message)\\n\"
    " 2>/dev/null

    log_warn "=========================================="
    echo ""
}

# ========== 主流程 ==========

# 初始化环境
init_toolkit_env

CHANGE_NUMBER=${1:-""}
MAX_LOOPS=${2:-10}
AI_CR_TIMEOUT=${3:-1200}
SEVERITY_THRESHOLD=${4:-5}
POLL_INTERVAL=10

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

echo ""
log_info "========== AI CR 流程 =========="
log_info "CR 编号: $CHANGE_NUMBER"
log_info "最大循环次数: $MAX_LOOPS"
log_info "AI 评审超时: ${AI_CR_TIMEOUT}s"
log_info "严重度阈值: $SEVERITY_THRESHOLD"
log_info "===================================="
echo ""

# 主循环
LOOP_COUNT=0

while [ $LOOP_COUNT -lt $MAX_LOOPS ]; do
    LOOP_COUNT=$((LOOP_COUNT + 1))

    echo ""
    log_phase "========== 第 $LOOP_COUNT 轮 (共 $MAX_LOOPS 轮) =========="
    echo ""

    log_phase "AI 代码评审"
    log_step "触发 AI 评审..."

    set +e
    CONVERSATION_ID=$(trigger_ai_review "$CHANGE_NUMBER")
    TRIGGER_EXIT_CODE=$?
    set -e

    if [ $TRIGGER_EXIT_CODE -ne 0 ] || [ -z "$CONVERSATION_ID" ]; then
        log_error "触发 AI 评审失败"
        exit 1
    fi

    log_info "会话 ID: $CONVERSATION_ID"
    log_step "轮询 AI 评审结果..."

    ELAPSED=0
    AI_RESULT=""

    while [ $ELAPSED -lt $AI_CR_TIMEOUT ]; do
        AI_RESULT=$(get_ai_review_result "$CONVERSATION_ID")
        AI_STATUS=$(check_ai_review_status "$AI_RESULT")

        case "$AI_STATUS" in
            "SUSS")
                log_info "AI 评审完成"
                break
                ;;
            "FAIL")
                log_error "AI 评审执行失败"
                exit 1
                ;;
            "TIMEOUT")
                log_error "AI 评审执行超时"
                exit 1
                ;;
            "EXECUTING")
                log_info "AI 评审执行中... (${ELAPSED}s / ${AI_CR_TIMEOUT}s)"
                sleep $POLL_INTERVAL
                ELAPSED=$((ELAPSED + POLL_INTERVAL))
                ;;
            *)
                log_warn "未知状态: $AI_STATUS，继续等待..."
                sleep $POLL_INTERVAL
                ELAPSED=$((ELAPSED + POLL_INTERVAL))
                ;;
        esac
    done

    if [ $ELAPSED -ge $AI_CR_TIMEOUT ]; then
        log_error "轮询超时（${AI_CR_TIMEOUT}s），AI 评审未完成"
        exit 1
    fi

    AI_ISSUE_COUNT=$(count_ai_issues "$AI_RESULT" "$SEVERITY_THRESHOLD")

    if [ "$AI_ISSUE_COUNT" -eq 0 ]; then
        echo ""
        log_info "=========================================="
        log_info "✓ AI CR 流程通过！"
        log_info "  - AI 评审: 无高优问题 (severityScore >= $SEVERITY_THRESHOLD)"
        log_info "=========================================="
        exit 0
    fi

    log_warn "AI 评审发现 $AI_ISSUE_COUNT 个需要修复的问题"
    print_ai_issues "$AI_RESULT" "$SEVERITY_THRESHOLD"

    if [ $LOOP_COUNT -lt $MAX_LOOPS ]; then
        log_warn "请 Agent 修复上述 AI 评审问题"
        log_warn "修复完成后："
        log_warn "  1. 使用 Edit 工具修复代码"
        log_warn "  2. 执行 submit-cr.sh 提交"
        log_warn "  3. 再次运行: $0 $CHANGE_NUMBER $MAX_LOOPS $AI_CR_TIMEOUT $SEVERITY_THRESHOLD"
        exit 2
    fi
done

echo ""
log_error "=========================================="
log_error "✗ AI CR 流程失败，已达到最大循环次数 ($MAX_LOOPS)"
log_error "=========================================="
exit 1
