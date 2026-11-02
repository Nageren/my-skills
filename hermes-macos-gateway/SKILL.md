---
name: hermes-macos-gateway
description: "Diagnose and fix macOS Hermes Gateway startup failures — launchd, scoped locks, permission residue from --system install, Feishu app_id conflicts, and restart-from-within blocks."
version: 1.0.0
author: Hermes Agent
platforms: [macos]
tags: [hermes, gateway, macos, troubleshooting, feishu, launchd, locks]
---

# Hermes macOS Gateway Troubleshooting

Fixes for common macOS-specific gateway startup failures. The `hermes-agent` skill
covers general setup and config; this skill addresses macOS-only pitfalls.

## Triggers

Gateway won't start, exits immediately, or produces any of:
- `PermissionError` on `gateway.lock` / `feishu_seen_message_ids.json` / `gateway-locks/`
- "Another local Hermes gateway is already using this Feishu app_id (PID N)"
- "Bootstrap failed: 125: Domain does not support specified action"
- `hermes gateway status` shows "not running" after `start` succeeds

## Quick Diagnostic

Run these from a shell OUTSIDE the gateway process:

```bash
hermes gateway status                # Is it loaded? LastExitStatus?
ls -la ~/.hermes/gateway.lock        # Who owns it?
ls -laR ~/.local/state/hermes/gateway-locks/  # Any root-owned stale locks?
pgrep -fl hermes_cli.main            # Is a process actually running?
```

## Pitfall 1: `--system` install leaves root-owned files

**Symptom:** `PermissionError: [Errno 13] Permission denied: '/Users/<user>/.hermes/gateway.lock'`
or similar on `feishu_seen_message_ids.json`.

**Root cause:** Running `sudo hermes gateway install --system` creates files owned by root.
macOS launchd can't manage system-level GUI services, so it falls back to a bg process.
The user then installs user-level, but root-owned residue blocks it.

**Fix — fix all three known root-owned paths:**

```bash
sudo chown $(whoami) ~/.hermes/gateway.lock
sudo chown $(whoami) ~/.hermes/feishu_seen_message_ids.json
sudo rm -rf ~/.local/state/hermes/gateway-locks/
```

Always use **user-level** install on macOS:
```bash
hermes gateway install    # NOT --system
```

## Pitfall 2: Stale Feishu scoped lock blocks restart

**Symptom:** Gateway starts then immediately exits with:
```
ERROR [Feishu] Another local Hermes gateway is already using this Feishu app_id (PID 87542).
```

**Root cause:** The Feishu adapter uses `acquire_scoped_lock` (in
`~/.local/state/hermes/gateway-locks/`) to prevent two gateways using the
same Feishu app_id concurrently. When the old gateway is killed (SIGKILL or
crash), the lock file persists with the dead PID. On macOS, `kill(pid, 0)`
can return success for recently-dead PIDs, so the stale-detection logic may
fail to mark the lock as stale.

**Fix:**

```bash
# Remove the stale lock directory (safe — will be recreated on next start)
rm -rf ~/.local/state/hermes/gateway-locks/
```

Also clean gateway state file if present:
```bash
rm -f ~/.hermes/gateway_state.json
```

## Pitfall 3: Cannot restart gateway from within the gateway

**Symptom:** Running `hermes gateway restart` or `kill` from a tool call
inside a gateway session produces:
```
Blocked: cannot restart or stop the gateway from inside the gateway process.
```

**Root cause:** The gateway intercepts SIGTERM/SIGKILL to prevent accidental
self-destruction. Even `nohup`, `background=true`, and `launchctl kill`
are blocked.

**Fix:** The user MUST run the restart command from a **separate terminal window**:
```bash
hermes gateway restart
```

Or two-step:
```bash
hermes gateway stop
hermes gateway start
```

## Pitfall 4: `GATEWAY_ALLOW_ALL_USERS` not in effect

**Symptom:** Gateway rejects user messages with "Unauthorized user" even
after adding `GATEWAY_ALLOW_ALL_USERS=true` to `.env`.

**Root cause:** The `.env` is read at process startup. If the gateway can't
be restarted (Pitfall 3), the old process never reads the new setting.

**Fix:** Fix Pitfall 1 and Pitfall 2, then restart from a separate terminal.

If `GATEWAY_ALLOW_ALL_USERS` is too broad, use per-platform allowlists:
```bash
# In ~/.hermes/.env
FEISHU_ALLOWED_USERS=ou_XXXXXXXXXXXXXXXX
```

## Fix-After-Restart Checklist

After a successful restart, verify:
1. `pgrep -fl hermes_cli.main` shows a running process
2. `tail -20 ~/.hermes/logs/gateway.log` shows "✓ feishu connected" (no "Unauthorized user" warnings)
3. `hermes gateway status` shows "Gateway service is loaded" with a fresh PID

## `hermes pairing` Quick Ref

```bash
hermes pairing list                     # Show pending codes
hermes pairing approve feishu <CODE>    # Approve a code
```

Codes expire quickly — if `not found or expired`, the user must re-send a
message to the bot from Feishu to get a new code.
