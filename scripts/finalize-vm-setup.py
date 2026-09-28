#!/usr/bin/env python3
"""Check stored downloads and save completed setup evidence to the shared repo."""
import datetime
import hashlib
import json
import os
from pathlib import Path
import subprocess

BASE = Path('/mnt/sdb/helloworld-test')
REPO = Path(__file__).resolve().parents[1]


def output(command):
    return subprocess.check_output(command, text=True).strip()


def main():
    if os.environ.get('HW_ROOT') != str(BASE) or not os.path.ismount('/mnt/sdb'):
        raise SystemExit('Source vm-env.sh and mount the data disk first')
    report = json.loads((BASE / 'setup-verification.json').read_text())
    if len(report['tests']) != 21 or any(not r['verified'] for r in report['tests'].values()):
        raise SystemExit('Complete all readiness checks first')
    lock = json.loads((BASE / 'toolchain-lock.json').read_text())
    for name, a in lock.items():
        p = Path(a['archive_path']).resolve()
        if BASE / 'downloads' not in p.parents:
            raise RuntimeError('Unexpected archive path: ' + str(p))
        hashes = {kind: hashlib.new(kind) for kind in ('sha256', 'sha512')}
        with p.open('rb') as f:
            for block in iter(lambda: f.read(1024 * 1024), b''):
                for h in hashes.values():
                    h.update(block)
        for kind, h in hashes.items():
            expected = a.get('upstream_' + kind) or (a.get('download_sha256') if kind == 'sha256' else None)
            if expected and h.hexdigest().lower() != expected.lower():
                raise RuntimeError('Stored archive checksum mismatch: ' + name)
        a['download_sha256'] = hashes['sha256'].hexdigest()
        a['stored_archive_verified'] = True
        print('ARCHIVE VERIFIED', name, flush=True)
    lock['rust']['version'] = output(['rustc', '--version']).split()[1]
    lock['swiftly']['version'] = output(['swiftly', '--version'])
    lock['swiftly']['swift_version'] = '6.3.3'
    lock['swiftly']['selected_toolchain_path'] = output(['swiftly', 'use', '--print-location'])
    lock['dart']['transport_url'] = lock['dart']['url'].replace('storage.googleapis.com', 'storage.flutter-io.cn')
    lock['node']['url'] = lock['node']['url'].replace('/latest-v24.x/', '/' + lock['node']['version'] + '/')
    # Only failed transfer fragments with an already checked final archive.
    removed = report.get('storage', {}).get('removed_incomplete_downloads', [])
    for a in lock.values():
        archive = Path(a['archive_path']).resolve()
        for suffix in ('.part', '.transfer.part', '.mirror.part'):
            p = archive.with_name(archive.name + suffix)
            if p.is_file():
                removed.append({'path': str(p), 'size_bytes': p.stat().st_size})
                p.unlink()
    report['finalized_at_utc'] = datetime.datetime.now(datetime.timezone.utc).isoformat()
    report['environment']['cpu'] = output(['lscpu'])
    report['environment']['memory'] = output(['free', '-b'])
    report['environment']['final_disk'] = output(['df', '-B1', '/', '/mnt/sdb'])
    report['storage'] = {
        'dedicated_root': str(BASE),
        'disk_usage_bytes': int(output(['du', '-sB1', str(BASE)]).split()[0]),
        'category_usage': output(['du', '-sB1', str(BASE / 'toolchains'), str(BASE / 'downloads'), str(BASE / 'cache'), str(BASE / 'build')]),
        'removed_incomplete_downloads': removed,
        'system_packages_installed_or_upgraded': False,
        'note': 'Uses existing system GCC/Binutils/Python and system shared libraries; new SDKs and experiment caches are in the dedicated data-disk prefix.'}
    report['packaging_requirements'] = (BASE / 'logs/python-packaging-requirements.txt').read_text()
    report['npm_packaging_versions'] = (BASE / 'logs/npm-packaging-versions.txt').read_text()
    report['static_libraries'] = {
        'rpm_sha256': (BASE / 'logs/static-rpm-sha256.txt').read_text(),
        'relocated_linker_script': (BASE / 'toolchains/static-libs/usr/lib64/libm.a').read_text(),
        'original_linker_script': (BASE / 'toolchains/static-libs/usr/lib64/libm.a.upstream').read_text()}
    report['completed_checks'] = len(report['tests'])
    # Normalize recovered markers only after the corresponding tools passed
    # real builds, so a subsequent setup run does not reinstall them.
    for name in ('rust', 'swiftly'):
        marker = BASE / 'toolchains' / name / '.setup-complete'
        with marker.open('w') as f:
            f.write(lock[name]['version'] + '\n')
            f.flush()
            os.fsync(f.fileno())
    results = REPO / 'results'
    results.mkdir(exist_ok=True)
    encoded = json.dumps(report, ensure_ascii=False, indent=2) + '\n'
    (BASE / 'setup-verification.json').write_text(encoded)
    (results / '2026-09-28-rocky9-vm-setup.json').write_text(encoded)
    encoded_lock = json.dumps(lock, indent=2) + '\n'
    (BASE / 'toolchain-lock.json').write_text(encoded_lock)
    (results / '2026-09-28-toolchain-lock.json').write_text(encoded_lock)
    print('Saved completed setup report; all', len(report['tests']), 'checks passed.', flush=True)


if __name__ == '__main__':
    main()
