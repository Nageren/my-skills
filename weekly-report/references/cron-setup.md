# Cron Job 设置参考

## 关键配置项

### deliver 设置（重要）

`deliver` 必须设为 `"origin"`，这样生成的周报草稿才会发到会话让用户确认。

| 值 | 行为 |
|---|---|
| `"origin"` | 输出发送到当前会话（推荐） |
| `"local"` | 只保存到本地 ~/.hermes/cron/output/（用户看不到草稿 ❌） |

### prompt 必须包含「先确认后发送」

Cron prompt 中要显式写出以下步骤，不可省略：

```
3. **将生成的周报草稿发送到当前会话，向用户确认。收到用户的明确确认指令后再发送邮件。用户没说确认之前，绝对不能发送。**
```

### 发送方式

不要用 `himalaya envelope send` 或 `himalaya message send`，可能因为 IMAP sent-folder 保存问题报错。
改用 `python3 scripts/send_email.py <收件人> <标题> <正文文件>`。

## 常出问题

1. **草稿没有出现在会话中** → 检查 cron job 的 `deliver` 是否设为 `"origin"`
2. **himalaya 发送报错** → 改用 send_email.py（Python smtplib 直连）
3. **用户没看到草稿就发了** → prompt 中缺少「先确认后发送」的强制步骤
