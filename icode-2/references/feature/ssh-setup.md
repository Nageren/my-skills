# ssh-setup - SSH 密钥配置

自动检测并配置 SSH 密钥，用于 iCode Git 操作认证。

## 执行流程

```
开始
  │
  ▼
检测本地 SSH 密钥：
  - 检查 ~/.ssh/id_ed25519 是否存在
  - 检查 ~/.ssh/id_rsa 是否存在
  │
  ├─ 密钥已存在 → 提示"检测到已有 SSH 密钥"
  │
  └─ 密钥不存在 → 生成新的 ed25519 密钥
       │
       ▼
     ssh-keygen -t ed25519 -f ~/.ssh/id_ed25519 -N ""
  │
  ▼
复制公钥到剪贴板：
  ├─ macOS → pbcopy < ~/.ssh/id_ed25519.pub
  ├─ Linux (xclip) → xclip -selection clipboard < ~/.ssh/id_ed25519.pub
  └─ 无剪贴板工具 → 打印公钥内容
  │
  ▼
输出引导信息：
  - 提示公钥已复制（或需手动复制）
  - 显示 iCode 密钥管理 URL
  - 提示用户粘贴公钥完成绑定
  │
  ▼
结束
```

## 快速使用

```bash
# 执行 SSH 密钥配置
./ssh-setup.sh
```

## 参数说明

此脚本无需参数，自动检测和配置。

## 密钥检测逻辑

### 检测优先级

1. **ed25519 密钥**（优先）: `~/.ssh/id_ed25519`
2. **RSA 密钥**（备选）: `~/.ssh/id_rsa`

### 检测结果处理

| 情况 | 处理方式 |
|------|----------|
| ed25519 密钥存在 | 使用已有密钥，不生成新密钥 |
| 仅 RSA 密钥存在 | 使用已有 RSA 密钥 |
| 无密钥 | 生成新的 ed25519 密钥 |

## 剪贴板复制

### 平台支持

| 平台 | 工具 | 命令 |
|------|------|------|
| macOS | pbcopy | `pbcopy < ~/.ssh/id_ed25519.pub` |
| Linux | xclip | `xclip -selection clipboard < ~/.ssh/id_ed25519.pub` |
| Linux | xsel | `xsel --clipboard < ~/.ssh/id_ed25519.pub` |

### 回退机制

如果剪贴板工具不可用，脚本会：
1. 打印公钥完整内容
2. 提示用户手动复制

## iCode 密钥绑定

完成密钥配置后，需要将公钥添加到 iCode 账户：

**管理页面**: https://console.cloud.baidu-int.com/devops/icode/account/keys

### 绑定步骤

1. 打开上述 URL
2. 点击"添加 SSH 密钥"
3. 粘贴公钥内容（已复制到剪贴板）
4. 填写密钥标题（如：MacBook Pro）
5. 点击确认保存

## 注意事项

1. **不覆盖已有密钥**：如果本地已有 SSH 密钥，脚本不会覆盖
2. **密钥安全**：私钥 (`id_ed25519`) 请勿分享，仅公钥 (`id_ed25519.pub`) 需要上传
3. **多设备使用**：每台设备需要单独配置密钥

## 相关命令

| 命令 | 说明 |
|------|------|
| `ssh-keygen -t ed25519` | 生成 ed25519 密钥 |
| `cat ~/.ssh/id_ed25519.pub` | 查看公钥内容 |
| `ssh -T git@icode.baidu.com` | 测试 SSH 连接 |
