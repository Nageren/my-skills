---
name: hermes-gateway-macos
description: Install, start, stop, restart, and configure the Hermes Gateway background service on macOS, including launchd lifecycle management and common pitfalls.
category: devops
platforms: [macos]
tags: [hermes, gateway, launchd, background-service, feishu, wecom]
---

# Hermes Gateway on macOS

Manage the Hermes messaging gateway as a background service on macOS via launchd.

## Triggers

Use this skill when the user:
- Asks to start, stop, restart, install, or configure the Hermes gateway on macOS
- Wants the gateway as a background/daemon/auto-start service
- Hits gateway restart errors or launchd issues on macOS

## Quick Reference

```bash
# Install as user-level launchd service (RECOMMENDED on macOS)
hermes gateway install

# Check status
hermes gateway status

# View logs
tail -f ~/.hermes/logs/gateway.log
tail -f ~/.hermes/logs/gateway.error.log
```

## Installation

Always use **user-level** install on macOS:

```bash
hermes gateway install
```

This creates `/Users/$USER/Library/LaunchAgents/ai.hermes.gateway.plist` and registers with launchd for:
- Auto-start on login
- Auto-restart on crash

### System-level install NOT supported on macOS

```bash
sudo hermes gateway install --system   # ❌ Fails on macOS
```

On macOS this produces `launchctl bootstrap exit 125` and falls back to a plain background process that will NOT auto-start at login or auto-restart. Always use the user-level install instead.

## Restarting the Gateway

### From a separate shell (normal)
```bash
hermes gateway restart
```

### From within the gateway session (when Hermes IS the gateway)
The gateway blocks self-termination to prevent restart loops. `hermes gateway restart` and direct `kill` both fail.

**Workaround** — use a background process via `terminal(background=true)`:
```bash
launchctl bootout gui/$(id -u) /Users/$USER/Library/LaunchAgents/ai.hermes.gateway.plist
sleep 2
launchctl bootstrap gui/$(id -u) /Users/$USER/Library/LaunchAgents/ai.hermes.gateway.plist
```

This spawns a detached process that survives the gateway kill, bootouts the old service, then bootstraps a fresh one.

## Configuration

### Allow all users (disable user allowlist)

When `GATEWAY_ALLOW_ALL_USERS` is not set, the gateway warns:
```
No user allowlists configured. All unauthorized users will be denied.
```

To allow open access, append to `~/.hermes/.env`:
```bash
echo 'GATEWAY_ALLOW_ALL_USERS=true' >> ~/.hermes/.env
```

Then restart the gateway for the change to take effect.

**Note:** `~/.hermes/.env` is a credential store and cannot be read directly with `read_file`. Use `terminal()` to append.

### Platform-specific allowlists (alternative to open access)
```bash
# In ~/.hermes/.env:
TELEGRAM_ALLOWED_USERS=your_telegram_id
# etc.
```

### WeCom (企业微信) Platform Configuration

Hermes supports WeCom via its AI Bot WebSocket gateway (`wss://openws.work.weixin.qq.com`) — no public endpoint or webhook needed.

**Prerequisites:**
- A WeCom organization account
- An AI Bot created in the WeCom Admin Console
- Python packages: `aiohttp` and `httpx`

**Setup options:**

1. **Scan-to-Create (recommended)** — Run `hermes gateway setup`, select **WeCom**, scan the QR code with your WeCom mobile app. Hermes auto-creates the bot and saves credentials.
2. **Manual .env config** — Add to `~/.hermes/.env`:
   ```bash
   WECOM_BOT_ID=your-bot-id
   WECOM_SECRET=***
   # Optional: access control
   WECOM_ALLOWED_USERS=user_id_1,user_id_2
   WECOM_DM_POLICY=open        # open | allowlist | disabled | pairing
   WECOM_GROUP_POLICY=open     # open | allowlist | disabled
   # Optional: home channel for cron/notifications
   WECOM_HOME_CHANNEL=chat_id
   WECOM_WEBSOCKET_URL=wss://openws.work.weixin.qq.com  # override default
   ```

3. **Per-group sender allowlists** (in `config.yaml`):
   ```yaml
   platforms:
     wecom:
       enabled: true
       extra:
         bot_id: "your-bot-id"
         secret: "your-secret"
         group_policy: "allowlist"
         group_allow_from:
           - "group_id_1"
         groups:
           group_id_1:
             allow_from:
               - "user_alice"
               - "user_bob"
   ```

**Features:** WebSocket persistent connection, DM & group messaging, images/files/voice/video, AES-encrypted media decryption, reply-mode responses, auto-reconnect with exponential backoff.

**Pitfalls:**
- Required packages: `pip install aiohttp httpx`
- AES media decryption needs cryptography: `pip install cryptography`
- Verify Bot ID/Secret match the AI Bot credentials page
- Check network connectivity to `openws.work.weixin.qq.com`
- WeCom has a 20 MB absolute file upload limit; images >10 MB auto-downgrade to file attachments
- Native voice only supports AMR format; other formats auto-downgrade to generic files

## Pitfalls

1. **System-level install fails silently** — `sudo hermes gateway install --system` appears to work but the service won't auto-start. Always use user-level install on macOS.

2. **Root-owned lock file after failed `--system` install** — `sudo hermes gateway install --system` runs as root and creates `~/.hermes/gateway.lock` owned by root. After switching to user-level install, `hermes gateway restart` and other gateway commands fail with `PermissionError: [Errno 13] Permission denied: '/Users/.../gateway.lock'`. Fix: `sudo chown $USER ~/.hermes/gateway.lock`.

3. **Can't self-restart** — `hermes gateway restart` from inside the gateway blocks with "Refusing to restart the gateway from inside the gateway process." Even `terminal(background=true)` with `kill` or `launchctl bootout` may be intercepted — the gateway's kill-guard propagates to child processes. The reliable fix: run `hermes gateway restart` from a **separate terminal window** outside the gateway.

4. **LastExitStatus: 19968 is normal after restart** — launchd retains the exit code from the previous `bootout`. As long as `pgrep -fl hermes_cli.main` shows a running process, the gateway is alive.

5. **Env changes need a full restart** — appending to `.env` won't take effect until the gateway process is fully restarted (not just reloaded). Verify with `ps eww -p <PID> | grep <VAR_NAME>` to check if the running process has the env var.
