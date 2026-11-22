"""打发布包：把运行时文件 + 词典 + 插件 + 说明组装成 dist/zen-trails-zh/，再压成 zip。

用法（仓库根目录执行）：
    uv run python tools/package.py             # 重建 dist/zen-trails-zh/ 并重新打 zip
    uv run python tools/package.py --verify    # 只重新组装+打包到临时目录，与现有 zip 比对
    uv run python tools/package.py --rebuild-plugin   # 先重新编译插件再打

运行时文件（BepInEx core/plugins、doorstop、字体 bundle）从游戏目录取，默认 paths.GAME，
可用 --game 或环境变量 ZEN_TRAILS_HOME 指定；词典由 tools/build.py + tools/adddict.py
从 translation/ 现生成，不复制游戏目录里的旧文件，所以打出来的包和源码一致。
"""
import os as _os, sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
import paths  # noqa: E402

import argparse
import os
import shutil
import subprocess
import zipfile

REL = "BepInEx/Translation/zh-CN/Text"

# 从游戏目录原样带走的运行时文件
RUNTIME_TOP = ["winhttp.dll", "doorstop_config.ini", ".doorstop_version"]
RUNTIME_DIRS = ["BepInEx/core"]
RUNTIME_FILES = [
    "BepInEx/config/AutoTranslatorConfig.ini",
    "BepInEx/config/BepInEx.cfg",
    "BepInEx/config/gravydevsupreme.xunity.resourceredirector.cfg",
    "BepInEx/plugins/README (AutoTranslator).md",
    "BepInEx/plugins/XUnity.AutoTranslator",
    "BepInEx/plugins/XUnity.ResourceRedirector",
    "arialuni_sdf_u2019",                      # 中文字体 bundle
]
# AutoTranslator 的空占位文件（可有可无，有就带上）
PLACEHOLDERS = ["_Preprocessors.txt", "_Postprocessors.txt", "_Substitutions.txt"]

ZIP_NAME = "ZenTrails-中文汉化-v1.1.zip"

# 控制台/管道按 UTF-8 输出，避免中文在 GBK 终端里变乱码
try:
    _sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass


def log(msg):
    print(msg, flush=True)


def need(path):
    if not os.path.exists(path):
        raise SystemExit("缺少 %s（游戏目录可用 --game 或 ZEN_TRAILS_HOME 指定）" % path)
    return path


def copy_tree(src, dst):
    if os.path.isdir(src):
        shutil.copytree(src, dst, dirs_exist_ok=True)
    else:
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        shutil.copy2(src, dst)


def build_plugin(stage):
    """编译插件并放进 staging。"""
    out_dll = os.path.join(paths.OUT, "ZenTrailsCN.dll")
    log("· 编译插件")
    subprocess.run(["powershell", "-ExecutionPolicy", "Bypass", "-File",
                    os.path.join(paths.PLUGIN, "build.ps1")], check=True)
    need(out_dll)
    dst = os.path.join(stage, "BepInEx/plugins/ZenTrailsCN.dll")
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    shutil.copy2(out_dll, dst)


def build_dict(stage):
    """用仓库里的 translation/ 现生成三个词典，写进 staging。"""
    text_dir = os.path.join(stage, REL)
    os.makedirs(text_dir, exist_ok=True)
    for script in ("build.py", "adddict.py"):
        log("· 生成词典 %s" % script)
        subprocess.run([_sys.executable, os.path.join(paths.TOOLS, script), "--out", text_dir],
                       check=True, stdout=subprocess.DEVNULL)
    for f in ("zhuanti.txt", "zh_extra.txt", "zz_regex.txt"):
        need(os.path.join(text_dir, f))


def stage_all(game, stage, rebuild_plugin):
    if os.path.isdir(stage):
        shutil.rmtree(stage)
    os.makedirs(stage, exist_ok=True)

    log("· 收集运行时文件（%s）" % game)
    for name in RUNTIME_TOP + RUNTIME_DIRS + RUNTIME_FILES:
        copy_tree(need(os.path.join(game, name)), os.path.join(stage, name))

    for name in PLACEHOLDERS:
        src = os.path.join(game, "BepInEx/Translation/zh-CN/Text", name)
        if os.path.exists(src):
            copy_tree(src, os.path.join(stage, REL, name))

    build_dict(stage)

    if rebuild_plugin:
        build_plugin(stage)
    else:
        log("· 用已有的 out/ZenTrailsCN.dll（要重编加 --rebuild-plugin）")
        need(os.path.join(paths.OUT, "ZenTrailsCN.dll"))
        copy_tree(os.path.join(paths.OUT, "ZenTrailsCN.dll"),
                  os.path.join(stage, "BepInEx/plugins/ZenTrailsCN.dll"))

    log("· 放入安装说明")
    copy_tree(need(os.path.join(paths.DOCS, "安装说明.txt")), os.path.join(stage, "安装说明.txt"))


def make_zip(stage, zip_path):
    """按路径排序写 zip（与 .NET CreateFromDirectory 一致：不写目录条目）。"""
    entries = []
    for dirpath, _, filenames in os.walk(stage):
        for fn in filenames:
            full = os.path.join(dirpath, fn)
            entries.append((os.path.relpath(full, stage).replace(os.sep, "/"), full))
    entries.sort()
    if os.path.exists(zip_path):
        os.remove(zip_path)
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as z:
        for name, full in entries:
            z.write(full, name)
    return len(entries)


def crc_map(zip_path):
    with zipfile.ZipFile(zip_path) as z:
        return {i.filename: i.CRC for i in z.infolist()}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--game", default=paths.GAME)
    ap.add_argument("--verify", action="store_true", help="与现有发布包比对，不覆盖")
    ap.add_argument("--rebuild-plugin", action="store_true", help="先重新编译插件")
    args = ap.parse_args()

    stage = os.path.join(paths.DIST, "_stage")
    stage_all(args.game, stage, args.rebuild_plugin)

    files = sum(len(f) for _, _, f in os.walk(stage))
    size = sum(os.path.getsize(os.path.join(d, f)) for d, _, fs in os.walk(stage) for f in fs)
    log("· 组装完成：%d 个文件，%.1f MB" % (files, size / 1048576.0))

    if args.verify:
        tmp_zip = os.path.join(paths.DIST, "_verify.zip")
        make_zip(stage, tmp_zip)
        old_zip = os.path.join(paths.DIST, ZIP_NAME)
        if not os.path.exists(old_zip):
            log("没有现成的发布包可比对：%s" % old_zip)
        else:
            a, b = crc_map(old_zip), crc_map(tmp_zip)
            diff = sorted(set(a) ^ set(b))
            bad = sorted(k for k in set(a) & set(b) if a[k] != b[k])
            log("\n比对 %s：" % os.path.basename(old_zip))
            log("  条目数  旧 %d / 新 %d" % (len(a), len(b)))
            log("  仅一侧有: %s" % (diff or "无"))
            if bad:
                log("  内容不同: %s" % ", ".join(bad))
                if all(k.endswith("ZenTrailsCN.dll") for k in bad):
                    log("  （只有插件不同：重新编译的 MVID/时间戳不一样，属正常）")
            else:
                log("  内容不同: 无（逐字节一致）")
        shutil.rmtree(stage, ignore_errors=True)
        os.remove(tmp_zip)
        return

    zip_path = os.path.join(paths.DIST, ZIP_NAME)
    n = make_zip(stage, zip_path)
    shutil.rmtree(stage, ignore_errors=True)
    log("· 打包完成：%s（%d 条目，%.1f MB）"
        % (zip_path, n, os.path.getsize(zip_path) / 1048576.0))


if __name__ == "__main__":
    main()
