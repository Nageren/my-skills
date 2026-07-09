---
name: autoclaw-im-cron
description: >
  Create scheduled tasks or reminders from AutoClaw IM channels. Use this for
  QQ, Weixin, DingTalk, Feishu, and WeCom when the user asks to create, list,
  remove, or test a scheduled IM task, reminder, cron job, or delayed reply.
---

# AutoClaw IM Cron

Use the unified `im_remind` tool first for IM scheduled tasks.

Supported channels:
- QQ: `qqbot`
- Weixin: `openclaw-weixin`
- DingTalk: `dingtalk-connector`
- Feishu: `feishu`
- WeCom: `wecom`

Rules:
- For creation from an IM conversation, do not manually construct raw `cron` JSON. Call `im_remind`.
- Do not use legacy channel tools such as `qqbot_remind` or `dingtalk_remind` for new IM scheduled tasks unless `im_remind` is unavailable.
- Keep the target as the current IM conversation unless the user explicitly asks for another target and the current sender is allowed.
- For repeated interval tasks such as "每30秒执行一次" or "每隔5分钟", call `im_remind` with `everyMs` or set `repeat: true` / `scheduleMode: "every"`. Do not reduce "每30秒" to a one-shot `time: "30s"`.
- For fixed text tasks such as "只回复...", set `executionMode` to `direct_reply`.
- For tasks that should decide wording, call tools, query data, or send richer content, set `executionMode` to `agent_task`.
- If unsure, use `executionMode: "auto"` and put the user's requested execution content in `content`.

Typical one-shot call:

```json
{
  "action": "add",
  "name": "example-once",
  "time": "1分钟后",
  "content": "只回复「[IM] once fired at 当前时间」",
  "executionMode": "direct_reply"
}
```

Typical flexible task:

```json
{
  "action": "add",
  "name": "example-free",
  "everyMs": 30000,
  "content": "结合当前时间，自由发挥提醒我检查今天的任务进展。",
  "executionMode": "agent_task"
}
```
