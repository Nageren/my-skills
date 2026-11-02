# MCP 503 / `[Errno 2]` Troubleshooting

## Problem

Hermes reports `API Error 503: [Errno 2] No such file or directory` when trying to use MCP tools.

## Root Cause

The session-level `mcp_discovery_timeout` (default 1.5s in this config) was too short to start all MCP servers. npx-based servers (`npx -y apifox-mcp-server@latest`, `npx -y @upstash/context7-mcp`, etc.) take 1-4 seconds to start because npx downloads and caches packages on first launch.

Consequence: the MCP client cancels the connection attempt (`CancelledError`), the server never registers its tools, and Hermes reports the unavailable service as a 503.

## Fix

```bash
hermes config set mcp_discovery_timeout 30
```

Then `/reload-mcp` (in-session) or `/reset`.

## Startup times measured (this config)

| Server | Connection time |
|--------|----------------|
| grafana (Go binary, 59MB) | 154ms |
| codebase-memory (Python binary, 269MB) | 572ms |
| sequential-thinking (npx) | 800ms |
| apifox-yibao (npx) | 1012ms |
| context7 (npx) | 1069ms |

## Secondary cause: deleted CWD

If `mcp-stderr.log` shows repeated:

```
shell-init: error retrieving current directory: getcwd: cannot access parent directories: No such file or directory
```

Hermes was launched from a directory that was later deleted. Child MCP processes inherit the stale CWD and bash cannot initialize. Fix: `cd ~ && hermes`.

## Diagnostic commands

```bash
hermes mcp list                              # Show all configured servers
hermes mcp test <name>                       # Test one server
grep -i "mcp.*error\|cancelled\|503" ~/.hermes/logs/agent.log
cat ~/.hermes/logs/mcp-stderr.log | grep -v "shell-init\|job-working-directory"
grep mcp_discovery_timeout ~/.hermes/config.yaml
```
