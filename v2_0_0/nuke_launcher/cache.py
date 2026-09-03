from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path

from .models import ScanResult


def default_cache_dir() -> Path:
    local_app_data = os.environ.get("LOCALAPPDATA")
    if local_app_data:
        return Path(local_app_data) / "NukeScriptLauncher" / "cache"
    return Path.home() / ".cache" / "NukeScriptLauncher"


class ProjectCache:
    def __init__(self, directory: Path | None = None) -> None:
        self.directory = directory or default_cache_dir()

    def _path_for(self, base_path: str, project: str) -> Path:
        digest = hashlib.sha256(f"{base_path.casefold()}\0{project.casefold()}".encode("utf-8")).hexdigest()[:20]
        return self.directory / f"{digest}.json"

    def load(self, base_path: str, project: str) -> ScanResult | None:
        cache_path = self._path_for(base_path, project)
        try:
            with cache_path.open("r", encoding="utf-8") as handle:
                data = json.load(handle)
            if not isinstance(data, dict):
                return None
            result = ScanResult.from_dict(data)
            return result if result.project == project else None
        except (OSError, ValueError, TypeError, json.JSONDecodeError):
            return None

    def save(self, base_path: str, result: ScanResult) -> None:
        self.directory.mkdir(parents=True, exist_ok=True)
        cache_path = self._path_for(base_path, result.project)
        temporary = cache_path.with_suffix(".tmp")
        try:
            with temporary.open("w", encoding="utf-8", newline="\n") as handle:
                json.dump(result.to_dict(), handle, ensure_ascii=False)
            os.replace(temporary, cache_path)
        except OSError:
            try:
                temporary.unlink(missing_ok=True)
            except OSError:
                pass
