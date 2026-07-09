# Error Transcripts — macOS Gateway

## System-level install failure

```bash
$ sudo hermes gateway install --system
Bootstrap failed: 125: Domain does not support specified action
Installing launchd service to: /var/root/Library/LaunchAgents/ai.hermes.gateway.plist
⚠ launchd cannot manage the gateway on this macOS version (launchctl bootstrap exit 125).
✓ Started gateway as a background process instead
  It will NOT auto-start at login or auto-restart on crash.
```

## PermissionError on gateway.lock (root-owned after failed --system)

```bash
$ hermes gateway restart
Traceback (most recent call last):
  ...
  File ".../gateway/status.py", line 555, in is_gateway_runtime_lock_active
    handle = open(resolved_lock_path, "a+", encoding="utf-8")
PermissionError: [Errno 13] Permission denied: '/Users/marvin/.hermes/gateway.lock'

$ ls -la ~/.hermes/gateway.lock
-rw-r--r--  1 root  staff  166  6月 24 13:50 /Users/marvin/.hermes/gateway.lock

# Fix:
$ sudo chown marvin ~/.hermes/gateway.lock
```

## Self-restart blocked from within gateway

```bash
$ hermes gateway restart
✗ Refusing to restart the gateway from inside the gateway process.
This command was blocked to prevent restart loops.
Use `hermes gateway restart` from a shell outside the running gateway.
```

## GATEWAY_ALLOW_ALL_USERS warning

```
WARNING gateway.run: No user allowlists configured. All unauthorized users will be denied.
Set GATEWAY_ALLOW_ALL_USERS=true in ~/.hermes/.env to allow open access,
or configure platform allowlists (e.g., TELEGRAM_ALLOWED_USERS=your_id).
```
