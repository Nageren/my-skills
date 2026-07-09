#!/bin/bash
# ssh-setup.sh - SSH 密钥检测与配置
# 自动检测本地 SSH 密钥，如不存在则生成，并引导用户完成 iCode 绑定

set -e

# 获取脚本所在目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# 引入公共函数
source "$SCRIPT_DIR/common.sh"

# ========== SSH 密钥路径 ==========
SSH_DIR="$HOME/.ssh"
ED25519_KEY="$SSH_DIR/id_ed25519"
ED25519_PUB="$SSH_DIR/id_ed25519.pub"
RSA_KEY="$SSH_DIR/id_rsa"
RSA_PUB="$SSH_DIR/id_rsa.pub"

# iCode 密钥管理页面
ICODE_KEYS_URL="https://console.cloud.baidu-int.com/devops/icode/account/keys"

# ========== 检测 SSH 密钥 ==========
detect_ssh_key() {
    log_step "检测本地 SSH 密钥..."

    if [ -f "$ED25519_KEY" ] && [ -f "$ED25519_PUB" ]; then
        log_info "检测到已有 SSH 密钥: $ED25519_KEY"
        echo "$ED25519_PUB"
        return 0
    fi

    if [ -f "$RSA_KEY" ] && [ -f "$RSA_PUB" ]; then
        log_info "检测到已有 SSH 密钥: $RSA_KEY"
        echo "$RSA_PUB"
        return 0
    fi

    log_warn "未检测到 SSH 密钥"
    echo ""
    return 0
}

# ========== 生成 SSH 密钥 ==========
generate_ssh_key() {
    log_step "生成新的 SSH 密钥 (ed25519)..."

    # 确保 .ssh 目录存在
    if [ ! -d "$SSH_DIR" ]; then
        mkdir -p "$SSH_DIR"
        chmod 700 "$SSH_DIR"
        log_info "创建目录: $SSH_DIR"
    fi

    # 生成密钥（无密码）
    ssh-keygen -t ed25519 -f "$ED25519_KEY" -N "" -C "icode-$(whoami)@$(hostname)"

    if [ -f "$ED25519_PUB" ]; then
        log_success "SSH 密钥生成成功: $ED25519_KEY"
        echo "$ED25519_PUB"
    else
        log_error "SSH 密钥生成失败"
        exit 1
    fi
}

# ========== 复制公钥到剪贴板 ==========
copy_to_clipboard() {
    local pub_key_file=$1
    local pub_key_content
    pub_key_content=$(cat "$pub_key_file")

    log_step "复制公钥到剪贴板..."

    # macOS
    if command -v pbcopy &> /dev/null; then
        echo "$pub_key_content" | pbcopy
        log_success "公钥已复制到剪贴板 (pbcopy)"
        return 0
    fi

    # Linux - xclip
    if command -v xclip &> /dev/null; then
        echo "$pub_key_content" | xclip -selection clipboard
        log_success "公钥已复制到剪贴板 (xclip)"
        return 0
    fi

    # Linux - xsel
    if command -v xsel &> /dev/null; then
        echo "$pub_key_content" | xsel --clipboard
        log_success "公钥已复制到剪贴板 (xsel)"
        return 0
    fi

    # 无剪贴板工具 - 打印公钥
    log_warn "未找到剪贴板工具，请手动复制以下公钥内容："
    echo ""
    echo "========== 公钥内容开始 =========="
    echo "$pub_key_content"
    echo "========== 公钥内容结束 =========="
    echo ""
    return 1
}

# ========== 显示引导信息 ==========
show_guidance() {
    local copied=$1

    echo ""
    log_phase "===== SSH 密钥配置完成 ====="
    echo ""

    if [ "$copied" = "true" ]; then
        echo "✅ 公钥已复制到剪贴板"
    else
        echo "⚠️  请手动复制上方的公钥内容"
    fi

    echo ""
    echo "📋 下一步操作："
    echo "   1. 打开 iCode 密钥管理页面："
    echo "      ${CYAN}${ICODE_KEYS_URL}${NC}"
    echo ""
    echo "   2. 点击「添加 SSH 密钥」"
    echo ""
    echo "   3. 粘贴公钥内容并保存"
    echo ""
    echo "💡 完成后可使用以下命令测试连接："
    echo "   ssh -T git@icode.baidu.com"
    echo ""
}

# ========== 主流程 ==========
main() {
    log_phase "===== SSH 密钥配置 ====="
    echo ""

    # 1. 检测已有密钥
    local pub_key_file
    pub_key_file=$(detect_ssh_key)

    # 2. 如果没有密钥，生成新的
    if [ -z "$pub_key_file" ]; then
        pub_key_file=$(generate_ssh_key)
    fi

    # 3. 复制公钥到剪贴板
    local copied="false"
    if copy_to_clipboard "$pub_key_file"; then
        copied="true"
    fi

    # 4. 显示引导信息
    show_guidance "$copied"
}

# 执行主流程
main "$@"
