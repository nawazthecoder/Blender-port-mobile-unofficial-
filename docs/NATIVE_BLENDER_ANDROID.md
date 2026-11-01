# Native Blender 5.2.3 Android backport

## Reproducible source

- Official Blender: https://github.com/blender/blender/tree/e13b728c6880d3084d9d57c30031ed5df8b39dee
- Release: **5.2.3 LTS**, `BLENDER_VERSION=502`, patch `3`, cycle `release`.
- Android implementation and attribution: https://github.com/simfeo/blender/tree/4bd0075178bdf71c9aa3de139af6d07e9da61b4d
- The Android-only delta was isolated relative to its upstream parent
  `3bcf2d172c1f879561b600d02707617912d22c7d`, then adapted to stable 5.2 APIs.
- Local changes are in `patches/blender-5.2.3-android.patch`; its SHA256 and
  dependency/toolchain pins are in `config/blender-android.json`.

Blender's version header is not changed. The original Android fork is 5.3 alpha;
that is why simply building its branch would not satisfy the stable-release goal.

## Build

Use the full-editor GitHub Actions workflow. On a Linux build host with CMake
3.26+, Ninja, Clang 18+, Java 17, Python, git-lfs, patchelf, zip and Android SDK:

```sh
GIT_LFS_SKIP_SMUDGE=1 git clone --depth 1 --branch v5.2.3 https://github.com/blender/blender.git blender-source
python3 scripts/prepare_stable_android.py blender-source
(cd blender-source && bash ../scripts/fetch_native_dependencies.sh)
```

Install NDK `30.0.16248370`, SDK platform `android-35` and build-tools `35.0.1`.
Set `ANDROID_HOME` to the SDK, `ANDROID_NDK_VERSION=30.0.16248370`, and install
Vulkan-Headers `1.4.341` under the sibling
`blender_build_android/lib/vulkan_headers/include` as shown by the workflow.
Then run:

```sh
cd blender-source
export ANDROID_HOST_CC=clang-18 ANDROID_HOST_CXX=clang++-18
export BLENDER_BUILD_JOBS=2 CMAKE_BUILD_PARALLEL_LEVEL=2
python3 build_files/android/build.py full
```

This also builds static OpenImageDenoise, required by the upstream Android
packaging implementation. The preparation script refuses a dirty checkout or
wrong source commit. Rerun builds in the prepared checkout; prepare a new clean
checkout if changing the patch.

The fetch script explicitly overrides `update=none` for host libraries and fetches
LFS payloads inside **both** host and Android submodules. An existing directory
or a Git LFS pointer is not accepted as a compiled dependency.

## Current limits

- Source backport only until a full native build succeeds. The source patch has
  been applied to a fresh stable checkout; that is not a compilation test.
- Android 12+ ARM64. This stable backport preserves the 5.2 Vulkan **1.2** loader
  requirement, geometry shaders, timeline semaphores, buffer-device address and
  shader draw parameters. OpenGL ES is not used as a desktop OpenGL substitute.
- Vendor Vulkan driver only. The 5.3 alternate Volk/Turnip loader was not
  backported. A driver reporting Vulkan 1.1 is currently unsupported.
- Full profile enables Cycles CPU, OIDN, USD, Alembic, OpenVDB, FFmpeg and simulation
  features. GPU Cycles CUDA/OptiX/HIP/oneAPI, OpenXR and OSL remain disabled by the
  inherited Android feature profile. This is not complete desktop feature parity.
- Package checks establish ELF architecture, dependency closure, runtime presence
  and signing. They do not establish successful startup, Vulkan rendering, audio,
  touch input, file access, suspend/resume, or memory reliability on any phone.
- A 4 GB phone may not have enough memory for demanding scenes or full-profile
  operations. Native display resolution is the default; the existing explicit
  `debug.blender.renderdiv` switch can reduce it.
- APKs use development signing, not an app-store release identity.

## Device verification

Save your current work before running `tests/blender_runtime_smoke.py` inside
Blender: it intentionally replaces the open scene. It checks version, Python,
mesh creation/modifiers, .blend save/reload and a 64×64 CPU Cycles render in a
new temporary directory. It does not execute itself during an APK build.

Also verify initial startup, mesh editing, material and rendered viewports,
sculpt brushes, imports, audio, keyboard/touch input, storage permission handling,
rotation, background/resume and low-memory recovery on real Android hardware.
Keep the logcat and smoke-test JSON with the exact build SHA and device model.

## Licensing

Blender as a combined work is GPL-3.0; component files retain their respective
licenses. Preserve all upstream source headers and third-party notices. A build
artifact includes its source lock, corresponding patch and `release/license`
notices. Reconstruct corresponding source with the pinned official source and
patch above; dependency sources and build recipes are in the prepared source
under `build_files/build_environment/` and pinned library repositories.

The older diagnostic APK and downloaded upstream APK are separate experiments.
Neither is evidence of this stable port being complete.
