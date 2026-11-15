#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
"""Recover exact source LFS assets from a checksum-pinned, validated build artifact."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import zipfile

ROOT = Path(__file__).resolve().parents[1]
RUNTIME_PREFIXES = ('assets/', 'release/datafiles/', 'scripts/', 'locale/')


def digest_file(path):
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def git(source, *args):
    return subprocess.run(['git', *args], cwd=source, check=True,
                          text=True, capture_output=True).stdout


def restore(source, artifact, artifact_sha256, source_commit):
    if not re.fullmatch(r'[0-9a-f]{64}', artifact_sha256):
        raise ValueError('Expected an explicit SHA-256 for the validated artifact')
    if digest_file(artifact) != artifact_sha256:
        raise ValueError('Validated artifact checksum mismatch')
    if git(source, 'rev-parse', 'HEAD').strip() != source_commit:
        raise ValueError('Source checkout does not match the locked upstream commit')

    required = {}
    for entry in json.loads(git(source, 'lfs', 'ls-files', '--json'))['files']:
        if not entry['name'].startswith(RUNTIME_PREFIXES):
            continue
        oid, size = entry['oid'], entry['size']
        if (entry['oid_type'] != 'sha256' or not re.fullmatch(r'[0-9a-f]{64}', oid)
                or type(size) is not int or size < 0):
            raise ValueError('Invalid source Git LFS metadata')
        if oid in required and required[oid][0] != size:
            raise ValueError('Conflicting sizes for one source Git LFS object')
        required[oid] = (size, entry['name'])
    if not required:
        raise ValueError('No runtime source LFS objects found')
    media_dirs = [line.partition('=')[2] for line in git(source, 'lfs', 'env').splitlines()
                  if line.startswith('LocalMediaDir=')]
    if len(media_dirs) != 1 or not media_dirs[0]:
        raise ValueError('Cannot locate the source Git LFS object store')
    media = Path(media_dirs[0])
    if not media.is_absolute():
        media = source / media

    def object_path(oid):
        return media / oid[:2] / oid[2:4] / oid

    missing = {}
    for oid, (size, name) in required.items():
        path = object_path(oid)
        if not path.is_file() or path.stat().st_size != size or digest_file(path) != oid:
            missing[oid] = (size, name)

    recovered = {}
    with zipfile.ZipFile(artifact) as archive:
        lock = json.loads(archive.read('source-lock.json'))
        if lock['source_commit'] != source_commit:
            raise ValueError('Validated artifact has a different upstream source commit')
        # Never extract archive paths into the source tree or reuse native libraries.
        with tempfile.TemporaryFile() as apk_file, tempfile.TemporaryFile() as runtime_file:
            with archive.open('blender-5.3.0-android-full.apk') as stream:
                shutil.copyfileobj(stream, apk_file)
            apk_file.seek(0)
            with zipfile.ZipFile(apk_file) as apk:
                with apk.open('assets/blender_runtime.zip') as stream:
                    shutil.copyfileobj(stream, runtime_file)
            runtime_file.seek(0)
            sizes = {size for size, _ in missing.values()}
            with zipfile.ZipFile(runtime_file) as runtime:
                for entry in runtime.infolist():
                    if entry.is_dir() or entry.file_size not in sizes:
                        continue
                    data = runtime.read(entry)
                    oid = hashlib.sha256(data).hexdigest()
                    if oid in missing and len(data) == missing[oid][0]:
                        recovered[oid] = data

    absent = set(missing) - set(recovered)
    if absent:
        raise ValueError('Validated artifact cannot recover required source assets:\n' +
                         '\n'.join(sorted(missing[oid][1] for oid in absent)))
    for oid, data in recovered.items():
        path = object_path(oid)
        path.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(dir=path.parent, delete=False) as stream:
            temporary = Path(stream.name)
            try:
                stream.write(data)
                stream.close()
                temporary.replace(path)
            finally:
                temporary.unlink(missing_ok=True)
    print(f'Verified {len(required)} source LFS objects; recovered {len(recovered)} from validated assets')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', type=Path)
    parser.add_argument('--artifact', required=True, type=Path)
    parser.add_argument('--artifact-sha256', required=True)
    args = parser.parse_args()
    manifest = json.loads((ROOT / 'config/blender-android.json').read_text())
    restore(args.source.resolve(), args.artifact.resolve(), args.artifact_sha256,
            manifest['source_commit'])
