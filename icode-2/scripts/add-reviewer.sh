#!/bin/bash
# add-reviewer.sh - 智能添加评审人脚本 (Linux/macOS)
# 按优先级从多个来源自动选择评审人，或使用用户指定的评审人
#
# 评审人来源优先级:
#   1. 当前 CR 已有评审人（续传 CR 场景）
#   2. 仓库成员（repo members）
#   3. 历史 CR 评审人（补充，当候选人不足 5 人时）
#
# 使用方法:
#   ./add-reviewer.sh [CR编号] [评审人]
#
# 示例:
#   ./add-reviewer.sh                    # 自动检测 CR，自动选择评审人
#   ./add-reviewer.sh 120247220          # 指定 CR，自动选择评审人
#   ./add-reviewer.sh 120247220 zhangsan # 指定 CR 和评审人

set -e

# 加载公共函数
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/common.sh"

# 获取候选评审人（按优先级）
get_reviewer_candidates() {
    local repo_name=$1
    local username=$2
    local change_number=$3

    local seen=""
    local candidates=""

    # 优先级 1: 当前 CR 已有评审人
    if [ -n "$change_number" ] && [ "$change_number" != "0" ]; then
        local cr_info
        cr_info=$("$ICODE_CLI" api get_review_info --change-number "$change_number" -o json 2>/dev/null || echo '{"data":{"globalReviewers":[]}}')

        local cr_reviewers
        cr_reviewers=$(echo "$cr_info" | "$ICODE_CLI" jq -r ".data.globalReviewers[]? | select(.username != \"$username\") | .username" 2>/dev/null || true)

        for r in $cr_reviewers; do
            if [[ ! " $seen " =~ " $r " ]]; then
                seen="$seen $r"
                candidates="$candidates $r"
            fi
        done
    fi

    # 优先级 2: 仓库成员
    local members
    members=$("$ICODE_CLI" api get_repo_members --repo "$repo_name" -o json 2>/dev/null || echo '{"data":[]}')

    local member_reviewers
    # 注意：API 返回的字段是 userName（驼峰式）而不是 username
    member_reviewers=$(echo "$members" | "$ICODE_CLI" jq -r ".data[]? | select(.userName != \"$username\") | .userName" 2>/dev/null || true)

    for r in $member_reviewers; do
        if [[ ! " $seen " =~ " $r " ]]; then
            seen="$seen $r"
            candidates="$candidates $r"
        fi
    done

    # 优先级 3: 历史 CR 评审人（当候选人不足 5 人时补充）
    local candidate_count
    candidate_count=$(echo "$candidates" | wc -w | tr -d ' ')

    if [ "$candidate_count" -lt 5 ]; then
        local merged_crs
        merged_crs=$("$ICODE_CLI" api get_repo_reviews --repo "$repo_name" --status MERGED -o json 2>/dev/null || echo '{"data":{"changes":[]}}')

        local my_cr_numbers
        my_cr_numbers=$(echo "$merged_crs" | "$ICODE_CLI" jq -r ".data.changes[] | select(.owner.username == \"$username\") | ._number" 2>/dev/null || true)

        for cr_num in $my_cr_numbers; do
            local cr_info
            cr_info=$("$ICODE_CLI" api get_review_info --change-number "$cr_num" -o json 2>/dev/null || echo '{"data":{"globalReviewers":[]}}')

            local cr_reviewers
            cr_reviewers=$(echo "$cr_info" | "$ICODE_CLI" jq -r ".data.globalReviewers[]? | select(.username != \"$username\") | .username" 2>/dev/null || true)

            for r in $cr_reviewers; do
                if [[ ! " $seen " =~ " $r " ]]; then
                    seen="$seen $r"
                    candidates="$candidates $r"
                fi
            done
        done
    fi

    # 输出去重后的候选人列表
    echo "$candidates" | tr ' ' '\n' | grep -v '^$' | head -20
}

# ========== 主流程 ==========

# 初始化环境
init_toolkit_env

CHANGE_NUMBER=${1:-""}
SPECIFIED_REVIEWER=${2:-""}

# 如果没有指定 CR 编号，自动检测
if [ -z "$CHANGE_NUMBER" ]; then
    log_step "检测当前 CR..."
    CHANGE_NUMBER=$(get_current_cr "$ICODE_CLI" "$REPO_NAME" "$USERNAME")

    if [ -z "$CHANGE_NUMBER" ]; then
        log_error "未找到当前 commit 对应的 CR"
        log_warn "请先使用 'icode-cli git push_cr' 提交 CR，或手动指定 CR 编号"
        exit 1
    fi
fi
log_info "CR 编号: $CHANGE_NUMBER"
echo ""

# 如果用户指定了评审人，直接添加
if [ -n "$SPECIFIED_REVIEWER" ]; then
    log_step "添加用户指定的评审人: $SPECIFIED_REVIEWER"
    $ICODE_CLI api add_reviewers --change-number "$CHANGE_NUMBER" --reviewers "$SPECIFIED_REVIEWER"
    echo ""
    log_info "评审人 $SPECIFIED_REVIEWER 已添加到 CR #$CHANGE_NUMBER"
    exit 0
fi

# 获取候选评审人（按优先级）
log_step "获取候选评审人..."
REVIEWERS=$(get_reviewer_candidates "$REPO_NAME" "$USERNAME" "$CHANGE_NUMBER")

if [ -z "$REVIEWERS" ]; then
    log_warn "未找到候选评审人"
    log_warn "请手动指定评审人: $0 $CHANGE_NUMBER <reviewer_username>"
    exit 1
fi

# 转为数组
IFS=$'\n' read -r -d '' -a REVIEWER_ARRAY <<< "$REVIEWERS" || true

COUNT=${#REVIEWER_ARRAY[@]}
log_info "找到 $COUNT 个候选评审人: ${REVIEWER_ARRAY[*]}"

# 随机选择一个
RANDOM_INDEX=$((RANDOM % COUNT))
SELECTED_REVIEWER=${REVIEWER_ARRAY[$RANDOM_INDEX]}

log_info "随机选择评审人: $SELECTED_REVIEWER"
echo ""

# 添加评审人
log_step "添加评审人..."
$ICODE_CLI api add_reviewers --change-number "$CHANGE_NUMBER" --reviewers "$SELECTED_REVIEWER"

echo ""
log_info "评审人 $SELECTED_REVIEWER 已添加到 CR #$CHANGE_NUMBER"
