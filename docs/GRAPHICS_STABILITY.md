# Android graphics stability — revision 11

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
  timeouts are not reported as errors. Repeated failures are logged on changes.

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
pass. Full native compilation/package validation is pending for this checkpoint.
Phone testing of flicker, viewport modes, rotation, background/resume and sustained
responsiveness remains necessary.

If the brief glitch persists, a short screen recording and what action triggered
it help distinguish a texture/geometry problem from a whole-frame flash. Vulkan
recovery warnings are captured by the existing blender-startup.log in shared
Downloads when storage permission allows, with app storage as its fallback.
