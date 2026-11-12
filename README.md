# Unofficial Blender 5.3.0 for Android

Android ARM64 port of the official **Blender 5.3.0 stable** source, using the
unofficial simfeo Android backend and the phone controls/fixes developed here.
Not affiliated with the Blender Foundation.

**Status: revision 13 source migration and local regression checks pass. Full
Android compilation, APK validation and phone testing are pending.** The last
validated APK is Blender 5.2.3 Android revision 12, from
[workflow 43175475404](https://github.com/nawazthecoder/Blender-port-mobile-unofficial-/actions/runs/43175475404).

The new source lock uses official tag `v5.3.0`, commit
`02f0899d78e374b63e7181d9061e1f7ab03419cc`. Blender's release/file-format metadata
is preserved. The Android patch is rebased onto that source; the version is not
changed by relabelling an older editor. See the
[official release](https://www.blender.org/releases/5-3/) and
[upgrade notes](docs/UPGRADE_5_3.md).

The full build includes EEVEE, Cycles CPU, Python, sculpting, animation,
Geometry Nodes, USD, Alembic, OpenVDB, FFmpeg and simulation. The upgrade adds
Android builds of Jolt physics, OpenTimelineIO and KTX texture dependencies from
the exact versions/checksums in Blender's source. GPU-specific desktop features
such as CUDA, OptiX and DLSS are disabled on Android. Jolt uses its CPU backend.

The virtual mouse stays above menus. It supports single-tap left click,
double-tap right click, two-finger middle drag and three-finger scrolling.
See [controls](docs/VIRTUAL_MOUSE.md). Shader cache validation, bounded shader
compilation, Vulkan frame recovery and previous-session crash diagnostics are
retained and adapted to 5.3's Vulkan resource tracking and Volk dispatch.

## Build

Use **Actions → Build Blender 5.3.0 Full Android Editor**. The workflow checks out
the locked stable commit, validates/applies the patch, fetches pinned host and
Android libraries, builds the new Android dependencies, then compiles the full
native editor. Download `blender-5.3.0-android-full-arm64` only from a successful
run. Build logs and dependency/compiler progress are preserved after failures.

To prepare source locally:

```bash
git clone --depth 1 --branch v5.3.0 https://github.com/blender/blender.git blender-source
python3 scripts/prepare_stable_android.py blender-source
cd blender-source
bash ../scripts/fetch_native_dependencies.sh
python3 build_files/android/build.py full
```

The SDK/NDK and host compiler must be installed as configured in the workflow.
The full build requires NDK 30.0.16248370, API 31+, Vulkan headers 1.4.341 and a
Linux x86-64 build host. The generated APK targets Android ARM64.

## Installation and verification

The package stays **Blender Android** (`org.blender.androidport`). Revision 13
uses versionCode **5030013** and versionName **5.3.0-android.13**. CI checks the
same signing certificate as revisions 9–12, so an unrelated key cannot silently
produce an incompatible update. Save projects before installing an update.

A successful package audit checks native ARM64 ELF dependencies, runtime/LFS
assets, package identity and the update signature. It does not prove phone
rendering, Shading stability or every editor feature. Those checks remain
necessary on the device. See [progress](docs/PORT_PROGRESS.md) and
[graphics diagnostics](docs/GRAPHICS_STABILITY.md).

Blender and these Android modifications are GPL-2.0-or-later. CI includes the
corresponding source patch, source lock and license files with validated APKs.
