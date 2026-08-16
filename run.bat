@echo off
chcp 65001 >nul
cd /d "%~dp0"

set "ARENA_PYTHON=%USERPROFILE%\anaconda3\envs\livestream\python.exe"
if exist "%ARENA_PYTHON%" (
    "%ARENA_PYTHON%" src\main.py
) else (
    python src\main.py
)
