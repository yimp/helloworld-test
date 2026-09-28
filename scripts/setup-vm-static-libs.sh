#!/usr/bin/env bash
# Extract matching Rocky 9.2 static libraries to a private prefix; no RPM install.
set -euo pipefail
source "$(dirname "$0")/vm-env.sh"
prefix="$HW_ROOT/toolchains/static-libs"
mkdir -p "$prefix" "$HW_ROOT/downloads/rpms"
for filename in glibc-static-2.34-60.el9_2.7.x86_64.rpm libstdc++-static-11.3.1-4.3.el9.x86_64.rpm; do
  case "$filename" in
    glibc-*) test ! -e /usr/lib64/libc.a || continue; letter=g;;
    libstdc*) test ! -e /usr/lib/gcc/x86_64-redhat-linux/11/libstdc++.a || continue; letter=l;;
  esac
  archive="$HW_ROOT/downloads/rpms/$filename"
  url="https://dl.rockylinux.org/vault/rocky/9.2/CRB/x86_64/os/Packages/$letter/$filename"
  if [ ! -f "$archive" ]; then
    curl -fL --connect-timeout 15 --max-time 300 --retry 2 "$url" -o "$archive"
  fi
  rpm --checksig "$archive"
  (cd "$prefix"; rpm2cpio "$archive" | cpio -idm --quiet)
done
# The RPM's libm.a is an ld script with absolute system paths. Relocate only
# this private text script; retain the original and keep archive bytes intact.
python3 - "$prefix/usr/lib64/libm.a" <<'PY'
from pathlib import Path
import shutil
import sys
p = Path(sys.argv[1])
if p.exists() and p.read_bytes().startswith(b'/* GNU ld script'):
    original = p.with_name('libm.a.upstream')
    if not original.exists():
        shutil.copy2(p, original)
    p.write_text(original.read_text().replace('/usr/lib64/', ''))
PY
sha256sum "$HW_ROOT"/downloads/rpms/*.rpm > "$HW_ROOT/logs/static-rpm-sha256.txt"
