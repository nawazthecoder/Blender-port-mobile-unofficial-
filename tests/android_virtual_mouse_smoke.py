#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
"""Exercise the actual GHOST virtual-mouse controller before the expensive native build."""
import os
from pathlib import Path
import subprocess
import sys
import tempfile

source = Path(sys.argv[1]).resolve()
fixture = Path(__file__).with_name('android_virtual_mouse_test.cc')
with tempfile.TemporaryDirectory(prefix='android-virtual-mouse-') as directory:
    executable = Path(directory) / 'virtual-mouse-test'
    subprocess.run([os.environ.get('CXX', 'g++'), '-std=c++20', '-Wall', '-Wextra', '-Werror',
                    '-fsanitize=address,undefined', '-fno-omit-frame-pointer', '-g',
                    '-I', str(source / 'intern/ghost'), str(fixture), '-o', str(executable)], check=True)
    subprocess.run([str(executable)], check=True)
