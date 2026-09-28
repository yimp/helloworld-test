#!/usr/bin/env bash
set -euo pipefail
source "$(dirname "$0")/vm-env.sh"
if ! python3 -c 'import PyInstaller' >/dev/null 2>&1; then
  if [ ! -x "$HW_ROOT/toolchains/python-packaging/bin/python" ]; then
    python3 -m venv "$HW_ROOT/toolchains/python-packaging"
  fi
  "$HW_ROOT/toolchains/python-packaging/bin/python" -m pip install --index-url https://pypi.org/simple 'pyinstaller==6.22.3'
  "$HW_ROOT/toolchains/python-packaging/bin/python" -m pip freeze > "$HW_ROOT/logs/python-packaging-requirements.txt"
  if [ ! -e "$HW_ROOT/bin/pyinstaller" ]; then
    ln -s "$HW_ROOT/toolchains/python-packaging/bin/pyinstaller" "$HW_ROOT/bin/pyinstaller"
  fi
fi
if [ ! -d "$HW_ROOT/toolchains/npm/lib/node_modules/postject" ]; then
  npm install --global --registry=https://registry.npmjs.org postject
fi
npm list --global --depth=0 > "$HW_ROOT/logs/npm-packaging-versions.txt"
