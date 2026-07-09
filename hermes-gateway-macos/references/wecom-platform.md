# WeCom (企业微信) Platform Reference

Full env vars, config options, media support, and troubleshooting for the WeCom Hermes adapter.

## All Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `WECOM_BOT_ID` | ✅ | — | WeCom AI Bot ID |
| `WECOM_SECRET` | ✅ | — | WeCom AI Bot Secret |
| `WECOM_ALLOWED_USERS` | — | (empty) | Comma-separated user IDs for gateway-level allowlist |
| `WECOM_HOME_CHANNEL` | — | — | Chat ID for cron/notification output |
| `WECOM_WEBSOCKET_URL` | — | `wss://openws.work.weixin.qq.com` | WebSocket gateway URL |
| `WECOM_DM_POLICY` | — | `open` | DM access: `open` / `allowlist` / `disabled` / `pairing` |
| `WECOM_GROUP_POLICY` | — | `open` | Group access: `open` / `allowlist` / `disabled` |

## Config Options (config.yaml -> platforms.wecom.extra)

| Key | Default | Description |
|-----|---------|-------------|
| `bot_id` | — | WeCom AI Bot ID (required) |
| `secret` | — | WeCom AI Bot Secret (required) |
| `websocket_url` | `wss://openws.work.weixin.qq.com` | WebSocket gateway URL |
| `dm_policy` | `open` | DM access policy |
| `group_policy` | `open` | Group access policy |
| `allow_from` | `[]` | User IDs allowed for DMs (when `dm_policy=allowlist`) |
| `group_allow_from` | `[]` | Group IDs allowed (when `group_policy=allowlist`) |
| `groups` | `{}` | Per-group config (see per-group sender allowlists) |

## Media Support

### Inbound (receiving)

| Type | Handling |
|------|----------|
| Images | Downloaded + cached locally (URL-based and base64) |
| Files | Downloaded + cached, filename preserved |
| Voice | Text transcription extracted if available |
| Mixed | WeCom mixed-type (text+image) fully parsed |
| Quoted | Media from replied-to messages also extracted |
| AES-encrypted | Auto-decrypted with AES-256-CBC + PKCS#7 padding (requires `cryptography`) |

### Outbound (sending)

| Method | Content | Size limit |
|--------|---------|------------|
| `send` | Markdown text | 4000 chars |
| `send_image` / `send_image_file` | Native image | 10 MB |
| `send_document` | File attachment | 20 MB |
| `send_voice` | Native voice (AMR only) | 2 MB |
| `send_video` | Video | 10 MB |

Auto-downgrade rules:
- Images >10 MB → sent as file
- Videos >10 MB → sent as file
- Voice >2 MB or not AMR → sent as file
- Files >20 MB → rejected with message

Chunked upload: 512 KB chunks via init → chunks → finish protocol.

## Connection & Reconnection

WebSocket endpoint: `wss://openws.work.weixin.qq.com`

| Attempt | Delay |
|---------|-------|
| 1st retry | 2s |
| 2nd retry | 5s |
| 3rd retry | 10s |
| 4th retry | 30s |
| 5th+ retry | 60s |

Heartbeat: application-level ping every 30s.
Deduplication: by message ID, 5-minute window, max 1000 entries.

## Troubleshooting

| Problem | Fix |
|---------|-----|
| `WECOM_BOT_ID` and `WECOM_SECRET` required | Set both env vars or use `hermes gateway setup` |
| `aiohttp not installed` | `pip install aiohttp` |
| `httpx not installed` | `pip install httpx` |
| `invalid secret (errcode=40013)` | Verify secret matches bot's credentials |
| `Timed out waiting for subscribe acknowledgement` | Check network to `openws.work.weixin.qq.com` |
| Bot doesn't respond in groups | Check `group_policy` and `group_allow_from` |
| Bot ignores certain users in a group | Check per-group `allow_from` lists |
| Media decryption fails | `pip install cryptography` |
| Voice messages sent as files | Only AMR supported for native voice |
| File too large | 20 MB absolute limit — compress or split |
| Images sent as files | Images >10 MB auto-downgraded |
| Timeout sending message | WebSocket may be disconnected — check logs |
| `invalid bot_id` | Verify bot_id is the AI Bot ID, not Corp ID |
