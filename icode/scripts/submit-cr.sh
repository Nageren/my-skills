#!/bin/bash
# submit-cr.sh - 智能提交代码评审脚本 (Linux/macOS)
# 自动判断新建 CR 或追加到已有 CR（Amend 模式）
#
# 使用方法:
#   ./submit-cr.sh [目标分支] [commit-message]
#
# 示例:
#   ./submit-cr.sh                                    # 默认 master 分支，交互式输入 commit message
#   ./submit-cr.sh develop                            # 指定 develop 分支
#   ./submit-cr.sh master "ComateStack-123 feat: xx"  # 指定 commit message（用于 Agent 调用）
#
# 返回值:
#   0 - 成功（amend 或新建 CR）
#   2 - 需要新建 CR，但未提供 commit message（Agent 应先完成选卡流程再调用）

set -e

# 加载公共函数
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/common.sh"

# 初始化环境
init_toolkit_env

# 获取本地信息
LOCAL_COMMIT=$(git rev-parse HEAD)
COMMIT_MSG=$(git log -1 --format="%s")
ICAFE_CARD=$(echo "$COMMIT_MSG" | grep -oE '^[A-Za-z0-9]+-[0-9]+' | head -1 || true)
DEFAULT_BRANCH=${1:-master}
NEW_COMMIT_MSG=${2:-}

echo ""
log_info "本地 Commit: $LOCAL_COMMIT"
log_info "Commit Message: $COMMIT_MSG"
log_info "iCafe 卡片号: ${ICAFE_CARD:-无}"
log_info "默认目标分支: $DEFAULT_BRANCH"
echo ""

# 查询远程 CR
log_step "查询远程 CR 列表..."
CR_LIST=$($ICODE_CLI api get_repo_reviews --repo "$REPO_NAME" --status NEW -o json 2>/dev/null || echo '{"data":{"changes":[]}}')

# 方式一：通过 commit hash 匹配
log_step "匹配已有 CR..."
MATCHED_BY_HASH=$(echo "$CR_LIST" | $ICODE_CLI jq -r ".data.changes[] | select(.owner.username == \"$USERNAME\" and .current_revision == \"$LOCAL_COMMIT\") | ._number" 2>/dev/null | head -1 || true)

# 方式二：通过 iCafe 卡片号匹配
MATCHED_BY_CARD=""
if [ -z "$MATCHED_BY_HASH" ] && [ -n "$ICAFE_CARD" ]; then
    MATCHED_BY_CARD=$(echo "$CR_LIST" | $ICODE_CLI jq -r ".data.changes[] | select(.owner.username == \"$USERNAME\" and (.subject | startswith(\"$ICAFE_CARD\"))) | ._number" 2>/dev/null | head -1 || true)
fi

MATCHED_CR=${MATCHED_BY_HASH:-$MATCHED_BY_CARD}

if [ -n "$MATCHED_CR" ]; then
    MATCHED_BRANCH=$(echo "$CR_LIST" | $ICODE_CLI jq -r ".data.changes[] | select(._number == $MATCHED_CR) | .branch" 2>/dev/null)

    if [ -n "$MATCHED_BY_HASH" ]; then
        log_info "通过 Commit Hash 匹配到 CR: #$MATCHED_CR"
    else
        log_info "通过 iCafe 卡片号 ($ICAFE_CARD) 匹配到 CR: #$MATCHED_CR"
    fi
    log_info "目标分支: $MATCHED_BRANCH"
    echo ""

    log_step "执行 Amend 模式..."

    if [ -n "$(git status --porcelain)" ]; then
        log_step "添加工作区修改..."
        git add -A
        log_step "Amend 提交..."
        git commit --amend --no-edit
    else
        log_warn "工作区没有新修改，直接推送"
    fi

    log_step "推送 CR..."
    $ICODE_CLI git push_cr --branch "$MATCHED_BRANCH"
else
    log_info "未找到匹配的 CR，需要新建"
    log_info "目标分支: $DEFAULT_BRANCH"
    echo ""

    # 检查是否有工作区修改
    if [ -z "$(git status --porcelain)" ]; then
        log_warn "工作区没有新修改，直接推送当前 commit"
        log_step "推送 CR..."
        $ICODE_CLI git push_cr --branch "$DEFAULT_BRANCH"
        echo ""
        log_info "CR 提交完成！"
        exit 0
    fi

    # 检查是否提供了 commit message
    if [ -z "$NEW_COMMIT_MSG" ]; then
        # 非交互模式：返回特殊退出码，提示 Agent 需要先完成选卡流程
        echo ""
        log_warn "需要新建 CR，但未提供 commit message"
        log_info "EXIT_CODE=2: 请先完成 iCafe 卡片选择，然后使用以下命令提交："
        log_info "  ./submit-cr.sh $DEFAULT_BRANCH \"<卡片ID> <描述>\""
        echo ""
        exit 2
    fi

    log_step "执行新建 CR 模式..."
    log_step "添加工作区修改..."
    git add -A

    log_step "创建新 commit..."
    git commit -m "$NEW_COMMIT_MSG"

    log_step "推送 CR..."
    $ICODE_CLI git push_cr --branch "$DEFAULT_BRANCH"
fi

echo ""
log_info "CR 提交完成！"
