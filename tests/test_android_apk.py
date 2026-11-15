# SPDX-License-Identifier: GPL-2.0-or-later
"""Package audit tests use synthetic ELF metadata, never claim runtime execution."""
import importlib.util
import io
from pathlib import Path
import struct
import tempfile
import unittest
from unittest.mock import patch
import zipfile

SPEC = importlib.util.spec_from_file_location(
    'check_android_apk', Path(__file__).parents[1] / 'scripts/check_android_apk.py')
audit_module = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(audit_module)


def elf(machine=183):
    data = bytearray(64)
    data[:6] = b'\x7fELF\x02\x01'
    struct.pack_into('<H', data, 18, machine)
    return bytes(data)


class PackageAuditTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.apk = Path(self.temp.name) / 'test.apk'
        self.runtime = {
            'scripts/startup/__init__.py': b'# startup',
            'scripts/modules/module.py': b'# module',
            'scripts/addons_core/cycles/__init__.py': b'# cycles',
            'datafiles/assets/brush.blend': b'BLENDER-v501',
            'python/lib/python3.11/encodings/__init__.py': b'# encodings',
            'python/lib/python3.11/lib-dynload/_ssl.so': elf(),
        }
        self.native = {'libblender.so': elf(), 'libc++_shared.so': elf()}

    def package(self):
        payload = io.BytesIO()
        with zipfile.ZipFile(payload, 'w') as runtime:
            for name, data in self.runtime.items():
                runtime.writestr(name, data)
        with zipfile.ZipFile(self.apk, 'w') as apk:
            apk.writestr('AndroidManifest.xml', b'manifest')
            apk.writestr('classes.dex', b'dex')
            apk.writestr('assets/blender_runtime.zip', payload.getvalue())
            for name, data in self.native.items():
                apk.writestr('lib/arm64-v8a/' + name, data)

    @staticmethod
    def readelf(args, **kwargs):
        if '-d' in args:
            return '(NEEDED) Shared library: [libc.so]\n'
        return '1: 00001000 64 FUNC GLOBAL DEFAULT 12 ANativeActivity_onCreate\n'

    def audit(self, reader=None):
        self.package()
        with patch.object(audit_module.subprocess, 'check_output',
                          side_effect=reader or self.readelf):
            return audit_module.audit(self.apk, 'unused-readelf')

    def test_complete_structure_reports_device_execution_unverified(self):
        result = self.audit()
        self.assertEqual(result['native_libraries'], 2)
        self.assertEqual(len(result['dependencies']), 3)
        self.assertIn('device execution unverified', result['validation'])

    def test_diagnostic_without_blender_is_rejected(self):
        del self.native['libblender.so']
        with self.assertRaisesRegex(ValueError, 'missing lib/arm64-v8a/libblender.so'):
            self.audit()

    def test_missing_python_standard_library_is_rejected(self):
        del self.runtime['python/lib/python3.11/encodings/__init__.py']
        with self.assertRaisesRegex(ValueError, 'encodings is missing'):
            self.audit()

    def test_lfs_pointer_is_not_accepted_as_brush_asset(self):
        self.runtime['datafiles/assets/brush.blend'] = (
            audit_module.LFS_POINTER + b'\noid sha256:' + b'0' * 64 + b'\nsize 500000\n')
        with self.assertRaisesRegex(ValueError, 'Unresolved Git LFS pointer'):
            self.audit()

    def test_host_python_extension_is_rejected(self):
        self.runtime['python/lib/python3.11/lib-dynload/_ssl.so'] = elf(machine=62)
        with self.assertRaisesRegex(ValueError, 'Not an AArch64 binary'):
            self.audit()

    def test_placeholder_native_library_is_rejected(self):
        self.native['libblender.so'] = b'not a shared library'
        with self.assertRaisesRegex(ValueError, 'Not an ELF64'):
            self.audit()

    def test_unpackaged_shared_dependency_is_rejected(self):
        def readelf(args, **kwargs):
            return '(NEEDED) Shared library: [libmissing.so]\n'
        with self.assertRaisesRegex(ValueError, 'unpackaged native dependencies'):
            self.audit(readelf)

    def test_undefined_entry_point_is_rejected(self):
        def readelf(args, **kwargs):
            if '-d' in args:
                return ''
            return '1: 00000000 0 FUNC GLOBAL DEFAULT UND ANativeActivity_onCreate\n'
        with self.assertRaisesRegex(ValueError, 'does not export'):
            self.audit(readelf)

    def test_missing_cycles_is_rejected(self):
        del self.runtime['scripts/addons_core/cycles/__init__.py']
        with self.assertRaisesRegex(ValueError, 'Cycles Python package'):
            self.audit()


if __name__ == '__main__':
    unittest.main()
