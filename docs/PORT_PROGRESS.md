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
