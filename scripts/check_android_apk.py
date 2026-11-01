#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
"""Reject diagnostic/missing-runtime APKs; audit ARM64 ELF dependency closure."""
import argparse
import hashlib
import io
import json
from pathlib import Path
import re
import struct
import subprocess
import tempfile
import zipfile

SYSTEM_LIBS = {'libc.so', 'libm.so', 'libdl.so', 'liblog.so', 'libandroid.so',
               'libvulkan.so', 'libz.so', 'libEGL.so', 'libGLESv2.so', 'libGLESv3.so',
               'libOpenSLES.so', 'libaaudio.so', 'libjnigraphics.so', 'libmediandk.so',
               'libcamera2ndk.so', 'libnativewindow.so', 'libsync.so', 'libneuralnetworks.so'}


def audit(apk, readelf, full=True):
    with zipfile.ZipFile(apk) as archive, tempfile.TemporaryDirectory() as temp:
        names = set(archive.namelist())
        for required in ('AndroidManifest.xml', 'classes.dex', 'lib/arm64-v8a/libblender.so',
                         'lib/arm64-v8a/libc++_shared.so', 'assets/blender_runtime.zip'):
            if required not in names:
                raise ValueError(f'Incomplete Blender APK: missing {required}')
        native = {Path(n).name: n for n in names if n.startswith('lib/arm64-v8a/') and n.endswith('.so')}
        runtime_data = archive.read('assets/blender_runtime.zip')
        with zipfile.ZipFile(io.BytesIO(runtime_data)) as runtime:
            files = set(runtime.namelist())
            for prefix in ('scripts/startup/', 'scripts/modules/', 'datafiles/', 'python/lib/'):
                if not any(n.startswith(prefix) for n in files):
                    raise ValueError(f'Missing runtime payload: {prefix}')
            if not any('/encodings/__init__.py' in n for n in files):
                raise ValueError('Python standard library encodings is missing')
            if not any(n.startswith('datafiles/assets/') and n.endswith('.blend') for n in files):
                raise ValueError('Essentials brush/node assets are missing')
            if full and not any(n.endswith('cycles/__init__.py') for n in files):
                raise ValueError('Full configuration is missing the Cycles Python package')
            payload_libs = {n: runtime.read(n) for n in files if n.endswith('.so')}
        payload_libs.update({name: archive.read(path) for name, path in native.items()})
        dependencies = {}
        for number, (name, data) in enumerate(sorted(payload_libs.items())):
            if len(data) < 64 or data[:4] != b'\x7fELF' or data[4:6] != b'\x02\x01':
                raise ValueError(f'Not an ELF64 little-endian binary: {name}')
            if struct.unpack_from('<H', data, 18)[0] != 183:
                raise ValueError(f'Not an AArch64 binary: {name}')
            p = Path(temp) / f'{number}.so'
            p.write_bytes(data)
            dynamic = subprocess.check_output([readelf, '-d', str(p)], text=True)
            needed = re.findall(r'\(NEEDED\).*?\[(.*?)\]', dynamic)
            missing = set(needed) - set(native) - SYSTEM_LIBS
            if missing:
                raise ValueError(f'{name} has unpackaged native dependencies: {sorted(missing)}')
            dependencies[name] = needed
            if name == 'libblender.so':
                symbols = subprocess.check_output([readelf, '--dyn-syms', '--wide', str(p)], text=True)
                if not re.search(r'\bGLOBAL\s+DEFAULT\s+(?!UND)\S+\s+ANativeActivity_onCreate\b', symbols):
                    raise ValueError('Blender does not export the NativeActivity entry point')
        return {'apk': apk.name, 'sha256': hashlib.sha256(apk.read_bytes()).hexdigest(),
                'native_libraries': len(native), 'dependencies': dependencies,
                'validation': 'package structure and ELF dependencies only; device execution unverified'}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('apk', type=Path)
    parser.add_argument('--readelf', default='llvm-readelf')
    parser.add_argument('--report', type=Path, required=True)
    args = parser.parse_args()
    args.report.write_text(json.dumps(audit(args.apk, args.readelf), indent=2) + '\n')
    print(f'Validated full Blender ARM64 package: {args.apk}')
