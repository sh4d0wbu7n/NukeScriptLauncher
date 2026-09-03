from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SyncStatus:
    text: str
    level: str


def asset_key(scene: str, shot: str, base_name: str) -> tuple[str, str, str]:
    return scene.casefold(), shot.casefold(), base_name.casefold()


def compare_versions(
    own_version: int | None,
    counterpart_version: int | None,
    counterpart_label: str,
    counterpart_exists: bool,
) -> SyncStatus:
    if own_version is None:
        return SyncStatus("NO VERSION", "warning")
    if not counterpart_exists:
        return SyncStatus(f"NO {counterpart_label.upper()}", "warning")
    if counterpart_version is None:
        return SyncStatus(f"MISMATCH · {counterpart_label} unversioned", "warning")
    if own_version != counterpart_version:
        return SyncStatus(
            f"MISMATCH · {counterpart_label} v{counterpart_version:03d}",
            "warning",
        )
    return SyncStatus("IN SYNC", "ok")
