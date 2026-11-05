#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
"""Apply the reviewed Android backport to an exact, clean Blender stable checkout."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[1]


def run(*args, cwd=None, capture=False):
    return subprocess.run(args, cwd=cwd, check=True, text=True,
                          stdout=subprocess.PIPE if capture else None,
                          env={**os.environ, 'GIT_LFS_SKIP_SMUDGE': '1'})


def prepare(source, manifest_path=ROOT / 'config/blender-android.json'):
    manifest = json.loads(manifest_path.read_text())
    patches = [{'path': manifest['patch'], 'sha256': manifest['patch_sha256']}]
    patches.extend(manifest.get('additional_patches', []))
    for item in patches:
        digest = hashlib.sha256((ROOT / item['path']).read_bytes()).hexdigest()
        if digest != item['sha256']:
            raise ValueError(f"Android patch checksum mismatch: {item['path']}")
    head = run('git', 'rev-parse', 'HEAD', cwd=source, capture=True).stdout.strip()
    if head != manifest['source_commit']:
        raise ValueError(f'Expected stable commit {manifest["source_commit"]}, got {head}')
    if run('git', 'status', '--porcelain', cwd=source, capture=True).stdout.strip():
        raise ValueError('Source checkout must be clean; use a separate checkout for this build')
    header = (source / 'source/blender/blenkernel/BKE_blender_version.h').read_text()
    version = int(re.search(r'#define BLENDER_VERSION\s+(\d+)', header)[1])
    patch_version = int(re.search(r'#define BLENDER_VERSION_PATCH\s+(\d+)', header)[1])
    cycle = re.search(r'#define BLENDER_VERSION_CYCLE\s+(\w+)', header)[1]
    found = f'{version // 100}.{version % 100}.{patch_version}'
    if found != manifest['blender_version'] or cycle != 'release':
        raise ValueError(f'Expected a stable release, found {found} {cycle}')
    for item in patches:
        patch = ROOT / item['path']
        run('git', 'apply', '--check', str(patch), cwd=source)
        run('git', 'apply', '--index', str(patch), cwd=source)
    if (source / 'source/blender/blenkernel/BKE_blender_version.h').read_text() != header:
        raise ValueError('Android patch must not relabel Blender version metadata')
    expected = manifest['android_libraries_commit']
    entry = run('git', 'ls-files', '--stage', 'lib/android_arm64', cwd=source,
                capture=True).stdout.split()
    if entry[:2] != ['160000', expected]:
        raise ValueError('Android dependency gitlink is not pinned to the expected commit')
    print(f'Prepared actual Blender {found} stable + Android port revision {manifest["port_revision"]}')
    print('Compilation and device validation are separate required steps.')
    return manifest


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', type=Path, help='Clean checkout at the locked Blender release commit')
    args = parser.parse_args()
    prepare(args.source.resolve())
