---
name: feishu-integration
description: "Set up and troubleshoot Feishu (Lark) integration with Hermes Agent. Use when user asks to connect Feishu, configure lark-cli, enable Feishu features, or fix Feishu auth/permission issues. Covers the Hermes-specific setup workflow: app creation, config bind, identity modes, and auth pitfalls."
version: 1.0.0
metadata:
  requires:
    bins: ["lark-cli"]
---

# Feishu Integration with Hermes

Setup and troubleshoot the Feishu (Lark) integration with Hermes Agent. This skill covers the Hermes-specific workflow — when using lark-cli standalone (no Hermes), follow the lark-shared skill instead.

## Quick Health Check

```bash
lark-cli config show     # Is lark-cli bound to Hermes?
lark-cli auth status     # Is authentication active?
hermes plugins list | grep feishu  # Is the Feishu gateway plugin enabled?
```

If `lark-cli` returns `"lark-cli is not bound to it"`, proceed to setup below.
If `feishu-platform` shows **"not enabled"**, run `hermes plugins enable feishu-platform` and restart the gateway.

## Setup Workflow (Hermes)

### Step 1: Create Feishu App

The user MUST create an app in the Feishu Developer Console first:

1. Open https://open.feishu.cn/app
2. Click **创建企业自建应用** (Create Enterprise Internal App)
3. Name it (e.g., "Hermes 助手")
4. From **凭证与基础信息** (Credentials & Basic Info), copy:
   - **App ID** (starts with `cli_`)
   - **App Secret**

### Step 2: Choose Identity Mode

| Mode | What it can do | What it CANNOT do |
|------|---------------|-------------------|
| `bot-only` | Send messages, create groups, manage chats, create docs | Access user's personal calendar, mail, drive |
| `user-default` | Everything above + user's calendar, mail, drive | Requires extra user authorization |

Default to `bot-only` if the user is unsure. Only use `user-default` when the user explicitly needs personal resource access.

### Step 3: Bind to Hermes

After the user provides App ID and App Secret, write the credentials and bind:

```bash
# Write credentials to Hermes .env
echo "FEISHU_APP_ID=cli_xxxxxxxx" >> ~/.hermes/.env
echo "FEISHU_APP_SECRET=your-secret" >> ~/.hermes/.env

# Bind with chosen identity
lark-cli config bind --source hermes --identity bot-only --app-id cli_xxxxxxxx
# or
lark-cli config bind --source hermes --identity user-default --app-id cli_xxxxxxxx
```

### Step 4: User Authorization (user-default only)

For `user-default` mode, the user must authorize the app to access their resources:

```bash
# Split-flow: get verification URL without blocking
lark-cli auth login --scope "calendar:calendar:readonly" --no-wait --json
```

Extract `verification_url` from output, show it to the user as a QR code + link for scanning. After user confirms completion:

```bash
lark-cli auth login --device-code <device_code>
```

For `bot-only` mode, Step 4 is skipped — the app's own permissions (scopes configured in Developer Console) are sufficient.

## Pitfalls

### DO NOT use `config init --new` in Hermes background mode

`lark-cli config init --force-init --new` launches an interactive TUI that hangs indefinitely when run via `terminal(background=true)`. The command produces no stdout while waiting for TUI input, making it impossible to extract the verification URL.

**Correct approach**: Have the user create the app manually in the Feishu Developer Console, then use `config bind` with the App ID. This is actually faster (1 minute manual + 10 seconds CLI) and more reliable than the TUI path.

### Identity confusion

- `--as bot` uses `tenant_access_token` — can only see bot's own resources
- `--as user` uses `user_access_token` — can see user's personal resources
- Many APIs fail silently with wrong identity rather than giving clear errors

### Permission errors

When a lark-cli command fails with permission issues:
- **Bot identity**: User must add the missing scope in Feishu Developer Console
- **User identity**: Run `lark-cli auth login --scope "<missing_scope>"`

### App visibility for bot identity

When bot identity can't resolve user names in messages (shows open_id instead of display name), check the app's visible range in the Developer Console — it must cover the users whose names need to be resolved.

### Plugin not enabled — bot receives messages but Hermes doesn't respond

The `feishu-platform` plugin must be enabled in Hermes for the gateway to connect to Feishu and process messages. Check with `hermes plugins list | grep feishu`. If "not enabled": `hermes plugins enable feishu-platform` then restart the gateway (`hermes gateway restart` or `/restart` in TUI).

### Unauthorized user — bot receives but rejects messages

If gateway logs show `Unauthorized user: ... on feishu`, either set `GATEWAY_ALLOW_ALL_USERS=true` in `~/.hermes/.env` for open access, or use `hermes pairing approve <code>` after the user sends a message.

## Verification

After setup, verify everything works:

```bash
# Check binding
lark-cli config show

# Check auth
lark-cli auth status

# Test a simple call
lark-cli im +chat-list --as bot --page-size 5
```
