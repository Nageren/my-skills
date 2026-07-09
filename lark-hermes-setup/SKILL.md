---
name: lark-hermes-setup
description: "Set up and configure Feishu/Lark integration on Hermes Agent. Use when the user wants to set up, configure, re-bind, add permissions, or troubleshoot Feishu on Hermes — especially when lark-cli reports 'not bound', missing scopes, or 'app pending approval'."
version: 1.0.0
metadata:
  requires:
    bins: ["lark-cli"]
---

# Feishu/Lark Setup on Hermes

Guide for setting up lark-cli on Hermes Agent from scratch and managing permissions over time.

## Prerequisites

- `lark-cli` installed (`which lark-cli`)
- Access to [Feishu Developer Console](https://open.feishu.cn/app)

## Setup Flow

### 1. Create Feishu App (manual, ~2 min)

Open https://open.feishu.cn/app → Create enterprise self-built app. Note the **App ID** (`cli_...`) and **App Secret**.

> ⚠️ Do NOT use `lark-cli config init --force-init --new` from Hermes — the TUI blocks and produces no output in background mode. Create the app manually in the browser, then bind.

### 2. Write Credentials

```bash
echo "FEISHU_APP_ID=cli_xxx" >> ~/.hermes/.env
echo "FEISHU_APP_SECRET=your_secret" >> ~/.hermes/.env
```

### 3. Bind to Hermes

Ask the user to choose identity mode:
- **`bot-only`** (safer): bot operations only, no personal resources
- **`user-default`**: full user impersonation (calendar, mail, drive, etc.)

```bash
lark-cli config bind --source hermes --identity user-default --app-id cli_xxx --lang zh_cn
```

### 4. Enable the Feishu Gateway Plugin

The Hermes gateway must have the Feishu platform plugin enabled to receive messages:

```bash
# Check if enabled (bundled, ships with Hermes)
hermes plugins list | grep feishu

# Enable if it shows "not enabled"
hermes plugins enable feishu-platform
```

Plugin changes take effect on next gateway restart. For TUI: type `/restart`. For launchd service: `hermes gateway restart`.

### 5. Allow User Access

By default, Hermes rejects messages from unauthorized users. For open access during setup:

```bash
echo "GATEWAY_ALLOW_ALL_USERS=true" >> ~/.hermes/.env
```

Or use the pairing system: user sends a message → `hermes pairing list` → `hermes pairing approve <code>`.

### 6. Initial Authorization

Use the **split-flow pattern** — never block on `--device-code` in the same turn as presenting the URL:

```bash
# Step A: Get device code + verification URL (returns immediately)
lark-cli auth login --scope "contact:user:search im:message ..." --no-wait --json

# Step B: Generate QR code
lark-cli auth qrcode "<verification_url>" --output ./feishu-auth-qr.png

# (Present URL + QR to user, wait for "已授权")

# Step C: Complete auth (after user confirms)
lark-cli auth login --device-code "<device_code>"
```

## Adding Permissions (Scopes)

### The Critical Rule

**Scopes must be enabled in the Developer Console AND the app version published BEFORE authorization will work.** If you skip publishing, you get:

```
"Unable to authorize. The app is pending approval."
```

### Correct Sequence

1. Open [Permission page](https://open.feishu.cn/app/<app_id>/permission)
2. Search and enable the needed scopes
3. Click **"发布版本"** (Publish Version) → Create → Publish
4. Run the split-flow auth (Steps A→B→C above)

### Commonly Needed Scopes

| Scope | Purpose |
|-------|---------|
| `contact:user:search` | Search users by name |
| `im:message` | Send messages |
| `im:message.send_as_user` | Send as the user (not bot) |
| `im:chat:read` | Read chat list |
| `im:chat.members:read` | Read chat members |
| `calendar:calendar.event:read` | Read calendar events |
| `calendar:calendar.event:create` | Create calendar events |
| `docx:document:readonly` | Read documents |
| `drive:file:download` | Download files |

## Finding Bots

`contact +search-user` does NOT return bots. To find a bot you've chatted with:

```bash
# List all P2P chats and grep for the bot name
lark-cli im +chat-list --as user --types p2p --page-size 50
```

Bots appear in the P2P chat list with their display name. Use the `chat_id` directly for `im +messages-send`.

## Troubleshooting: Bot Not Responding

When the Feishu bot receives messages but Hermes doesn't respond, diagnose in this order:

### 1. Check plugin status
```bash
hermes plugins list | grep feishu
# Must show "enabled". If "not enabled": hermes plugins enable feishu-platform
```

### 2. Check gateway logs
```bash
grep -i "feishu\|unauthorized\|error\|permission denied" ~/.hermes/logs/gateway.log | tail -20
```

Key patterns and their fixes:

| Log pattern | Fix |
|---|---|
| `feishu-platform ... not enabled` | `hermes plugins enable feishu-platform` + restart |
| `Unauthorized user: ... on feishu` | Set `GATEWAY_ALLOW_ALL_USERS=true` in `.env` or use `hermes pairing approve` |
| `Permission denied: .../gateway-locks` | `mkdir -p ~/.local/state/hermes/gateway-locks` |
| `Another local Hermes gateway is already using this Feishu app_id` | Stop the other gateway process first; cannot have both launchd service and TUI gateway running simultaneously |
| `Gateway started with no connected platforms` | Feishu failed to start — fix the error above and restart |
| `No user allowlists configured` | Set `GATEWAY_ALLOW_ALL_USERS=true` in `.env` |

### 3. Restart after changes
```bash
# For launchd background service
hermes gateway restart

# For TUI (in-session)
/restart
```

### 4. Verify Feishu connected
```bash
grep "connected to wss://.*feishu" ~/.hermes/logs/gateway.log | tail -1
# Should show: "connected to wss://msg-frontier.feishu.cn/..."
```

## Pitfalls

- **"App pending approval"**: App version not published after enabling scopes. Publish in Developer Console.
- **TUI blocking**: `config init --force-init --new` hangs with no output. Create the app manually instead.
- **Bot not found in search**: `contact +search-user` only returns human users. Use `im +chat-list` for bots.
- **Device code expired**: Each `--no-wait` call creates a one-time device code. If auth times out, generate a new one.
- **Short timeout on device-code**: The `--device-code` flow blocks up to 10 min. Set timeout ≥ 120s.
- **Bot not responding / no reaction**: Most common cause is the `feishu-platform` plugin not enabled. Run `hermes plugins list | grep feishu` — if it shows "not enabled", run `hermes plugins enable feishu-platform` and restart the gateway. Second most common: user not authorized — check logs for "Unauthorized user" and set `GATEWAY_ALLOW_ALL_USERS=true` in `.env`.
- **Launchd gateway crash (exit 19968)**: Often caused by the TUI gateway already holding the Feishu connection. Only one gateway can run at a time. If using TUI, stop the launchd service: `hermes gateway stop`.
- **Permission denied on gateway-locks**: `mkdir -p ~/.local/state/hermes/gateway-locks` to create the directory manually.

## Keeping Updated

The user prefers lark-cli always at latest version. When `_notice.update` appears in output, offer to run:

```bash
lark-cli update
```

This updates both the CLI binary and all installed skills.
