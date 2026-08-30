@echo off
setlocal
cd /d "%~dp0"

set "ARENA_ENV="
if exist "%CD%\.venv\Scripts\pyinstaller.exe" set "ARENA_ENV=%CD%\.venv"
if not defined ARENA_ENV if exist "%USERPROFILE%\anaconda3\envs\livestream\Scripts\pyinstaller.exe" set "ARENA_ENV=%USERPROFILE%\anaconda3\envs\livestream"
if not defined ARENA_ENV if exist "%USERPROFILE%\miniconda3\envs\livestream\Scripts\pyinstaller.exe" set "ARENA_ENV=%USERPROFILE%\miniconda3\envs\livestream"
if not defined ARENA_ENV if exist "%LOCALAPPDATA%\miniconda3\envs\livestream\Scripts\pyinstaller.exe" set "ARENA_ENV=%LOCALAPPDATA%\miniconda3\envs\livestream"
if not defined ARENA_ENV where conda >nul 2>&1
if not defined ARENA_ENV if not errorlevel 1 (
    for /f "usebackq delims=" %%P in (`conda info --base`) do if exist "%%P\envs\livestream\Scripts\pyinstaller.exe" set "ARENA_ENV=%%P\envs\livestream"
)
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
if exist "%CD%\build\ArenaStream" rmdir /s /q "%CD%\build\ArenaStream"
if exist "%CD%\dist\ArenaStream.exe" del /q "%CD%\dist\ArenaStream.exe"

echo [2/3] Building ArenaStream.exe...
set "ARENA_SSL_ARGS="
if exist "%ARENA_ENV%\Library\bin\libssl-3-x64.dll" if exist "%ARENA_ENV%\Library\bin\libcrypto-3-x64.dll" set "ARENA_SSL_ARGS=--add-binary "%ARENA_ENV%\Library\bin\libssl-3-x64.dll;." --add-binary "%ARENA_ENV%\Library\bin\libcrypto-3-x64.dll;.""
"%ARENA_PYINSTALLER%" --noconfirm --onefile --name ArenaStream --collect-all streamlink --collect-all playwright --hidden-import streamlink.plugins --hidden-import yt_dlp %ARENA_SSL_ARGS% --add-data "src\web;web" src\main.py
if errorlevel 1 (
    echo [ERROR] Build failed.
    pause
    exit /b 1
)

echo [3/3] Build complete: dist\ArenaStream.exe
pause
exit /b 0
