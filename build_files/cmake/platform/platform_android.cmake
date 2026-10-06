# SPDX-FileCopyrightText: 2026 Blender Android Port
#
# SPDX-License-Identifier: GPL-2.0-or-later

# ------------------------------------------------------------------------
# Blender Android platform configuration.
#
# This is intentionally a minimal first-stage platform file.
# It prevents Android from falling through to platform_unix.cmake.
#
# Android-specific dependencies, GHOST, EGL/Vulkan surface creation,
# linker configuration, and packaging will be added separately.
# ------------------------------------------------------------------------

message(STATUS "==========================================")
message(STATUS "Configuring Blender for Android")
message(STATUS "Android ABI: ${CMAKE_ANDROID_ARCH_ABI}")
message(STATUS "Android API: ${CMAKE_ANDROID_API}")
message(STATUS "C Compiler: ${CMAKE_C_COMPILER}")
message(STATUS "CXX Compiler: ${CMAKE_CXX_COMPILER}")
message(STATUS "==========================================")

# Android/Bionic.
add_definitions(-D__ANDROID__)

# ------------------------------------------------------------------------
# Desktop window systems are not used by the native Android build.
# ------------------------------------------------------------------------

set(WITH_GHOST_X11 OFF CACHE BOOL "" FORCE)
set(WITH_GHOST_WAYLAND OFF CACHE BOOL "" FORCE)

# We will add the actual Android GHOST implementation later.
set(WITH_GHOST_SDL OFF CACHE BOOL "" FORCE)

# ------------------------------------------------------------------------
# Graphics backend.
#
# The target is Vulkan through Android's native Vulkan interface.
# The actual VK_KHR_android_surface / ANativeWindow integration will be
# implemented in the Android GHOST/context layer.
# ------------------------------------------------------------------------

set(WITH_VULKAN_BACKEND ON CACHE BOOL "" FORCE)
set(WITH_OPENGL_BACKEND OFF CACHE BOOL "" FORCE)

# ------------------------------------------------------------------------
# Android system libraries.
# ------------------------------------------------------------------------

list(APPEND PLATFORM_LINKLIBS
  android
  log
  dl
  m
  z
)

# ------------------------------------------------------------------------
# Do not use the normal Linux desktop installation/link flags.
# ------------------------------------------------------------------------

set(PLATFORM_LINKFLAGS "" CACHE STRING "" FORCE)
set(PLATFORM_LINKFLAGS_DEBUG "" CACHE STRING "" FORCE)

# ------------------------------------------------------------------------
# Android does not have Blender's normal desktop precompiled library
# directory. Dependency handling will be added by the Android build
# system rather than pretending linux_arm64 is available.
# ------------------------------------------------------------------------

set(LIBDIR "" CACHE PATH "" FORCE)

message(STATUS "Blender Android platform configuration loaded successfully")
