---
name: lark-setup
description: "飞书/Lark 在 Hermes 中的首次配置与权限开通全流程。当用户说「配置飞书」「开通飞书」「飞书权限」「lark-cli 设置」「飞书授权」或遇到 missing_scope / FEISHU_APP_ID not found / app pending approval 等错误时使用。覆盖：创建应用、绑定身份、凭证写入、scope 授权、权限开通与发布、常见陷阱。"
version: 1.0.0
metadata:
  requires:
    bins: ["lark-cli"]
  cliHelp: "lark-cli config bind --help; lark-cli auth login --help"
---

# lark-setup — 飞书在 Hermes 中的配置与授权

配套 `lark-shared`（身份认证全局规则），本 skill 专注**首次配置**和**权限开通**的完整操作链路。

## 前置条件

- 飞书管理员权限（或能自建企业自建应用）
- `lark-cli` 已安装（`which lark-cli`）

---

## 完整配置流程（推荐手动路线）

### 第一步：创建飞书应用

1. 打开 [飞书开发者后台](https://open.feishu.cn/app)
2. 创建「企业自建应用」，记下 **App ID**（`cli_xxx`）和 **App Secret**

### 第二步：写入凭证

```bash
# 写入 ~/.hermes/.env
cat >> ~/.hermes/.env << 'EOF'
FEISHU_APP_ID=cli_xxxxxxxxxxxx
FEISHU_APP_SECRET=xxxxxxxxxxxx
EOF
```

> ⚠️ 写入后用 `wc -c` 验证行长度（Hermes 会脱敏终端输出中的 secret，`grep` 看到的是脱敏后的内容）

### 第三步：绑定到 Hermes

```bash
lark-cli config bind --source hermes --identity user-default --app-id cli_xxx --lang zh_cn
```

身份模式二选一：
- `bot-only`：安全默认，不能访问用户个人资源
- `user-default`：可访问日历/邮箱/云盘等个人资源（需要用户额外授权）

### 第四步：首次授权（推荐 scopes）

```bash
# 获取授权链接（不阻塞等待）
lark-cli auth login --recommend --no-wait --json

# 用返回的 verification_url 生成二维码
lark-cli auth qrcode "<verification_url>" --output ./feishu-auth-qr.png

# 用户扫码确认后，完成授权
lark-cli auth login --device-code "<device_code>"
```

> ⚠️ `--recommend` 会请求所有推荐 scope，但只有已在**开发者后台开通并发布版本**的 scope 才能成功授予。

### 第五步：按需追加权限

当遇到 `missing_scope` 错误时，追加授权：

```bash
# 获取授权链接
lark-cli auth login --scope "contact:user:search im:message im:message.send_as_user" --no-wait --json

# 生成二维码 → 用户扫码 → 完成授权
lark-cli auth qrcode "<url>" --output ./feishu-auth-qr.png
lark-cli auth login --device-code "<device_code>"
```

---

## 常见陷阱

### ❌ `FEISHU_APP_ID not found in .env`

凭证未写入 `~/.hermes/.env`。用第二步的命令写入。

### ❌ `Unable to authorize. The app is pending approval`

权限 scope 已在后台开通但**未发布版本**。解决：
1. 打开 [开发者后台 — 你的应用](https://open.feishu.cn/app)
2. 权限管理 → 确认 scope 已勾选
3. 右上角「发布版本」→ 创建版本 → 发布

### ❌ `config init --force-init --new` 在后台/TUI 模式卡住

这是交互式 TUI，不适合 AI agent 后台执行。改用手动路线（第一步创建应用 → `config bind`）。

### ❌ 授权后 scope 仍然 missing

1. `lark-cli auth status` 查看当前已授予的 scopes
2. 确认缺失的 scope 已在开发者后台开通并发布
3. 用 `lark-cli auth login --scope "xxx"` 单独追加

### ❌ 通讯录搜索不到人

- 尝试不加 `--has-chatted` 扩大范围
- 单字/昵称可能搜不到，尝试全名或邮箱
- 若仍搜不到，需要 `im:chat:read` scope 通过聊天列表查找

---

## 常用 scope 速查

| 场景 | 所需 scope |
|------|-----------|
| 搜索同事 | `contact:user:search` |
| 发送消息 | `im:message` + `im:message.send_as_user` |
| 查看群聊 | `im:chat:read` |
| 查看日程 | `calendar:calendar.event:read` |
| 创建日程 | `calendar:calendar.event:create` |
| 读取文档 | `docx:document:readonly` |
| 云盘文件 | `drive:drive.metadata:readonly` |
| 任务 | `task:task:read` + `task:task:write` |
| 邮件 | `mail:user_mailbox:readonly` |

---

## 验证

```bash
lark-cli auth status          # 查看当前授权状态和 scope 列表
lark-cli config show          # 查看绑定信息
```
