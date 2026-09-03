from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from .config import AppConfig


def build_launch_command(config: AppConfig, mode: str, script_path: str | Path) -> list[str]:
    if mode not in config.launch_modes:
        raise ValueError(f"Unbekannter Startmodus: {mode}")
    executable = Path(config.nuke_executable)
    script = Path(script_path)
    if not executable.is_file():
        raise FileNotFoundError(f"Nuke wurde nicht gefunden: {executable}")
    if not script.is_file():
        raise FileNotFoundError(f"Nuke-Script wurde nicht gefunden: {script}")
    return [str(executable), *config.launch_modes[mode], str(script)]


def launch_nuke(config: AppConfig, mode: str, script_path: str | Path) -> subprocess.Popen[bytes]:
    command = build_launch_command(config, mode, script_path)
    return subprocess.Popen(command, shell=False)


def reveal_in_file_manager(script_path: str | Path) -> None:
    path = Path(script_path)
    if not path.exists():
        raise FileNotFoundError(f"Datei wurde nicht gefunden: {path}")
    if sys.platform == "win32":
        subprocess.Popen(["explorer.exe", "/select,", str(path)], shell=False)
    elif sys.platform == "darwin":
        subprocess.Popen(["open", "-R", str(path)], shell=False)
    else:
        subprocess.Popen(["xdg-open", str(path.parent)], shell=False)
