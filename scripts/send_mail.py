# -*- coding: utf-8 -*-
"""综合源更新后发送订阅通知邮件（由 GitHub Actions 调用）。

邮件内容：
  1) 最新订阅地址（gh-proxy + 直连）
  2) 订阅地址包含的接口清单（大佬公共接口 74 条 + 三套聚合源统计）
凭据全部来自环境变量（GitHub Actions Secrets）。发送失败不阻塞工作流。
"""
import os
import json
import smtplib
import ssl
from email.mime.text import MIMEText
from email.header import Header
from email.utils import formataddr

HOST = os.environ.get("SMTP_HOST", "smtp.qq.com")
PORT = int(os.environ.get("SMTP_PORT", "465"))
USER = os.environ.get("SMTP_USER", "")
PASS = os.environ.get("SMTP_PASS", "")
TO = os.environ.get("MAIL_TO", "")

SUB_URL = "https://gh-proxy.com/https://raw.githubusercontent.com/hubeizgd1979/tvbox-merge/main/config_all.json"
RAW_URL = "https://raw.githubusercontent.com/hubeizgd1979/tvbox-merge/main/config_all.json"


def load_status():
    try:
        with open("status.json", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def load_public_interfaces():
    """从 config_all.json 提取"公共·"前缀的 url 型接口清单。"""
    out = []
    try:
        with open("config_all.json", encoding="utf-8") as f:
            cfg = json.load(f)
        for s in cfg.get("sites", []):
            if isinstance(s, dict) and str(s.get("name", "")).startswith("公共·"):
                out.append((s.get("name", ""), s.get("url", "")))
    except Exception:
        pass
    return out


def load_ysc_info():
    """从 ysc_download.json 读取影视仓官网/版本/下载信息（构建时自动抓取）。"""
    try:
        with open("ysc_download.json", encoding="utf-8") as f:
            d = json.load(f)
        v = d.get("version", {}) or {}
        dl = d.get("download", {}) or {}
        return {
            "site": d.get("official_site", ""),
            "tv": v.get("tv", ""),
            "mobile": v.get("mobile", ""),
            "gate": dl.get("gate", ""),
            "pan": dl.get("pan_quark", ""),
            "notes": d.get("notes", ""),
        }
    except Exception:
        return None


def main():
    if not (USER and PASS and TO):
        print("SMTP 配置缺失，跳过发信")
        return

    st = load_status()
    total = st.get("total_sites", "-")
    lives = st.get("total_lives", "-")
    src = st.get("sources", {})

    def src_stat(key):
        v = src.get(key, {})
        if isinstance(v, dict):
            return "%s源/%s直播" % (v.get("sites", "-"), v.get("lives", "-"))
        return "-"

    lines = [
        "综合源已更新，最新订阅地址如下：",
        "",
        "【1. 最新订阅地址】",
        "订阅地址（推荐，国内加速）：",
        SUB_URL,
        "",
        "直连地址（国内较慢）：",
        RAW_URL,
        "",
        "【2. 订阅地址包含的接口】",
        "· 三套聚合源（自动合并去重 + 每4小时核查 + 无效自动剔除）：",
        "  - tvbox-config（影视仓配置源）：%s" % src_stat("tvbox-config"),
        "  - qist/tvbox（小苹果源）：%s" % src_stat("qist/tvbox"),
        "  - ysc 单仓聚合（肥猫/饭太硬/王二小等）：%s" % src_stat("ysc-单仓聚合(肥猫/饭太硬/王二小等)"),
        "  - 大佬公共接口：%s 条" % src.get("external(大佬公共接口)", {}).get("added", "-"),
        "",
        "· 大佬公共接口清单：",
    ]
    for i, (nm, u) in enumerate(load_public_interfaces(), 1):
        lines.append("  %d. %s %s" % (i, nm, u))
    if not load_public_interfaces():
        lines.append("  （暂无公共接口条目）")

    ysc = load_ysc_info()
    if ysc and ysc.get("site"):
        lines += [
            "",
            "【3. 影视仓（TVBox 二开版）下载】",
            "  官网: %s" % ysc.get("site", ""),
            "  最新版本: TV版 %s / 手机版 %s" % (ysc.get("tv", "?"), ysc.get("mobile", "?")),
            "  下载入口: 官网点「TV版下载」（盒子/大屏）或「手机版下载」，自动跳转网盘",
            "  网盘直链: %s" % ysc.get("pan", ""),
        ]
        if ysc.get("gate"):
            lines.append("  中转页: %s" % ysc.get("gate", ""))
        if ysc.get("notes"):
            lines.append("  备注: %s" % ysc.get("notes", ""))
    else:
        lines += [
            "",
            "【3. 影视仓（TVBox 二开版）下载】",
            "  （本次构建未抓到官网信息，请直接访问 https://ysctvbox.github.io/ ）",
        ]

    lines += [
        "",
        "【本次核查统计】",
        "  影视源: %s 个 | 直播组: %s 个" % (total, lives),
        "  核查: %s 有效 / %s 跳过 / %s 待观察" % (
            st.get("valid_urls", "-"), st.get("skipped_urls", "-"), st.get("invalid_count", "-")),
        "  自动剔除无效: %s 条" % st.get("removed_count", "-"),
        "  生成时间: %s" % st.get("generated_at", "-"),
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
        print("MAIL SENT ->", TO, "| interfaces:", len(load_public_interfaces()))
    except Exception as e:
        print("MAIL FAIL (non-blocking):", repr(e))


if __name__ == "__main__":
    main()
