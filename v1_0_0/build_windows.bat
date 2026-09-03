@echo off
setlocal
cd /d "%~dp0"

where py >nul 2>nul
if errorlevel 1 (
    echo Python Launcher wurde nicht gefunden.
    echo Bitte Python 3.11 oder 3.12 von python.org installieren.
    pause
    exit /b 1
)

if not exist ".venv\Scripts\python.exe" (
    echo Erstelle lokale Build-Umgebung ...
    py -3.13 -m venv .venv
    if errorlevel 1 goto :error
)

call ".venv\Scripts\activate.bat"
python -m pip install --upgrade pip
if errorlevel 1 goto :error
python -m pip install -r requirements-build.txt
if errorlevel 1 goto :error

echo Fuehre Tests aus ...
python -m unittest discover -s tests -v
if errorlevel 1 goto :error

echo Baue portable Windows-Anwendung ...
python -m PyInstaller ^
    --noconfirm ^
    --clean ^
    --windowed ^
    --name NukeScriptLauncher ^
    --contents-directory _internal ^
    app.py
if errorlevel 1 goto :error

copy /Y "config.json" "dist\NukeScriptLauncher\config.json" >nul
copy /Y "README.md" "dist\NukeScriptLauncher\README.md" >nul

echo.
echo Fertig: dist\NukeScriptLauncher\NukeScriptLauncher.exe
echo Der komplette Ordner dist\NukeScriptLauncher ist portabel.
pause
exit /b 0

:error
echo.
echo Build fehlgeschlagen.
pause
exit /b 1
