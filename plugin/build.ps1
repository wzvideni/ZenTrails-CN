<#
  编译界面微调插件 ZenTrailsCN.dll

  用法（在本仓库根目录）：
      powershell -ExecutionPolicy Bypass -File plugin\build.ps1
      powershell -ExecutionPolicy Bypass -File plugin\build.ps1 -Deploy    # 顺便装进游戏目录

  游戏目录默认取环境变量 ZEN_TRAILS_HOME，没有的话按 Steam 的常见安装位置拼出来；
  也可以用 -Game 显式指定。仓库内路径都以本脚本位置为基准，整个仓库可以随意搬动。
  产物：out\ZenTrailsCN.dll
#>
param(
    [string]$Game = $(if ($env:ZEN_TRAILS_HOME) { $env:ZEN_TRAILS_HOME }
                      else { Join-Path ${env:ProgramFiles(x86)} "Steam\steamapps\common\Zen Trails" }),
    [switch]$Deploy
)

$ErrorActionPreference = "Stop"

$Repo    = Split-Path $PSScriptRoot -Parent          # 仓库根目录
$Csc     = Join-Path $env:WINDIR "Microsoft.NET\Framework64\v4.0.30319\csc.exe"
$Managed = Join-Path $Game "Zen Trails_Data\Managed"
$OutDir  = Join-Path $Repo "out"
$OutDll  = Join-Path $OutDir "ZenTrailsCN.dll"

if (-not (Test-Path $Csc))     { throw "找不到 csc.exe: $Csc" }
if (-not (Test-Path $Managed)) { throw "找不到游戏托管程序集目录: $Managed（可用 -Game 或 ZEN_TRAILS_HOME 指定游戏目录）" }

New-Item -ItemType Directory -Force -Path $OutDir | Out-Null

$refs = @(
    (Join-Path $Game    "BepInEx\core\BepInEx.dll"),
    (Join-Path $Managed "UnityEngine.dll"),
    (Join-Path $Managed "UnityEngine.CoreModule.dll"),
    (Join-Path $Managed "UnityEngine.UI.dll"),
    (Join-Path $Managed "UnityEngine.UIModule.dll"),
    (Join-Path $Managed "UnityEngine.TextRenderingModule.dll"),
    (Join-Path $Managed "netstandard.dll"),
    (Join-Path $Managed "Unity.TextMeshPro.dll")
)
foreach ($r in $refs) {
    if (-not (Test-Path $r)) { throw "缺少引用: $r" }
}

$cargs = @("/nologo", "/target:library", "/out:$OutDll")
foreach ($r in $refs) { $cargs += "/r:`"$r`"" }
$cargs += (Join-Path $PSScriptRoot "ZenTrailsCN.cs")

& $Csc @cargs
if ($LASTEXITCODE -ne 0) { throw "编译失败 (exit $LASTEXITCODE)" }

$item = Get-Item $OutDll
"OK  $($item.FullName)  $($item.Length) B"

if ($Deploy) {
    $dst = Join-Path $Game "BepInEx\plugins\ZenTrailsCN.dll"
    Copy-Item $OutDll $dst -Force
    "已安装 -> $dst（重启游戏生效）"
}
