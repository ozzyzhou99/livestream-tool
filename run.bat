@echo off
chcp 65001 >nul
cd /d "%~dp0"
"%USERPROFILE%\anaconda3\envs\livestream\python.exe" src\main.py
