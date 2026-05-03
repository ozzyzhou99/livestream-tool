@echo off
chcp 65001 >nul
title 直播解析工具 — Conda 环境配置

echo.
echo ╔══════════════════════════════════════════════╗
echo ║   直播解析工具 — Conda 环境配置脚本           ║
echo ╚══════════════════════════════════════════════╝
echo.

:: 检查 conda 是否可用
where conda >nul 2>&1
if errorlevel 1 (
    echo [错误] 未检测到 conda 命令。
    echo        请先安装 Anaconda 或 Miniconda，并确保已添加到 PATH。
    echo        下载地址: https://docs.conda.io/en/latest/miniconda.html
    pause
    exit /b 1
)

echo [1/4] 检查环境 "livestream" 是否已存在...
conda env list | findstr /C:"livestream" >nul 2>&1
if not errorlevel 1 (
    echo       环境已存在，跳过创建步骤。
    goto activate
)

echo [1/4] 创建 conda 环境 "livestream"（Python 3.11）...
conda create -n livestream python=3.11 -y
if errorlevel 1 (
    echo [错误] 创建环境失败，请检查网络连接或 conda 配置。
    pause
    exit /b 1
)

:activate
echo.
echo [2/4] 激活环境 "livestream"...
call conda activate livestream
if errorlevel 1 (
    echo [错误] 激活环境失败。
    pause
    exit /b 1
)

echo.
echo [3/4] 安装依赖包...
pip install -r requirements.txt
if errorlevel 1 (
    echo [警告] 部分包安装失败，请检查错误信息。
)

echo.
echo [4/4] 验证安装...
python -c "import streamlink; print('  streamlink:', streamlink.__version__)"
python -c "import yt_dlp; print('  yt-dlp:    ', yt_dlp.version.__version__)"
python -c "import PyInstaller; print('  PyInstaller:', PyInstaller.__version__)"

echo.
echo ══════════════════════════════════════════════
echo   环境配置完成！
echo   使用方法：
echo     运行工具   →  双击 run.bat
echo     打包 exe   →  双击 build.bat
echo ══════════════════════════════════════════════
echo.
pause
