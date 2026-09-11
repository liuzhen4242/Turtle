#!/bin/bash
# Turtle — Mac 一键编译
# 用法：双击运行（首次需 chmod +x build.command），或终端里 ./build.command

set -e
cd "$(dirname "$0")"

echo "==> 检查 dotnet..."
if ! command -v dotnet >/dev/null 2>&1; then
    echo "未找到 dotnet，请先安装 .NET 7 SDK: https://dotnet.microsoft.com/download" >&2
    exit 1
fi

echo "==> 还原依赖并编译 Release..."
dotnet build -c Release

echo ""
echo "编译成功：bin/Release/net7.0/Turtle.rhp"
echo "把 Turtle.rhp 和 Turtle.rui 放在同一文件夹，拖进 Rhino 窗口即可加载。"
