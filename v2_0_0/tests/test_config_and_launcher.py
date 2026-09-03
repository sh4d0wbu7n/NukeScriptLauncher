from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from nuke_launcher.config import AppConfig, ConfigStore
from nuke_launcher.launcher import build_launch_command


class ConfigAndLauncherTests(unittest.TestCase):
    def test_config_round_trip(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            config_path = Path(temporary) / "config.json"
            store = ConfigStore(config_path)
            expected = AppConfig(
                base_path="X:/01_projects",
                nuke_executable="C:/Nuke/Nuke.exe",
                default_launch_mode="Nuke",
            )
            store.save(expected)
            actual = store.load()
            self.assertEqual(actual.to_dict(), expected.to_dict())

    def test_auto_refresh_defaults_to_sixty_seconds(self) -> None:
        config = AppConfig.from_dict({})
        self.assertEqual(config.auto_refresh_seconds, 60)

    def test_negative_auto_refresh_is_clamped_to_disabled(self) -> None:
        config = AppConfig.from_dict({"auto_refresh_seconds": -5})
        self.assertEqual(config.auto_refresh_seconds, 0)

    def test_builds_nukex_command_without_shell_string(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            executable = root / "Nuke 14.exe"
            script = root / "shot with spaces_v001.nk"
            executable.touch()
            script.touch()
            config = AppConfig(
                base_path=str(root),
                nuke_executable=str(executable),
                default_launch_mode="NukeX",
            )
            self.assertEqual(
                build_launch_command(config, "NukeX", script),
                [str(executable), "--nukex", str(script)],
            )

    def test_builds_plain_nuke_command(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            executable = root / "Nuke.exe"
            script = root / "shot_v001.nk"
            executable.touch()
            script.touch()
            config = AppConfig(base_path=str(root), nuke_executable=str(executable))
            self.assertEqual(build_launch_command(config, "Nuke", script), [str(executable), str(script)])


if __name__ == "__main__":
    unittest.main()
