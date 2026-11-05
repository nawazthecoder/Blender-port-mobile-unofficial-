/* SPDX-License-Identifier: GPL-2.0-or-later */
#include "GHOST_VulkanAcquire.hh"
#include "vk_image_barrier.hh"
#include <array>
#include <cassert>
#include <iostream>
#include <vector>
using namespace blender::gpu::render_graph;

static VkImageMemoryBarrier barrier(int mip, int layer,
    VkImageLayout old_layout = VK_IMAGE_LAYOUT_GENERAL,
    VkImageLayout new_layout = VK_IMAGE_LAYOUT_COLOR_ATTACHMENT_OPTIMAL)
{
  return {VK_STRUCTURE_TYPE_IMAGE_MEMORY_BARRIER, nullptr,
          VK_ACCESS_SHADER_WRITE_BIT, VK_ACCESS_COLOR_ATTACHMENT_WRITE_BIT,
          old_layout, new_layout, VK_QUEUE_FAMILY_IGNORED, VK_QUEUE_FAMILY_IGNORED,
          VkImage(uintptr_t(1)), {VK_IMAGE_ASPECT_COLOR_BIT, uint32_t(mip), 1, uint32_t(layer), 1}};
}
static void append(std::vector<VkImageMemoryBarrier> &batch, const VkImageMemoryBarrier &next)
{
  for (auto &current : batch) {
    if (image_barrier_try_merge(current, next)) { return; }
  }
  batch.push_back(next);
}
int main()
{
  std::vector<VkImageMemoryBarrier> batch;
  for (int mip = 0; mip < 2; mip++) {
    for (int layer = 0; layer < 2; layer++) { append(batch, barrier(mip, layer)); }
  }
  assert(batch.size() == 4); /* The old image-handle-only merge silently left three cells stale. */
  std::array<std::array<VkImageLayout, 2>, 2> layouts;
  for (auto &mips : layouts) { mips.fill(VK_IMAGE_LAYOUT_GENERAL); }
  for (const auto &b : batch) {
    auto &layout = layouts[b.subresourceRange.baseMipLevel][b.subresourceRange.baseArrayLayer];
    assert(layout == b.oldLayout); layout = b.newLayout;
  }
  for (const auto &mips : layouts) {
    for (auto layout : mips) { assert(layout == VK_IMAGE_LAYOUT_COLOR_ATTACHMENT_OPTIMAL); }
  }
  batch.clear();
  for (int mip = 0; mip < 2; mip++) {
    for (int layer = 0; layer < 2; layer++) {
      append(batch, barrier(mip, layer, VK_IMAGE_LAYOUT_COLOR_ATTACHMENT_OPTIMAL, VK_IMAGE_LAYOUT_GENERAL));
      auto next = barrier(mip, layer, VK_IMAGE_LAYOUT_GENERAL, VK_IMAGE_LAYOUT_TRANSFER_SRC_OPTIMAL);
      next.dstAccessMask = VK_ACCESS_TRANSFER_READ_BIT; append(batch, next);
    }
  }
  assert(batch.size() == 4);
  for (const auto &b : batch) {
    auto &layout = layouts[b.subresourceRange.baseMipLevel][b.subresourceRange.baseArrayLayer];
    assert(layout == b.oldLayout); layout = b.newLayout;
    assert(layout == VK_IMAGE_LAYOUT_TRANSFER_SRC_OPTIMAL);
    assert(b.dstAccessMask & VK_ACCESS_TRANSFER_READ_BIT);
  }
  {
    auto original = barrier(0, 0), duplicate = original;
    duplicate.srcAccessMask = VK_ACCESS_TRANSFER_WRITE_BIT;
    duplicate.dstAccessMask = VK_ACCESS_SHADER_READ_BIT;
    assert(image_barrier_try_merge(original, duplicate));
    assert(original.srcAccessMask & VK_ACCESS_SHADER_WRITE_BIT);
    assert(original.srcAccessMask & VK_ACCESS_TRANSFER_WRITE_BIT);
    assert(original.dstAccessMask & VK_ACCESS_COLOR_ATTACHMENT_WRITE_BIT);
    assert(original.dstAccessMask & VK_ACCESS_SHADER_READ_BIT);
    auto incompatible = barrier(0, 0, VK_IMAGE_LAYOUT_PRESENT_SRC_KHR, VK_IMAGE_LAYOUT_GENERAL);
    assert(!image_barrier_try_merge(original, incompatible));
  }
  {
    auto full = barrier(0, 0), partial = full;
    full.subresourceRange.levelCount = VK_REMAINING_MIP_LEVELS;
    assert(!image_barrier_try_merge(full, partial));
    full = partial; full.subresourceRange.layerCount = VK_REMAINING_ARRAY_LAYERS;
    assert(!image_barrier_try_merge(full, partial));
    full = partial; full.image = VkImage(uintptr_t(2));
    assert(!image_barrier_try_merge(full, partial));
    full = partial; full.subresourceRange.aspectMask = VK_IMAGE_ASPECT_DEPTH_BIT;
    partial.subresourceRange.aspectMask = VK_IMAGE_ASPECT_STENCIL_BIT;
    assert(!image_barrier_try_merge(full, partial));
    full = partial; full.dstQueueFamilyIndex = 2;
    assert(!image_barrier_try_merge(full, partial));
  }
  assert(!image_access_needs_dependency(VK_ACCESS_SHADER_READ_BIT, VK_ACCESS_SHADER_READ_BIT));
  assert(!image_access_needs_dependency(VK_ACCESS_TRANSFER_READ_BIT, VK_ACCESS_SHADER_READ_BIT));
  assert(image_access_needs_dependency(VK_ACCESS_SHADER_WRITE_BIT, VK_ACCESS_SHADER_WRITE_BIT));
  assert(image_access_needs_dependency(VK_ACCESS_DEPTH_STENCIL_ATTACHMENT_WRITE_BIT,
                                        VK_ACCESS_DEPTH_STENCIL_ATTACHMENT_WRITE_BIT));
  assert(image_access_needs_dependency(VK_ACCESS_SHADER_READ_BIT, VK_ACCESS_SHADER_WRITE_BIT));
  assert(image_access_needs_dependency(VK_ACCESS_MEMORY_WRITE_BIT, VK_ACCESS_SHADER_READ_BIT));
  assert(!image_access_needs_dependency(0, VK_ACCESS_SHADER_WRITE_BIT));

  for (VkResult status : {VK_SUCCESS, VK_SUBOPTIMAL_KHR}) {
    int calls = 0, recreates = 0;
    auto result = GHOST_vulkan_acquire_image([&](uint32_t *index) {
      calls++; *index = 3; return status;
    }, [&]() { recreates++; return true; });
    assert(result.image_index && *result.image_index == 3 && calls == 1 && recreates == 0);
  }
  for (VkResult status : {VK_TIMEOUT, VK_NOT_READY, VK_ERROR_DEVICE_LOST,
                          VK_ERROR_SURFACE_LOST_KHR, VK_ERROR_OUT_OF_DEVICE_MEMORY})
  {
    int calls = 0, recreates = 0;
    auto result = GHOST_vulkan_acquire_image([&](uint32_t *index) {
      calls++; *index = 99; return status; /* A driver must never make this an owned image. */
    }, [&]() { recreates++; return true; });
    assert(!result.image_index && result.result == status && calls == 1 && recreates == 0);
  }
  {
    int calls = 0, recreates = 0;
    auto result = GHOST_vulkan_acquire_image([&](uint32_t *index) {
      *index = 2; return ++calls == 1 ? VK_ERROR_OUT_OF_DATE_KHR : VK_SUCCESS;
    }, [&]() { recreates++; return true; });
    assert(result.image_index && *result.image_index == 2 && calls == 2 && recreates == 1);
  }
  {
    int calls = 0, recreates = 0;
    auto result = GHOST_vulkan_acquire_image([&](uint32_t *) {
      calls++; return VK_ERROR_OUT_OF_DATE_KHR;
    }, [&]() { recreates++; return true; });
    assert(!result.image_index && calls == 3 && recreates == 2);
    result = GHOST_vulkan_acquire_image([&](uint32_t *) {
      calls++; return VK_ERROR_OUT_OF_DATE_KHR;
    }, [&]() { recreates++; return false; });
    assert(!result.image_index && calls == 4 && recreates == 3);
  }
  std::cout << "Vulkan regressions: independent mip/layer/aspect transitions, write hazards, "
               "acquire ownership and bounded recovery passed\n";
}
