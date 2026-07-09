# lark-cli 在 Hermes 中的完整配置流程

> 适用场景：用户在 Hermes Agent 中首次配置飞书功能，选择 `user-default` 或 `bot-only` 身份。

## 前提

- 用户已有飞书账号和目标企业
- 用户能访问 [飞书开发者后台](https://open.feishu.cn/app)

## 完整流程（7 步）

### 1. 用户在飞书开发者后台创建应用

引导用户：
1. 打开 https://open.feishu.cn/app
2. 点击「创建企业自建应用」
3. 填写应用名称（如「Hermes 助手」）
4. 在「凭证与基础信息」页获取 **App ID**（`cli_` 开头）和 **App Secret**

### 2. 写入凭证到 Hermes .env

```bash
# 方式：execute_code 中直接写文件（推荐，避免 shell 中 secret 泄露风险）
# 或通过 terminal 追加：echo "FEISHU_APP_ID=..." >> ~/.hermes/.env
```

**⚠️ 秘钥脱敏陷阱：** Hermes 的 secret redaction 会对终端输出中的 secret 做脱敏处理（如 `tNDdlN...n8Rs`），导致看起来像写入不完整。验证方式：用 `wc -c` 检查行长度，不要靠肉眼判断输出。

### 3. 绑定应用到 Hermes

```bash
lark-cli config bind --source hermes --identity <bot-only|user-default> --app-id <APP_ID> --lang zh_cn
```

- `bot-only`：推荐默认值，无法访问用户个人资源（日历/邮箱/云盘）
- `user-default`：可以用户身份操作所有资源，需要额外授权

**不要用 `config init --force-init`**：它在 Hermes 上下文中会进入 TUI 模式，在 background 中挂起无输出。`config bind` 是 Hermes 的正确绑定方式。

### 4. 发起用户授权（split-flow）

```bash
lark-cli auth login --recommend --no-wait --json
```

- 返回 `device_code`、`verification_url`、`expires_in`
- **必须用 split-flow**：不要在同一条命令中同时打印 URL 和阻塞轮询

### 5. 生成授权二维码

```bash
lark-cli auth qrcode "<verification_url>" --output ./feishu-auth-qr.png
```

**⚠️ `--output` 必须是相对路径**（如 `./qr.png`），绝对路径（如 `/tmp/qr.png`）会被拒绝。

将二维码图片展示给用户，同时附上原始 URL。二维码有效期通常 10 分钟。

### 6. 用户授权后完成登录

等用户确认「已授权」后：

```bash
lark-cli auth login --device-code "<device_code>"
```

**预期行为：** 使用 `--recommend` 时，大部分 scopes 会显示「未授予」。这是因为应用的权限 scope 尚未在飞书开发者后台启用。此时用户已完成身份绑定，只是 scope 还没开通。

### 7. 用户在开发者后台开通权限 scope

引导用户：
1. 打开应用的管理页面 → 「权限管理」
2. 搜索并按需开通所需 scope（见下方常用 scope 列表）
3. 点击右上角「发布版本」→ 创建新版本 → 发布
4. 发布后，重新执行步骤 4-6 授权

### 常用 Scope 列表

| 场景 | Scope |
|------|-------|
| 发消息 | `im:message` |
| 读取群聊/成员 | `im:chat:read`, `im:chat.members:read` |
| 日历读写 | `calendar:calendar.event:read`, `calendar:calendar.event:create` |
| 忙闲查询 | `calendar:calendar.free_busy:read` |
| 读文档 | `docx:document:readonly`, `docs:document.content:read` |
| 写文档 | `docx:document:write_only`, `docx:document:create` |
| 云盘 | `drive:drive.metadata:readonly`, `drive:file:download` |
| 通讯录 | `contact:user.base:readonly` |
| 多维表格 | `base:app:read`, `base:record:read`, `base:record:create` |
| 任务 | `task:task:read`, `task:task:write` |
| 邮件 | `mail:user_mailbox:readonly` |

> **原则：** 用到什么开什么，不用一次性全开。授权是增量的。

## 常见陷阱

1. **`config init` 在 Hermes 中挂起** → 用 `config bind` 替代
2. **`auth qrcode --output` 绝对路径报错** → 改用相对路径
3. **终端输出中的秘钥看似截断** → 是 secret redaction，实际文件完整，用 `wc -c` 验证
4. **`auth login --recommend` 后大部分 scope 失败** → 正常，需要先在后台开通并发布
5. **在同一条回复中展示 URL 后又阻塞执行 `--device-code`** → 必须 split-flow，先给用户 URL + 二维码，等用户确认后再执行 device-code 轮询
