@echo off
setlocal
cd /d "%~dp0"

if exist ".venv\Scripts\pythonw.exe" (
    start "" ".venv\Scripts\pythonw.exe" "app.py"
    exit /b 0
)

echo Keine lokale Umgebung gefunden.
echo Bitte zuerst build_windows.bat ausfuehren oder PySide6 installieren.
pause
exit /b 1
