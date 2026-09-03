from __future__ import annotations

import unittest

from nuke_launcher.sync_status import asset_key, compare_versions


class SyncStatusTests(unittest.TestCase):
    def test_matching_versions_are_in_sync(self) -> None:
        status = compare_versions(4, 4, "Preview", True)
        self.assertEqual(status.text, "IN SYNC")
        self.assertEqual(status.level, "ok")

    def test_mismatch_names_counterpart_version(self) -> None:
        status = compare_versions(2, 3, "Preview", True)
        self.assertEqual(status.text, "MISMATCH · Preview v003")
        self.assertEqual(status.level, "warning")

    def test_missing_counterpart_is_reported(self) -> None:
        status = compare_versions(2, None, "Preview", False)
        self.assertEqual(status.text, "NO PREVIEW")

    def test_asset_key_is_case_insensitive(self) -> None:
        self.assertEqual(
            asset_key("SC0001", "S0010", "Project_SC0001_S0010"),
            asset_key("sc0001", "s0010", "project_sc0001_s0010"),
        )


if __name__ == "__main__":
    unittest.main()
