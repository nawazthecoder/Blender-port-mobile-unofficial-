# SPDX-License-Identifier: GPL-2.0-or-later
"""Exercise runtime LFS fetching without downloading native library archives."""
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

FETCH = Path(__file__).parents[1] / 'scripts/fetch_native_dependencies.sh'
POINTER = b'version https://git-lfs.github.com/spec/v1\noid sha256:' + b'0' * 64 + b'\nsize 10000\n'


class RuntimeFetchTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        for path in ('assets/brushes/brush.blend', 'release/datafiles/font.woff2',
                     'scripts/startup/bl_app_templates_system/Storyboarding/startup.blend',
                     'scripts/startup/bl_app_templates_system/2D_Animation/startup.blend',
                     'tests/data/large.blend'):
            file = self.root / path
            file.parent.mkdir(parents=True, exist_ok=True)
            file.write_bytes(POINTER)
        for prefix in ('linux_x64', 'android_arm64'):
            for dep in ('jpeg', 'python', 'tbb', 'openimageio', 'openexr'):
                file = self.root / 'lib' / prefix / dep / 'lib' / f'lib{dep}.so'
                file.parent.mkdir(parents=True, exist_ok=True)
                file.write_bytes(b'fixture library payload')
        bin_dir = self.root / 'bin'
        bin_dir.mkdir()
        git = bin_dir / 'git'
        git.write_text('''#!/usr/bin/env python3
import fnmatch, os, sys
from pathlib import Path
args = sys.argv[1:]
if args[:2] == ['lfs', 'pull']:
    includes = next(a.split('=', 1)[1].split(',') for a in args if a.startswith('--include='))
    excludes = next(a.split('=', 1)[1].split(',') for a in args if a.startswith('--exclude='))
    for path in Path('.').rglob('*'):
        name = path.as_posix()
        if path.is_file() and any(fnmatch.fnmatch(name, p) for p in includes):
            if any(fnmatch.fnmatch(name, p) for p in excludes):
                continue
            if name != os.environ.get('LEAVE_LFS_POINTER'):
                path.write_bytes(b'materialized runtime asset')
''')
        git.chmod(0o755)
        self.env = {**os.environ, 'PATH': str(bin_dir) + os.pathsep + os.environ['PATH']}

    def fetch(self):
        return subprocess.run(['bash', str(FETCH)], cwd=self.root, env=self.env,
                              text=True, capture_output=True)

    def test_application_template_assets_are_fetched_and_tests_stay_excluded(self):
        result = self.fetch()
        self.assertEqual(result.returncode, 0, result.stderr)
        for path in ('Storyboarding', '2D_Animation'):
            asset = self.root / 'scripts/startup/bl_app_templates_system' / path / 'startup.blend'
            self.assertEqual(asset.read_bytes(), b'materialized runtime asset')
        self.assertEqual((self.root / 'tests/data/large.blend').read_bytes(), POINTER)
        self.assertIn('Runtime source payloads verified', result.stdout)

    def test_missing_template_payload_fails_before_compilation(self):
        path = 'scripts/startup/bl_app_templates_system/Storyboarding/startup.blend'
        self.env['LEAVE_LFS_POINTER'] = path
        result = self.fetch()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('Unresolved runtime Git LFS payloads', result.stderr)
        self.assertIn(path, result.stderr)
        self.assertNotIn('Native dependency payload verified', result.stdout)


if __name__ == '__main__':
    unittest.main()
