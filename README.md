# TVBox 综合源（tvbox-merge）

把以下多套源合并为**一个订阅地址**，并**每 4 小时**重建、核查各源地址有效性：

| 来源 | 内容 |
|---|---|
| hubeizgd1979/tvbox-config | 自己的 TVBOX 配置源（164 影视源 + 37 直播组，每天自动更新） |
| hubeizgd1979/tvbox (qist/tvbox) | OK影视配置全家桶（js.json，298 源） |
| hubeizgd1979/tvbox-ysc-config | 影视仓配置聚合（肥猫/饭太硬/王二小/讴歌/小盒子/4K 等 10 源每日自动更新，517 源） |
| 大佬们的公共接口 | 饭太硬/肥猫/摸鱼/王二小/欧歌/凯速/小盒子4K/二月红/菜妮丝/宝盒/潇洒/苍蓝/catbox/影视仓/UUCCC/日后/真心/传说/蓝天/毒盒/小马/蜗牛/朱雀/动漫/茄子/小米/vox/L佬/分享/喵影/脑斧/心魔/雷蒙/道长/俊佬/枫斗 等 70+ 条最新接口 |

> 已按要求剔除成人源；枫斗接口（http://枫斗.top/tv）在影视仓里首次使用需输入激活码 **5678**。

## 订阅地址（填进影视仓/TVboxOSC 即可）

```
https://gh-proxy.com/https://raw.githubusercontent.com/hubeizgd1979/tvbox-merge/main/config_all.json
```

直连地址（国内可能慢）：

```
https://raw.githubusercontent.com/hubeizgd1979/tvbox-merge/main/config_all.json
```

当前实测规模：**740 影视源 + 26 直播**（构建时自动剔除失效源，规模随核查浮动）。

## 核查报告与自动剔除

每次运行生成 `status.json`：总源数 / 有效数 / 无效清单（HTTP 状态或超时原因），并在 Actions 页面的 Run 里展示。

- **自动剔除**：确定性无效（HTTP 4xx/5xx、DNS 解析失败、连接被拒）的源**立即从综合源剔除**；超时/SSL 等不稳定错误**连续两轮**核查无效才剔除。每轮从三套源全量重建，被误剔的源恢复有效后会自动重新加入，不会永久丢失。
- 自动运行：每 4 小时（北京 08:00 / 12:00 / 16:00 / 20:00 / 00:00 / 04:00）
- 手动运行：Actions → Merge all → Run workflow
