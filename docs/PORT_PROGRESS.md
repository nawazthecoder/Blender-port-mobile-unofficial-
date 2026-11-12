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
  Native compilation/package checks for revision 8 passed in workflow 41431024412.
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
5. Keep the PR draft pending broader device checks. The user confirmed revision 7
   startup; record later device feature checks separately from build/package checks.

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
  All 16 preparation/package unit tests and sanitizer-backed input tests pass.
- Full native build, runtime payload checks, ELF dependency closure, APK identity
  and v3 signature validation passed for implementation
  `046d5dd630471df8fe32b819e27017d9bb0227d4` in
  [workflow 41582692540](https://github.com/nawazthecoder/Blender-port-mobile-unofficial-/actions/runs/41582692540).
  The workflow checks out PR merge `de5244332aabb70f3441a884597f572c7c59c1db`,
  whose parents include that implementation commit.
- Final APK: 283,076,223 bytes, 149 native libraries, versionCode 5020309.
  SHA256: `f87bd3e1d2e2e46a2da6ea56e5fff0d5ed20856e75d41b0d1646fe9b471ca2fe`.
  Artifact ID 13207590715 expires 2026-11-17.
- The development signing identity was restored successfully from the first
  revision 9 CI run. Source changes are saved on the existing PR branch.
- Revision 9 virtual mouse phone validation remains pending.


## Revision 10 — gesture mouse and menu visibility

- User reports revision 9 works, but popup menus cover its pointer and pointer
  movement lags while Blender remains responsive.
- Draw the pointer after menus, gesture overlays, drag previews and other cursors.
  Leave the toolbar at the normal overlay stage.
- Replace per-touch full-window update notifiers with state-based compositing
  requests. Coalesce idle/hover motions to the newest position each frame while
  preserving held-button paths and flushing before button/wheel boundaries.
- Add single-tap Left, double-tap Right (no preceding Left), two-finger Right tap,
  two-finger Middle hold/drag, and three-finger vertical wheel. Existing explicit
  click/hold/wheel controls remain available.
- Retain application ID org.blender.androidport and development signing cache
  so revision 10 can update the installed Blender Android revision 9.
- Local controller/queue sanitizer tests, 16 preparation/package unit tests and
  overlay syntax checks pass. Full native compilation, runtime/ELF dependency
  audits, APK identity and v3 signing passed in
  [workflow 41589347500](https://github.com/nawazthecoder/Blender-port-mobile-unofficial-/actions/runs/41589347500).
- Validated implementation: `fda2b8a4206a23fe855afedcd6aaeaede649c696`.
  Artifact provenance records merge `e46f748c62e1910d7a66b38bd2c8bb0a145fad75`,
  whose parents include that source commit.
- APK: 283,076,223 bytes; 149 native libraries; versionCode 5020310.
  SHA256: `3d53cbfcaf73b08fd7b3f28aee4498f9f0b8b0c347a23c7c41df66d53d805554`.
  Artifact 13209154437 expires 2026-11-17.
- Revision 10 and revision 9 signing certificate SHA256 match:
  `45971c45d2531454994f4382a402bdb3a491159cbee356a8a0effd831c76ab3e`.
  The download was checked against the CI ZIP/APK digests and saved.
- Gesture behavior, menu visibility and latency on the phone still need device
  testing; no measured FPS or end-to-end latency is claimed.


## Revision 11 — transient graphics and scheduling

- User reports intermittent brief graphics glitches and requests more optimization.
  The phone incident is not yet reproduced; do not claim a confirmed single cause.
- Fix image-handle-only barrier merging dropping independent mip/layer/aspect
  transitions. Keep temporary subresource state separate from whole-image state,
  synchronize matching ranges and repeated writes, and preserve depth/stencil access.
- Check acquired-image ownership and fence results, bound stale-swapchain retries,
  and skip drawing after failure. Request Android surface recovery at swap boundary.
- Use interruptible native idle waits and skip UI drawing while paused/windowless;
  background jobs/timers continue at a lower cadence.
- Add sanitizer-backed CPU Vulkan helper regression fixtures; mouse and 16 existing
  preparation/package tests pass. Full native build and phone verification pending.
- Preserve application ID and enforce the revision 9/10 signing certificate
  fingerprint so incompatible updates cannot be uploaded silently.
- Details and primary Vulkan references: docs/GRAPHICS_STABILITY.md.

- Initial revision 11 CI 42000537825 passed unit, mouse and new Vulkan-helper
  regressions. Compilation was blocked before C++ work by an ISPC release download
  returning HTTP 504. The download path now retries into a temporary file, validates
  the archive before extracting, and caches pinned OIDN/ISPC build progress. An
  install-complete marker prevents partial denoiser installs from being reused.

- Successful revision 11 implementation: `695724c0c7f99abb4bd622937a286e7e75876db7`.
  [Workflow 42001650804](https://github.com/nawazthecoder/Blender-port-mobile-unofficial-/actions/runs/42001650804)
  passed full native compile/link, regression fixtures, runtime/ELF dependency
  audits, package identity, v3 signing and matching-update-certificate checks.
  The artifact records merge `d8ddbf3655dcfba64997bc2fd55312a3a3df77bd`, whose
  parents include the implementation commit. OIDN/ISPC cache progress was saved.
- APK: 283,076,223 bytes; 149 native libraries; versionCode 5020311.
  SHA256: `a27498aa3cb1b9e2f6b6096a9632058ef4b6da77d7428a192d451bf49e74839c`.
  Artifact 13403890275 expires 2026-11-19. Download checked against CI ZIP/APK
  hashes and saved. Signing fingerprint matches revisions 9/10.
- Exact phone glitch cause, visual behavior and performance/power measurements
  remain unverified. A recording and triggering action are useful if it persists.

## Revision 12 — Shading crash investigation

Work continues from validated revision 11 at `15a598cb0fee6e5bd94c117d383fc67889ae4763`.
The user reports that opening Shading crashes Blender on the phone. There is no
device trace yet, so the incident's exact cause remains unconfirmed.

Patch `0012-android-shading-crash-recovery.patch` corrects the Vulkan 1.1 shader
target, invalidates old incompatible SPIR-V caches, validates cache sizes/headers,
bounds Android shader compilation concurrency and preserves phone-only exit
diagnostics. APK revision 12 is an update to `org.blender.androidport`.

The CPU regression fixture covers actual compiler-target/cache helpers,
unsupported cached SPIR-V versions, truncated and oversized caches, and the
Android worker budget, alongside the existing barrier/acquisition fixtures.
All 16 package/preparation tests, native dependency collection, virtual-mouse
fixtures and Vulkan helper fixtures pass locally. ASan/UBSan remain enabled;
local LeakSanitizer detection is disabled because this executor uses ptrace.
Native compilation, APK audits and signing validation also passed in the workflow
recorded below. Do not describe the phone crash as fixed until the user has
retested Shading.


### Revision 12 validated artifact

- Implementation `b0a76abf1b672a1b337b6fad367dec749f6125ab` passed
  [workflow 43175475404](https://github.com/nawazthecoder/Blender-port-mobile-unofficial-/actions/runs/43175475404),
  job `131038579582`. Full native compilation/linking, Java packaging, regression
  fixtures, runtime/ARM64 ELF audits, APK identity, v3 signature and the retained
  update certificate all passed. The signing-key and compiler caches restored.
- Artifact provenance merge `d8f0129210921b5c334e2a367c7ad0944f925bee` was checked
  to include the implementation. The source lock matches revision 12's patches.
- Artifact `13924422570`, `blender-5.2.3-android-full-arm64`, expires 2026-11-26.
  ZIP size 281,021,036 bytes; SHA256
  `508fd2c9a90d3b595cb42c6f24b81eb1e774d883e395923049625a4351e4b962`.
- APK `blender-5.2.3-android.12-shading-arm64.apk`, 283,080,319 bytes, 149 native
  libraries, package `org.blender.androidport`, versionCode 5020312, versionName
  `5.2.3-android.12`, minimum API 31 and target API 34. APK SHA256
  `a1aa7cb3ebc6bfb4e6d918e4c39dd3c1813c5824513ded688eefa8d00455094a`.
  The ZIP/APK digests, identity, source lock and signing fingerprint were verified
  on download. The certificate remains
  `45971c45d2531454994f4382a402bdb3a491159cbee356a8a0effd831c76ab3e`.
- The exact Shading crash has not been reproduced on the user's phone. Retest
  Shading with a default cube and the original scene. If it persists, reopen once
  and attach the preserved previous log and Android exit report from Downloads.


## Revision 13 — official 5.3.0 upgrade

Migrating to stable tag v5.3.0, official commit
`02f0899d78e374b63e7181d9061e1f7ab03419cc`, with release/file metadata preserved.
Patch and checksum are locked in config/blender-android.json. The existing input,
Vulkan stability and crash diagnostics changes are adapted to 5.3's Volk/resource
APIs. Jolt, OpenTimelineIO and KTX dependencies are built from the official source
locks. See docs/UPGRADE_5_3.md. Local regression checks and clean source preparation
pass; the full native build and a new phone APK test are pending.
