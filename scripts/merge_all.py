# -*- coding: utf-8 -*-
"""合并综合源：tvbox-config + qist/tvbox + tvbox-ysc-config(单仓聚合) + 大佬们的最新公共接口，
并核查每个源地址有效性。

TVBox 新版配置格式：sites 条目的接口位于 api/ext/jar 字段（csp_xxx 爬虫函数名 或 ./lib/xxx.js 相对路径），
公共接口为 url 型条目（远程订阅）。核查时收集 api/ext/jar 中的 http 地址、相对路径（解析到所属源 raw 基址）、
以及 url 型条目，连同 lives 的 url 一并检查。

产物：
  config_all.json  综合订阅配置（sites/lives/parses/flags 去重合并 + 公共接口）
  status.json      核查报告（总源数 / 有效数 / 无效清单 / 各来源统计）
"""
import json
import urllib.request
import urllib.error
import urllib.parse
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

UA = "Mozilla/5.0 (Linux; Android 11; TV) AppleWebKit/537.36 TVBox/1.0 okhttp/3.15"
TIMEOUT = 6
FETCH_TIMEOUT = 60

SOURCES = {
    "tvbox-config": "https://raw.githubusercontent.com/hubeizgd1979/tvbox-config/main/dist/config.json",
    "qist/tvbox": "https://raw.githubusercontent.com/hubeizgd1979/tvbox/master/js.json",
    "ysc-单仓聚合(肥猫/饭太硬/王二小等)": "https://raw.githubusercontent.com/hubeizgd1979/tvbox-ysc-config/main/output/"
    + urllib.parse.quote("单仓聚合.json"),
}

# 大佬们的最新公共接口（用户提供清单 + Excel + gitlab 道长接口）
EXTERNAL_INTERFACES = [
    ("枫斗(激活码5678)", "http://枫斗.top/tv"),
    ("饭太硬.cc", "http://www.饭太硬.cc/tv"),
    ("饭太硬.net", "http://www.饭太硬.net/tv"),
    ("饭太硬.xxooo", "http://fty.xxooo.cf/tv"),
    ("饭太硬.art", "http://www.饭太硬.art/tv"),
    ("饭太硬.888484", "http://fty.888484.xyz/tv"),
    ("饭太硬.333232", "http://fty.333232.xyz/tv"),
    ("饭太硬.qist", "https://qist.wyfc.qzz.io/fty.json"),
    ("肥猫.net", "http://肥猫.net/"),
    ("肥猫.hello", "http://hello.肥猫.net"),
    ("肥猫.net/tv", "http://肥猫.net/tv"),
    ("肥猫.one", "https://9877.kstore.space/ONE/one.json"),
    ("肥猫.com", "http://肥猫.com"),
    ("摸鱼儿", "http://我不是.摸鱼儿.top"),
    ("摸鱼·小不点", "http://www.小不点.com"),
    ("王二小.newwex", "https://9280.kstore.vip/newwex.json"),
    ("王二小.top", "http://tvbox.王二小放牛娃.top"),
    ("王二小.999888987", "http://tv.999888987.xyz/"),
    ("王二小.999888123", "http://tv.999888123.xyz/"),
    ("王二小.wex", "https://9280.kstore.vip/wex.json"),
    ("王二小.iyouhun", "https://www.iyouhun.com/tv/wex"),
    ("王二小.punycode", "http://tvbox.xn--4kq62z5rby2qupq9ub.top"),
    ("欧歌.id3", "https://xn--sdds-rp5imh.v.nxog.top/apitv.php?id=3"),
    ("欧歌.id2", "https://xn--54qz74d.u.xn--dkw.xn--6qq986b3xl/apib.php?id=2"),
    ("欧歌.id3b", "https://xn--i8sz35d1yr.u.nxog.top/apib.php?id=3"),
    ("欧歌.id4", "https://xn--z7x900a.e.nxog.top/apib.php?id=4"),
    ("欧歌免费", "https://tv.nxog.top/m/111.php?ou=%E5%85%AC%E4%BC%97%E5%8F%B7%E6%AC%A7%E6%AD%8Capp&mz=index&jar=index&123&b=tv"),
    ("凯速", "https://6800.kstore.vip/fish.json"),
    ("小盒子4K", "http://xhztv.top/4k.json"),
    ("二月红", "https://700sjro44343.vicp.fun/eggp/0211/tv.json"),
    ("菜妮丝", "https://tv.菜妮丝.top"),
    ("宝盒", "https://宝盒接口.top"),
    ("潇洒", "https://qist.wyfc.qzz.io/xiaosa/api.json"),
    ("苍蓝.punycode", "http://xn--6orr3pi6g9uu.top"),
    ("苍蓝.kstore", "https://13537.kstore.vip/tvbox/test.json"),
    ("catbox", "https://catbox.n13.club/jk/t4.json"),
    ("影视仓", "http://影视仓.com/"),
    ("UUCCC", "http://xn--5mqx81b535a.com"),
    ("日后", "http://rihou.cc:555/nzk/nzk0722.json"),
    ("真心", "https://cnb.cool/fish2018/zx/-/git/raw/master/FongMi.json"),
    ("传说", "https://chuanshuo.77blog.cn/tv.json"),
    ("蓝天", "https://gitee.com/lukei7/lib/raw/Luck/%E8%87%AA%E5%BB%BA.json"),
    ("毒盒", "https://xn--8owq8u.com/tv/"),
    ("小马", "https://szyyds.cn/tv/x.json"),
    ("蜗牛", "https://tv.xn--11x555b.top/svip"),
    ("朱雀", "https://gitee.com/yiwu369/6758/raw/master/%E6%9C%B1%E9%9B%80/api.json"),
    ("动漫", "https://www.yingm.cc/dm/dm.json"),
    ("茄子", "https://700sjro44343.vicp.fun/eggp/qzku/tv.json"),
    ("小米", "http://miqk.cc/%E5%B0%8F%E7%B1%B3/DEMO.json"),
    ("vox", "https://code.onedev.io/vox/~raw/master/demo.json"),
    ("L佬", "https://android.lushunming.qzz.io/json/index.json"),
    ("分享", "http://hucongrong.web3v.work/%E9%A3%8E%E6%B0%B4/fxz/fxz.json"),
    ("喵影", "https://bitbucket.org/xduo/duoapi/raw/master/xpg.json"),
    ("脑斧", "https://6492.kstore.space/xnf/xnf.json"),
    ("心魔", "https://fastgit.cc/https://raw.githubusercontent.com/yw88075/tvbox/main/yw.json"),
    ("雷蒙", "https://fastgit.cc/https://raw.githubusercontent.com/n3rddd/N3RD/master/JN/lemj.json"),
    ("道长(同步)", "https://gitlab.com/duomv/dzhipy/-/raw/main/index.json"),
    ("俊佬", "http://home.jundie.top:81/top98.json"),
    ("少儿频道", "https://jihulab.com/ymz1231/xymz/-/raw/main/ymshaoer"),
    ("电视jsm", "https://raw.githubusercontent.com/qist/tvbox/master/jsm.json"),
    ("牛二", "https://9280.kstore.space/newwex.json"),
    ("fmys", "http://fmys.top/fmys.json"),
    ("麒麟影仓", "https://gitee.com/qlysgzs/qlys/raw/master/qlycZHCK.json"),
    ("ok", "https://raw.liucn.cc/box/m.json"),
    ("看戏网", "https://www.gunys.com/"),
    ("青苹果影视", "https://www.yzyunhai.com"),
    ("荐片", "https://tv.203511.xyz/0821.json"),
    ("my interface", "http://124.223.214.31:8/api.json"),
    ("vip", "https://700sjro44343.vicp.fun/vip/vip/tv.json"),
    ("cs", "http://tv.nxog.top/m/"),
    ("MyTV直播", "https://raw.githubusercontent.com/cwezhd/TVList/refs/heads/main/fenghuang.m3u"),
    ("软件", "http://47.96.82.41:5188/api.json"),
    ("我的fty", "https://codeberg.org/wei88976862/tvbox001/raw/branch/main/fty.json"),
    ("TVBox", "https://pastebin.com/raw/sbPpDm9G"),
]


def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=FETCH_TIMEOUT) as r:
        return r.read().decode("utf-8", "replace")


def name_key(s):
    return str(s.get("name") or "").strip() or str(s.get("key") or "").strip()


def live_key(l):
    u = (l.get("url") or "").strip()
    return ("u:" + u) if u else ("n:" + str(l.get("name") or "").strip())


def resolve(base_url, ref):
    """相对路径 -> 所属源 raw 基址下的绝对地址；非 URL 引用(如 csp_函数名/字典) 返回 None。"""
    ref = (ref or "").strip()
    if not ref or not isinstance(ref, str):
        return None
    if ref.startswith(("http://", "https://")):
        return ref.split(";")[0].split("|")[0].strip()
    if "://" in ref[:12]:
        return None
    if ref.startswith(("./", "/", "../")):
        base_dir = base_url.rsplit("/", 1)[0]
        p = ref[2:] if ref.startswith("./") else ref.lstrip("/")
        while p.startswith("../"):
            p = p[3:]
            base_dir = base_dir.rsplit("/", 1)[0]
        return base_dir + "/" + p
    return None


def collect_urls(j, base_url):
    """从一份源配置中收集候选核查 URL，附带 (类型, 名称, url)。"""
    cands = []
    for s in j.get("sites", []):
        nm = name_key(s)
        for fld in ("api", "ext", "jar"):
            v = s.get(fld)
            if isinstance(v, str):
                u = resolve(base_url, v)
                if u:
                    cands.append(("site", nm, u))
        u = (s.get("url") or "").strip()
        if u:
            cands.append(("site", nm, u))
    for lv in j.get("lives", []):
        u = (lv.get("url") or "").strip()
        if u:
            cands.append(("live", lv.get("name", ""), u))
    for p in j.get("parses", []):
        u = (p.get("url") or "").strip()
        if u:
            cands.append(("parse", p.get("name", ""), u))
    return cands


def check(url):
    """核查单个地址：返回 (ok, reason)。非 http(s)（127.0.0.1、clan:// 等）跳过不判无效。$$$ 多参数取首段。"""
    u = (url or "").strip()
    if not u or not u.startswith(("http://", "https://")):
        return True, "skip(非http)"
    if "$$$" in u:
        u = u.split("$$$")[0].strip()
    try:
        parts = urllib.parse.urlsplit(u)
        host = parts.hostname or ""
        if host in ("127.0.0.1", "localhost", "0.0.0.0"):
            return True, "skip(本地代理)"
        if any(ord(c) > 127 for c in host):
            host = host.encode("idna").decode("ascii")
        path = urllib.parse.quote(parts.path, safe="/%:@!$&'()*+,;=.-_~")
        query = urllib.parse.quote(parts.query, safe="=&?%:/[]@!$'()*+,;.-_~")
        u = urllib.parse.urlunsplit((parts.scheme, host, path, query, parts.fragment))
    except Exception as e:
        return False, "url-err:%s" % str(e)[:60]
    try:
        req = urllib.request.Request(u, headers={"User-Agent": UA}, method="GET")
        with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
            ok = 200 <= r.status < 400
            return ok, "http:%d" % r.status
    except urllib.error.HTTPError as e:
        return False, "http:%d" % e.code
    except Exception as e:
        return False, str(e)[:60]


def main():
    data = {}
    stats = {}
    for name, url in SOURCES.items():
        try:
            j = json.loads(fetch(url))
            data[name] = j
            stats[name] = {"fetch": "ok", "sites": len(j.get("sites", [])), "lives": len(j.get("lives", []))}
        except Exception as e:
            stats[name] = {"fetch": "err:%s" % str(e)[:80]}
            print("FETCH FAIL %s: %s" % (name, e))

    if not data:
        print("NO SOURCE FETCHED - abort")
        raise SystemExit(1)

    base = data.get("tvbox-config") or next(iter(data.values()))
    merged = dict(base)

    def merge_list(dst_key, key_fn):
        seen = {}
        for src_name in SOURCES:
            for item in data.get(src_name, {}).get(dst_key, []):
                if not isinstance(item, dict):
                    continue
                k = key_fn(item)
                if k and k not in seen:
                    seen[k] = item
        return list(seen.values())

    merged["sites"] = merge_list("sites", name_key)
    merged["lives"] = merge_list("lives", live_key)
    merged["parses"] = merge_list("parses", lambda p: "u:" + (p.get("url") or "").strip() if (p.get("url") or "").strip() else "n:" + str(p.get("name") or "").strip())
    merged["flags"] = merge_list("flags", lambda f: "n:" + str(f.get("name") or "").strip())

    # 追加大佬们的公共接口（url 型条目，按 url 去重，已存在则跳过）
    existing_urls = {norm(s.get("url")) for s in merged["sites"] if (s.get("url") or "").strip()}
    added = 0
    for nm, u in EXTERNAL_INTERFACES:
        if not u.strip():
            continue
        if norm(u) in existing_urls:
            continue
        merged["sites"].append({"name": "公共·" + nm, "url": u.strip()})
        existing_urls.add(norm(u))
        added += 1
    stats["external(大佬公共接口)"] = {"added": added}

    # 收集候选核查 URL
    cands = []
    for name in SOURCES:
        if name in data:
            cands += collect_urls(data[name], SOURCES[name])
    for nm, u in EXTERNAL_INTERFACES:
        if u.strip():
            cands.append(("site", "公共·" + nm, u.strip()))

    uniq = {}
    for typ, nm, u in cands:
        if u and u not in uniq:
            uniq[u] = (typ, nm)

    results = {}
    with ThreadPoolExecutor(max_workers=12) as ex:
        fut = {ex.submit(check, u): u for u in uniq}
        for f in as_completed(fut):
            u = fut[f]
            try:
                results[u] = f.result()
            except Exception as e:
                results[u] = (False, str(e)[:60])

    invalid = []
    valid_cnt = 0
    skipped = 0
    for u, (ok, reason) in results.items():
        typ, nm = uniq[u]
        if ok:
            if reason.startswith("skip"):
                skipped += 1
            else:
                valid_cnt += 1
        else:
            invalid.append({"type": typ, "name": nm, "url": u, "reason": reason})

    with open("config_all.json", "w", encoding="utf-8", newline="\n") as f:
        json.dump(merged, f, ensure_ascii=False, indent=1)

    status = {
        "generated_at": time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime()),
        "sources": stats,
        "total_sites": len(merged["sites"]),
        "total_lives": len(merged["lives"]),
        "checked_urls": len(results),
        "valid_urls": valid_cnt,
        "skipped_urls": skipped,
        "invalid_count": len(invalid),
        "invalid": invalid[:200],
    }
    with open("status.json", "w", encoding="utf-8", newline="\n") as f:
        json.dump(status, f, ensure_ascii=False, indent=1)

    print(json.dumps(status, ensure_ascii=False, indent=1))


def norm(u):
    u = (u or "").strip().rstrip("/")
    return u.lower() if u.startswith(("http://", "https://")) else u


if __name__ == "__main__":
    main()
