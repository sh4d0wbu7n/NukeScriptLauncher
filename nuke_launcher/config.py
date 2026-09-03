from __future__ import annotations

import json
import os
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


DEFAULT_BASE_PATH = r"\\192.168.70.10\BackupKI\production\01_projects"
DEFAULT_NUKE_EXECUTABLE = r"C:\Program Files\Nuke14.0v5\Nuke14.0.exe"


def application_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parents[1]


@dataclass
class AppConfig:
    base_path: str = DEFAULT_BASE_PATH
    nuke_executable: str = DEFAULT_NUKE_EXECUTABLE
    default_launch_mode: str = "NukeX"
    launch_modes: dict[str, list[str]] = field(
        default_factory=lambda: {"Nuke": [], "NukeX": ["--nukex"]}
    )

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "AppConfig":
        modes = data.get("launch_modes")
        if not isinstance(modes, dict) or not modes:
            modes = {"Nuke": [], "NukeX": ["--nukex"]}
        cleaned_modes: dict[str, list[str]] = {}
        for name, arguments in modes.items():
            if isinstance(name, str) and isinstance(arguments, list):
                cleaned_modes[name] = [str(argument) for argument in arguments]
        if not cleaned_modes:
            cleaned_modes = {"Nuke": [], "NukeX": ["--nukex"]}

        default_mode = str(data.get("default_launch_mode", "NukeX"))
        if default_mode not in cleaned_modes:
            default_mode = next(iter(cleaned_modes))

        return cls(
            base_path=str(data.get("base_path", DEFAULT_BASE_PATH)),
            nuke_executable=str(data.get("nuke_executable", DEFAULT_NUKE_EXECUTABLE)),
            default_launch_mode=default_mode,
            launch_modes=cleaned_modes,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "base_path": self.base_path,
            "nuke_executable": self.nuke_executable,
            "default_launch_mode": self.default_launch_mode,
            "launch_modes": self.launch_modes,
        }

    def validate(self) -> list[str]:
        errors: list[str] = []
        if not self.base_path.strip():
            errors.append("Der Base-Pfad fehlt.")
        elif not Path(self.base_path).is_dir():
            errors.append(f"Der Base-Pfad ist nicht erreichbar: {self.base_path}")

        if not self.nuke_executable.strip():
            errors.append("Der Pfad zur Nuke-EXE fehlt.")
        elif not Path(self.nuke_executable).is_file():
            errors.append(f"Die Nuke-EXE wurde nicht gefunden: {self.nuke_executable}")

        if self.default_launch_mode not in self.launch_modes:
            errors.append("Der Standard-Startmodus ist nicht definiert.")
        return errors


class ConfigStore:
    def __init__(self, path: Path | None = None) -> None:
        self.path = path or application_dir() / "config.json"

    def load(self) -> AppConfig:
        if not self.path.exists():
            config = AppConfig()
            self.save(config)
            return config
        try:
            with self.path.open("r", encoding="utf-8") as handle:
                data = json.load(handle)
        except (OSError, json.JSONDecodeError) as exc:
            raise ValueError(f"Die Konfiguration konnte nicht gelesen werden: {exc}") from exc
        if not isinstance(data, dict):
            raise ValueError("Die Konfiguration muss ein JSON-Objekt enthalten.")
        return AppConfig.from_dict(data)

    def save(self, config: AppConfig) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.path.with_suffix(".json.tmp")
        with temporary.open("w", encoding="utf-8", newline="\n") as handle:
            json.dump(config.to_dict(), handle, indent=2, ensure_ascii=False)
            handle.write("\n")
        os.replace(temporary, self.path)
