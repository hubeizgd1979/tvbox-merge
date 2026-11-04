# -*- coding: utf-8 -*-
"""抓取影视仓官网下载页/版本信息，生成 ysc_download.json（每次构建自动刷新）。

数据链路：官网 ysctvbox.github.io → 下载按钮 tvbox666.pages.dev → 夸克网盘。
抓取任一环节失败时保留旧文件，不阻塞综合源构建。
"""
import json
import os
import re
import time
import urllib.request

URL = "https://ysctvbox.github.io/"
GATE = "https://tvbox666.pages.dev/"
OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "ysc_download.json")


def fetch(url, timeout=30):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read().decode("utf-8", "replace")


def main():
    info = {
        "name": "影视仓TVBox二开版(官方下载信息)",
        "official_site": URL,
        "fetched_at": time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime()),
        "version": {},
        "download": {},
        "raw_title": "",
        "notes": "认准影视仓TVBox二开版(YSCTVbox)，勿与贵阳惠跃同名商业App混淆；TV版适配盒子大屏",
    }
    # 1) 官网
    try:
        html = fetch(URL)
        m = re.search(r"<title[^>]*>(.*?)</title>", html, re.S)
        info["raw_title"] = m.group(1).strip() if m else ""
        m = re.search(r"<h1[^>]*>(.*?)</h1>", html, re.S)
        h1 = re.sub(r"<[^>]+>", "", m.group(1)).strip() if m else ""
        info["title_h1"] = h1
        vm = re.search(r"v?(\d+\.\d+\.\d+)\s*/\s*v?(\d+\.\d+\.\d+)", h1)
        if vm:
            info["version"] = {"mobile": "v" + vm.group(1), "tv": "v" + vm.group(2)}
        else:
            vers = re.findall(r"v?\d+\.\d+(?:\.\d+)?", html)
            info["version"]["all_seen"] = sorted(set(vers), key=len, reverse=True)[:8]
        # 下载按钮
        for label, key in (("TV版下载", "tv"), ("手机版下载", "mobile")):
            mm = re.search(r'<a[^>]+href=["\']([^"\']+)["\'][^>]*>\s*' + re.escape(label), html)
            info["download"][key] = mm.group(1) if mm else None
    except Exception as e:
        info["fetch_error_official_site"] = repr(e)
    # 2) 下载中转页 → 网盘
    try:
        gh = fetch(GATE)
        info["download"]["gate"] = GATE
        m = re.search(r"https://pan\.quark\.cn/s/[A-Za-z0-9]+", gh)
        if m:
            info["download"]["pan_quark"] = m.group(0)
        else:
            info["download"]["pan_quark"] = None
    except Exception as e:
        info["fetch_error_gate"] = repr(e)

    # 保留旧数据（部分抓取失败时合并）
    if os.path.exists(OUT):
        try:
            old = json.load(open(OUT, encoding="utf-8"))
        except Exception:
            old = {}
        for k, v in old.items():
            info.setdefault(k, v)

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(info, f, ensure_ascii=False, indent=2)
    print(json.dumps(info, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
