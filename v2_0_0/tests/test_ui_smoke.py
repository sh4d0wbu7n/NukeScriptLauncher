from __future__ import annotations

import os
import tempfile
import time
import unittest
from pathlib import Path


os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

try:
    from PySide6.QtWidgets import QApplication

    from nuke_launcher.config import AppConfig, ConfigStore
    from nuke_launcher.ui import MainWindow

    QT_IMPORT_ERROR: Exception | None = None
except Exception as exc:  # pragma: no cover - depends on the test system's Qt runtime
    QT_IMPORT_ERROR = exc


@unittest.skipIf(QT_IMPORT_ERROR is not None, f"Qt runtime unavailable: {QT_IMPORT_ERROR}")
class UiSmokeTests(unittest.TestCase):
    def test_loads_project_and_displays_latest_version(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            base = root / "01_projects"
            comp = base / "demo" / "work" / "SC0001" / "S0010" / "comp"
            comp.mkdir(parents=True)
            (comp / "demo_SC0001_S0010_v001.nk").touch()
            (comp / "demo_SC0001_S0010_v002.nk").touch()
            preview = base / "demo" / "work" / "SC0001" / "S0010" / "_OUT" / "PREVIEW"
            preview.mkdir(parents=True)
            preview_v001 = preview / "demo_SC0001_S0010_v001"
            preview_v003 = preview / "demo_SC0001_S0010_v003"
            preview_v001.mkdir()
            preview_v003.mkdir()
            (preview_v001 / "demo_SC0001_S0010_v001_preview.mov").touch()
            (preview_v003 / "demo_SC0001_S0010_v003_preview.mov").touch()
            nuke = root / "Nuke.exe"
            nuke.touch()

            store = ConfigStore(root / "config.json")
            store.save(AppConfig(base_path=str(base), nuke_executable=str(nuke)))
            app = QApplication.instance() or QApplication([])
            window = MainWindow(store)
            window.show()

            deadline = time.time() + 5
            while time.time() < deadline and window.preview_tree.topLevelItemCount() != 1:
                app.processEvents()
                time.sleep(0.02)

            self.assertEqual(window.project_list.count(), 1)
            self.assertEqual(window.script_tree.topLevelItemCount(), 1)
            top = window.script_tree.topLevelItem(0)
            self.assertEqual(top.text(2), "v002")
            self.assertEqual(top.childCount(), 1)
            self.assertEqual(window.preview_tree.topLevelItemCount(), 1)
            preview_top = window.preview_tree.topLevelItem(0)
            self.assertEqual(preview_top.text(2), "v003")
            self.assertEqual(preview_top.text(4), "MISMATCH · Script v002")
            self.assertEqual(preview_top.childCount(), 1)
            self.assertEqual(window.auto_refresh_timer.interval(), 60_000)
            window.close()


if __name__ == "__main__":
    unittest.main()
