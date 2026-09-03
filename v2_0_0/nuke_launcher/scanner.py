from __future__ import annotations

import re
from collections import defaultdict
from pathlib import Path

from .models import PreviewGroup, PreviewVersion, ScanResult, ScriptGroup, ScriptVersion


VERSION_PATTERN = re.compile(r"^(?P<base>.+)_v(?P<version>\d+)$", re.IGNORECASE)
PREVIEW_VERSION_PATTERN = re.compile(
    r"^(?P<base>.+)_v(?P<version>\d+)_preview$", re.IGNORECASE
)
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


def parse_preview_name(path: Path) -> tuple[str, int | None]:
    match = PREVIEW_VERSION_PATTERN.match(path.stem)
    if not match:
        return path.stem, None
    return match.group("base"), int(match.group("version"))


class ProjectScanner:
    def __init__(self, base_path: str | Path) -> None:
        self.base_path = Path(base_path)

    def list_projects(self) -> list[str]:
        if not self.base_path.is_dir():
            raise FileNotFoundError(f"Base path is not available: {self.base_path}")
        try:
            projects = [entry.name for entry in self.base_path.iterdir() if entry.is_dir()]
        except OSError as exc:
            raise OSError(f"Projects could not be read: {exc}") from exc
        return sorted(projects, key=natural_key)

    def scan_project(self, project: str) -> ScanResult:
        project_path = self.base_path / project
        work_path = project_path / "work"
        if not project_path.is_dir():
            raise FileNotFoundError(f"Project not found: {project_path}")
        if not work_path.is_dir():
            return ScanResult(project=project, groups=[], warnings=["No work folder found."])

        grouped: dict[tuple[str, str], list[ScriptVersion]] = defaultdict(list)
        preview_grouped: dict[tuple[str, str], list[PreviewVersion]] = defaultdict(list)
        warnings: list[str] = []

        for scene_path in self._safe_directories(work_path, warnings):
            for shot_path in self._safe_directories(scene_path, warnings):
                comp_path = shot_path / "comp"
                if comp_path.is_dir():
                    for script_path in self._safe_files(comp_path, ".nk", warnings):
                        base_name, version = parse_script_name(script_path)
                        modified_at, size_bytes = self._metadata(script_path, warnings)
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
                            warnings.append(f"No version number recognized: {script_path.name}")

                preview_path = shot_path / "_OUT" / "PREVIEW"
                if preview_path.is_dir():
                    for movie_path in self._safe_preview_files(preview_path, warnings):
                        base_name, version = parse_preview_name(movie_path)
                        modified_at, size_bytes = self._metadata(movie_path, warnings)
                        item = PreviewVersion(
                            project=project,
                            scene=scene_path.name,
                            shot=shot_path.name,
                            base_name=base_name,
                            path=movie_path,
                            version=version,
                            modified_at=modified_at,
                            size_bytes=size_bytes,
                        )
                        group_key = (str(preview_path).casefold(), base_name.casefold())
                        preview_grouped[group_key].append(item)
                        if version is None:
                            warnings.append(f"No preview version recognized: {movie_path.name}")

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
        preview_groups: list[PreviewGroup] = []
        for items in preview_grouped.values():
            first = items[0]
            preview_groups.append(
                PreviewGroup(
                    project=first.project,
                    scene=first.scene,
                    shot=first.shot,
                    base_name=first.base_name,
                    versions=items,
                )
            )
        preview_groups.sort(
            key=lambda group: (
                natural_key(group.scene),
                natural_key(group.shot),
                natural_key(group.base_name),
            )
        )
        return ScanResult(
            project=project,
            groups=groups,
            preview_groups=preview_groups,
            warnings=warnings,
        )

    @staticmethod
    def _safe_directories(parent: Path, warnings: list[str]) -> list[Path]:
        try:
            return sorted((entry for entry in parent.iterdir() if entry.is_dir()), key=lambda entry: natural_key(entry.name))
        except OSError as exc:
            warnings.append(f"Folder could not be read: {parent} ({exc})")
            return []

    @staticmethod
    def _safe_files(folder: Path, suffix: str, warnings: list[str]) -> list[Path]:
        try:
            return sorted(
                (
                    entry
                    for entry in folder.iterdir()
                    if entry.is_file() and entry.suffix.casefold() == suffix.casefold()
                ),
                key=lambda entry: natural_key(entry.name),
            )
        except OSError as exc:
            warnings.append(f"Folder could not be read: {folder} ({exc})")
            return []

    @staticmethod
    def _safe_preview_files(preview_path: Path, warnings: list[str]) -> list[Path]:
        movies: list[Path] = []
        try:
            version_folders = sorted(
                (entry for entry in preview_path.iterdir() if entry.is_dir()),
                key=lambda entry: natural_key(entry.name),
            )
        except OSError as exc:
            warnings.append(f"Preview folder could not be read: {preview_path} ({exc})")
            return movies

        for version_folder in version_folders:
            try:
                movies.extend(
                    entry
                    for entry in version_folder.iterdir()
                    if entry.is_file() and entry.suffix.casefold() == ".mov"
                )
            except OSError as exc:
                warnings.append(
                    f"Preview version folder could not be read: {version_folder} ({exc})"
                )

        return sorted(movies, key=lambda entry: natural_key(entry.name))

    @staticmethod
    def _metadata(path: Path, warnings: list[str]) -> tuple[float | None, int | None]:
        try:
            stat = path.stat()
            return stat.st_mtime, stat.st_size
        except OSError as exc:
            warnings.append(f"Metadata could not be read: {path} ({exc})")
            return None, None
