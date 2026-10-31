// SPDX-License-Identifier: GPL-2.0-or-later
// Android host: a native EGL/GLES smoke test and a dynamic integration seam.
// This is NOT Blender's drawing backend or GHOST implementation.

#include "blender_runtime_api.h"

#include <jni.h>
#include <android/log.h>
#include <android/native_window_jni.h>
#include <EGL/egl.h>
#include <EGL/eglext.h>
#include <GLES3/gl3.h>
#include <vulkan/vulkan.h>
#include <dlfcn.h>

#include <algorithm>
#include <cmath>
#include <cstdint>
#include <sstream>
#include <string>
#include <vector>

namespace {
constexpr const char *kLogTag = "BlenderAndroidHost";

ANativeWindow *g_window = nullptr;
EGLDisplay g_display = EGL_NO_DISPLAY;
EGLSurface g_surface = EGL_NO_SURFACE;
EGLContext g_context = EGL_NO_CONTEXT;
int g_width = 0;
int g_height = 0;
float g_grid_spacing = 60.f;
float g_offset_x = 0.f;
float g_offset_y = 0.f;

void *g_runtime_handle = nullptr;
const BlenderMobileRuntimeAPI *g_runtime = nullptr;
bool g_runtime_attempted = false;
bool g_runtime_active = false;

void log_error(const char *what) {
  __android_log_print(ANDROID_LOG_ERROR, kLogTag, "%s (EGL: 0x%x)", what,
                      eglGetError());
}

void load_runtime_once() {
  if (g_runtime_attempted) {
    return;
  }
  g_runtime_attempted = true;
  g_runtime_handle = dlopen("libblender_mobile_runtime.so", RTLD_NOW | RTLD_LOCAL);
  if (!g_runtime_handle) {
    __android_log_print(ANDROID_LOG_INFO, kLogTag,
                        "Blender native runtime is not packaged: %s", dlerror());
    return;
  }
  auto entry = reinterpret_cast<BlenderMobileRuntimeEntry>(
      dlsym(g_runtime_handle, "blender_android_runtime_api"));
  if (entry) {
    g_runtime = entry();
  }
  if (!g_runtime || g_runtime->version != BLENDER_MOBILE_RUNTIME_API_VERSION ||
      !g_runtime->attach_surface || !g_runtime->draw_frame ||
      !g_runtime->detach_surface) {
    __android_log_print(ANDROID_LOG_ERROR, kLogTag,
                        "Bundled Blender runtime has an incompatible API");
    g_runtime = nullptr;
    dlclose(g_runtime_handle);
    g_runtime_handle = nullptr;
  }
}

void destroy_egl() {
  if (g_display != EGL_NO_DISPLAY) {
    eglMakeCurrent(g_display, EGL_NO_SURFACE, EGL_NO_SURFACE, EGL_NO_CONTEXT);
    if (g_surface != EGL_NO_SURFACE) {
      eglDestroySurface(g_display, g_surface);
    }
    if (g_context != EGL_NO_CONTEXT) {
      eglDestroyContext(g_display, g_context);
    }
    eglTerminate(g_display);
  }
  g_display = EGL_NO_DISPLAY;
  g_surface = EGL_NO_SURFACE;
  g_context = EGL_NO_CONTEXT;
  g_width = 0;
  g_height = 0;
}

bool create_egl() {
  if (!g_window) {
    return false;
  }
  g_display = eglGetDisplay(EGL_DEFAULT_DISPLAY);
  if (g_display == EGL_NO_DISPLAY || !eglInitialize(g_display, nullptr, nullptr)) {
    log_error("Failed to initialize EGL");
    destroy_egl();
    return false;
  }
  if (!eglBindAPI(EGL_OPENGL_ES_API)) {
    log_error("eglBindAPI failed");
    destroy_egl();
    return false;
  }

  const EGLint config_attrs[] = {
      EGL_SURFACE_TYPE, EGL_WINDOW_BIT,
      EGL_RENDERABLE_TYPE, EGL_OPENGL_ES3_BIT_KHR,
      EGL_RED_SIZE, 8, EGL_GREEN_SIZE, 8,
      EGL_BLUE_SIZE, 8, EGL_ALPHA_SIZE, 8, EGL_NONE};
  EGLConfig config = nullptr;
  EGLint config_count = 0;
  if (!eglChooseConfig(g_display, config_attrs, &config, 1, &config_count) ||
      config_count < 1) {
    log_error("No ES3 window EGL configuration");
    destroy_egl();
    return false;
  }
  const EGLint context_attrs[] = {EGL_CONTEXT_CLIENT_VERSION, 3, EGL_NONE};
  g_context = eglCreateContext(g_display, config, EGL_NO_CONTEXT, context_attrs);
  if (g_context == EGL_NO_CONTEXT) {
    log_error("Failed to create ES3 context");
    destroy_egl();
    return false;
  }
  g_surface = eglCreateWindowSurface(g_display, config, g_window, nullptr);
  if (g_surface == EGL_NO_SURFACE ||
      !eglMakeCurrent(g_display, g_surface, g_surface, g_context)) {
    log_error("Failed to create/make current EGL window surface");
    destroy_egl();
    return false;
  }
  eglQuerySurface(g_display, g_surface, EGL_WIDTH, &g_width);
  eglQuerySurface(g_display, g_surface, EGL_HEIGHT, &g_height);
  glViewport(0, 0, g_width, g_height);
  __android_log_print(ANDROID_LOG_INFO, kLogTag, "EGL preview %dx%d, GPU: %s",
                      g_width, g_height,
                      reinterpret_cast<const char *>(glGetString(GL_RENDERER)));
  return true;
}

void detach_surface() {
  if (g_runtime_active) {
    g_runtime->detach_surface();
    g_runtime_active = false;
  }
  destroy_egl();
  if (g_window) {
    ANativeWindow_release(g_window);
    g_window = nullptr;
  }
}

std::string vulkan_summary() {
  uint32_t api_version = VK_API_VERSION_1_0;
  if (vkEnumerateInstanceVersion(&api_version) != VK_SUCCESS) {
    return "Vulkan loader unavailable";
  }
  VkApplicationInfo app_info{};
  app_info.sType = VK_STRUCTURE_TYPE_APPLICATION_INFO;
  app_info.pApplicationName = "Blender Android GPU diagnostic";
  app_info.apiVersion = VK_API_VERSION_1_0;

  VkInstanceCreateInfo info{};
  info.sType = VK_STRUCTURE_TYPE_INSTANCE_CREATE_INFO;
  info.pApplicationInfo = &app_info;
  VkInstance instance = VK_NULL_HANDLE;
  VkResult result = vkCreateInstance(&info, nullptr, &instance);
  std::ostringstream os;
  os << "Vulkan " << VK_VERSION_MAJOR(api_version) << "."
     << VK_VERSION_MINOR(api_version);
  if (result != VK_SUCCESS) {
    os << " (instance creation failed: " << result << ")";
    return os.str();
  }
  uint32_t count = 0;
  result = vkEnumeratePhysicalDevices(instance, &count, nullptr);
  if (result == VK_SUCCESS && count > 0) {
    std::vector<VkPhysicalDevice> devices(count);
    result = vkEnumeratePhysicalDevices(instance, &count, devices.data());
    if (result == VK_SUCCESS && count > 0) {
      VkPhysicalDeviceProperties props{};
      vkGetPhysicalDeviceProperties(devices[0], &props);
      os << " | " << props.deviceName;
    }
  } else {
    os << " (no physical device reported)";
  }
  vkDestroyInstance(instance, nullptr);
  return os.str();
}

void preview_frame() {
  if (g_display == EGL_NO_DISPLAY || g_surface == EGL_NO_SURFACE) {
    return;
  }
  if (!eglMakeCurrent(g_display, g_surface, g_surface, g_context)) {
    log_error("EGL context was lost");
    return;
  }
  // A plain full-resolution GPU smoke test. No fake Blender mesh rendering.
  glViewport(0, 0, g_width, g_height);
  glDisable(GL_DEPTH_TEST);
  glDisable(GL_BLEND);
  glClearColor(0.105f, 0.113f, 0.129f, 1.f);
  glClear(GL_COLOR_BUFFER_BIT);
  const int spacing = std::max(20, static_cast<int>(g_grid_spacing));
  const int offset_x = (static_cast<int>(std::fmod(g_offset_x, float(spacing))) +
                        spacing) % spacing;
  const int offset_y = (static_cast<int>(std::fmod(g_offset_y, float(spacing))) +
                        spacing) % spacing;
  glEnable(GL_SCISSOR_TEST);
  glClearColor(0.18f, 0.19f, 0.21f, 1.f);
  for (int x = offset_x; x < g_width; x += spacing) {
    glScissor(x, 0, 1, g_height);
    glClear(GL_COLOR_BUFFER_BIT);
  }
  for (int y = offset_y; y < g_height; y += spacing) {
    glScissor(0, y, g_width, 1);
    glClear(GL_COLOR_BUFFER_BIT);
  }
  glDisable(GL_SCISSOR_TEST);
  if (!eglSwapBuffers(g_display, g_surface)) {
    log_error("eglSwapBuffers failed");
  }
}
}  // namespace

extern "C" JNIEXPORT jstring JNICALL
Java_org_blender_mobile_port_BlenderActivity_nativeStatus(JNIEnv *env, jclass) {
  load_runtime_once();
  std::string output = g_runtime
                           ? "Blender native runtime: bundled (integration experimental)"
                           : "Blender native runtime: NOT BUILT / NOT INSTALLED";
  output += "  |  " + vulkan_summary();
  if (g_context != EGL_NO_CONTEXT) {
    const auto *renderer = reinterpret_cast<const char *>(glGetString(GL_RENDERER));
    output += "  |  GLES: ";
    output += renderer ? renderer : "unknown";
  }
  return env->NewStringUTF(output.c_str());
}

extern "C" JNIEXPORT jboolean JNICALL
Java_org_blender_mobile_port_BlenderActivity_nativeHasRuntime(JNIEnv *, jclass) {
  load_runtime_once();
  return g_runtime != nullptr ? JNI_TRUE : JNI_FALSE;
}

extern "C" JNIEXPORT jboolean JNICALL
Java_org_blender_mobile_port_BlenderActivity_nativeAttachSurface(
    JNIEnv *env, jclass, jobject java_surface, jstring cache_dir) {
  detach_surface();
  if (!java_surface || !cache_dir) {
    return JNI_FALSE;
  }
  g_window = ANativeWindow_fromSurface(env, java_surface);
  if (!g_window) {
    return JNI_FALSE;
  }
  load_runtime_once();
  if (g_runtime) {
    const char *path = env->GetStringUTFChars(cache_dir, nullptr);
    if (path) {
      g_runtime_active = g_runtime->attach_surface(g_window, path) != 0;
      env->ReleaseStringUTFChars(cache_dir, path);
    }
    if (g_runtime_active) {
      return JNI_TRUE;
    }
    __android_log_print(ANDROID_LOG_WARN, kLogTag,
                        "Blender runtime surface attach failed; using GPU test");
  }
  if (!create_egl()) {
    detach_surface();
    return JNI_FALSE;
  }
  return JNI_TRUE;
}

extern "C" JNIEXPORT void JNICALL
Java_org_blender_mobile_port_BlenderActivity_nativeResize(
    JNIEnv *, jclass, jint width, jint height) {
  if (width <= 0 || height <= 0) {
    return;
  }
  g_width = width;
  g_height = height;
  if (g_runtime_active && g_runtime->resize) {
    g_runtime->resize(width, height);
  } else if (g_context != EGL_NO_CONTEXT) {
    glViewport(0, 0, width, height);
  }
}

extern "C" JNIEXPORT void JNICALL
Java_org_blender_mobile_port_BlenderActivity_nativeDrawFrame(JNIEnv *, jclass) {
  if (g_runtime_active) {
    g_runtime->draw_frame();
  } else {
    preview_frame();
  }
}

extern "C" JNIEXPORT void JNICALL
Java_org_blender_mobile_port_BlenderActivity_nativeGesture(
    JNIEnv *, jclass, jfloat dx, jfloat dy, jfloat scale) {
  if (g_runtime_active) {
    if (g_runtime->gesture) {
      g_runtime->gesture(dx, dy, scale);
    }
    return;
  }
  if (!std::isfinite(scale) || scale <= 0.f) {
    return;
  }
  g_grid_spacing = std::clamp(g_grid_spacing * scale, 20.f, 180.f);
  if (std::isfinite(dx) && std::isfinite(dy)) {
    g_offset_x += dx;
    g_offset_y -= dy;
    if (std::abs(g_offset_x) > 100000.f || std::abs(g_offset_y) > 100000.f) {
      g_offset_x = 0.f;
      g_offset_y = 0.f;
    }
  }
}

extern "C" JNIEXPORT jboolean JNICALL
Java_org_blender_mobile_port_BlenderActivity_nativeOpenBlend(
    JNIEnv *env, jclass, jstring absolute_path) {
  if (!g_runtime_active || !g_runtime->open_blend_file || !absolute_path) {
    return JNI_FALSE;
  }
  const char *path = env->GetStringUTFChars(absolute_path, nullptr);
  if (!path) {
    return JNI_FALSE;
  }
  const bool opened = g_runtime->open_blend_file(path) != 0;
  env->ReleaseStringUTFChars(absolute_path, path);
  return opened ? JNI_TRUE : JNI_FALSE;
}

extern "C" JNIEXPORT void JNICALL
Java_org_blender_mobile_port_BlenderActivity_nativeDetachSurface(JNIEnv *, jclass) {
  detach_surface();
}

extern "C" JNIEXPORT void JNICALL
Java_org_blender_mobile_port_BlenderActivity_nativeShutdown(JNIEnv *, jclass) {
  detach_surface();
  if (g_runtime_handle) {
    dlclose(g_runtime_handle);
    g_runtime_handle = nullptr;
    g_runtime = nullptr;
  }
  g_runtime_attempted = false;
}
