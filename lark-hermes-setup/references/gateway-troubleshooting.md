# Gateway Troubleshooting: Feishu Bot Not Responding

Step-by-step diagnostic recipe when the Feishu bot receives messages but Hermes doesn't respond.

## Diagnostic Flow

Run these in order until you find the issue:

### 1. Plugin enabled?
```bash
hermes plugins list | grep feishu
```
Expected: `enabled`. If `not enabled`: `hermes plugins enable feishu-platform` + restart.

### 2. Gateway running?
```bash
hermes gateway status
```
For TUI mode, check if the TUI process is alive: `ps aux | grep tui_gateway`.

### 3. Check gateway logs for Feishu connection
```bash
grep -i "feishu\|lark" ~/.hermes/logs/gateway.log | tail -20
```

Success pattern:
```
[Feishu] connected to wss://msg-frontier.feishu.cn/ws/v2?...
[Feishu] Received raw message type=text message_id=om_...
```

Failure patterns and fixes:

| Pattern | Meaning | Fix |
|---|---|---|
| `feishu-platform ... not enabled` | Plugin disabled | `hermes plugins enable feishu-platform` |
| `Another local Hermes gateway is already using this Feishu app_id (PID N)` | Two gateways running | Stop one: `hermes gateway stop` or kill the TUI |
| `Permission denied: .../gateway-locks` | Lock directory missing | `mkdir -p ~/.local/state/hermes/gateway-locks` |
| `Gateway started with no connected platforms` | All platforms failed | Fix the error above, restart |
| `✗ feishu failed to connect` | Connection error | Check error above this line for specific cause |

### 4. Message received but rejected?
```bash
grep -i "unauthorized" ~/.hermes/logs/gateway.log | tail -10
```

If you see `Unauthorized user: ou_xxx (name) on feishu`:
- Quick fix: `echo "GATEWAY_ALLOW_ALL_USERS=true" >> ~/.hermes/.env` + restart
- Secure fix: user sends a message, then `hermes pairing approve <code>`

### 5. Launchd service crash loop
```bash
hermes gateway status | grep LastExitStatus
```
If `LastExitStatus = 19968` (or non-zero):
- Check if TUI gateway is already running (only one gateway at a time)
- Check `~/.hermes/logs/gateway.error.log` for the crash reason
- Common: `Permission denied` on lock files, or port conflict

### 6. After fixing, restart and verify
```bash
# Launchd service
hermes gateway restart
sleep 5

# Verify Feishu connected
grep "connected to wss.*feishu" ~/.hermes/logs/gateway.log | tail -1

# Send a test message from Feishu and check
grep "Received raw message" ~/.hermes/logs/gateway.log | tail -3
```

## Real Example: 2026-06-24

Log excerpt from a working-then-broken-then-fixed session:

```
# Working (13:50):
[Feishu] connected to wss://msg-frontier.feishu.cn/...
[Feishu] Received raw message type=text ...
WARNING gateway.run: Unauthorized user: ou_759255cfba6f79978153999f94e9896b (马文磊) on feishu
# ↑ Messages received but rejected — user not authorized

# Broken (13:58):
ERROR [Feishu] Another local Hermes gateway is already using this Feishu app_id (PID 87542)
# ↑ TUI + launchd conflict

# Broken (14:12):
ERROR [Feishu] Failed to connect: Permission denied: .../gateway-locks
# ↑ Lock directory missing after conflict cleanup

# Fixed: hermes plugins list showed feishu-platform "not enabled"
# → hermes plugins enable feishu-platform
# → mkdir -p ~/.local/state/hermes/gateway-locks
# → GATEWAY_ALLOW_ALL_USERS=true already in .env
# → Needs /restart to take effect
```
