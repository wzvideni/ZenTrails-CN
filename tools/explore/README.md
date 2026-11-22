# tools/explore（存档）

这里是摸索阶段用的一次性脚本，保留下来是为了说明当时是怎么拿到数据的，**不是稳定工具**：

- `dump_us.py` / `scan_text.py` / `scan2.py` / `filter_text.py` / `make_csv.py` / `mklist.py`
  从 `Zen Trails_Data` 的 assets 里扒字符串，最终产出 `translation/ZenTrails_文本清单.csv`
- `dump_tmp*.py` / `dump_ugui.py` / `dump_scripts.py`
  导出 TextMeshPro / UGUI 的层级与文本，用来核对界面用词
- `font_probe.py`
  列出 TMP 字体图集里实际存在的字形，产出 `translation/font_chars.json`
- `shot.py` / `shot2.py` / `pwcap.py` / `mouse.py` / `pclick.py` / `crop.py`
  早期抓图与模拟输入的尝试，后来被 `tools/ctl.py` 取代
- `qa.py` / `tour.py` / `drive.py`
  配合调试插件的半自动巡检，依赖 `tools/ctl.py`

注意：这些脚本用的是 `tools/paths.py` 里的统一约定（仓库内路径相对仓库定位，游戏目录见 `ZEN_TRAILS_HOME`），换机器或搬目录都不需要改代码；不过它们依赖的中间产物（`scratch/*.json`、`asm_us.json` 之类）只在当初的机器上生成过，重跑需要先按顺序把上游脚本跑一遍。
