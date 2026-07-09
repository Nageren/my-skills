# config-init TUI Hang (Hermes Background Mode)

## Reproduction

```bash
# In Hermes, using terminal(background=true):
lark-cli config init --force-init --new --lang zh_cn
```

## Symptoms

- Process starts but produces ZERO stdout (not even a banner or prompt)
- `process poll` shows `uptime_seconds` incrementing with empty `output_preview`
- `process log` returns 0 lines of output
- `process wait --timeout 15` times out — process still running
- The process never exits on its own

## Root Cause

`lark-cli config init --new` launches an interactive TUI (bubbletea-based) that requires a real pseudo-terminal. When run via Hermes's `terminal(background=true)`, the TUI cannot render and silently blocks waiting for terminal input that never arrives.

## Resolution

Kill the stuck process and switch to the manual workflow:

```bash
# Kill stuck process
process(action='kill', session_id='proc_xxx')

# Then follow feishu-integration skill Step 1-3:
# User creates app manually at https://open.feishu.cn/app
# Then: lark-cli config bind --source hermes --identity <mode> --app-id <id>
```

## Environment

- lark-cli version: 1.0.44
- Hermes terminal backend: local (macOS 26.5.1)
- The issue is likely universal — the TUI needs a real PTY, which background mode doesn't provide
