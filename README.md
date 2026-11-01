# Unofficial Blender Port for Android

Experimental, community-maintained Android ARM64 porting work for Blender
5.2.2. Not affiliated with or endorsed by the Blender Foundation.

## Current state (October 2026)

**There is not yet a functioning Blender-on-Android editor.**

This repository previously held only Blender cross-compilation and dependency
configuration workflows. It now additionally contains an installable Android
**native-host diagnostic application**. Its renderer is a deliberately simple
full-resolution OpenGL ES smoke test; it is **not Blender's viewport**, does not
parse .blend files, and must not be distributed as a finished Blender port.

The Android host provides:
- Android 10+ ARM64 APK project, landscape SurfaceView, native JNI bridge.
- GPU diagnostic readout with Vulkan instance/device probing.
- EGL/OpenGL ES 3 diagnostic grid at the SurfaceView's real pixel size.
- Touch dragging and pinch scaling, and Android document picker with private
  temporary-file staging (no broad storage permissions).
- Versioned native runtime interface for future libblender_mobile_runtime.so.
  When that library is absent, the app states that Blender has not been linked.
- GitHub Actions APK build and 14-day downloadable CI artifact.

The repository's older workflows still experiment with Blender 5.2.2,
Android CPython, OpenImageIO, LLVM/OSL, and CMake. They **do not produce**
a usable Blender runtime or establish that Blender compiles for Android.

## Build the diagnostic APK

On GitHub, open **Actions -> Android APK - Native Host -> Run workflow**,
or push to main. When the build succeeds, download the artifact named
blender-android-native-host-arm64-debug from the workflow run. Inside is a
debug APK for arm64-v8a.

For local Android SDK/NDK builds:
1. Install JDK 17, Android SDK platform 35, NDK 27.3.13750724 and CMake 3.22.1.
2. Install Gradle 8.11.1.
3. From android-app, run: gradle :app:assembleDebug
4. Install app/build/outputs/apk/debug/app-debug.apk.

The app targets API 29+ (Android 10 or newer). It is a diagnostic build and
not a production release. The included full-resolution preview is a **graphics
smoke test**, not a fix for Blender's Vulkan renderer.

## Native integration boundary

The contract in android-app/app/src/main/cpp/blender_runtime_api.h describes
the exported function for a future libblender_mobile_runtime.so. The host
attempts to dynamically load this library from the APK's native-library
directory. The runtime must supply its own Android-compatible Blender/GHOST
windowing implementation, a working render backend, runtime resources, Python
and other libraries before a .blend file can be opened.

The bridge does **not** attempt to run a Linux Blender executable on Bionic.
It also does not silently claim success when the runtime is unavailable.

## Porting work still required

1. Implement an Android GHOST window/surface/event loop and native Vulkan
   surface/swapchain integration in Blender itself.
2. Build/resolve all of Blender's required Android dependencies, including
   embedded CPython and assets, and remove Linux-only assumptions.
3. Produce libblender_mobile_runtime.so implementing the versioned interface.
4. Package Blender scripts, fonts, Python modules, shared libraries, resources.
5. Verify Blender startup, .blend loading, mesh editing, GPU compatibility,
   memory use and device restarts on real Android hardware.
6. Preserve GPL and other third-party notices and source availability.

Older experimental actions under .github/workflows remain untouched.
Do not confuse a green APK-build status with a successfully ported Blender.

## Licensing

The native code and Android host added here are GPL-2.0-or-later; Blender
and third-party components retain their original license obligations.
See source-file headers and upstream Blender license terms when integrating
Blender itself.

## Actual Blender Android Vulkan editor

The original Android app remains a lightweight **GPU diagnostic host**. For an
**actual Blender modelling editor**, this repository now includes:

- [Build Actual Blender Android Vulkan Editor](.github/workflows/real-blender-native.yml), a pinned-source C++/ARM64 compilation pipeline using Blender's real Android GHOST/Vulkan backend.
- [Verify Native Blender Android Test APK](.github/workflows/real-blender-test-apk.yml), which SHA256-verifies and provides an **unmodified, GPL-attributed upstream Blender Android APK** for testing. This test APK is not compiled by this repository.

See [native Blender build, requirements, provenance and current limits](docs/NATIVE_BLENDER_ANDROID.md).
