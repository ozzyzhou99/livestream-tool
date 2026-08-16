@echo off
setlocal
cd /d "%~dp0"

set "ARENA_ENV=%USERPROFILE%\anaconda3\envs\livestream"
set "ARENA_PYINSTALLER=%ARENA_ENV%\Scripts\pyinstaller.exe"

echo.
echo ==========================================
echo   Arena Stream - Build Windows EXE
echo ==========================================
echo.

if not exist "%ARENA_PYINSTALLER%" (
    echo [ERROR] PyInstaller was not found:
    echo   %ARENA_PYINSTALLER%
    echo Run setup_conda.bat first.
    pause
    exit /b 1
)

echo [1/3] Removing previous project build output...
if exist "%CD%\build" rmdir /s /q "%CD%\build"
if exist "%CD%\dist" rmdir /s /q "%CD%\dist"

echo [2/3] Building ArenaStream.exe...
"%ARENA_PYINSTALLER%" --noconfirm --onefile --name ArenaStream --collect-all streamlink --collect-all playwright --hidden-import streamlink.plugins --hidden-import yt_dlp --add-binary "%ARENA_ENV%\Library\bin\libssl-3-x64.dll;." --add-binary "%ARENA_ENV%\Library\bin\libcrypto-3-x64.dll;." --add-data "src\web;web" src\main.py
if errorlevel 1 (
    echo [ERROR] Build failed.
    pause
    exit /b 1
)

echo [3/3] Build complete: dist\ArenaStream.exe
pause
exit /b 0
