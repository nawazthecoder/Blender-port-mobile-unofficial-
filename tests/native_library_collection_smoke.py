#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
"""Check the prepared packager's dependency collection with real host ELF files.

This exercises collection only. The resulting fixtures are never Android APKs.
Run: python3 tests/native_library_collection_smoke.py /path/to/prepared/blender
"""
import argparse
import os
from pathlib import Path
import shutil
import subprocess
import tempfile


def check(source):
    package = (source / 'build_files/android/apk/package.sh').read_text()
    helpers = package[package.index('readelf_needed() {'):
                      package.index('# Assemble the runtime payload first,')]
    collection = package[package.index('echo "[apk] gathering native libraries (unversioned)"'):
                         package.index('echo "[apk] rewriting sonames + NEEDED to unversioned"')]
    compiler = shutil.which('cc')
    readelf = shutil.which('readelf')
    if not compiler or not readelf:
        raise RuntimeError('This smoke check requires a host C compiler and readelf')
    with tempfile.TemporaryDirectory(prefix='android-native-collection-') as temp:
        root = Path(temp)
        libdir = root / 'deps'
        payload = root / 'payload'
        jni = root / 'jni'
        tools = root / 'tools'
        jni.mkdir()
        tools.mkdir()
        (payload / 'python').mkdir(parents=True)
        (tools / 'llvm-readelf').symlink_to(readelf)

        def shared(relative, code, soname, dependencies=()):
            output = root / relative
            output.parent.mkdir(parents=True, exist_ok=True)
            c_source = output.with_suffix('.c')
            c_source.write_text(code)
            subprocess.run([compiler, '-shared', '-fPIC', str(c_source),
                            '-Wl,-soname,' + soname, '-o', str(output),
                            *map(str, dependencies)], check=True, capture_output=True)
            return output

        codec = shared('deps/codec/lib/libcodec.so.2',
                       'int codec(void) { return 42; }', 'libcodec.so.2')
        draco = shared('deps/draco/lib/libdraco.so',
                       'extern int codec(void); int draco(void) { return codec(); }',
                       'libdraco.so', [codec])
        shared('payload/scripts/addons_core/io_scene_gltf2/libbf_intern_draco_bridge.so',
               'extern int draco(void); int bridge(void) { return draco(); }',
               'libbf_intern_draco_bridge.so', [draco])
        shared('jni/libblender.so', 'int blender(void) { return 0; }', 'libblender.so')

        env = {**os.environ, 'LIBDIR': str(libdir), 'PAYLOAD': str(payload),
               'JNI': str(jni), 'ANDROID_LLVM_BIN': str(tools)}
        subprocess.run(['bash', '-c', 'set -euo pipefail\n' + helpers + collection],
                       env=env, check=True, capture_output=True, text=True)
        for name, original in (('libdraco.so', draco), ('libcodec.so', codec)):
            packaged = jni / name
            if not packaged.is_file() or packaged.read_bytes() != original.read_bytes():
                raise AssertionError(f'Add-on dependency not collected: {name}')
    print('Native collection PASS: add-on bridge, transitive library, versioned SONAME')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', type=Path)
    check(parser.parse_args().source.resolve())
