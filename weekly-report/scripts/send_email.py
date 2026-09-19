#!/usr/bin/env python3
"""
发送企业微信周报邮件。
用法:
  python3 scripts/send_email.py <收件人邮箱> <邮件标题> <邮件正文文件路径>

如果 himalaya SMTP 发送失败，用此脚本作为 fallback。
"""

import smtplib
import sys
from email.mime.text import MIMEText

SMTP_HOST = "smtp.exmail.qq.com"
SMTP_PORT = 465
SMTP_USER = "mawenlei@wanlianyida.com"
PASSWORD_FILE = "/Users/marvin/.config/himalaya/password"


def send(to: str, subject: str, body_file: str) -> None:
    with open(PASSWORD_FILE) as f:
        pwd = f.read().strip()

    with open(body_file) as f:
        content = f.read()

    # 如果文件包含原始邮件头，只取正文部分
    parts = content.split('\n\n', 1)
    body = parts[1] if len(parts) > 1 else parts[0]

    msg = MIMEText(body, 'plain', 'utf-8')
    msg['Subject'] = subject
    msg['From'] = f'马文磊 <{SMTP_USER}>'
    # 支持逗号分隔的多收件人
    if ',' in to:
        msg['To'] = ', '.join(a.strip() for a in to.split(','))
    else:
        msg['To'] = to

    with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT) as s:
        s.login(SMTP_USER, pwd)
        # send_message 会自动处理多收件人
        s.send_message(msg)


if __name__ == '__main__':
    if len(sys.argv) != 4:
        print(f"用法: {sys.argv[0]} <收件人> <标题> <正文文件>")
        sys.exit(1)
    send(sys.argv[1], sys.argv[2], sys.argv[3])
    print(f"✅ 已发送到 {sys.argv[1]}")
