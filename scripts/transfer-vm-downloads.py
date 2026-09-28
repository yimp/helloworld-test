#!/usr/bin/env python3
"""Fallback HTTPS transport via the PC; stream archives directly to VM data disk.

No credentials or archive data are stored in this repository. Downloads retain
their official URL and are checked against the setup lock before finalization.
"""
import argparse
import concurrent.futures
import hashlib
import json
import shlex
import subprocess
import urllib.request

HOST = 'root@192.168.45.23'
BASE = '/mnt/sdb/helloworld-test'


def ssh(command):
    return subprocess.check_output(['ssh', HOST, command], text=True)


def transfer(name, a):
    final = BASE + '/downloads/' + name + '-' + a['url'].rsplit('/', 1)[1]
    if ssh('test -f ' + shlex.quote(final) + ' && echo yes || echo no').strip() == 'yes':
        print('ALREADY DOWNLOADED', name, flush=True)
        return
    url = a.get('transport_url', a['url'])
    tmp = final + ('.mirror.part' if 'transport_url' in a else '.transfer.part')
    print('TRANSFER', name, url, flush=True)
    h = {kind: hashlib.new(kind) for kind in ('sha256', 'sha512')}
    size = 0
    with urllib.request.urlopen(url, timeout=60) as r:
        p = subprocess.Popen(['ssh', HOST, 'cat > ' + shlex.quote(tmp)], stdin=subprocess.PIPE)
        try:
            while True:
                block = r.read(1024 * 1024)
                if not block:
                    break
                for digest in h.values():
                    digest.update(block)
                p.stdin.write(block)
                size += len(block)
        finally:
            p.stdin.close()
        if p.wait() != 0:
            raise RuntimeError('SSH transfer failed: ' + name)
    for kind, digest in h.items():
        expected = a.get('upstream_' + kind)
        if expected and digest.hexdigest().lower() != expected.lower():
            raise RuntimeError('Checksum mismatch: ' + name)
    ssh('mv ' + shlex.quote(tmp) + ' ' + shlex.quote(final))
    print('TRANSFERRED', name, size, h['sha256'].hexdigest(), flush=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--manifest', default=BASE + '/toolchain-lock.json')
    parser.add_argument('--dart-mirror', action='store_true')
    parser.add_argument('names', nargs='+')
    args = parser.parse_args()
    d = json.loads(ssh('cat ' + shlex.quote(args.manifest)))
    if args.dart_mirror:
        d['dart']['transport_url'] = d['dart']['url'].replace('storage.googleapis.com', 'storage.flutter-io.cn')
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
        jobs = [pool.submit(transfer, name, d[name]) for name in args.names]
        for job in jobs:
            job.result()


if __name__ == '__main__':
    main()
