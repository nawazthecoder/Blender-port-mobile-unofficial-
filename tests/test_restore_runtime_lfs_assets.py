# SPDX-License-Identifier: GPL-2.0-or-later
"""Recovery must use the source's content hashes, never names or old native binaries."""
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import zipfile

SCRIPT = Path(__file__).parents[1] / 'scripts/restore_runtime_lfs_assets.py'
SPEC = importlib.util.spec_from_file_location('restore_runtime_lfs_assets', SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)
SOURCE_COMMIT = 'a' * 40
PAYLOAD = b'unchanged official brush payload'
OID = hashlib.sha256(PAYLOAD).hexdigest()


class RuntimeRecoveryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.media = self.root / 'lfs/objects'
        self.asset = self.media / OID[:2] / OID[2:4] / OID
        self.files = [{'name': 'assets/brushes/brush.blend', 'oid': OID,
                       'oid_type': 'sha256', 'size': len(PAYLOAD)},
                      {'name': 'tests/data/large.blend', 'oid': '0' * 64,
                       'oid_type': 'sha256', 'size': 99999},
                      {'name': 'release/windows/desktop.png', 'oid': '1' * 64,
                       'oid_type': 'sha256', 'size': 99999}]
        self.mock_git = patch.object(MODULE, 'git', side_effect=self.git).start()
        self.addCleanup(patch.stopall)

    def git(self, source, *args):
        return {('rev-parse', 'HEAD'): SOURCE_COMMIT + '\n',
                ('lfs', 'ls-files', '--json'): json.dumps({'files': self.files}),
                ('lfs', 'env'): f'LocalMediaDir={self.media}\n'}[args]

    def artifact(self, data=PAYLOAD, commit=SOURCE_COMMIT):
        runtime = io.BytesIO()
        with zipfile.ZipFile(runtime, 'w') as archive:
            # Deliberately unrelated names: the hash must decide what gets restored.
            archive.writestr('../../renamed-asset.blend', data)
        apk = io.BytesIO()
        with zipfile.ZipFile(apk, 'w') as archive:
            archive.writestr('assets/blender_runtime.zip', runtime.getvalue())
            archive.writestr('lib/arm64-v8a/libblender.so', b'do not reuse')
        path = self.root / 'validated.zip'
        with zipfile.ZipFile(path, 'w') as archive:
            archive.writestr('source-lock.json', json.dumps({'source_commit': commit}))
            archive.writestr('blender-5.3.0-android-full.apk', apk.getvalue())
        return path, MODULE.digest_file(path)

    def recover(self, **kwargs):
        artifact, sha = self.artifact(**kwargs)
        MODULE.restore(self.root, artifact, sha, SOURCE_COMMIT)

    def test_exact_content_recovers_under_object_hash_without_extracting_paths(self):
        self.recover()
        self.assertEqual(self.asset.read_bytes(), PAYLOAD)
        self.assertEqual({p for p in self.root.rglob('*') if p.is_file()},
                         {self.root / 'validated.zip', self.asset})

    def test_same_size_wrong_content_is_rejected(self):
        with self.assertRaisesRegex(ValueError, 'cannot recover'):
            self.recover(data=b'x' * len(PAYLOAD))
        self.assertFalse(self.asset.exists())

    def test_missing_required_asset_is_rejected_without_partial_writes(self):
        self.files.append({'name': 'scripts/template/startup.blend', 'oid': '2' * 64,
                           'oid_type': 'sha256', 'size': 123})
        with self.assertRaisesRegex(ValueError, 'scripts/template/startup.blend'):
            self.recover()
        self.assertFalse(self.asset.exists())

    def test_corrupt_cached_object_is_replaced_by_verified_content(self):
        self.asset.parent.mkdir(parents=True)
        self.asset.write_bytes(b'x' * len(PAYLOAD))
        self.recover()
        self.assertEqual(self.asset.read_bytes(), PAYLOAD)

    def test_valid_cached_object_is_kept(self):
        self.asset.parent.mkdir(parents=True)
        self.asset.write_bytes(PAYLOAD)
        before = self.asset.stat().st_mtime_ns
        self.recover(data=b'unrelated')
        self.assertEqual(self.asset.stat().st_mtime_ns, before)

    def test_wrong_artifact_checksum_is_rejected(self):
        artifact, _ = self.artifact()
        with self.assertRaisesRegex(ValueError, 'checksum mismatch'):
            MODULE.restore(self.root, artifact, '0' * 64, SOURCE_COMMIT)
        self.assertFalse(self.asset.exists())

    def test_different_upstream_commit_is_rejected(self):
        with self.assertRaisesRegex(ValueError, 'different upstream source commit'):
            self.recover(commit='b' * 40)
        self.assertFalse(self.asset.exists())


if __name__ == '__main__':
    unittest.main()
