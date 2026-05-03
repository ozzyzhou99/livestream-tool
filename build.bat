@echo off
chcp 65001 >nul
title LiveStreamTool - Build

:: 用绝对路径定位 conda 环境中的 pyinstaller，避免 activate 失效问题
set CONDA_ENV=%USERPROFILE%\anaconda3\envs\livestream
set PYINSTALLER=%CONDA_ENV%\Scripts\pyinstaller.exe

echo.
echo ==========================================
echo   直播解析工具 - 打包 exe
echo ==========================================
echo.

:: 检查 pyinstaller 是否存在
if not exist "%PYINSTALLER%" (
    echo [错误] 未找到 PyInstaller：
    echo   %PYINSTALLER%
    echo.
    echo 请先运行 setup_conda.bat 安装依赖。
    pause
    exit /b 1
)

:: 进入项目目录（bat 所在目录）
cd /d "%~dp0"

:: 清理旧构建
echo [1/3] 清理旧构建文件...
if exist build  rmdir /s /q build
if exist dist   rmdir /s /q dist

:: 显式指定 Tcl/Tk 路径，避免版本冲突
set TCL_LIB=%CONDA_ENV%\Library\lib\tcl8.6
set TK_LIB=%CONDA_ENV%\Library\lib\tk8.6
set TCL_DLL=%CONDA_ENV%\Library\bin\tcl86t.dll
set TK_DLL=%CONDA_ENV%\Library\bin\tk86t.dll

:: 打包
echo [2/3] 开始打包（约 1~3 分钟）...
set TCL_LIBRARY=%TCL_LIB%
set TK_LIBRARY=%TK_LIB%
"%PYINSTALLER%" ^
    --onefile ^
    --windowed ^
    --name LiveStreamTool ^
    --collect-all streamlink ^
    --hidden-import streamlink.plugins ^
    --hidden-import yt_dlp ^
    --hidden-import tkinter ^
    --hidden-import tkinter.ttk ^
    --add-data "%TCL_LIB%;tcl8.6" ^
    --add-data "%TK_LIB%;tk8.6" ^
    --add-binary "%TCL_DLL%;." ^
    --add-binary "%TK_DLL%;." ^
    src\main.py

if errorlevel 1 (
    echo.
    echo [错误] 打包失败，请查看上方错误信息。
    pause
    exit /b 1
)

echo.
echo [3/3] 打包完成！
echo.
echo   输出文件：dist\LiveStreamTool.exe
echo   可直接复制到任意位置双击运行（无需 Python）。
echo.
pause
