@echo off
setlocal
cd /d "%~dp0"

where py >nul 2>nul
if errorlevel 1 (
    echo Python Launcher was not found.
    echo Install the standard 64-bit version of Python 3.10 or newer from python.org.
    pause
    exit /b 1
)

if not exist ".venv\Scripts\python.exe" (
    echo Creating local build environment ...
    py -3 -m venv .venv
    if errorlevel 1 goto :error
)

call ".venv\Scripts\activate.bat"
python -m pip install --upgrade pip
if errorlevel 1 goto :error
python -m pip install -r requirements-build.txt
if errorlevel 1 goto :error

echo Running tests ...
python -m unittest discover -s tests -v
if errorlevel 1 goto :error

echo Building portable Windows application ...
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
echo Done: dist\NukeScriptLauncher\NukeScriptLauncher.exe
echo The complete dist\NukeScriptLauncher folder is portable.
pause
exit /b 0

:error
echo.
echo Build failed.
pause
exit /b 1
