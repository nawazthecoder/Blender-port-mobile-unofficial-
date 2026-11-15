#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
"""Exercise production pool allocation/routing with mocked VMA calls, without a GPU."""
import argparse
import os
from pathlib import Path
import subprocess
import tempfile


def definition(text, marker):
    start = text.index(marker)
    end = text.index('{', start) + 1
    depth = 1
    while depth:
        depth += (text[end] == '{') - (text[end] == '}')
        end += 1
    return text[start:end]


parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('source', type=Path)
parser.add_argument('--vulkan-include', required=True, type=Path)
parser.add_argument('--negative-control', action='store_true')
args = parser.parse_args()
source = args.source.resolve()
pool = (source / 'source/blender/gpu/vulkan/vk_texture_pool.cc').read_text()
header = (source / 'source/blender/gpu/vulkan/vk_texture_pool.hh').read_text()
ghost = (source / 'intern/ghost/intern/GHOST_ContextVK.cc').read_text()
config_start = header.index('{', header.index('class VKTexturePool :')) + 1
config_end = header.index('  /* Defer deallocation enough cycles', config_start)
routing_start = pool.index('  /* Find a compatible segment of allocated memory. */')
routing_end = pool.index('  /* Generate debug label name, attempt', routing_start)
parts = {
    'CONFIG': header[config_start:config_end],
    'ROUTING': pool[routing_start:routing_end],
    'ALLOC': definition(pool, 'void VKTexturePool::AllocationHandle::alloc('),
    'ACQUIRE': definition(pool, 'std::optional<VKMemorySegment> VKTexturePool::AllocationHandle::acquire('),
    'RELEASE': definition(pool, 'void VKTexturePool::AllocationHandle::release('),
    'GHOST_ALLOCATOR': definition(ghost, 'void init_memory_allocator(VkInstance vk_instance)'),
}
if args.negative_control:
    old = 'if (!bool(requirements.memoryTypeBits & memory_type_bit))'
    assert parts['ACQUIRE'].count(old) == 1
    parts['ACQUIRE'] = parts['ACQUIRE'].replace(
        old, 'if (allocation_info.memoryType != 0 && !bool(requirements.memoryTypeBits & memory_type_bit))')
fixture = Path(__file__).with_suffix('.cc.in').read_text()
for name, code in parts.items():
    fixture = fixture.replace('@' + name + '@', code)
with tempfile.TemporaryDirectory(prefix='android-gpu-memory-') as directory:
    cpp = Path(directory) / 'memory.cc'
    cpp.write_text(fixture)
    for android in (True,) if args.negative_control else (True, False):
        binary = Path(directory) / ('android' if android else 'desktop')
        command = [os.environ.get('CXX', 'g++'), '-std=c++20', '-Wall', '-Wextra', '-Werror',
                   '-Wno-missing-field-initializers',
                   '-fsanitize=address,undefined', '-fno-omit-frame-pointer', '-g']
        if android:
            command.append('-D__ANDROID__')
        command += ['-I', str(args.vulkan_include.resolve()),
                    '-I', str(source / 'extern/vulkan_memory_allocator'),
                    str(cpp), '-o', str(binary)]
        subprocess.run(command, check=True)
        result = subprocess.run([str(binary)], text=True, capture_output=True, timeout=30)
        if args.negative_control:
            assert result.returncode != 0 and 'memory_type_zero_must_be_rejected' in result.stderr, result.stderr
            print('Negative control rejected: incompatible memory type zero was reused')
        else:
            if result.returncode:
                raise RuntimeError(result.stderr)
            print(result.stdout.strip())
