# -*- coding: utf-8 -*-
"""综合源更新后发送订阅地址通知邮件（由 GitHub Actions 调用）。

凭据全部来自环境变量（GitHub Actions Secrets），不落盘不进代码。
发送失败不阻塞工作流（打印警告并正常退出）。
"""
import os
import json
import smtplib
import ssl
from email.mime.text import MIMEText
from email.header import Header
from email.utils import formataddr

HOST = os.environ.get("SMTP_HOST", "smtp.139.com")
PORT = int(os.environ.get("SMTP_PORT", "465"))
USER = os.environ.get("SMTP_USER", "")
PASS = os.environ.get("SMTP_PASS", "")
TO = os.environ.get("MAIL_TO", "")

SUB_URL = "https://gh-proxy.com/https://raw.githubusercontent.com/hubeizgd1979/tvbox-merge/main/config_all.json"
RAW_URL = "https://raw.githubusercontent.com/hubeizgd1979/tvbox-merge/main/config_all.json"


def main():
    if not (USER and PASS and TO):
        print("SMTP 配置缺失，跳过发信")
        return
    summary = {}
    try:
        with open("status.json", encoding="utf-8") as f:
            summary = json.load(f)
    except Exception:
        pass
    total = summary.get("total_sites", "-")
    lines = [
        "综合源已更新，订阅地址如下：",
        "",
        "订阅地址（推荐，国内加速）：",
        SUB_URL,
        "",
        "直连地址：",
        RAW_URL,
        "",
        "本次统计：",
        "  影视源: %s 个" % total,
        "  直播组: %s 个" % summary.get("total_lives", "-"),
        "  核查: %s 有效 / %s 跳过 / %s 待观察" % (
            summary.get("valid_urls", "-"), summary.get("skipped_urls", "-"), summary.get("invalid_count", "-")),
        "  自动剔除无效: %s 条" % summary.get("removed_count", "-"),
        "  生成时间: %s" % summary.get("generated_at", "-"),
        "",
        "影视仓 / TVboxOSC 填入上方订阅地址即可，每 4 小时自动更新。",
    ]
    msg = MIMEText("\n".join(lines), "plain", "utf-8")
    msg["Subject"] = Header("[综合源] 订阅已更新（%s 源）" % total, "utf-8")
    msg["From"] = formataddr(("综合源自动通知", USER))
    msg["To"] = TO
    try:
        ctx = ssl.create_default_context()
        with smtplib.SMTP_SSL(HOST, PORT, context=ctx, timeout=30) as s:
            s.login(USER, PASS)
            s.sendmail(USER, [TO], msg.as_string())
        print("MAIL SENT ->", TO)
    except Exception as e:
        print("MAIL FAIL (non-blocking):", repr(e))


if __name__ == "__main__":
    main()
