# Actual Blender native Android build

The existing android-app directory is an OpenGL ES diagnostic host, NOT Blender.
Two additional workflows are now available:

1. Build Actual Blender Android Vulkan Editor: compile the actual Blender C++ editor
   with Android GHOST/Vulkan and package a native ARM64 APK. It uses pinned
   upstream Android source commit 4bd0075178bdf71c9aa3de139af6d07e9da61b4d.
2. Verify Native Blender Android Test APK: download and checksum-verify a
   ready-built **unmodified third-party Blender Android** APK so an actual
   modelling editor can be tried while the source compile is being resolved.

Source and credits: https://github.com/simfeo/blender
Upstream build guide: https://github.com/simfeo/blender/blob/android/build_files/android/BUILDING.md
Upstream compiled APK release: https://github.com/simfeo/blender/releases/tag/android-alpha-4

Blender as a whole is GPL-3.0. The actual Blender Android code and binary
are derived from this existing GPL port and authored by its contributors.
All corresponding source and notices must accompany redistribution.
The upstream binary is NOT a build made by this repository; see the
verified APK workflow for the binary SHA256 and provenance.

Android OpenGL ES 3.x is not desktop OpenGL 4.3. The real port uses Vulkan
and an Android-specific GHOST window implementation instead. Its upstream
requirements include Android 12+ ARM64 and a compatible Vulkan driver.
The compiled Android library set specifically requires NDK r30 beta1; the
r27 build experiments from the diagnostic stage cannot link those libraries.

This user's Redmi 13C 5G with 4 GB RAM is a reason to start with the lite
modeling editor, and to expect slower shader compilation and limited RAM.
Some Mali GPUs may show Vulkan visual errors; a diagnostic GLES grid
working proves nothing about Vulkan Blender. Test actual device launch,
mesh editing, file opening/saving, memory use, and screen rotation.

**Status reporting:** until the source workflow reports success and has
an APK artifact, the source compile is not confirmed. Even then, a native
APK artifact is not proof that the editor runs correctly on this specific phone.

No changes are made to Polyvra or Forge Mobile Studio.
