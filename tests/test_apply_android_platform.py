# SPDX-License-Identifier: GPL-2.0-or-later
"""Offline tests for the Blender source integration step."""

import importlib.util
from pathlib import Path
import tempfile
import unittest

REPO = Path(__file__).resolve().parents[1]
SCRIPT = REPO / "scripts/apply_android_platform.py"
OVERLAY = REPO / "build_files/cmake/platform/platform_android.cmake"

spec = importlib.util.spec_from_file_location("apply_android_platform", SCRIPT)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class AndroidPlatformOverlayTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.source = Path(self.temp.name) / "blender-test-source"
        (self.source / "build_files/cmake/platform").mkdir(parents=True)
        self.cmake = self.source / "CMakeLists.txt"
        self.cmake.write_text(
            "cmake_minimum_required(VERSION 3.22)\ninclude(platform_unix)\n",
            encoding="utf-8"
        )

    def test_patches_exactly_once(self):
        status = module.apply_overlay(self.source, OVERLAY, False)
        self.assertEqual(status, "overlay changes required")
        patched = self.cmake.read_text()
        self.assertIn(module.BLOCK, patched)
        target = self.source / "build_files/cmake/platform/platform_android.cmake"
        self.assertEqual(target.read_bytes(), OVERLAY.read_bytes())
        self.assertEqual(
            module.apply_overlay(self.source, OVERLAY, False),
            "overlay already applied"
        )
        self.assertEqual(self.cmake.read_text(), patched)

    def test_dry_run_makes_no_changes(self):
        original = self.cmake.read_text()
        self.assertEqual(
            module.apply_overlay(self.source, OVERLAY, True),
            "overlay changes required"
        )
        self.assertEqual(self.cmake.read_text(), original)
        self.assertFalse(
            (self.source / "build_files/cmake/platform/platform_android.cmake").exists()
        )

    def test_unsupported_source_fails_closed(self):
        self.cmake.write_text("project(ChangedBlender)\n")
        with self.assertRaisesRegex(ValueError, "exactly one"):
            module.apply_overlay(self.source, OVERLAY, False)

    def test_does_not_overwrite_modified_platform(self):
        target = self.source / "build_files/cmake/platform/platform_android.cmake"
        target.write_text("# user custom code")
        with self.assertRaisesRegex(ValueError, "Refusing to replace"):
            module.apply_overlay(self.source, OVERLAY, False)
        self.assertNotIn(module.BEGIN, self.cmake.read_text())

    def test_rejects_partial_patch_markers(self):
        self.cmake.write_text(module.BEGIN + "\ninclude(platform_unix)\n")
        with self.assertRaisesRegex(ValueError, "markers"):
            module.apply_overlay(self.source, OVERLAY, False)


if __name__ == "__main__":
    unittest.main()
