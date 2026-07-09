# Upgrading Hermes Web UI from Git Source

When the target version hasn't been published to npm yet, install directly from the GitHub repository and build from source.

## Quick Reference

```bash
# Current version
npm list -g hermes-web-ui

# Check available tags
git ls-remote --tags https://github.com/EKKOLearnAI/hermes-studio.git | grep -E "v[0-9]+\.[0-9]+\.[0-9]+$"

# Check npm dist-tags
npm view hermes-web-ui dist-tags

# Install from git tag (tarball avoids SSH key requirement)
npm install -g "https://github.com/EKKOLearnAI/hermes-studio/archive/refs/tags/v0.6.22.tar.gz"
```

## Build from Source

The tarball installs raw source — no `dist/` directory. Build it:

```bash
PKG_DIR="/Users/marvin/.nvm/versions/node/v23.9.0/lib/node_modules/hermes-web-ui"

cd "$PKG_DIR"

# Install all dependencies (including devDeps)
npm install --include=dev --ignore-scripts

# Type-check frontend
npx vue-tsc -b

# Build frontend (vite/rolldown)
npx vite build

# Build server (esbuild, creates dist/server/index.js)
node scripts/build-server.mjs
```

## Restart the Service

The Hermes Web UI runs as a background Node.js process (PPID 1, daemonized). Steps:

```bash
# 1. Find and kill the old server process
ps aux | grep "hermes-web-ui.*dist/server" | grep -v grep
kill -9 <PID>

# 2. Start the new version in background
cd ~ && npx hermes-web-ui &
# Or use Hermes' background process management

# 3. Verify readiness
sleep 6 && curl -s -o /dev/null -w "HTTP %{http_code}" http://127.0.0.1:8648/
# Expected: HTTP 200
```

## Troubleshooting

### `uv_cwd ENOENT`

The old process had a stale CWD (working directory was deleted). Always `cd ~` before restarting.

### `Cannot find module '.../dist/server/index.js'`

The build step was skipped. Run the full build sequence above. The `dist/` directory is not included in source-only git tarballs.

### `sh: vue-tsc: command not found`

Dev dependencies weren't installed. Run `npm install --include=dev` first. The `--ignore-scripts` flag prevents the prepack script from failing partway through.

### `npx hermes-web-ui` fails silently

Check logs:
```bash
tail -30 ~/.hermes-web-ui/server.log
```

Common causes: missing `dist/`, stale CWD, port already in use.

## Architecture

- **Frontend**: Vue 3 + Vite, built to `dist/client/`
- **Backend**: Node.js server (esbuild-bundled TypeScript), built to `dist/server/index.js`
- **MCP entry**: `bin/hermes-studio-mcp.mjs` (reuses the server codebase via MCP protocol)
- **Data dir**: `~/.hermes-web-ui/` (DB, logs, cache, profiles, server.pid)
