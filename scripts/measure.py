#!/usr/bin/env python3
"""Exact-byte Hello World measurements on the documented Linux VM, stdlib only."""
import argparse
import csv
import datetime as dt
import gzip
import hashlib
import json
import os
from pathlib import Path
import platform
import re
import shlex
import shutil
import stat
import subprocess
import tarfile
import time

REPO = Path(__file__).resolve().parent.parent
BASE = Path('/mnt/sdb/helloworld-test')
EXPECTED = b'Hello World\n'
STATIC = BASE / 'toolchains/static-libs'
LIBFLAGS = ['-L' + str(STATIC / 'usr/lib64'),
            '-L' + str(STATIC / 'usr/lib/gcc/x86_64-redhat-linux/11')]
GLIBC_PATHS = set()


def sha(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for data in iter(lambda: f.read(1024 * 1024), b''):
            h.update(data)
    return h.hexdigest()


def capture(command, cwd=None, env=None, timeout=60):
    return subprocess.run([str(x) for x in command], cwd=cwd, env=env,
                          capture_output=True, timeout=timeout)


def inventory(root):
    entries = []
    for path in sorted(root.rglob('*')):
        rel = str(path.relative_to(root))
        s = path.lstat()
        if stat.S_ISLNK(s.st_mode):
            target = os.readlink(path)
            if not path.resolve().is_relative_to(root.resolve()):
                raise RuntimeError('External symlink: ' + str(path))
            if not path.exists():
                raise RuntimeError('Broken symlink: ' + str(path))
            entries.append({'path': rel, 'type': 'symlink',
                            'bytes': len(target.encode('utf-8')), 'target': target})
        elif stat.S_ISREG(s.st_mode):
            entries.append({'path': rel, 'type': 'file', 'bytes': s.st_size,
                            'sha256': sha(path), 'mode': oct(s.st_mode & 0o777)})
    return {'bytes': sum(e['bytes'] for e in entries),
            'files': len(entries), 'entries': entries}


def elf(path):
    if path.is_symlink() or not path.is_file():
        return False
    with path.open('rb') as f:
        return f.read(4) == b'\x7fELF'


def elf_report(root):
    results = []
    for path in sorted(root.rglob('*')):
        if not elf(path):
            continue
        p = capture(['readelf', '-W', '-h', '-S', '-l', '-d', path])
        text = p.stdout.decode(errors='replace')
        results.append({'path': str(path.relative_to(root)),
                        'needed': re.findall(r'\(NEEDED\).*\[(.*?)\]', text),
                        'interpreter': re.findall(r'Requesting program interpreter: (.*?)\]', text),
                        'rpath_runpath': re.findall(r'\((?:RPATH|RUNPATH)\).*\[(.*?)\]', text),
                        'rwx_load_segment': bool(re.search(r'^\s*LOAD\s+.*\bRWE\b', text, re.M)),
                        'readelf': text})
    return results


def copy_payload(source, destination, excluded):
    if source.is_dir():
        destination.mkdir(parents=True, exist_ok=True)
        for path in sorted(source.iterdir()):
            copy_payload(path, destination / path.name, excluded)
    elif source.suffix in ('.pdb', '.dbg'):
        excluded.append({'path': str(source), 'bytes': source.stat().st_size,
                         'sha256': sha(source), 'reason': 'external debug symbols'})
    elif source.is_symlink():
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.symlink_to(os.readlink(source))
    else:
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)


def specs():
    cases = []

    def add(id, language, profile, builds, output='hello', run=None,
            packaged=True, note='', env=None, archive_mode='none', hints=None):
        cases.append(dict(id=id, language=language, profile=profile, builds=builds,
                          output=output, run=run or ['./hello'], packaged=packaged,
                          note=note, env=env or {}, archive_mode=archive_mode,
                          hints=hints or []))

    for profile, flags in [('default', []), ('stripped', ['-s']), ('tiny-rwx', ['-N', '-s'])]:
        add('asm-' + profile, 'Assembly', profile,
            [['as', 'hello.s', '-o', 'hello.o'], ['ld', *flags, 'hello.o', '-o', 'hello']],
            note='Linux write/exit syscall' + ('; RWX LOAD segment, appendix only' if profile == 'tiny-rwx' else ''))
    for lang, tool, src in [('C', 'gcc', 'hello.c'), ('C++', 'g++', 'hello.cpp')]:
        for profile, flags in [('default', []), ('size-dynamic', ['-Os', '-s']),
                               ('size-static', ['-static', '-Os', '-s', *LIBFLAGS])]:
            add(('c' if lang == 'C' else 'cpp') + '-' + profile, lang, profile,
                [[tool, '-march=x86-64', *flags, src, '-o', 'hello']],
                note='puts' if lang == 'C' else 'iostream; external libstdc++/libgcc counted in B when dynamic')
    add('zig-debug', 'Zig', 'Debug std.Io', [['zig', 'build-exe', 'hello.zig', '-target', 'x86_64-linux', '-mcpu', 'baseline', '-femit-bin=hello']])
    add('zig-small', 'Zig', 'ReleaseSmall std.Io', [['zig', 'build-exe', 'hello.zig', '-target', 'x86_64-linux', '-mcpu', 'baseline', '-O', 'ReleaseSmall', '-fstrip', '-femit-bin=hello']])
    add('zig-libc-small', 'Zig', 'ReleaseSmall libc puts', [['zig', 'build-exe', 'hello-libc.zig', '-lc', '-target', 'x86_64-linux-gnu', '-mcpu', 'baseline', '-O', 'ReleaseSmall', '-fstrip', '-femit-bin=hello']], note='Different output API; separate source')
    add('nim-default', 'Nim', 'default ORC', [['nim', 'c', '--mm:orc', '--nimcache:nimcache', '--out:hello', 'hello.nim']])
    add('nim-small', 'Nim', 'release size ORC', [['nim', 'c', '--mm:orc', '-d:release', '--opt:size', '--passC:-march=x86-64', '--passC:-Os', '--passL:-s', '--nimcache:nimcache', '--out:hello', 'hello.nim']])
    for profile, flags in [('default', []), ('release', ['-C', 'opt-level=3']),
                           ('release-stripped', ['-C', 'opt-level=3', '-C', 'strip=symbols']),
                           ('size-abort', ['-C', 'opt-level=z', '-C', 'strip=symbols', '-C', 'panic=abort', '-C', 'lto=fat', '-C', 'codegen-units=1'])]:
        add('rust-' + profile, 'Rust', profile,
            [['rustc', '-C', 'target-cpu=x86-64', *flags, 'hello.rs', '-o', 'hello']],
            note='panic=abort changes panic behavior' if profile == 'size-abort' else 'default panic=unwind')
    add('crystal-default', 'Crystal', 'default', [['crystal', 'build', 'hello.cr', '-o', 'hello']])
    add('crystal-release', 'Crystal', 'release stripped', [['crystal', 'build', '--release', '--no-debug', 'hello.cr', '-o', 'hello'], ['strip', '--strip-unneeded', 'hello']])
    for profile, flags in [('default', []), ('stripped', ['-trimpath', '-ldflags=-s -w'])]:
        add('go-' + profile, 'Go', profile, [['go', 'build', *flags, '-o', 'hello', 'hello.go']], env={'CGO_ENABLED': '0', 'GOAMD64': 'v1'})
    dotnet = ['dotnet', 'publish', 'Hello.csproj', '-c', 'Release', '-r', 'linux-x64', '-o', 'publish']
    add('csharp-framework', 'C#', 'Release framework-dependent', [[*dotnet, '--self-contained', 'false', '-p:UseAppHost=false']], 'publish', ['dotnet', 'Hello.dll'], False, 'External .NET runtime; DLL/config directory')
    add('csharp-selfcontained', 'C#', 'Release self-contained', [[*dotnet, '--self-contained', 'true']], 'publish', ['./Hello'], note='Directory deployment, full .NET runtime')
    add('csharp-trimmed', 'C#', 'Release self-contained trimmed', [[*dotnet, '--self-contained', 'true', '-p:PublishTrimmed=true']], 'publish', ['./Hello'], note='Trimming changes reflection availability')
    add('csharp-singlefile', 'C#', 'trimmed compressed single-file', [[*dotnet, '--self-contained', 'true', '-p:PublishTrimmed=true', '-p:PublishSingleFile=true', '-p:IncludeNativeLibrariesForSelfExtract=true', '-p:EnableCompressionInSingleFile=true']], 'publish', ['./Hello'], note='Native libraries extracted to /tmp; validation covers this output path only', archive_mode='internal compression + runtime extraction')
    add('csharp-aot', 'C#', 'NativeAOT Release', [[*dotnet, '--self-contained', 'true', '-p:PublishAot=true']], 'publish', ['./Hello'], note='External .dbg excluded; NativeAOT has reflection/dynamic-code limits')
    add('csharp-aot-small-invariant', 'C#', 'NativeAOT size invariant', [[*dotnet, '--self-contained', 'true', '-p:PublishAot=true', '-p:OptimizationPreference=Size', '-p:InvariantGlobalization=true']], 'publish', ['./Hello'], note='Size preference + invariant globalization; culture-specific behavior is restricted; external .dbg excluded')
    for profile, flags in [('default', []), ('size-dynamic', ['-Osize']), ('size-static-stdlib', ['-Osize', '-static-stdlib', LIBFLAGS[1]])]:
        commands = [['swiftc', '-target', 'x86_64-unknown-linux-gnu', '-module-cache-path', str(BASE / 'cache/swift-modules'), *flags, 'hello.swift', '-o', 'hello']]
        if profile != 'default':
            commands.append(['strip', '--strip-unneeded', 'hello'])
        add('swift-' + profile, 'Swift', profile, commands, note='-static-stdlib does not mean all system libraries are static' if 'static' in profile else 'Swift shared runtime counted in B')
    add('dart-source', 'Dart', 'source', [], 'hello.dart', ['dart', 'hello.dart'], False, 'External Dart runtime')
    add('dart-aot', 'Dart', 'compile exe', [['dart', 'compile', 'exe', 'hello.dart', '-o', 'hello']], note='Dart AOT executable')
    add('python-source', 'Python', 'source', [], 'hello.py', ['python3', 'hello.py'], False, 'External Python runtime')
    add('python-zipapp', 'Python', 'zipapp', [['python3', '-c', "from pathlib import Path; import zipapp; Path('zipapp').mkdir(); Path('zipapp/__main__.py').write_bytes(Path('hello.py').read_bytes()); zipapp.create_archive('zipapp', 'hello.pyz')"]], 'hello.pyz', ['python3', 'hello.pyz'], False, 'ZIP container; external Python runtime')
    for profile in ['onedir', 'onefile']:
        add('python-' + profile, 'Python', 'PyInstaller ' + profile,
            [['pyinstaller', '--' + profile, '--noconfirm', '--clean', '--noupx', '--name', 'hello', 'hello.py']],
            'dist/hello', ['./hello'] if profile == 'onedir' else ['./hello'],
            note='Bootloader + Python runtime; no UPX',
            archive_mode='internal PYZ compression' + (' + runtime extraction' if profile == 'onefile' else ''),
            hints=['python-onedir'] if profile == 'onefile' else [])
    jc = ['javac', '-J-Djava.io.tmpdir=' + str(BASE / 'tmp'), 'Hello.java']
    jar = ['jar', '--create', '--file', 'Hello.jar', '--main-class', 'Hello', 'Hello.class']
    add('java-class', 'Java', 'class', [jc], 'Hello.class', ['java', 'Hello'], False, 'External JVM')
    add('java-jar', 'Java', 'JAR', [jc, jar], 'Hello.jar', ['java', '-jar', 'Hello.jar'], False, 'External JVM; JAR uses ZIP compression', archive_mode='JAR ZIP compression')
    for profile, modules in [('base', 'java.base'), ('all', 'ALL-MODULE-PATH')]:
        add('java-jlink-' + profile, 'Java', 'JAR + jlink ' + modules,
            [jc, jar, ['jlink', '-J-Djava.io.tmpdir=' + str(BASE / 'tmp'), '--module-path', str(Path(os.environ['JAVA_HOME']) / 'jmods'), '--add-modules', modules, '--strip-debug', '--no-header-files', '--no-man-pages', '--compress=zip-6', '--output', 'runtime']],
            ['Hello.jar', 'runtime'], ['./runtime/bin/java', '-jar', 'Hello.jar'], note='Module set differs; full runtime directory counted', archive_mode='jlink zip-6 resources + JAR')
    add('java-jpackage', 'Java', 'jpackage java.base app-image',
        [jc, ['python3', '-c', "from pathlib import Path; Path('input').mkdir()"],
         ['jar', '--create', '--file', 'input/Hello.jar', '--main-class', 'Hello', 'Hello.class'],
         ['jpackage', '-J-Djava.io.tmpdir=' + str(BASE / 'tmp'), '--type', 'app-image', '--input', 'input', '--main-jar', 'Hello.jar', '--name', 'HelloJava', '--add-modules', 'java.base', '--jlink-options', '--strip-debug --no-header-files --no-man-pages --compress=zip-6', '--dest', 'package']],
        'package/HelloJava', ['./bin/HelloJava'], note='Entire launcher/app/runtime image, not launcher alone', archive_mode='jlink zip-6 resources + JAR')
    ni = ['native-image', '--no-fallback', '-march=x86-64', '-J-Xmx3g', '-J-Djava.io.tmpdir=' + str(BASE / 'tmp'), '-H:NativeLinkerOption=' + LIBFLAGS[1]]
    for profile, flags in [('default', []), ('size', ['-Os'])]:
        commands = [jc, [*ni, *flags, 'Hello', 'hello']]
        if profile == 'size':
            commands.append(['strip', '--strip-unneeded', 'hello'])
        add('java-native-' + profile, 'Java', 'Native Image ' + profile, commands, note='Closed-world AOT; no JVM; --no-fallback')
    for lang, tool in [('Bun', 'bun'), ('Deno', 'deno'), ('Node.js', 'node')]:
        add(tool + '-source', lang, 'JS source', [], 'hello.js', [tool, 'hello.js'], False, 'External ' + lang + ' runtime')
    add('bun-compile', 'Bun', 'compile', [['bun', 'build', '--compile', 'hello.js', '--outfile', 'hello']], note='Embedded Bun runtime')
    add('bun-minify', 'Bun', 'compile minify', [['bun', 'build', '--compile', '--minify', 'hello.js', '--outfile', 'hello']], note='Embedded Bun runtime; JS minified')
    add('deno-compile', 'Deno', 'compile', [['deno', 'compile', '--output', 'hello', 'hello.js']], note='Embedded Deno runtime')
    add('node-sea', 'Node.js', 'SEA',
        [['python3', '-c', "import json,shutil; from pathlib import Path; Path('sea.json').write_text(json.dumps(dict(main='hello.js',output='sea.blob',disableExperimentalSEAWarning=True))); shutil.copy2(shutil.which('node'), 'hello')"],
         ['node', '--experimental-sea-config', 'sea.json'],
         ['postject', 'hello', 'NODE_SEA_BLOB', 'sea.blob', '--sentinel-fuse', 'NODE_SEA_FUSE_fce680ab2cc467b6e072b8b5df1996b2']], note='Official Node SEA blob + copied Node executable')
    return cases


def make_baseline(root):
    for d in ['usr/lib64', 'app', 'tmp', 'proc', 'dev', 'etc']:
        (root / d).mkdir(parents=True, exist_ok=True)
    (root / 'tmp').chmod(0o1777)
    for name in ['lib', 'lib64']:
        (root / name).symlink_to('usr/lib64')
    paths = capture(['rpm', '-ql', 'glibc']).stdout.decode().splitlines()
    for name in paths:
        path = Path(name)
        if path.parent in (Path('/lib64'), Path('/usr/lib64')) and path.is_file() and ('.so' in path.name):
            GLIBC_PATHS.add(str(path.resolve()))
            target = root / 'usr/lib64' / path.name
            # Flatten aliases to real contents so every glibc SONAME is available.
            shutil.copy2(path.resolve(), target)
    (root / 'etc/passwd').write_text('root:x:0:0:root:/tmp:/bin/false\n')
    (root / 'etc/group').write_text('root:x:0:\n')
    (root / 'etc/nsswitch.conf').write_text('passwd: files\ngroup: files\nhosts: files\n')
    (root / 'etc/hosts').write_text('127.0.0.1 localhost\n::1 localhost\n')
    (root / 'etc/resolv.conf').write_text('')
    for name, minor in [('null', 3), ('zero', 5), ('random', 8), ('urandom', 9)]:
        os.mknod(root / 'dev' / name, stat.S_IFCHR | 0o666, os.makedev(1, minor))
        (root / 'dev' / name).chmod(0o666)


def collect_dependencies(package, hint_dirs):
    log, added = [], []
    libdir = package / 'lib'
    libdir.mkdir(exist_ok=True)
    scanned = set()
    for iteration in range(8):
        paths = [p for d in [package, *hint_dirs] for p in sorted(d.rglob('*')) if elf(p) and str(p) not in scanned]
        if not paths:
            break
        for path in paths:
            scanned.add(str(path))
            env = os.environ.copy()
            env['LD_LIBRARY_PATH'] = str(libdir) + ':' + env.get('LD_LIBRARY_PATH', '')
            p = capture(['ldd', path], env=env)
            output = (p.stdout + p.stderr).decode(errors='replace')
            log.append({'path': str(path), 'output': output, 'exit_code': p.returncode})
            for soname, absolute in re.findall(r'^\s*(\S+)\s+=>\s+(/\S+)', output, re.M):
                src = Path(absolute)
                real = src.resolve()
                if str(real) in GLIBC_PATHS or real.is_relative_to(package.resolve()):
                    continue
                # A library already shipped elsewhere in the payload is not duplicated.
                shipped = [p for p in package.rglob(soname) if p.is_file()]
                if shipped:
                    dst = libdir / soname
                    if not dst.exists():
                        target = os.path.relpath(shipped[0], libdir)
                        dst.symlink_to(target)
                        added.append({'path': 'lib/' + soname, 'source': str(shipped[0]),
                                      'reason': 'Search-path alias to an already shipped library'})
                    continue
                # Hint directories describe libraries embedded in an opaque onefile.
                # Their mutual dependencies are already embedded, but the actual
                # bootloader ELF still needs its own external libraries before extraction.
                if not path.is_relative_to(package) and any(p.is_file() for d in hint_dirs for p in d.rglob(soname)):
                    continue
                dst = libdir / soname
                if not dst.exists():
                    shutil.copy2(real, dst)
                    added.append({'path': 'lib/' + soname, 'source': str(real), 'reason': 'ELF dependency'})
            for soname in re.findall(r'^\s*(\S+)\s+=>\s+not found', output, re.M):
                shipped = [p for p in package.rglob(soname) if p.is_file()]
                # Runtime loaders may resolve bundled libraries themselves (e.g. JVM).
                # Keep the raw ldd evidence; the clean-root execution is decisive.
                log[-1].setdefault('unresolved', []).append({'soname': soname,
                    'bundled_paths': [str(p.relative_to(package)) for p in shipped]})
    return added, log


def add_icu(package):
    added = []
    output = capture(['/sbin/ldconfig', '-p']).stdout.decode()
    for name in ['libicui18n', 'libicuuc', 'libicudata']:
        found = re.search(r'\b(' + name + r'\.so\.\d+)\s+.*=>\s+(/\S+)', output)
        if not found:
            raise RuntimeError('Cannot resolve ICU ' + name)
        soname, source = found.groups()
        dst = package / 'lib' / soname
        if not dst.exists():
            shutil.copy2(Path(source).resolve(), dst)
            added.append({'path': 'lib/' + soname, 'source': str(Path(source).resolve()),
                          'reason': 'Observed .NET globalization initialization failure in isolated run'})
    return added


def isolated_run(run_dir, case_dir, package, command):
    root = case_dir / 'isolated-root'
    if root.exists():
        shutil.rmtree(root)
    # Preserve devices explicitly; copytree cannot copy device nodes.
    baseline = run_dir / 'baseline'
    shutil.copytree(baseline, root, symlinks=True, copy_function=os.link,
                    ignore=lambda d, names: ['dev'] if Path(d) == baseline else [])
    (root / 'dev').mkdir()
    for name, minor in [('null', 3), ('zero', 5), ('random', 8), ('urandom', 9)]:
        os.mknod(root / 'dev' / name, stat.S_IFCHR | 0o666, os.makedev(1, minor))
        (root / 'dev' / name).chmod(0o666)
    shutil.copytree(package, root / 'app', dirs_exist_ok=True, symlinks=True, copy_function=os.link)
    target = '/app/' + command[0][2:] if command[0].startswith('./') else command[0]
    invocation = ['unshare', '--mount', '--pid', '--fork',
                  shutil.which('python3'), str(REPO / 'scripts/isolated-exec.py'), str(root), json.dumps([target, *command[1:]])]
    p = capture(invocation, timeout=120)
    result = {'command': [target, *command[1:]], 'environment': 'scripts/isolated-exec.py',
              'exit_code': p.returncode, 'stdout_hex': p.stdout.hex(),
              'stderr': p.stderr.decode(errors='replace'),
              'verified': p.returncode == 0 and p.stdout == EXPECTED and p.stderr == b''}
    # Free temporary app hardlinks and extraction files; the measured package stays.
    shutil.rmtree(root)
    return result


def archive(package, path):
    with path.open('wb') as raw:
        with gzip.GzipFile(filename='', fileobj=raw, mode='wb', compresslevel=9, mtime=0) as gz:
            with tarfile.open(fileobj=gz, mode='w', format=tarfile.PAX_FORMAT) as tar:
                for file in sorted(package.rglob('*')):
                    info = tar.gettarinfo(str(file), arcname=str(file.relative_to(package)))
                    info.uid = info.gid = info.mtime = 0
                    info.uname = info.gname = ''
                    # Count hardlinks as separate delivered paths, same as the main metric.
                    if file.is_file() and not file.is_symlink():
                        info.type = tarfile.REGTYPE
                        info.linkname = ''
                        info.size = file.stat().st_size
                        with file.open('rb') as f:
                            tar.addfile(info, f)
                    else:
                        tar.addfile(info)
    return {'bytes': path.stat().st_size, 'sha256': sha(path), 'path': str(path),
            'parameters': 'tar PAX sorted paths uid/gid/mtime=0; gzip level=9 mtime=0'}


def run_case(spec, run_dir, previous=None):
    entry = {k: v for k, v in spec.items() if k not in ('builds', 'output', 'run', 'hints')}
    entry.update(build_commands=[], status='failed', runner_sha256=sha(Path(__file__)),
                 isolated_helper_sha256=sha(REPO / 'scripts/isolated-exec.py'),
                 measured_at_utc=dt.datetime.now(dt.timezone.utc).isoformat())
    case_dir = run_dir / spec['id']
    if case_dir.exists():
        attempts = run_dir / 'superseded-attempts'
        attempts.mkdir(exist_ok=True)
        old_dir = attempts / (spec['id'] + '-' + dt.datetime.now(dt.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'))
        if previous:
            (case_dir / 'measurement.json').write_text(json.dumps(previous, ensure_ascii=False, indent=2) + '\n')
        shutil.move(str(case_dir), str(old_dir))
        entry['superseded_attempts'] = (previous or {}).get('superseded_attempts', []) + [str(old_dir)]
    work, app, package = [case_dir / name for name in ('work', 'application', 'deployment')]
    entry['artifact_paths'] = {'application': str(app), 'deployment': str(package)}
    work.mkdir(parents=True)
    app.mkdir()
    env = os.environ.copy()
    env.update(spec['env'])
    env['ZIG_LOCAL_CACHE_DIR'] = str(work / 'zig-cache')
    try:
        for src in (REPO / 'src/standard').iterdir():
            shutil.copy2(src, work / src.name)
        for index, command in enumerate(spec['builds']):
            started = time.monotonic()
            invocation = ['unshare', '--mount', shutil.which('python3'),
                          str(REPO / 'scripts/data-tmp-exec.py'), str(BASE / 'tmp'), *command]
            p = capture(invocation, cwd=work, env=env, timeout=1200)
            log = case_dir / ('build-%02d.log' % index)
            log.write_bytes(p.stdout + p.stderr)
            entry['build_commands'].append({'argv': command, 'cwd': str(work),
                                             'invocation': invocation,
                                             'tmp_helper_sha256': sha(REPO / 'scripts/data-tmp-exec.py'),
                                             'exit_code': p.returncode, 'log': str(log),
                                             'log_sha256': sha(log), 'output': (p.stdout + p.stderr).decode(errors='replace'),
                                             'elapsed_seconds': round(time.monotonic() - started, 3)})
            if p.returncode:
                raise RuntimeError('Build failed: ' + str(command) + '\n' + (p.stdout + p.stderr).decode(errors='replace')[-4000:])
        excluded = []
        outputs = spec['output'] if isinstance(spec['output'], list) else [spec['output']]
        for name in outputs:
            source = work / name
            # Multi-output cases preserve runtime/; single directories become the app root.
            dest = app / source.name if len(outputs) > 1 or not source.is_dir() else app
            copy_payload(source, dest, excluded)
        # PyInstaller's onefile filename is hello; onedir contents include the hello launcher.
        entry['excluded_debug_files'] = excluded
        entry['application'] = inventory(app)
        entry['application_elf'] = elf_report(app)
        entry['run_command'] = spec['run']
        host = capture(spec['run'], cwd=app, env=env, timeout=120)
        entry['host_run'] = {'exit_code': host.returncode, 'stdout_hex': host.stdout.hex(),
                             'stderr': host.stderr.decode(errors='replace'),
                             'verified': host.returncode == 0 and host.stdout == EXPECTED and host.stderr == b''}
        if not entry['host_run']['verified']:
            raise RuntimeError('Host validation failed: ' + str(entry['host_run']))
        if spec['packaged']:
            shutil.copytree(app, package, symlinks=True)
            hints = [run_dir / name / 'application' for name in spec['hints']]
            added, deps = collect_dependencies(package, hints)
            result = isolated_run(run_dir, case_dir, package, spec['run'])
            attempts = [result]
            if not result['verified'] and spec['language'] == 'C#' and 'ICU' in result['stderr']:
                added.extend(add_icu(package))
                more, moredeps = collect_dependencies(package, [])
                added.extend(more)
                deps.extend(moredeps)
                result = isolated_run(run_dir, case_dir, package, spec['run'])
                attempts.append(result)
            entry.update(added_dependencies=added, ldd=deps, isolated_attempts=attempts,
                         isolated_run=result)
            if not result['verified']:
                raise RuntimeError('Isolated validation failed: ' + str(result))
            entry['deployment'] = inventory(package)
            entry['deployment_elf'] = elf_report(package)
            entry['download_archive'] = archive(package, case_dir / 'deployment.tar.gz')
        else:
            entry['download_archive'] = archive(app, case_dir / 'application.tar.gz')
        entry['status'] = 'passed'
    except Exception as e:
        entry['error'] = str(e)
    return entry


def save(report, run_dir):
    path = run_dir / 'measurements.json'
    temporary = run_dir / 'measurements.json.tmp'
    temporary.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    temporary.replace(path)


def export(report, run_dir):
    path = REPO / 'results/2026-09-28-rocky9-measurements.csv'
    with path.open('w', newline='', encoding='utf-8') as f:
        fields = ['id', 'language', 'profile', 'status', 'application_bytes', 'application_files',
                  'deployment_bytes', 'deployment_files', 'gzip_bytes', 'internal_compression', 'note']
        writer = csv.DictWriter(f, fields)
        writer.writeheader()
        for e in report['cases'].values():
            writer.writerow(dict(id=e['id'], language=e['language'], profile=e['profile'], status=e['status'],
                                 application_bytes=e.get('application', {}).get('bytes', ''),
                                 application_files=e.get('application', {}).get('files', ''),
                                 deployment_bytes=e.get('deployment', {}).get('bytes', ''),
                                 deployment_files=e.get('deployment', {}).get('files', ''),
                                 gzip_bytes=e.get('download_archive', {}).get('bytes', ''),
                                 internal_compression=e['archive_mode'], note=e['note']))
    lines = ['# Rocky Linux VM 正式测量结果', '',
             '测量时间（UTC）：`' + report['started_at_utc'] + '`。构建目录：`' + str(run_dir) + '`。', '',
             '所有有效项目均输出精确的 `Hello World\\n`（12 B），stderr 为空，退出码为 0。', '',
             'A 为工具生成的应用文件集合；B 为补齐依赖、通过 glibc 基线隔离验证的分发集合。',
             '表中单位全部为精确字节 B。外部运行时的源码/class/JAR只列 A，B 的空值不等于零。', '',
             '文件统计、基线、压缩与语义边界见 [测量标准](../METHODOLOGY.md)。版本与安装见 [VM 环境](../VM_SETUP.md)。', '',
             'gzip 列是整个 B 集合的 tar+gzip9 下载归档；无 B 的项目则压缩 A。它与原始文件字节分开。', '',
             '共 ' + str(len(report['cases'])) + ' 种配置，' + str(sum(e['status'] == 'passed' for e in report['cases'].values())) + ' 项通过；'
             + str(sum(e.get('isolated_run', {}).get('verified', False) for e in report['cases'].values())) + ' 个分发集合通过隔离验证。', '',
             'Assembly tiny-rwx 是极限配置附录；源码、字节码和 framework-dependent 行只是 A 口径参照。', '',
             '| 项目 | 配置 | A 应用（B） | A 文件数 | B 分发（B） | B 文件数 | gzip（B） | 状态 |',
             '|---|---|---:|---:|---:|---:|---:|---|']
    for e in report['cases'].values():
        a, b, z = [e.get(name, {}) for name in ('application', 'deployment', 'download_archive')]
        lines.append('| ' + ' | '.join([e['language'], e['profile'], str(a.get('bytes', '—')),
                                       str(a.get('files', '—')), str(b.get('bytes', '—')),
                                       str(b.get('files', '—')), str(z.get('bytes', '—')), e['status']]) + ' |')
    lines += ['', '## 构建、依赖与边界', '']
    for e in report['cases'].values():
        lines += ['### ' + e['id'], '', e['note'] or e['profile'], '',
                  '- 内部压缩/解包：' + e['archive_mode'],
                  '- 运行：`' + shlex.join(e.get('run_command', [])) + '`']
        for dependency in e.get('added_dependencies', []):
            lines.append('- B 补齐：`' + dependency['path'] + '`，来源 `' + dependency['source'] + '`')
        for excluded in e.get('excluded_debug_files', []):
            lines.append('- 外部调试文件排除：`' + Path(excluded['path']).name + '`，' + str(excluded['bytes']) + ' B')
        for unresolved in e.get('ldd_unresolved_summary', []):
            lines.append('- ldd 单独扫描未解析 `' + unresolved['soname'] + '`：' + unresolved['classification']
                         + ('；已打包 `' + '`, `'.join(unresolved['bundled_paths']) + '`' if unresolved['bundled_paths'] else ''))
        if e.get('superseded_attempts'):
            lines.append('- 修正前构建/失败证据保留于 JSON 的 `superseded_attempts` 路径。')
        lines += ['', '```text']
        lines.extend(shlex.join([str(x) for x in command['argv']]) for command in e['build_commands'])
        lines += ['```', '']
        if e['status'] != 'passed':
            lines += ['失败原因：', '', '```text', e.get('error', ''), '```', '']
    lines += ['## 原始证据', '',
              '- [JSON](2026-09-28-rocky9-measurements.json)：源文件与产物哈希、版本、完整 argv、构建日志、ELF/ldd 依赖、隔离验证、基线清单。',
              '- [CSV](2026-09-28-rocky9-measurements.csv)：可直接分析的精确整数。',
              '- VM 数据盘保留每个项目的 application/、deployment/、归档和构建日志；JSON 记录绝对位置。', '']
    if report.get('artifact_audit'):
        audit = report['artifact_audit']
        lines += ['最终产物审计：GNU find 的文件字节数与 sha256sum 独立复核通过，'
                  + str(audit['case_count']) + ' 项、' + str(audit['language_count']) + ' 个项目、'
                  + str(audit['isolated_package_count']) + ' 个隔离分发集合。', '']
    (REPO / 'results/2026-09-28-rocky9-report.md').write_text('\n'.join(lines))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--resume', type=Path)
    parser.add_argument('--only', help='Comma-separated case IDs; resume preserves other cases')
    args = parser.parse_args()
    if os.environ.get('HW_ROOT') != str(BASE) or os.geteuid() != 0:
        raise SystemExit('Run as root after sourcing scripts/vm-env.sh')
    if not os.path.ismount('/mnt/sdb'):
        raise SystemExit('Data disk not mounted')
    if args.resume:
        run_dir = args.resume.resolve()
        if not run_dir.is_relative_to(BASE / 'build/formal'):
            raise SystemExit('Resume path must be under the formal data directory')
        report = json.loads((run_dir / 'measurements.json').read_text())
        GLIBC_PATHS.update(report['glibc_realpaths'])
    else:
        run_dir = BASE / 'build/formal' / dt.datetime.now(dt.timezone.utc).strftime('%Y%m%dT%H%M%SZ')
        run_dir.mkdir(parents=True)
        baseline = run_dir / 'baseline'
        make_baseline(baseline)
        setup = json.loads((REPO / 'results/2026-09-28-rocky9-vm-setup.json').read_text())
        report = {'schema_version': 1, 'started_at_utc': dt.datetime.now(dt.timezone.utc).isoformat(),
                  'run_directory': str(run_dir), 'expected_stdout_hex': EXPECTED.hex(),
                  'environment': {'os_release': Path('/etc/os-release').read_text(),
                                  'kernel': platform.release(), 'architecture': platform.machine(),
                                  'cpu': capture(['lscpu']).stdout.decode(),
                                  'memory': Path('/proc/meminfo').read_text(),
                                  'disk_before': capture(['df', '-B1', '/', '/mnt/sdb']).stdout.decode(),
                                  'workspace_mount': capture(['findmnt', '-n', '-T', str(REPO)]).stdout.decode(),
                                  'data_mount': capture(['findmnt', '-n', '-T', str(run_dir)]).stdout.decode()},
                  'toolchains': setup['toolchains'], 'baseline': inventory(baseline),
                  'glibc_realpaths': sorted(GLIBC_PATHS),
                  'sources': [{'path': str(p.relative_to(REPO)), 'bytes': p.stat().st_size, 'sha256': sha(p)}
                              for p in sorted((REPO / 'src/standard').iterdir())],
                  'methodology_sha256': sha(REPO / 'METHODOLOGY.md'),
                  'runner_sha256': sha(Path(__file__)), 'cases': {}}
    print('RUN_DIRECTORY', run_dir, flush=True)
    revision = sha(Path(__file__))
    shutil.copy2(Path(__file__), run_dir / ('runner-' + revision + '.py'))
    helper_revision = sha(REPO / 'scripts/isolated-exec.py')
    shutil.copy2(REPO / 'scripts/isolated-exec.py', run_dir / ('isolated-exec-' + helper_revision + '.py'))
    report['latest_runner_sha256'] = revision
    report['latest_isolated_helper_sha256'] = helper_revision
    tmp_revision = sha(REPO / 'scripts/data-tmp-exec.py')
    shutil.copy2(REPO / 'scripts/data-tmp-exec.py', run_dir / ('data-tmp-exec-' + tmp_revision + '.py'))
    report['latest_tmp_helper_sha256'] = tmp_revision
    save(report, run_dir)
    for spec in specs():
        if args.only and spec['id'] not in args.only.split(','):
            continue
        if args.resume and not args.only and report['cases'].get(spec['id'], {}).get('status') == 'passed':
            continue
        print('BUILD', spec['id'], flush=True)
        entry = run_case(spec, run_dir, report['cases'].get(spec['id']))
        report['cases'][spec['id']] = entry
        save(report, run_dir)
        a, b = entry.get('application', {}).get('bytes'), entry.get('deployment', {}).get('bytes')
        print(entry['status'].upper(), spec['id'], 'A=', a, 'B=', b,
              entry.get('error', '')[-1600:], flush=True)
    report['last_updated_at_utc'] = dt.datetime.now(dt.timezone.utc).isoformat()
    report['methodology_sha256'] = sha(REPO / 'METHODOLOGY.md')
    report['cases'] = {s['id']: report['cases'][s['id']] for s in specs() if s['id'] in report['cases']}
    report['environment']['disk_after'] = capture(['df', '-B1', '/', '/mnt/sdb']).stdout.decode()
    save(report, run_dir)
    shutil.copy2(run_dir / 'measurements.json', REPO / 'results/2026-09-28-rocky9-measurements.json')
    export(report, run_dir)
    failed = [id for id, entry in report['cases'].items() if entry['status'] != 'passed']
    print('TOTAL', len(report['cases']), 'FAILED', failed, flush=True)
    raise SystemExit(bool(failed))


if __name__ == '__main__':
    main()
