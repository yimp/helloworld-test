#!/usr/bin/env python3
"""Audit saved artifacts with GNU find/sha256sum, then publish the measured snapshot."""
import argparse
import datetime as dt
import json
import os
from pathlib import Path
import re
import shutil
import subprocess

import measure


def check_tree(root, recorded):
    # Independent OS tools check byte sums and hashes against the Python measurement.
    p = subprocess.run(['find', str(root), '-type', 'f', '-printf', r'%P\t%s\0',
                        '-o', '-type', 'l', '-printf', r'%P\t%s\0'], check=True, capture_output=True)
    rows = [row.decode().rsplit('\t', 1) for row in p.stdout.split(b'\0') if row]
    actual = {name: int(size) for name, size in rows}
    expected = {e['path']: e['bytes'] for e in recorded['entries']}
    if actual != expected or sum(actual.values()) != recorded['bytes'] or len(actual) != recorded['files']:
        raise RuntimeError('File/byte manifest mismatch: ' + str(root))
    regular = [root / e['path'] for e in recorded['entries'] if e['type'] == 'file']
    if regular:
        output = subprocess.check_output(['sha256sum', '-z', *map(str, regular)])
        hashes = {row[66:].decode(): row[:64].decode() for row in output.split(b'\0') if row}
        for entry in recorded['entries']:
            path = root / entry['path']
            if entry['type'] == 'file' and hashes[str(path)] != entry['sha256']:
                raise RuntimeError('Hash mismatch: ' + str(path))
            if entry['type'] == 'symlink' and os.readlink(path) != entry['target']:
                raise RuntimeError('Symlink mismatch: ' + str(path))
    return {'files': len(actual), 'bytes': sum(actual.values()), 'hashes_verified': len(regular)}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('run_directory', type=Path)
    args = parser.parse_args()
    run_dir = args.run_directory.resolve()
    if not run_dir.is_relative_to(measure.BASE / 'build/formal'):
        raise SystemExit('Expected formal data disk run directory')
    report = json.loads((run_dir / 'measurements.json').read_text())
    all_specs = {s['id']: s for s in measure.specs()}
    if set(report['cases']) != set(all_specs):
        raise RuntimeError('Missing/unexpected cases')
    audit = {'checked_at_utc': dt.datetime.now(dt.timezone.utc).isoformat(),
             'verifier': 'GNU find stat size + sha256sum; recorded raw stdout/stderr/exit validation',
             'cases': {}, 'baseline': check_tree(run_dir / 'baseline', report['baseline'])}
    for source in report['sources']:
        path = measure.REPO / source['path']
        if measure.sha(path) != source['sha256']:
            raise RuntimeError('Source changed: ' + str(path))
        data = path.read_bytes()
        if data.startswith(b'\xef\xbb\xbf') or b'\r' in data:
            raise RuntimeError('Source must be UTF-8 no BOM, LF: ' + str(path))
        data.decode('utf-8')
    for id, entry in report['cases'].items():
        if entry['status'] != 'passed':
            raise RuntimeError('Failed case: ' + id)
        root = run_dir / id
        entry['artifact_paths'] = {'application': str(root / 'application'), 'deployment': str(root / 'deployment')}
        result = {'application': check_tree(root / 'application', entry['application'])}
        for name in ['host_run'] + (['isolated_run'] if entry['packaged'] else []):
            execution = entry[name]
            if execution['exit_code'] != 0 or execution['stdout_hex'] != measure.EXPECTED.hex() or execution['stderr']:
                raise RuntimeError('Invalid saved run: ' + id + '/' + name)
        if entry['packaged']:
            result['deployment'] = check_tree(root / 'deployment', entry['deployment'])
        for build in entry['build_commands']:
            if measure.sha(build['log']) != build['log_sha256']:
                raise RuntimeError('Build log changed: ' + build['log'])
        download = entry['download_archive']
        if Path(download['path']).stat().st_size != download['bytes'] or measure.sha(download['path']) != download['sha256']:
            raise RuntimeError('Archive changed: ' + id)
        result['archive_verified'] = True
        # Enrich ELF evidence without rebuilding or changing any saved payload.
        entry['application_elf'] = measure.elf_report(root / 'application')
        if entry['packaged']:
            entry['deployment_elf'] = measure.elf_report(root / 'deployment')
        missing = {}
        for analysis in entry.get('ldd', []):
            for soname in re.findall(r'^\s*(\S+)\s+=>\s+not found', analysis['output'], re.M):
                shipped = [str(p.relative_to(root / 'deployment')) for p in (root / 'deployment').rglob(soname) if p.is_file()]
                label = 'bundled; runtime loader resolves it during successful execution' if shipped else 'not shipped; not exercised by this Hello World run'
                missing.setdefault(soname, {'soname': soname, 'classification': label, 'bundled_paths': shipped, 'reported_by': []})
                missing[soname]['reported_by'].append(analysis['path'])
        entry['ldd_unresolved_summary'] = list(missing.values())
        entry['note'] = all_specs[id]['note']
        audit['cases'][id] = result
        print('AUDIT', id, 'OK', flush=True)
    audit.update(passed=True, case_count=len(report['cases']),
                 language_count=len({e['language'] for e in report['cases'].values()}),
                 isolated_package_count=sum(e['packaged'] for e in report['cases'].values()),
                 finalizer_sha256=measure.sha(Path(__file__)))
    report['artifact_audit'] = audit
    report['methodology_sha256'] = measure.sha(measure.REPO / 'METHODOLOGY.md')
    report['environment']['disk_after'] = measure.capture(['df', '-B1', '/', '/mnt/sdb']).stdout.decode()
    shutil.copy2(measure.REPO / 'METHODOLOGY.md', run_dir / 'METHODOLOGY.md')
    measure.save(report, run_dir)
    shutil.copy2(run_dir / 'measurements.json', measure.REPO / 'results/2026-09-28-rocky9-measurements.json')
    measure.export(report, run_dir)
    print('AUDIT_PASSED', audit['case_count'], 'cases', audit['language_count'], 'languages',
          audit['isolated_package_count'], 'isolated packages', flush=True)


if __name__ == '__main__':
    main()
