#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
"""Exercise production framebuffer retirement with mock Vulkan calls and containers.

The production timeline container, cache class, discard-pool class and method
bodies are compiled directly. Vulkan calls record destruction order; this does
not claim to execute shaders or a phone driver.
"""
import argparse
import os
from pathlib import Path
import subprocess
import tempfile


def definition(text, marker, semicolon=False):
    start = text.index(marker)
    opening = text.index('{', start)
    depth = 1
    end = opening + 1
    while depth:
        depth += (text[end] == '{') - (text[end] == '}')
        end += 1
    return text[start:end] + (';' if semicolon else '')


parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('source', type=Path)
parser.add_argument('--vulkan-include', required=True, type=Path)
parser.add_argument('--negative-control', action='store_true',
                    help='Prove the test rejects the missing presentation cleanup')
args = parser.parse_args()
gpu = args.source.resolve() / 'source/blender/gpu/vulkan'
pool_header = (gpu / 'vk_resource_pool.hh').read_text()
pool_source = (gpu / 'vk_resource_pool.cc').read_text()
fallback_header = (gpu / 'vk_render_pass_fallback.hh').read_text()
fallback_source = (gpu / 'vk_render_pass_fallback.cc').read_text()
methods = '\n'.join(definition(pool_source, 'void VKDiscardPool::' + name + '(')
                    for name in ['discard_swapchain_image', 'discard_image_view',
                                 'discard_resources', 'destroy_discarded_resources'])
if args.negative_control:
    missing = '''      for (VkFramebuffer framebuffer :
           device.render_pass_fallback.take_framebuffers_for_view(image_view))
      {
        device.functions.vkDestroyFramebuffer(device.vk_handle(), framebuffer, nullptr);
      }
'''
    assert methods.count(missing) == 1
    methods = methods.replace(missing, '')
parts = {
    'FALLBACK_CLASS': definition(fallback_header, 'class VKRenderPassFallback {', True)
        .replace(' private:', ' public:'),
    'TIMELINE_CLASS': definition(pool_header, 'template<typename Item> class TimelineResources', True),
    'POOL_CLASS': definition(pool_header, 'class VKDiscardPool {', True)
        .replace(' private:', ' public:'),
    'METHODS': definition(fallback_source,
        'Vector<VkFramebuffer> VKRenderPassFallback::take_framebuffers_for_view(') + '\n' + methods,
}
fixture = Path(__file__).with_suffix('.cc.in').read_text()
for name, code in parts.items():
    fixture = fixture.replace('@' + name + '@', code)
with tempfile.TemporaryDirectory(prefix='android-framebuffer-lifetime-') as directory:
    cpp = Path(directory) / 'lifetime.cc'
    binary = Path(directory) / 'lifetime'
    cpp.write_text(fixture)
    subprocess.run([os.environ.get('CXX', 'g++'), '-std=c++20', '-Wall', '-Wextra', '-Werror',
                    '-pthread', '-fsanitize=address,undefined', '-fno-omit-frame-pointer', '-g',
                    '-I', str(args.vulkan_include.resolve()), str(cpp), '-o', str(binary)],
                   check=True)
    result = subprocess.run([str(binary)], capture_output=True, text=True, timeout=30)
    if args.negative_control:
        assert result.returncode != 0 and 'presentation_cleanup' in result.stderr, result.stderr
        print('Negative control rejected: missing presentation cleanup')
    else:
        if result.returncode:
            raise RuntimeError(result.stderr)
        print(result.stdout.strip())
