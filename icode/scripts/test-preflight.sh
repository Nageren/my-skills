#!/bin/bash
# test-preflight.sh - icode 前置检测测试

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

PASS_COUNT=0
FAIL_COUNT=0

log_test() { echo -e "${BLUE}[TEST]${NC} $1"; }
log_pass() { echo -e "${GREEN}[PASS]${NC} $1"; PASS_COUNT=$((PASS_COUNT + 1)); }
log_fail() { echo -e "${RED}[FAIL]${NC} $1"; FAIL_COUNT=$((FAIL_COUNT + 1)); }
log_skip() { echo -e "${YELLOW}[SKIP]${NC} $1"; }

REQUIRED_ICODE_CLI_VERSION="0.1.9"

version_ge() {
    [ "$(printf '%s\n' "$1" "$2" | sort -V | head -n1)" = "$2" ]
}

echo ""
echo "=========================================="
echo "icode 前置检测测试"
echo "=========================================="
echo ""

# ----- 测试 icode-cli -----
log_test "检测 icode-cli..."
CLI_PATH=""
if command -v icode-cli &> /dev/null; then
    CLI_PATH="icode-cli"
    log_pass "icode-cli 在 PATH 中"
elif [ -x "$HOME/.icode/bin/icode-cli" ]; then
    CLI_PATH="$HOME/.icode/bin/icode-cli"
    log_pass "icode-cli 在 ~/.icode/bin/ 中"
else
    log_fail "icode-cli 未找到"
fi

if [ -n "$CLI_PATH" ]; then
    CLI_VERSION=$("$CLI_PATH" version 2>/dev/null | grep -oE '[0-9]+\.[0-9]+\.[0-9]+' | head -1)
    if [ -n "$CLI_VERSION" ]; then
        if version_ge "$CLI_VERSION" "$REQUIRED_ICODE_CLI_VERSION"; then
            log_pass "版本 $CLI_VERSION >= $REQUIRED_ICODE_CLI_VERSION"
        else
            log_fail "版本 $CLI_VERSION < $REQUIRED_ICODE_CLI_VERSION"
        fi
    fi
fi

echo ""

# ----- 测试登录状态 -----
log_test "检测登录状态..."
if [ -n "$CLI_PATH" ]; then
    LOGIN_OUTPUT=$("$CLI_PATH" login 2>&1)
    if echo "$LOGIN_OUTPUT" | grep -q "Logged in as"; then
        USERNAME=$(echo "$LOGIN_OUTPUT" | grep "Logged in as" | awk '{print $NF}')
        log_pass "已登录: $USERNAME"
    elif echo "$LOGIN_OUTPUT" | grep -q "Not logged in"; then
        log_fail "未登录"
    else
        log_skip "无法确定登录状态"
    fi
else
    log_skip "icode-cli 未安装"
fi

echo ""

# ----- 测试 git 仓库 -----
log_test "检测 git 仓库..."
if git rev-parse --is-inside-work-tree &> /dev/null; then
    log_pass "当前目录是 git 仓库"
else
    log_skip "当前目录不是 git 仓库"
fi

echo ""
echo "=========================================="
echo "测试结果: 通过 $PASS_COUNT / 失败 $FAIL_COUNT"
echo "=========================================="

[ $FAIL_COUNT -gt 0 ] && exit 1 || exit 0
