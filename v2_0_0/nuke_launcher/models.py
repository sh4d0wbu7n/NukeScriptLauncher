from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class ScriptVersion:
    project: str
    scene: str
    shot: str
    base_name: str
    path: Path
    version: int | None
    modified_at: float | None
    size_bytes: int | None

    @property
    def version_label(self) -> str:
        return f"v{self.version:03d}" if self.version is not None else "—"

    @property
    def is_versioned(self) -> bool:
        return self.version is not None

    def to_dict(self) -> dict[str, Any]:
        return {
            "project": self.project,
            "scene": self.scene,
            "shot": self.shot,
            "base_name": self.base_name,
            "path": str(self.path),
            "version": self.version,
            "modified_at": self.modified_at,
            "size_bytes": self.size_bytes,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ScriptVersion":
        return cls(
            project=str(data["project"]),
            scene=str(data["scene"]),
            shot=str(data["shot"]),
            base_name=str(data["base_name"]),
            path=Path(str(data["path"])),
            version=int(data["version"]) if data.get("version") is not None else None,
            modified_at=float(data["modified_at"]) if data.get("modified_at") is not None else None,
            size_bytes=int(data["size_bytes"]) if data.get("size_bytes") is not None else None,
        )


@dataclass
class ScriptGroup:
    project: str
    scene: str
    shot: str
    base_name: str
    versions: list[ScriptVersion] = field(default_factory=list)

    @property
    def latest(self) -> ScriptVersion:
        if not self.versions:
            raise ValueError("A script group cannot be empty")
        versioned = [item for item in self.versions if item.version is not None]
        if versioned:
            return max(versioned, key=lambda item: item.version or 0)
        return max(self.versions, key=lambda item: item.modified_at or 0)

    @property
    def older(self) -> list[ScriptVersion]:
        latest = self.latest
        return sorted(
            (item for item in self.versions if item.path != latest.path),
            key=lambda item: (
                item.version is not None,
                item.version if item.version is not None else -1,
                item.modified_at or 0,
            ),
            reverse=True,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "project": self.project,
            "scene": self.scene,
            "shot": self.shot,
            "base_name": self.base_name,
            "versions": [item.to_dict() for item in self.versions],
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ScriptGroup":
        return cls(
            project=str(data["project"]),
            scene=str(data["scene"]),
            shot=str(data["shot"]),
            base_name=str(data["base_name"]),
            versions=[ScriptVersion.from_dict(item) for item in data.get("versions", [])],
        )


@dataclass(frozen=True)
class PreviewVersion:
    project: str
    scene: str
    shot: str
    base_name: str
    path: Path
    version: int | None
    modified_at: float | None
    size_bytes: int | None

    @property
    def version_label(self) -> str:
        return f"v{self.version:03d}" if self.version is not None else "—"

    @property
    def is_versioned(self) -> bool:
        return self.version is not None

    def to_dict(self) -> dict[str, Any]:
        return {
            "project": self.project,
            "scene": self.scene,
            "shot": self.shot,
            "base_name": self.base_name,
            "path": str(self.path),
            "version": self.version,
            "modified_at": self.modified_at,
            "size_bytes": self.size_bytes,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "PreviewVersion":
        return cls(
            project=str(data["project"]),
            scene=str(data["scene"]),
            shot=str(data["shot"]),
            base_name=str(data["base_name"]),
            path=Path(str(data["path"])),
            version=int(data["version"]) if data.get("version") is not None else None,
            modified_at=float(data["modified_at"]) if data.get("modified_at") is not None else None,
            size_bytes=int(data["size_bytes"]) if data.get("size_bytes") is not None else None,
        )


@dataclass
class PreviewGroup:
    project: str
    scene: str
    shot: str
    base_name: str
    versions: list[PreviewVersion] = field(default_factory=list)

    @property
    def latest(self) -> PreviewVersion:
        if not self.versions:
            raise ValueError("A preview group cannot be empty")
        versioned = [item for item in self.versions if item.version is not None]
        if versioned:
            return max(versioned, key=lambda item: item.version or 0)
        return max(self.versions, key=lambda item: item.modified_at or 0)

    @property
    def older(self) -> list[PreviewVersion]:
        latest = self.latest
        return sorted(
            (item for item in self.versions if item.path != latest.path),
            key=lambda item: (
                item.version is not None,
                item.version if item.version is not None else -1,
                item.modified_at or 0,
            ),
            reverse=True,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "project": self.project,
            "scene": self.scene,
            "shot": self.shot,
            "base_name": self.base_name,
            "versions": [item.to_dict() for item in self.versions],
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "PreviewGroup":
        return cls(
            project=str(data["project"]),
            scene=str(data["scene"]),
            shot=str(data["shot"]),
            base_name=str(data["base_name"]),
            versions=[PreviewVersion.from_dict(item) for item in data.get("versions", [])],
        )


@dataclass
class ScanResult:
    project: str
    groups: list[ScriptGroup]
    preview_groups: list[PreviewGroup] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "project": self.project,
            "groups": [group.to_dict() for group in self.groups],
            "preview_groups": [group.to_dict() for group in self.preview_groups],
            "warnings": self.warnings,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ScanResult":
        return cls(
            project=str(data["project"]),
            groups=[ScriptGroup.from_dict(item) for item in data.get("groups", [])],
            preview_groups=[PreviewGroup.from_dict(item) for item in data.get("preview_groups", [])],
            warnings=[str(item) for item in data.get("warnings", [])],
        )
