# Blender Android port checkpoint — 1 November 2026

Work is preserved on `codex/blender-5.2.3-full-android`, PR #1. Do not treat
this checkpoint as a successful APK build or device test.

## Verified by the first native CI build

Run: https://github.com/nawazthecoder/Blender-port-mobile-unofficial-/actions/runs/41268228964

- Applied the Android backport to the pinned, official Blender 5.2.3 release.
- Downloaded actual host/Android libraries and resolved their LFS payloads.
- Built static OpenImageDenoise and native Blender code-generation tools.
- Configured the full Android target and started compiling the 7,391 build steps.
- Stopped at `intern/cycles/bvh/octree.cpp`: `embree4/rtcore.h` was not found.
- The log also exposed an inherited NDK r27 root overriding the requested r30.

## Revision 2 fixes

- Find Embree using Blender 5.2's `WITH_CYCLES_EMBREE` option; the newer global
  `WITH_EMBREE` option does not exist in the stable source.
- Resolve the NDK from the explicitly selected SDK/version instead of accepting
  an unrelated NDK root inherited from the CI image.
- Reuse the already-built native code generators and refresh them on every build.
- Cache verified dependencies and compiler output to retain expensive progress
  across failed attempts. No APK is uploaded after a failed compile/audit.

## Package validation checkpoint

- Fourteen local unit tests pass, including rejection of missing Blender/Python/
  Cycles, host-architecture Python modules, unresolved shared libraries, missing
  NativeActivity exports, and unresolved LFS asset pointers. These are synthetic
  package tests, not evidence of Android execution.
- CI now runs these guards before the source build. New checkpoints queue behind
  an active build rather than cancelling expensive compilation.
- Revision 2 build: https://github.com/nawazthecoder/Blender-port-mobile-unofficial-/actions/runs/41296960629
  Source preparation, library downloads, and toolchain installation passed.
  The build reached 4,811 of 7,383 Ninja steps before a touch UI API error.
  NDK r30 and Embree compiled successfully; compiler/dependency caches saved.
  Run 41297287151 reproduced the same failure after successfully restoring caches.
- Remaining review item: stable Vulkan clipping shaders need a complete mobile
  fallback, including geometry-stage paths, when shaderClipDistance is absent.

## Revision 3 compiler fix

- The Android popup touch handler called `uiblocks.first()`, a Blender 5.3
  container API. Stable 5.2 stores this as `ListBase.first` (`void *`). Use the
  same `static_cast<Block *>` access as the stable mouse handlers.
- Searched the added patch lines for other `first()`, `last()`, and `is_empty()`
  calls; this was the only added ListBase mismatch.
- CI permits up to 20 failed Ninja commands to expose independent port errors
  in one run. Ninja still returns failure and no APK is packaged on failure.
- Local patch preparation, 14 package/overlay unit tests, and shell syntax
  checks pass. Revision 3 fixed the touch UI compiler error.

## Revision 4 keyboard backport

Run: https://github.com/nawazthecoder/Blender-port-mobile-unofficial-/actions/runs/41300813855

- Revision 3 reached 7,381 of 7,383 Ninja steps. All scheduled translation units
  except `wm_virtual_keyboard.cc` compiled, including the Vulkan backend. This
  does not establish successful linking or Android runtime behavior.
- The keyboard stopped at the first of eight headers renamed after Blender 5.2.
  Restored their stable `.h` names, including `BLI_math_base.h` and
  `BLI_math_vector.h`. The range-based list loops already work in stable 5.2
  and are preserved.
- The full keyboard translation unit passes local GCC 13 C++20 syntax checking
  against actual stable Blender headers, fmt 12.1.0 and the official 5.2 host
  OpenImageIO headers. Used `-funsigned-char` to match Android ARM64 character
  signedness. This is an API check, not an Android link or device test.
- Patch 4 applies after patches 1–3 and preserves official release metadata.
  Revision 4 native compilation/linking and APK packaging remain pending.
  Run: https://github.com/nawazthecoder/Blender-port-mobile-unofficial-/actions/runs/41321911101
- Corrected the manual runtime smoke test to use the stable Python property
  `bpy.app.build_options.fluid`; `mod_fluid` is not a Python build-options field.
  All four referenced feature names were checked against the stable C API table.

## Resume procedure

1. Read this file and `config/blender-android.json` from the current PR head.
2. Inspect the newest full-editor workflow jobs/logs for that head.
3. Reconstruct a clean source checkout at `source_commit` and run
   `scripts/prepare_stable_android.py`. Apply all listed patches in order.
4. Fix actual compiler/linker/package failures, preserve each source change as a
   new patch, update its checksum and commit it to the same PR branch.
5. Keep the PR draft until compilation/package validation succeeds. Record device
   testing separately; no real-device startup or render has been validated yet.

Main was not updated: automatic review rejected the direct main push. The branch
and PR safely preserve the implementation without changing the default branch.
Polyvra and Forge Mobile Studio have not been modified.
