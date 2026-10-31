#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
"""Apply this repo's Android CMake platform overlay to a Blender source tree.

Intentionally strict and idempotent: we refuse to overwrite someone else's
platform_android.cmake or silently patch a Blender version with a changed
platform selection. This prepares upstream source; it does NOT build Blender.
"""

import argparse
from pathlib import Path
import sys

BEGIN = "# BEGIN unofficial Blender Android platform"
END = "# END unofficial Blender Android platform"
UNIX_INCLUDE = "include(platform_unix)"
BLOCK = (
    BEGIN + "\n"
    "if(ANDROID)\n"
    "  include(platform_android)\n"
    "else()\n"
    "  include(platform_unix)\n"
    "endif()\n"
    + END
)


def apply_overlay(blender_source: Path, overlay: Path, dry_run: bool) -> str:
    cmake_file = blender_source / "CMakeLists.txt"
    target = blender_source / "build_files/cmake/platform/platform_android.cmake"

    if not cmake_file.is_file():
        raise ValueError("Blender CMakeLists.txt does not exist: " + str(cmake_file))
    if not target.parent.is_dir():
        raise ValueError("Blender platform directory is missing: " + str(target.parent))
    if not overlay.is_file():
        raise ValueError("Android platform overlay is missing: " + str(overlay))

    text = cmake_file.read_text(encoding="utf-8")
    bundled_platform = overlay.read_bytes()

    if BEGIN in text or END in text:
        if text.count(BEGIN) != 1 or text.count(END) != 1 or BLOCK not in text:
            raise ValueError("Existing Android patch markers do not match expected block")
        patched = text
    else:
        count = text.count(UNIX_INCLUDE)
        if count != 1:
            raise ValueError(
                "Expected exactly one include(platform_unix), got "
                + str(count)
                + ". Check Blender version/source before patching."
            )
        patched = text.replace(UNIX_INCLUDE, BLOCK, 1)

    if target.exists() and target.read_bytes() != bundled_platform:
        raise ValueError(
            "Refusing to replace modified platform_android.cmake: " + str(target)
        )

    changed = (patched != text) or not target.exists()
    if not dry_run:
        if patched != text:
            cmake_file.write_text(patched, encoding="utf-8")
        if not target.exists():
            target.write_bytes(bundled_platform)
    return "overlay changes required" if changed else "overlay already applied"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", required=True, type=Path,
                        help="Root of extracted Blender source tree")
    parser.add_argument("--overlay", type=Path,
                        default=Path(__file__).resolve().parents[1]
                        / "build_files/cmake/platform/platform_android.cmake",
                        help="Android platform file to copy into Blender source")
    parser.add_argument("--dry-run", action="store_true",
                        help="Validate patch without modifying source")
    args = parser.parse_args()
    try:
        message = apply_overlay(args.source, args.overlay, args.dry_run)
    except (OSError, ValueError) as error:
        print("ERROR:", error, file=sys.stderr)
        return 1
    print(message + (" (dry run)" if args.dry_run else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
