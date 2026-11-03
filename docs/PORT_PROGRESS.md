# Blender Android port checkpoint — 2 November 2026

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

## Revision 5 Vulkan link fix

Run: https://github.com/nawazthecoder/Blender-port-mobile-unofficial-/actions/runs/41321911101

- Revision 4 compiled all native translation units, including the keyboard, and
  reached the final `libblender.so` link (step 7,383/7,383).
- The linker rejected direct imports of `vkGetDeviceBufferMemoryRequirements`,
  `vkGetDeviceImageMemoryRequirements`, and
  `vkGetPhysicalDeviceSurfaceCapabilities2KHR` from Android libvulkan.
- Use VMA dynamic dispatch on Android and supply instance/device procedure
  lookups when creating its allocator. Load the optional surface-capabilities
  extension through `vkGetInstanceProcAddr`, with an explicit missing-entry check.
- Local validation: VMA compiles to an object with no undefined Vulkan imports;
  the modified GHOST Vulkan context passes host C++20 syntax checking. The next
  Android link and package audit remain required.

## Revision 6 runtime asset fix

Run: https://github.com/nawazthecoder/Blender-port-mobile-unofficial-/actions/runs/41322731665

- Revision 5 compiled and linked the full Android native editor, assembled its
  runtime, and packaged the APK successfully. The Vulkan linker fixes worked.
- The separate package audit rejected an unresolved Git LFS pointer at
  `scripts/startup/bl_app_templates_system/Storyboarding/startup.blend`.
- Fetch source LFS payloads under `scripts/**` and `locale/**` in addition to
  `assets/**` and `release/**`. Tests remain excluded.
- Check every packaged source directory for remaining pointers immediately after
  fetching, before native compilation starts. Keep the final APK pointer check.
- Sixteen local unit tests pass. The new integration tests reproduce application
  template fetching and prove unresolved templates fail before compilation.
- Revision 6 changes the APK version label to identify the asset-corrected build.
  Final package validation and real-device execution remain unverified.

## Revision 7 native add-on dependencies

Run: https://github.com/nawazthecoder/Blender-port-mobile-unofficial-/actions/runs/41407273106

- Revision 6 passed the early runtime source check, rebuilt the native editor,
  and packaged the APK. The final audit passed the LFS checks, then found
  `libdraco.so` missing from the glTF Draco bridge dependency chain.
- Seed native dependency collection from all payload modules, including add-on
  bridges and USD plugins, rather than only Python modules. Include versioned
  `.so.*` files and normalize runtime module dependencies consistently.
- A host ELF smoke check reproduces the omission with the old packager. The
  revised packager collects the add-on codec, a transitive library, and a
  versioned SONAME correctly. The same check runs before the expensive CI build.
- Final Android package validation and device execution remain required.

## Successful package checkpoint — revision 7

- Workflow passed: https://github.com/nawazthecoder/Blender-port-mobile-unofficial-/actions/runs/41408648885
- Validated implementation: `e24c84bda8375d1c3dd015f986e1b049223c2107`.
- Full Android native compilation/linking, APK packaging, all runtime source
  payloads, ELF architecture/dependency audit, and Android v3 signing passed.
- Artifact: `blender-5.2.3-android-full-arm64`, ID `13124204862`.
- APK: `5.2.3-android.7`, 283,068,031 bytes, 149 packaged native libraries.
- SHA256: `d847c96dd95b83402e6c1dbd76139e8c057fb29291970509648b92801ccfc5f5`.
- Downloaded the artifact and confirmed the APK hash matches its CI audit.
- Sixteen unit tests and the real host-ELF collection regression check passed.
- This checkpoint only updates documentation/status and deliberately skips CI;
  the implementation and seven source patches are unchanged from the passed run.
- Next: validate startup, editing, save/reload, CPU Cycles rendering, Vulkan
  viewports and lifecycle on actual Android hardware. Device behavior and the
  documented mobile clipping fallback remain unverified.

## Device feedback and revision 8 graphics preferences

- The user reports that revision 7 launches and displays Blender on their phone.
  This confirms user-observed startup; rendering, save/reload and lifecycle are
  not established by that report.
- They also report the popup saying Vulkan failed and OpenGL is being used.
  Source inspection found the reverse: desktop preferences request OpenGL,
  which is not compiled into Android, then detection selects Vulkan. The shared
  popup is hardcoded for a desktop Vulkan-to-OpenGL fallback.
- Revision 8 converts unsupported OpenGL/Metal preferences to Vulkan on Android
  before selection. Explicit launch overrides keep their priority. Capability
  requirements are unchanged. The Android popup reports the active backend.
- A local C++ check reproduced the old preference choice and validated the new
  Android selection, explicit overrides, and unchanged desktop preference logic.
  Native compilation/package checks for revision 8 remain pending.
- The texture-paint warning matches the stock missing-image/linked-data check;
  no evidence yet establishes a texture-paint renderer defect. Instructions are
  in `docs/ANDROID_TROUBLESHOOTING.md`.

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


## Revision 9 — Android virtual mouse

- Added a native relative pointer mode with real left/middle/right GHOST events,
  held-button dragging, two-finger and button scrolling, a movable control strip,
  keyboard exclusion, and lifecycle release handling.
- Added a status-bar MOUSE toggle and searchable Toggle Virtual Mouse operator.
- Revision 8 compiled and passed package checks in workflow run 41431024412.
- Revision 9 uses org.blender.androidport and launcher label Blender Android to
  install alongside the user's working revision 7. The old ephemeral signing key
  is unavailable; the new CI development identity is cached for future updates.
- Added sanitizer-backed tests against the actual portable input controller.
  Full native build/package and device checks remain pending for revision 9.
