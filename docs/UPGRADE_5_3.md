# Official Blender 5.3.0 Android migration — revision 13

The user requested the newest official stable Blender. The official release
page lists 5.3.0, released 2026-11-10. Source is pinned to tag v5.3.0 and commit
`02f0899d78e374b63e7181d9061e1f7ab03419cc`; its release and file-format header
is untouched. The previous validated 5.2.3 Android revision 12 remains recorded
at repository commit `9c93feb403b4ca0f96ab5dc63e391c4b3978c57c`.

The existing Android integration branch/PR is retained so the established
signing-key and build caches remain available. Its historical branch name still
contains 5.2.3; the source lock and native workflow determine the actual release.

## Changes

- Rebased the Android platform/GHOST backend, native activity, touch/keyboard,
  virtual mouse and packaging onto the released 5.3 source. Resolved source/API
  changes while retaining new official rendering and editor code.
- Migrated Android render-pass fallback and recovery paths to Volk's per-device
  dispatch table. Adapted framebuffer retirement to the new batched resource/view
  lifetime tracking, including the submission timeline and lock ordering.
- Preserved the Qualcomm SPIR-V 1.3 workaround and versioned shader caches. The
  compiler follows the device's SPIR-V 1.4 extension support while retaining the
  Vulkan 1.1 target on those devices. Cache sidecar and compiled-module versions
  use the same policy as 5.3's shader post-processing.
- Host libraries use official 5.3 gitlink
  `e92f1a54a92c774fbeb0cf51c4652bc510d9a50a`. The Android library baseline
  remains `59001bef2a4983d0f42e3281cf622a5734c1cb02`.
- New Android dependencies are built using the versions, source checksums and
  relevant patches from the official release: Jolt 5.6.0, KTX 4.4.2,
  OpenTimelineIO 31e3101e750be2aa992274ac02c0679077872e57, RapidJSON
  24b5e7a8b27f42fa16b96fc70aade9106cf7102f and minizip-ng 4.2.2.
  Successful installation markers validate settings/artifacts; downloads and
  partial builds are cached independently. Jolt's CPU backend is enabled.
- KTX's glTF native bridge and OpenTimelineIO Python bindings are included in the
  runtime payload and native dependency collection. Desktop Cycles GPU backends,
  DLSS, OSL and OpenXR remain disabled as in the mobile configuration.
- APK identity is org.blender.androidport, 5030013 / 5.3.0-android.13. Native runtime
  resources use the 5.3 directory. CI retains the existing certificate fingerprint
  guard before releasing an APK.

## Validation

The patch applies cleanly to a fresh exact stable checkout without altering its
version header. The 16 package/preparation tests, virtual-mouse sanitizer fixture,
Vulkan policy/barrier/acquisition sanitizer fixture and native collection fixture
pass locally. Local LeakSanitizer is disabled because the executor uses ptrace;
address/undefined sanitizers stay enabled. Native compilation and device behavior
are pending. Do not treat source preparation alone as a working 5.3 APK.

After a validated APK is available, save a copy of existing projects before
upgrading. Test launch/version, opening/saving a .blend, Shading, Texture Paint,
virtual-mouse menus, lifecycle changes and a small Cycles CPU render. These phone
checks have not yet run.
