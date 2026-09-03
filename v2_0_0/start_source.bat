@echo off
setlocal
cd /d "%~dp0"

if exist ".venv\Scripts\pythonw.exe" (
    start "" ".venv\Scripts\pythonw.exe" "app.py"
    exit /b 0
)

echo No local environment was found.
echo Run build_windows.bat first or install PySide6.
pause
exit /b 1
