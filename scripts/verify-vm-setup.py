#!/usr/bin/env python3
"""Readiness checks only: build/run smoke programs, not benchmark measurements."""
import argparse
import datetime
import json
import os
from pathlib import Path
import platform
import shutil
import subprocess

BASE = Path('/mnt/sdb/helloworld-test')
WORK = BASE / 'build/setup-smoke'
EXPECTED = b'Hello World\n'


def call(command, cwd=WORK, timeout=300):
    p = subprocess.run(command, cwd=cwd, capture_output=True, timeout=timeout)
    if p.returncode:
        raise RuntimeError(f'{command!r}: exit {p.returncode}: {(p.stdout + p.stderr).decode(errors="replace")[-7000:]}')
    return p


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--only', help='Comma-separated checks to retry; preserve other recorded checks')
    args = parser.parse_args()
    if os.environ.get('HW_ROOT') != str(BASE):
        raise SystemExit('Source vm-env.sh first')
    WORK.mkdir(parents=True, exist_ok=True)
    sources = {
        'hello.c': '#include <stdio.h>\nint main(void){puts("Hello World");return 0;}\n',
        'hello.cpp': '#include <iostream>\nint main(){std::cout << "Hello World\\n";}\n',
        'hello.zig': 'extern "c" fn puts([*:0]const u8) c_int;\npub fn main() void { _ = puts("Hello World"); }\n',
        'hello.nim': 'echo "Hello World"\n',
        'hello.rs': 'fn main(){println!("Hello World");}\n',
        'hello.cr': 'puts "Hello World"\n',
        'hello.go': 'package main\nimport "fmt"\nfunc main(){fmt.Println("Hello World")}\n',
        'hello.swift': 'print("Hello World")\n',
        'hello.dart': 'void main(){print("Hello World");}\n',
        'hello.js': 'console.log("Hello World");\n',
        'hello.py': 'print("Hello World")\n',
        'Hello.java': 'class Hello { public static void main(String[] args){System.out.println("Hello World");}}\n',
        'hello.s': '.global _start\n.text\n_start:\nmov $1,%rax\nmov $1,%rdi\nlea msg(%rip),%rsi\nmov $12,%rdx\nsyscall\nmov $60,%rax\nxor %rdi,%rdi\nsyscall\n.section .rodata\nmsg: .ascii "Hello World\\n"\n',
    }
    for name, source in sources.items():
        (WORK / name).write_text(source)
    (WORK / 'dotnet').mkdir(exist_ok=True)
    (WORK / 'dotnet/Hello.csproj').write_text('<Project Sdk="Microsoft.NET.Sdk"><PropertyGroup><OutputType>Exe</OutputType><TargetFramework>net10.0</TargetFramework></PropertyGroup></Project>\n')
    (WORK / 'dotnet/Program.cs').write_text('System.Console.WriteLine("Hello World");\n')
    static = BASE / 'toolchains/static-libs'
    libflags = ['-L' + str(static / 'usr/lib64'), '-L' + str(static / 'usr/lib/gcc/x86_64-redhat-linux/11')]
    tests = {
        'assembly': ([['as', 'hello.s', '-o', 'hello.o'], ['ld', 'hello.o', '-o', 'hello-asm']], ['./hello-asm']),
        'c': ([['gcc', 'hello.c', '-o', 'hello-c']], ['./hello-c']),
        'cpp': ([['g++', 'hello.cpp', '-o', 'hello-cpp']], ['./hello-cpp']),
        'c_static': ([['gcc', '-static', *libflags, 'hello.c', '-o', 'hello-c-static']], ['./hello-c-static']),
        'cpp_static': ([['g++', '-static', *libflags, 'hello.cpp', '-o', 'hello-cpp-static']], ['./hello-cpp-static']),
        'zig': ([['zig', 'build-exe', 'hello.zig', '-lc', '-femit-bin=hello-zig']], ['./hello-zig']),
        'nim': ([['nim', 'c', '--nimcache:' + str(WORK / 'nimcache'), '--out:hello-nim', 'hello.nim']], ['./hello-nim']),
        'rust': ([['rustc', 'hello.rs', '-o', 'hello-rust']], ['./hello-rust']),
        'crystal': ([['crystal', 'build', 'hello.cr', '-o', 'hello-crystal']], ['./hello-crystal']),
        'go': ([['go', 'build', '-o', 'hello-go', 'hello.go']], ['./hello-go']),
        'csharp': ([['dotnet', 'publish', 'dotnet/Hello.csproj', '-c', 'Release', '-r', 'linux-x64', '--self-contained', 'true', '-o', 'dotnet-publish']], ['./dotnet-publish/Hello']),
        'csharp_aot': ([['dotnet', 'publish', 'dotnet/Hello.csproj', '-c', 'Release', '-r', 'linux-x64', '-p:PublishAot=true', '-o', 'dotnet-aot']], ['./dotnet-aot/Hello']),
        'swift': ([['swiftc', '-module-cache-path', str(BASE / 'cache/swift-modules'), 'hello.swift', '-o', 'hello-swift']], ['./hello-swift']),
        'dart': ([['dart', 'compile', 'exe', 'hello.dart', '-o', 'hello-dart']], ['./hello-dart']),
        'python_packaged': ([['pyinstaller', '--onefile', '--noconfirm', '--name', 'hello-python', 'hello.py']], ['./dist/hello-python']),
        'java': ([['javac', '-J-Djava.io.tmpdir=' + str(BASE / 'tmp'), 'Hello.java']], ['java', '-Djava.io.tmpdir=' + str(BASE / 'tmp'), 'Hello']),
        'java_jpackage': ([['javac', '-J-Djava.io.tmpdir=' + str(BASE / 'tmp'), 'Hello.java'], ['jar', '--create', '--file', 'java-input/Hello.jar', '--main-class', 'Hello', 'Hello.class'], ['jpackage', '-J-Djava.io.tmpdir=' + str(BASE / 'tmp'), '--type', 'app-image', '--input', 'java-input', '--main-jar', 'Hello.jar', '--name', 'HelloJava', '--dest', 'java-package']], ['./java-package/HelloJava/bin/HelloJava']),
        'java_native_image': ([['native-image', '--no-fallback', '-march=x86-64', '-J-Xmx3g', '-J-Djava.io.tmpdir=' + str(BASE / 'tmp'), '-H:NativeLinkerOption=-L' + str(static / 'usr/lib/gcc/x86_64-redhat-linux/11'), 'Hello', 'hello-java-native']], ['./hello-java-native']),
        'bun': ([['bun', 'build', '--compile', 'hello.js', '--outfile', 'hello-bun']], ['./hello-bun']),
        'deno': ([['deno', 'compile', '--output', 'hello-deno', 'hello.js']], ['./hello-deno']),
    }
    sea = {'main': 'hello.js', 'output': 'sea.blob', 'disableExperimentalSEAWarning': True}
    (WORK / 'sea.json').write_text(json.dumps(sea))
    (WORK / 'java-input').mkdir(exist_ok=True)
    # jpackage refuses an existing destination; remove only this check's output.
    package_output = WORK / 'java-package/HelloJava'
    if (not args.only or 'java_jpackage' in args.only.split(',')) and package_output.exists():
        shutil.rmtree(package_output)
    shutil.copy2(shutil.which('node'), WORK / 'hello-node')
    tests['node_sea'] = ([['node', '--experimental-sea-config', 'sea.json'], ['postject', 'hello-node', 'NODE_SEA_BLOB', 'sea.blob', '--sentinel-fuse', 'NODE_SEA_FUSE_fce680ab2cc467b6e072b8b5df1996b2']], ['./hello-node'])
    report = {'recorded_at_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
              'purpose': 'Toolchain readiness; not experimental size results',
              'environment': {'system': platform.system(), 'machine': platform.machine(), 'kernel': platform.release(),
                              'os_release': Path('/etc/os-release').read_text(),
                              'disk': subprocess.check_output(['df', '-B1', '/', '/mnt/sdb'], text=True),
                              'data_mount': subprocess.check_output(['findmnt', '-n', '-T', '/mnt/sdb'], text=True),
                              'workspace_mount': subprocess.check_output(['findmnt', '-n', '-T', '/home/dev/common'], text=True)},
              'tests': {}}
    if args.only and (BASE / 'setup-verification.json').exists():
        report['tests'] = json.loads((BASE / 'setup-verification.json').read_text())['tests']
    versions = {'gcc': ['--version'], 'g++': ['--version'], 'clang': ['--version'], 'python3': ['--version'], 'node': ['--version'], 'javac': ['--version'], 'java': ['-version'], 'jpackage': ['--version'], 'native-image': ['--version'], 'zig': ['version'], 'nim': ['--version'], 'rustc': ['--version'], 'cargo': ['--version'], 'crystal': ['--version'], 'go': ['version'], 'dotnet': ['--info'], 'swiftc': ['--version'], 'dart': ['--version'], 'bun': ['--version'], 'deno': ['--version'], 'pyinstaller': ['--version']}
    report['toolchains'] = {}
    for name, flags in versions.items():
        p = shutil.which(name)
        if p:
            try:
                result = call([name, *flags], timeout=30)
                report['toolchains'][name] = {'path': p, 'realpath': str(Path(p).resolve()), 'version': (result.stdout + result.stderr).decode(errors='replace').strip()}
            except Exception as e:
                report['toolchains'][name] = {'path': p, 'error': str(e)}
        else:
            report['toolchains'][name] = {'missing': True}
    for name, (builds, command) in tests.items():
        if args.only and name not in args.only.split(','):
            continue
        print('CHECK', name, flush=True)
        entry = {'build': builds, 'command': command}
        try:
            for build in builds:
                call(build)
            result = call(command)
            if result.stdout != EXPECTED or result.stderr:
                raise RuntimeError(f'Unexpected stdout/stderr: {result.stdout!r}, {result.stderr!r}')
            entry.update(verified=True, stdout='Hello World\n', exit_code=0)
            print('PASS', name, flush=True)
        except Exception as e:
            entry.update(verified=False, error=str(e))
            print('FAIL', name, str(e)[-2500:], flush=True)
        report['tests'][name] = entry
        (BASE / 'setup-verification.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    failed = [k for k, v in report['tests'].items() if not v['verified']]
    print('FAILED', failed, flush=True)
    raise SystemExit(bool(failed))


if __name__ == '__main__':
    main()
