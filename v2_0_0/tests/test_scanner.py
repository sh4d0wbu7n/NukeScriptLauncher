from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from nuke_launcher.scanner import (
    ProjectScanner,
    natural_key,
    parse_preview_name,
    parse_script_name,
)


class ScannerTests(unittest.TestCase):
    def test_parse_versioned_script_name(self) -> None:
        base, version = parse_script_name(Path("helendorn_SC0026_S0120_v002.nk"))
        self.assertEqual(base, "helendorn_SC0026_S0120")
        self.assertEqual(version, 2)

    def test_parse_unversioned_script_name(self) -> None:
        base, version = parse_script_name(Path("notes_final.nk"))
        self.assertEqual(base, "notes_final")
        self.assertIsNone(version)

    def test_parse_preview_name(self) -> None:
        base, version = parse_preview_name(Path("grenzgaenger_SC0001_S0391_v017_preview.mov"))
        self.assertEqual(base, "grenzgaenger_SC0001_S0391")
        self.assertEqual(version, 17)

    def test_natural_sort(self) -> None:
        values = ["S1003", "S120", "S20", "S0010"]
        self.assertEqual(sorted(values, key=natural_key), ["S0010", "S20", "S120", "S1003"])

    def test_scans_expected_structure_and_uses_highest_version(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary) / "01_projects"
            comp = base / "helendorn" / "work" / "SC0026" / "S0120" / "comp"
            comp.mkdir(parents=True)
            for name in (
                "helendorn_SC0026_S0120_v001.nk",
                "helendorn_SC0026_S0120_v010.nk",
                "helendorn_SC0026_S0120_v002.nk",
            ):
                (comp / name).write_text("Root {}", encoding="utf-8")

            result = ProjectScanner(base).scan_project("helendorn")
            self.assertEqual(len(result.groups), 1)
            self.assertEqual(result.groups[0].latest.version, 10)
            self.assertEqual([item.version for item in result.groups[0].older], [2, 1])

    def test_lists_only_first_level_projects(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary) / "01_projects"
            (base / "project10" / "work").mkdir(parents=True)
            (base / "project2" / "work").mkdir(parents=True)
            self.assertEqual(ProjectScanner(base).list_projects(), ["project2", "project10"])

    def test_missing_work_directory_is_reported(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary) / "01_projects"
            (base / "empty_project").mkdir(parents=True)
            result = ProjectScanner(base).scan_project("empty_project")
            self.assertEqual(result.groups, [])
            self.assertIn("No work folder found.", result.warnings)

    def test_scans_preview_without_comp_folder_and_uses_highest_version(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary) / "01_projects"
            preview = base / "grenzgaenger" / "work" / "SC0001" / "S0391" / "_OUT" / "PREVIEW"
            preview.mkdir(parents=True)
            for name in (
                "grenzgaenger_SC0001_S0391_v001_preview.mov",
                "grenzgaenger_SC0001_S0391_v010_preview.mov",
                "grenzgaenger_SC0001_S0391_v002_preview.mov",
            ):
                version_folder = name.removesuffix("_preview.mov")
                folder = preview / version_folder
                folder.mkdir()
                (folder / name).touch()
            ignored_folder = preview / "grenzgaenger_SC0001_S0391_v999"
            ignored_folder.mkdir()
            (ignored_folder / "grenzgaenger_SC0001_S0391_v999_preview.mp4").touch()
            (preview / "grenzgaenger_SC0001_S0391_v777_preview.mov").touch()

            result = ProjectScanner(base).scan_project("grenzgaenger")
            self.assertEqual(result.groups, [])
            self.assertEqual(len(result.preview_groups), 1)
            self.assertEqual(result.preview_groups[0].latest.version, 10)
            self.assertEqual(
                [item.version for item in result.preview_groups[0].older],
                [2, 1],
            )


if __name__ == "__main__":
    unittest.main()
