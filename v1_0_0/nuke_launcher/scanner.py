from __future__ import annotations

import re
from collections import defaultdict
from pathlib import Path

from .models import ScanResult, ScriptGroup, ScriptVersion


VERSION_PATTERN = re.compile(r"^(?P<base>.+)_v(?P<version>\d+)$", re.IGNORECASE)
NATURAL_PARTS_PATTERN = re.compile(r"(\d+)")


def natural_key(value: str) -> tuple[object, ...]:
    return tuple(
        int(part) if part.isdigit() else part.casefold()
        for part in NATURAL_PARTS_PATTERN.split(value)
    )


def parse_script_name(path: Path) -> tuple[str, int | None]:
    match = VERSION_PATTERN.match(path.stem)
    if not match:
        return path.stem, None
    return match.group("base"), int(match.group("version"))


class ProjectScanner:
    def __init__(self, base_path: str | Path) -> None:
        self.base_path = Path(base_path)

    def list_projects(self) -> list[str]:
        if not self.base_path.is_dir():
            raise FileNotFoundError(f"Base-Pfad nicht erreichbar: {self.base_path}")
        try:
            projects = [entry.name for entry in self.base_path.iterdir() if entry.is_dir()]
        except OSError as exc:
            raise OSError(f"Projekte konnten nicht gelesen werden: {exc}") from exc
        return sorted(projects, key=natural_key)

    def scan_project(self, project: str) -> ScanResult:
        project_path = self.base_path / project
        work_path = project_path / "work"
        if not project_path.is_dir():
            raise FileNotFoundError(f"Projekt nicht gefunden: {project_path}")
        if not work_path.is_dir():
            return ScanResult(project=project, groups=[], warnings=["Kein work-Ordner gefunden."])

        grouped: dict[tuple[str, str], list[ScriptVersion]] = defaultdict(list)
        warnings: list[str] = []

        for scene_path in self._safe_directories(work_path, warnings):
            for shot_path in self._safe_directories(scene_path, warnings):
                comp_path = shot_path / "comp"
                if not comp_path.is_dir():
                    continue
                for script_path in self._safe_scripts(comp_path, warnings):
                    base_name, version = parse_script_name(script_path)
                    try:
                        stat = script_path.stat()
                        modified_at = stat.st_mtime
                        size_bytes = stat.st_size
                    except OSError as exc:
                        modified_at = None
                        size_bytes = None
                        warnings.append(f"Metadaten nicht lesbar: {script_path} ({exc})")

                    item = ScriptVersion(
                        project=project,
                        scene=scene_path.name,
                        shot=shot_path.name,
                        base_name=base_name,
                        path=script_path,
                        version=version,
                        modified_at=modified_at,
                        size_bytes=size_bytes,
                    )
                    group_key = (str(comp_path).casefold(), base_name.casefold())
                    grouped[group_key].append(item)
                    if version is None:
                        warnings.append(f"Keine Versionsnummer erkannt: {script_path.name}")

        groups: list[ScriptGroup] = []
        for items in grouped.values():
            first = items[0]
            groups.append(
                ScriptGroup(
                    project=first.project,
                    scene=first.scene,
                    shot=first.shot,
                    base_name=first.base_name,
                    versions=items,
                )
            )
        groups.sort(key=lambda group: (natural_key(group.scene), natural_key(group.shot), natural_key(group.base_name)))
        return ScanResult(project=project, groups=groups, warnings=warnings)

    @staticmethod
    def _safe_directories(parent: Path, warnings: list[str]) -> list[Path]:
        try:
            return sorted((entry for entry in parent.iterdir() if entry.is_dir()), key=lambda entry: natural_key(entry.name))
        except OSError as exc:
            warnings.append(f"Ordner nicht lesbar: {parent} ({exc})")
            return []

    @staticmethod
    def _safe_scripts(comp_path: Path, warnings: list[str]) -> list[Path]:
        try:
            return sorted(
                (
                    entry
                    for entry in comp_path.iterdir()
                    if entry.is_file() and entry.suffix.casefold() == ".nk"
                ),
                key=lambda entry: natural_key(entry.name),
            )
        except OSError as exc:
            warnings.append(f"Comp-Ordner nicht lesbar: {comp_path} ({exc})")
            return []
