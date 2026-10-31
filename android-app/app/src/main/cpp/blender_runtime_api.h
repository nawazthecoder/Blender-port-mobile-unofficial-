// SPDX-License-Identifier: GPL-2.0-or-later
#pragma once

// Native ABI between the Android host APK and a future Android Blender
// build.  This header does NOT claim that Blender is already ported.
// Ship libblender_mobile_runtime.so as an APK native library to enable it.

#include <android/native_window.h>
#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

#define BLENDER_MOBILE_RUNTIME_API_VERSION 1u

typedef struct BlenderMobileRuntimeAPI {
  uint32_t version;
  // Called when a SurfaceView window becomes available. Return 1 on success.
  int (*attach_surface)(ANativeWindow *window, const char *cache_directory);
  void (*resize)(int width, int height);
  // Called on the Android UI thread. The renderer owns its graphics context.
  void (*draw_frame)(void);
  // Receive a file path staged into the application's private cache.
  int (*open_blend_file)(const char *absolute_path);
  // dx/dy are pixels; scale is a multiplicative pinch zoom factor.
  void (*gesture)(float dx, float dy, float scale);
  void (*detach_surface)(void);
} BlenderMobileRuntimeAPI;

// Export this function from libblender_mobile_runtime.so.
typedef const BlenderMobileRuntimeAPI *(*BlenderMobileRuntimeEntry)(void);

#ifdef __cplusplus
}
#endif
