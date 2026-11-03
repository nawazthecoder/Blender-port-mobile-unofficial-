# Unofficial Blender Port for Android

Native Android ARM64 porting work targeting **Blender 5.2.3 LTS**, based on the
actual stable release source. Not affiliated with the Blender Foundation.

**Status: full native build, APK packaging, runtime asset checks, ARM64 native
dependency audit and Android signature verification pass. The user confirms
revision 7 launches on their phone; individual features still need testing.**

The native build now applies the repository's Android patch to the exact official
5.2.3 release commit. The source lock, patch and build scripts are committed here;
the build does not rename a 5.3 alpha binary or substitute a diagnostic renderer.

**Virtual mouse:** revision 10 keeps the pointer above menus, adds double-tap
right click, two-finger middle drag and three-finger scrolling, and reduces
pointer redraw and hover-queue overhead. See [controls and installation](docs/VIRTUAL_MOUSE.md).
**Blender Android** revision 10 updates revision 9 and can remain alongside
revision 7. Native build and package checks pass; the new behavior and latency still need
phone validation.

Validated build: [revision 10 gesture mouse workflow](https://github.com/nawazthecoder/Blender-port-mobile-unofficial-/actions/runs/41589347500).
The full ARM64 APK is available in its `blender-5.2.3-android-full-arm64` artifact.

## Build the full editor

Use **Actions → Build Blender 5.2.3 Full Android Editor**. Changes to its locked
source, patch or build scripts start it automatically. It builds the `full`
configuration, including Cycles CPU rendering, EEVEE, Python, animation, sculpting,
USD, Alembic, OpenVDB, FFmpeg and simulation features enabled by the Android port.
These are build targets, not a claim that every feature has passed device tests.

A successful run must compile `libblender.so`, package the real Blender runtime,
pass the ARM64 ELF and dependency audit, and pass Android signature verification
before uploading `blender-5.2.3-android-full-arm64`.

- [Graphics/texture-paint troubleshooting](docs/ANDROID_TROUBLESHOOTING.md)
- [Latest checkpoint and resume instructions](docs/PORT_PROGRESS.md)
- [Source/version lock](config/blender-android.json)
- [Android backport patch](patches/blender-5.2.3-android.patch)
- [Build instructions, attribution and limits](docs/NATIVE_BLENDER_ANDROID.md)
- [Full source build workflow](.github/workflows/real-blender-native.yml)
- [Device Python smoke test](tests/blender_runtime_smoke.py)

The patch adapts the existing `simfeo/blender` Android GHOST, lifecycle, input,
AAudio and packaging work to the stable source. It preserves Blender's 5.2.3
version/file-format metadata and uses the matching `5.2` runtime directory.
Default rendering uses the display's native resolution. An explicit render-scale
setting remains available for memory-constrained devices.

## Existing experiments

`android-app/` is the older **GPU diagnostic host**, not Blender. Its APK and green
workflow status do not prove the full editor works. The old upstream-test-APK
workflow downloads a separately authored, unmodified 5.3 alpha port; it is not
the stable build produced by this repository. Older dependency experiments are
retained for reference.

## License and credits

Blender is GPL software; constituent files retain their original SPDX licenses.
The Android backport derives from [simfeo/blender](https://github.com/simfeo/blender)
and its credited contributors. This repository's preparation and validation tools
are GPL-2.0-or-later. Corresponding source is the pinned official Blender source
plus the committed patch. Keep Blender and third-party notices with distributions.
