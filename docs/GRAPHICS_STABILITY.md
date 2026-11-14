# Android graphics stability

## Revision 14 — Blender 5.3 presentation cleanup

The user reports lag and an exit after a few seconds with 5.3.0 revision 13.
No device report has been supplied yet, so a specific phone crash cause is not
confirmed. Investigation found a concrete error in the 5.3 resource migration:
completed swapchain resources destroyed their registered image views without
evicting the classic-render-pass framebuffers referencing those views. This left
stale GPU objects in the cache, allowing growth and reuse of invalid handles.

- All three view-retirement paths now detach dependent cached framebuffers.
- Detaching only touches the cache. It returns ownership to the caller and never
  calls back into the discard pool while holding the cache lock. This permits
  cleanup while the pool lock is already held, without recursive locking.
- Batched resources use their submission timeline; explicit views use the pool
  timeline. Completed presentation views destroy their framebuffers immediately.
- Framebuffers are destroyed before their referenced image views, exactly once
  even when a framebuffer references multiple retiring views.

A new ASan/UBSan CPU fixture compiles the actual cache and discard-pool classes,
method bodies and timeline container with mock Vulkan destruction calls. It checks
presentation cleanup, deferred destruction, shared views, handle reuse and
concurrent cleanup. Removing the presentation eviction from the tested method
causes the regression test to fail. The existing preparation/package tests and
mouse/Vulkan regressions also pass. These tests do not execute a Mali driver.

Revision 14 remains Blender 5.3.0, with versionCode 5030014 and versionName
5.3.0-android.14. Full native ARM64 build, the new regression fixture, package
audit, identity, APK v3 signature and update-certificate checks passed in
[workflow 43570439821](https://github.com/nawazthecoder/Blender-port-mobile-unofficial-/actions/runs/43570439821).
The downloaded ZIP/APK hashes, source lock and corresponding source patch match
the validated implementation. Another phone test remains pending. App identity,
update certificate, render resolution and mouse controls are retained. If the next APK still exits, reopen it once and collect
blender-previous.log and blender-last-exit.txt from Downloads (or the log path
shown at launch). Android may also supply blender-last-exit.trace.

## Revision 12 — Shading workspace crash hardening

The user reports a crash when opening Shading. A device crash log has not yet
been supplied, so neither a specific driver fault nor an Android low-memory
termination has been confirmed.

The investigation found a concrete compatibility bug. The shader compiler
always selected Vulkan 1.2, including on Vulkan 1.1 devices supported by the
Android backend. It now selects Vulkan 1.1 / SPIR-V 1.3 for those devices.
Newer devices retain Vulkan 1.2 / SPIR-V 1.5, with the existing Qualcomm
SPIR-V 1.3 workaround preserved. See the official
[Vulkan/SPIR-V version mapping](https://docs.vulkan.org/guide/latest/versions.html).

- Shader cache directories now encode the compiler settings and a new format
  revision, so previously emitted incompatible modules are rebuilt automatically.
- Cached SPIR-V sizes, word alignment, header and version are checked before
  reuse. Failed reads and partial cache files are treated as misses. File access
  is serialized across compiler workers. Pipeline cache headers and exact payload
  lengths are checked before passing data to the driver, and rejected driver
  caches are ignored.
- Android compiler concurrency is capped at two workers below 6 GiB of RAM or
  when RAM detection fails, and four on larger devices. This bounds temporary
  compiler allocations when Material Preview starts. The viewport resolution,
  materials and scene data are preserved. No measured memory reduction is claimed.
- The prior session's startup log is preserved as `blender-previous.log` before
  a new session starts. Android's newest available process-exit record is saved
  as `blender-last-exit.txt`, with an optional `blender-last-exit.trace` alongside
  it. These use the existing log destination, normally Downloads after granting
  file access. Android may not retain a native trace. Reports stay on the phone.

The APK uses versionCode **5020312**, versionName **5.2.3-android.12**, and the
existing **org.blender.androidport** package and signing identity. Full native
compilation, regression fixtures, runtime/ELF audits, APK identity, v3 signing
and matching-update-certificate checks passed in
[workflow 43175475404](https://github.com/nawazthecoder/Blender-port-mobile-unofficial-/actions/runs/43175475404).
The downloaded ZIP and APK hashes were checked against CI, and the APK source
merge was verified to contain implementation `b0a76abf1b672a1b337b6fad367dec749f6125ab`.
The user's Shading test remains pending.

After installing, save any unsaved project and test opening Shading on a new
default cube, then on the scene that originally crashed. If it still exits,
reopen Blender once and attach `blender-last-exit.txt` and `blender-previous.log`.
The optional trace can help locate native driver faults. Do not clear app data
to refresh shaders; the cache namespace handles this update.

## Revision 11 — Synchronization and scheduling

This update targets real synchronization and presentation faults found while
investigating the user's report of occasional short graphics glitches. The exact
phone incident has not been reproduced or attributed to a single cause.

## Rendering changes

- Barrier merging now compares the complete image subresource range: aspect,
  mip levels, array layers and counts, plus compatible layouts and queue ownership.
  Matching only the image handle could discard a transition for another texture
  level or layer, leaving stale or incorrectly interpreted image contents.
- Scoped attachment changes stay in the subresource tracker rather than changing
  the whole-image layout state. Its access dependencies target the same mip/layer
  as the layout transition. Duplicate range detection compares both axes and aspect.
- Repeated writes require synchronization even when their access flags match.
  Read-after-read access can avoid a redundant memory dependency. Depth/stencil
  writes are included when a rendering scope is suspended.
- Vulkan acquire results are checked before using an image index. Only SUCCESS
  and SUBOPTIMAL own an image; timeouts/errors skip the draw without clearing its
  dirty flags. OUT_OF_DATE retries are bounded, and Android surface-loss recovery
  is requested at the existing synchronized surface boundary.
- Android frame-fence and image-acquire waits have a 20 ms budget so a temporarily
  busy GPU/compositor can return control to input and lifecycle handling. Expected
  timeouts are not reported as errors. Repeated acquire failures are logged on changes.

Vulkan references: [image-barrier scope/layout rules](https://docs.vulkan.org/refpages/latest/refpages/source/VkImageMemoryBarrier.html)
and [swapchain image acquisition](https://docs.vulkan.org/refpages/latest/refpages/source/vkAcquireNextImageKHR.html).
The regression fixtures exercise the actual helper functions used by the port.
They simulate independent mip/layer transitions and acquisition failures without
claiming to execute Vulkan commands on a Mali GPU.

## Power and responsiveness

Android idle waiting now uses looper readiness instead of an unconditional 5 ms
sleep. Input/lifecycle file descriptors wake it immediately; Blender's next timer
can shorten its 16 ms idle budget. UI drawing stops while the activity is paused
or has no window. Background job/timer handling continues at a lower rate, with
native events waking the loop immediately.

The viewport resolution and supported Vulkan features are not reduced. These
changes remove unnecessary synchronization/wakeups and invalid presentation;
no measured FPS, temperature, memory or battery improvement is claimed yet.

## Installation and verification

Revision 11 updates **Blender Android** (org.blender.androidport). Save the current
project before installing it over revision 9 or 10. CI verifies the signing
certificate against the public fingerprint recorded from those releases, so a
newly generated unrelated development key cannot silently produce an incompatible
update.

Local CPU regression tests, virtual-mouse tests and package/preparation tests
pass. Full native compilation, runtime/ELF dependency audits, APK identity, v3
signing and update-certificate validation passed in [workflow 42001650804](https://github.com/nawazthecoder/Blender-port-mobile-unofficial-/actions/runs/42001650804).
Phone testing of flicker, viewport modes, rotation, background/resume and sustained
responsiveness remains necessary.

If the brief glitch persists, a short screen recording and what action triggered
it help distinguish a texture/geometry problem from a whole-frame flash. Vulkan
recovery warnings are captured by the existing blender-startup.log in shared
Downloads when storage permission allows, with app storage as its fallback.
