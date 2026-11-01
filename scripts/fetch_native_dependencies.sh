#!/usr/bin/env bash
# SPDX-License-Identifier: GPL-2.0-or-later
# Run from the prepared Blender source tree. Honour each pinned submodule SHA.
set -euo pipefail
git lfs install --local
git config --local lfs.url https://projects.blender.org/blender/blender.git/info/lfs
git config --local credential.https://projects.blender.org.helper '!f() { echo username=; echo password=; }; f'
# Skip test fixtures: these are not needed by the editor and consume several GB.
git lfs pull --include='assets/**,release/**' --exclude='tests/**'
# .gitmodules intentionally sets update=none for desktop libs. Override it.
GIT_LFS_SKIP_SMUDGE=1 git -c submodule.lib/linux_x64.update=checkout \
  submodule update --init --checkout --depth 1 lib/linux_x64 lib/android_arm64
for prefix in lib/linux_x64 lib/android_arm64; do
  git -C "$prefix" config --local credential.https://projects.blender.org.helper '!f() { echo username=; echo password=; }; f'
  git -C "$prefix" lfs pull
  python3 - "$prefix" <<'PY'
from pathlib import Path
import sys
root = Path(sys.argv[1])
for dep in ('jpeg', 'python', 'tbb', 'openimageio', 'openexr'):
    path = root / dep
    binaries = [p for p in path.rglob('*') if p.is_file() and (p.suffix == '.a' or '.so' in p.name)]
    if not binaries:
        raise SystemExit(f'Missing actual {dep} libraries in {root}')
    for p in binaries:
        with p.open('rb') as f:
            if f.read(43).startswith(b'version https://git-lfs.github.com/spec/v1'):
                raise SystemExit(f'Unresolved Git LFS pointer: {p}')
print(f'Native dependency payload verified: {root}')
PY
done
