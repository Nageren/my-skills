#!/bin/bash
# Force-restart the Hermes Gateway launchd service when running from inside
# the gateway (where self-termination is blocked).
# Usage: bash restart-gateway-from-inside.sh

LAUNCHD_PLIST="$HOME/Library/LaunchAgents/ai.hermes.gateway.plist"
GID=$(id -u)

echo "→ Bootout existing service..."
launchctl bootout "gui/$GID" "$LAUNCHD_PLIST"
sleep 2

echo "→ Bootstrap fresh service..."
launchctl bootstrap "gui/$GID" "$LAUNCHD_PLIST"
sleep 1

if pgrep -fl hermes_cli.main > /dev/null 2>&1; then
    echo "✓ Gateway restarted successfully"
else
    echo "✗ Gateway did not start — check ~/.hermes/logs/gateway.error.log"
    exit 1
fi
