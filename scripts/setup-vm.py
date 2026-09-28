#!/usr/bin/env python3
"""Install missing experiment tools on the mounted data disk, not the root FS.

Run on the VM after sourcing vm-env.sh. Official archive metadata is resolved
once into a lock file. Reruns reuse it and skip installed dedicated tools.
"""
import argparse
import concurrent.futures
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import time

BASE = Path('/mnt/sdb/helloworld-test')
REPO = Path(__file__).resolve().parents[1]
LOCK = BASE / 'toolchain-lock.json'


def run(args, **kwargs):
    print('RUN', ' '.join(map(str, args)), flush=True)
    return subprocess.run(list(map(str, args)), check=True, **kwargs)


def get(url):
    return subprocess.check_output(['curl', '-fsSL', '--retry', '2', '--connect-timeout', '15', '--max-time', '90', url], text=True)


def metadata(url):
    return json.loads(get(url))


def gh(repo, pattern):
    release = metadata('https://api.github.com/repos/' + repo + '/releases/latest')
    asset = next(a for a in release['assets'] if re.search(pattern, a['name']))
    return {'version': release['tag_name'], 'url': asset['browser_download_url'],
            'upstream_sha256': (asset.get('digest') or '').removeprefix('sha256:') or None}


def plan():
    if LOCK.exists():
        d = json.loads(LOCK.read_text())
        if 'rust' in d and not re.fullmatch(r'\d+\.\d+\.\d+', d['rust']['version']):
            manifest = get('https://static.rust-lang.org/dist/channel-rust-stable.toml')
            d['rust']['version'] = re.search(r'\[pkg\.rust\]\s*version = "([\d.]+)', manifest).group(1)
        if 'node' in d:
            d['node']['url'] = d['node']['url'].replace('/latest-v24.x/', '/' + d['node']['version'] + '/')
        if 'swiftly' in d:
            d['swiftly']['swift_version'] = '6.3.3'
        LOCK.write_text(json.dumps(d, indent=2) + '\n')
        return d
    d = {}
    # Each tool is first probed in the existing environment; do not reinstall it.
    if not shutil.which('zig'):
        idx = metadata('https://ziglang.org/download/index.json')
        ver = max((v for v in idx if re.fullmatch(r'\d+\.\d+\.\d+', v)), key=lambda v: tuple(map(int, v.split('.'))))
        a = idx[ver]['x86_64-linux']
        d['zig'] = {'version': ver, 'url': a['tarball'], 'upstream_sha256': a['shasum']}
    if not shutil.which('nim'):
        html = get('https://nim-lang.org/install_unix.html')
        url = re.search(r'href="([^"]*nim-\d+\.\d+\.\d+-linux_x64\.tar\.xz)"', html).group(1)
        if url.startswith('/'):
            url = 'https://nim-lang.org' + url
        d['nim'] = {'version': re.search(r'nim-([\d.]+)-', url).group(1), 'url': url,
                    'upstream_sha256': get(url + '.sha256').split()[0]}
    if not shutil.which('crystal'):
        d['crystal'] = gh('crystal-lang/crystal', r'linux-x86_64-bundled\.tar\.gz$')
    if not shutil.which('go'):
        releases = metadata('https://go.dev/dl/?mode=json')
        a = next(a for a in releases[0]['files'] if a['os'] == 'linux' and a['arch'] == 'amd64' and a['kind'] == 'archive')
        d['go'] = {'version': releases[0]['version'], 'url': 'https://go.dev/dl/' + a['filename'], 'upstream_sha256': a['sha256']}
    if not shutil.which('dotnet') or not subprocess.check_output(['dotnet', '--list-sdks'], text=True).strip():
        rel = metadata('https://builds.dotnet.microsoft.com/dotnet/release-metadata/10.0/releases.json')
        ver = rel['latest-sdk']
        sdk = next(s for r in rel['releases'] for s in r.get('sdks', [r['sdk']]) if s['version'] == ver)
        a = next(a for a in sdk['files'] if a['rid'] == 'linux-x64' and a['name'].endswith('.tar.gz'))
        d['dotnet'] = {'version': ver, 'url': a['url'], 'upstream_sha512': a['hash']}
    if not shutil.which('dart'):
        ver = metadata('https://storage.googleapis.com/dart-archive/channels/stable/release/latest/VERSION')['version']
        url = 'https://storage.googleapis.com/dart-archive/channels/stable/release/' + ver + '/sdk/dartsdk-linux-x64-release.zip'
        d['dart'] = {'version': ver, 'url': url, 'upstream_sha256': get(url + '.sha256sum').split()[0]}
    if not shutil.which('bun'):
        d['bun'] = gh('oven-sh/bun', r'^bun-linux-x64\.zip$')
    if not shutil.which('deno'):
        d['deno'] = gh('denoland/deno', r'^deno-x86_64-unknown-linux-gnu\.zip$')
        if not d['deno']['upstream_sha256']:
            d['deno']['upstream_sha256'] = get(d['deno']['url'] + '.sha256sum').split()[0]
    # Installed Node 16 lacks SEA; install a separate LTS 24 without replacing it.
    if not shutil.which('node') or int(subprocess.check_output(['node', '--version'], text=True).strip().lstrip('v').split('.')[0]) < 20:
        files = get('https://nodejs.org/dist/latest-v24.x/SHASUMS256.txt')
        sha, filename = next(line.split() for line in files.splitlines() if line.endswith('-linux-x64.tar.xz'))
        version = re.search(r'node-(v[\d.]+)-', filename).group(1)
        d['node'] = {'version': version, 'url': 'https://nodejs.org/dist/' + version + '/' + filename, 'upstream_sha256': sha}
    # jpackage and native-image are missing; one GraalVM JDK supplies both.
    if not shutil.which('jpackage') or not shutil.which('native-image'):
        d['java'] = gh('graalvm/graalvm-ce-builds', r'linux-x64.*\.tar\.gz$')
    if not shutil.which('rustc'):
        manifest = get('https://static.rust-lang.org/dist/channel-rust-stable.toml')
        ver = re.search(r'\[pkg\.rust\]\s*version = "([\d.]+)', manifest).group(1)
        d['rust'] = {'version': ver, 'url': 'https://static.rust-lang.org/rustup/dist/x86_64-unknown-linux-gnu/rustup-init'}
    if not shutil.which('swiftc'):
        d['swiftly'] = {'version': 'resolved-by-swiftly', 'swift_version': '6.3.3', 'url': 'https://download.swift.org/swiftly/linux/swiftly-x86_64.tar.gz'}
    LOCK.write_text(json.dumps(d, indent=2) + '\n')
    print(json.dumps(d, indent=2), flush=True)
    return d


def download(item):
    name, a = item
    archive = BASE / 'downloads' / (name + '-' + a['url'].rsplit('/', 1)[1])
    if not archive.exists():
        partial = archive.with_name(archive.name + '.part')
        run(['curl', '-fL', '--retry', '3', '--connect-timeout', '20', '--max-time', '1800', '--output', partial, a['url']], stdout=subprocess.DEVNULL, stderr=open(BASE / 'logs' / (name + '-download.log'), 'w'))
        partial.rename(archive)
    for kind in ('sha256', 'sha512'):
        expected = a.get('upstream_' + kind) or (a.get('download_sha256') if kind == 'sha256' else None)
        if expected:
            h = hashlib.new(kind)
            with archive.open('rb') as f:
                for block in iter(lambda: f.read(1024 * 1024), b''):
                    h.update(block)
            if h.hexdigest().lower() != expected.lower():
                raise RuntimeError('Checksum mismatch: ' + name)
    h = hashlib.sha256()
    with archive.open('rb') as f:
        for block in iter(lambda: f.read(1024 * 1024), b''):
            h.update(block)
    a['archive_path'] = str(archive)
    a['download_sha256'] = h.hexdigest()
    print('DOWNLOADED', name, archive.stat().st_size, flush=True)
    return name, a


def link(binary, target):
    p = BASE / 'bin' / binary
    if not p.exists() and not p.is_symlink():
        p.symlink_to(target)


def install(name, a):
    target = BASE / 'toolchains' / name
    archive = Path(a['archive_path'])
    marker = target / '.setup-complete'
    if marker.exists() and marker.read_text().strip() == a['version']:
        print('SKIP installed', name, flush=True)
        return
    target.mkdir(parents=True, exist_ok=True)
    if name == 'rust':
        installer = target / 'rustup-init'
        shutil.copy2(archive, installer)
        installer.chmod(0o755)
        run([installer, '-y', '--profile', 'minimal', '--no-modify-path', '--default-toolchain', 'none'])
        run([BASE / 'toolchains/cargo/bin/rustup', 'toolchain', 'install', a['version'], '--profile', 'minimal'])
        run([BASE / 'toolchains/cargo/bin/rustup', 'default', a['version']])
    elif archive.name.endswith('.zip'):
        run(['unzip', '-q', '-o', archive, '-d', target])
        if name == 'dart':
            link('dart', target / 'dart-sdk/bin/dart')
        elif name == 'bun':
            link('bun', target / 'bun-linux-x64/bun')
        elif name == 'deno':
            (target / 'deno').chmod(0o755)
            link('deno', target / 'deno')
    else:
        args = ['tar', '-xf', archive, '-C', target]
        if name != 'swiftly' and name != 'dotnet':
            args += ['--strip-components=1']
        run(args)
        if name == 'zig':
            link('zig', target / 'zig')
        elif name == 'dotnet':
            link('dotnet', target / 'dotnet')
        elif name == 'swiftly':
            link('swiftly', target / 'swiftly')
            run([target / 'swiftly', 'init', '--no-modify-profile', '--skip-install', '--platform', 'ubi9', '--assume-yes'], cwd=BASE)
            run([target / 'bin/swiftly', 'install', a['swift_version'], '--use', '--assume-yes'], cwd=BASE)
        else:
            tools = {'nim': ['nim', 'nimble'], 'crystal': ['crystal', 'shards'], 'go': ['go', 'gofmt'], 'node': ['node', 'npm', 'npx'], 'java': ['java', 'javac', 'jar', 'jlink', 'jpackage', 'native-image']}[name]
            for tool in tools:
                candidates = list(target.glob('**/bin/' + tool))
                if candidates:
                    link(tool, candidates[0])
    # Flush the extracted filesystem before publishing the completion marker.
    run(['sync', '-f', target])
    with marker.open('w') as f:
        f.write(a['version'] + '\n')
        f.flush()
        os.fsync(f.fileno())


def main():
    if os.environ.get('HW_ROOT') != str(BASE) or not os.path.ismount('/mnt/sdb'):
        raise SystemExit('Source scripts/vm-env.sh and mount the data disk first')
    if shutil.disk_usage(BASE).free < 20 * 1024 ** 3:
        raise SystemExit('Need at least 20 GiB of free data-disk space for setup')
    parser = argparse.ArgumentParser()
    parser.add_argument('--plan-only', action='store_true')
    parser.add_argument('--only', help='Comma-separated tools from the locked plan to repair')
    args = parser.parse_args()
    d = plan()
    if args.plan_only:
        return
    errors = {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
        jobs = {pool.submit(download, item): item[0] for item in d.items()
                if not args.only or item[0] in args.only.split(',')}
        for future in concurrent.futures.as_completed(jobs):
            name = jobs[future]
            try:
                name, a = future.result()
                d[name] = a
                LOCK.write_text(json.dumps(d, indent=2) + '\n')
                install(name, a)
            except Exception as e:
                errors[name] = str(e)
                print('ERROR', name, str(e), flush=True)
    (BASE / 'setup-errors.json').write_text(json.dumps(errors, indent=2) + '\n')
    print('Setup errors:', json.dumps(errors), flush=True)
    raise SystemExit(bool(errors))


if __name__ == '__main__':
    main()
