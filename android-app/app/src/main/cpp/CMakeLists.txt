cmake_minimum_required(VERSION 3.22.1)
project(blender_android_bridge LANGUAGES C CXX)

add_library(blender_android_bridge SHARED android_bridge.cpp)
target_compile_features(blender_android_bridge PRIVATE cxx_std_17)
target_compile_options(blender_android_bridge PRIVATE -Wall -Wextra)
target_link_libraries(blender_android_bridge PRIVATE android log EGL GLESv3 vulkan dl)
