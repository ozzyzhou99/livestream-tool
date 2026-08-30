@echo off
setlocal
chcp 65001 >nul
cd /d "%~dp0"

set "ARENA_PYTHON="

if exist "%CD%\.venv\Scripts\python.exe" set "ARENA_PYTHON=%CD%\.venv\Scripts\python.exe"
if not defined ARENA_PYTHON if exist "%USERPROFILE%\anaconda3\envs\livestream\python.exe" set "ARENA_PYTHON=%USERPROFILE%\anaconda3\envs\livestream\python.exe"
if not defined ARENA_PYTHON if exist "%USERPROFILE%\miniconda3\envs\livestream\python.exe" set "ARENA_PYTHON=%USERPROFILE%\miniconda3\envs\livestream\python.exe"
if not defined ARENA_PYTHON if exist "%LOCALAPPDATA%\miniconda3\envs\livestream\python.exe" set "ARENA_PYTHON=%LOCALAPPDATA%\miniconda3\envs\livestream\python.exe"

if not defined ARENA_PYTHON where conda >nul 2>&1
if not defined ARENA_PYTHON if not errorlevel 1 (
    for /f "usebackq delims=" %%P in (`conda info --base`) do if exist "%%P\envs\livestream\python.exe" set "ARENA_PYTHON=%%P\envs\livestream\python.exe"
)

if not defined ARENA_PYTHON where python >nul 2>&1
if not defined ARENA_PYTHON if not errorlevel 1 set "ARENA_PYTHON=python"

if not defined ARENA_PYTHON (
    echo [错误] 未找到可用的 Python 环境。
    echo        请先双击 setup_conda.bat 完成首次安装。
    pause
    exit /b 1
)

"%ARENA_PYTHON%" -c "import streamlink, yt_dlp, ddgs, playwright, requests" >nul 2>&1
if errorlevel 1 (
    echo [错误] 当前 Python 环境缺少 Arena Stream 依赖。
    echo        请先双击 setup_conda.bat 完成或修复安装。
    pause
    exit /b 1
)

"%ARENA_PYTHON%" src\main.py %*
set "ARENA_EXIT=%ERRORLEVEL%"
if not "%ARENA_EXIT%"=="0" pause
exit /b %ARENA_EXIT%
