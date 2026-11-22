"""统一的路径约定。

仓库内的目录一律以本文件为基准（纯相对定位，整个仓库可以随意搬动）；
游戏安装目录在仓库之外，用环境变量 ZEN_TRAILS_HOME 覆盖，默认按 Steam 的常见安装位置拼出来。
"""
import os

# ---------- 仓库内（相对本文件） ----------
TOOLS = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(TOOLS)
TRANSLATION = os.path.join(ROOT, "translation")   # 词条源文件
PLUGIN = os.path.join(ROOT, "plugin")             # 插件源码
DOCS = os.path.join(ROOT, "docs")
OUT = os.path.join(ROOT, "out")                   # 插件编译产物
DIST = os.path.join(ROOT, "dist")                 # 发布包
SCRATCH = os.path.join(ROOT, "scratch")           # 中间产物
SHOTS = os.path.join(ROOT, "shots")               # 过程截图
DUMPS = os.path.join(ROOT, "dumps")               # 调试插件 F9 导出的界面树

# ---------- 游戏安装目录（仓库外，可用环境变量覆盖） ----------
GAME = os.environ.get("ZEN_TRAILS_HOME") or os.path.join(
    os.environ.get("ProgramFiles(x86)", "C:\\Program Files (x86)"),
    "Steam", "steamapps", "common", "Zen Trails",
)

BEPINEX = os.path.join(GAME, "BepInEx")
TEXT_DIR = os.path.join(BEPINEX, "Translation", "zh-CN", "Text")   # 词典落盘位置
DATA = os.path.join(GAME, "Zen Trails_Data")                       # Unity 资源
MANAGED = os.path.join(DATA, "Managed")
ASSEMBLY_CSHARP = os.path.join(MANAGED, "Assembly-CSharp.dll")
FONT_BUNDLE = os.path.join(GAME, "arialuni_sdf_u2019")             # 中文字体 bundle
DUMP_TEXTS = os.path.join(BEPINEX, "dump_texts.txt")
DIAG = os.path.join(BEPINEX, "diag.txt")
CLICK_REQ = os.path.join(BEPINEX, "click_req.txt")
CLICK_LOG = os.path.join(BEPINEX, "click_log.txt")
PLUGINS = os.path.join(BEPINEX, "plugins")


def scratch(*parts):
    """scratch/ 下的路径，例如 scratch("tmp_texts.json")。"""
    return os.path.join(SCRATCH, *parts)


def translation(*parts):
    """translation/ 下的路径，例如 translation("zh_01.txt")。"""
    return os.path.join(TRANSLATION, *parts)


def has_game():
    """游戏目录在不在（脚本里做前置检查用）。"""
    return os.path.isdir(GAME)


if __name__ == "__main__":
    for k in ("ROOT", "TRANSLATION", "GAME", "TEXT_DIR", "DATA"):
        print("%-12s %s" % (k, globals()[k]))
    print("%-12s %s" % ("game ok", has_game()))
