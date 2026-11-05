#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
"""Run CPU-only tests against the actual barrier/acquire helpers; no phone GPU is required."""
import argparse
import os
from pathlib import Path
import subprocess
import tempfile

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('source', type=Path)
parser.add_argument('--vulkan-include', required=True, type=Path)
args = parser.parse_args()
source = args.source.resolve()
with tempfile.TemporaryDirectory(prefix='android-vulkan-regressions-') as directory:
    binary = Path(directory) / 'vulkan-regressions'
    subprocess.run([os.environ.get('CXX', 'g++'), '-std=c++20', '-Wall', '-Wextra', '-Werror',
                    '-fsanitize=address,undefined', '-fno-omit-frame-pointer', '-g',
                    '-I', str(args.vulkan_include.resolve()),
                    '-I', str(source / 'intern/ghost'),
                    '-I', str(source / 'source/blender/gpu/vulkan/render_graph'),
                    str(Path(__file__).with_suffix('.cc')), '-o', str(binary)], check=True)
    subprocess.run([str(binary)], check=True)
