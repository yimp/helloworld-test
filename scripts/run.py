#!/usr/bin/env python3
"""Build and run the Hello World variants available on this Linux machine.

Usage: python3 scripts/run.py [--include-jpackage] [--output results/local.json]
No compiler or package manager downloads are performed.
"""

from __future__ import annotations

import argparse
import json
import platform
import shutil
import subprocess
import zipapp
from datetime import datetime, timezone
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

ROOT = Path(__file__).resolve().parents[1]
BUILD = ROOT / "build"
EXPECTED = "Hello World\n"
SOURCES = ["hello.s", "hello.c", "hello.cpp", "hello.py", "hello.js", "Hello.java", "Compile.java"]


def run(args: list[str], cwd: Path = BUILD) -> subprocess.CompletedProcess[str]:
    proc = subprocess.run(args, cwd=cwd, text=True, capture_output=True, timeout=120)
    if proc.returncode != 0:
        raise RuntimeError(f"{args!r} failed ({proc.returncode}): {proc.stderr}")
    return proc


def checked(args: list[str], cwd: Path = BUILD) -> dict:
    proc = run(args, cwd)
    if proc.stdout != EXPECTED or proc.stderr:
        raise RuntimeError(f"Unexpected output for {args!r}: {proc.stdout!r}, {proc.stderr!r}")
    return {"command": args, "size_bytes": (cwd / args[0]).stat().st_size,
            "stdout": proc.stdout, "verified": True}


def dependency_sizes(executable: str) -> dict[str, int]:
    lines = run(["ldd", executable]).stdout.splitlines()
    found = {}
    for line in lines:
        words = line.split()
        if not words:
            continue
        candidate = words[2] if len(words) > 2 and words[1] == "=>" else words[0]
        if candidate.startswith("/") and Path(candidate).exists():
            found[words[0]] = Path(candidate).stat().st_size
    return found


def directory_bytes(path: Path) -> int:
    return int(run(["du", "-sb", str(path)]).stdout.split()[0])


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--include-jpackage", action="store_true",
                        help="Also bundle the whole installed JRE (about 193 MB here)")
    parser.add_argument("--output", type=Path, default=BUILD / "results.json")
    args = parser.parse_args()
    BUILD.mkdir(parents=True, exist_ok=True)
    for name in SOURCES:
        shutil.copyfile(ROOT / "src" / name, BUILD / name)

    data: dict = {
        "recorded_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "environment": {
            "system": platform.system(), "machine": platform.machine(),
            "kernel": platform.release(),
            "gcc": run(["gcc", "--version"]).stdout.splitlines()[0],
            "binutils": run(["ld", "--version"]).stdout.splitlines()[0],
            "python": platform.python_version(),
            "node": run(["node", "--version"]).stdout.strip(),
            "java": run(["java", "-version"]).stderr.splitlines()[0],
        },
        "source_bytes": {name: (ROOT / "src" / name).stat().st_size for name in SOURCES},
        "results": {},
        "unavailable_toolchains": {},
    }
    results = data["results"]

    run(["as", "-o", "hello.o", "hello.s"])
    for key, command in {
        "asm_default": ["ld", "-o", "hello_asm", "hello.o"],
        "asm_stripped": ["ld", "-s", "-o", "hello_asm_stripped", "hello.o"],
        "asm_tiny": ["ld", "-N", "-s", "-o", "hello_asm_tiny", "hello.o"],
    }.items():
        built = run(command)
        exe = command[command.index("-o") + 1]
        results[key] = {"build": command, **checked(["./" + exe]),
                        "build_warning": built.stderr.strip() or None}

    for key, command, exe in [
        ("c_default", ["gcc", "hello.c", "-o", "hello_c"], "hello_c"),
        ("c_dynamic_small", ["gcc", "-Os", "-s", "hello.c", "-o", "hello_c_small"], "hello_c_small"),
        ("c_static_small", ["gcc", "-static", "-Os", "-s", "hello.c", "-o", "hello_c_static"], "hello_c_static"),
        ("cpp_default", ["g++", "hello.cpp", "-o", "hello_cpp"], "hello_cpp"),
        ("cpp_dynamic_small", ["g++", "-Os", "-s", "hello.cpp", "-o", "hello_cpp_small"], "hello_cpp_small"),
        ("cpp_static_small", ["g++", "-static", "-Os", "-s", "hello.cpp", "-o", "hello_cpp_static"], "hello_cpp_static"),
    ]:
        run(command)
        entry = {"build": command, **checked(["./" + exe])}
        if "static" not in key:
            entry["shared_dependencies_bytes"] = dependency_sizes("./" + exe)
        results[key] = entry

    py = run(["python3", "hello.py"])
    assert py.stdout == EXPECTED and not py.stderr
    results["python_source"] = {"command": ["python3", "hello.py"],
                                 "size_bytes": (BUILD / "hello.py").stat().st_size,
                                 "requires_external_interpreter": True, "verified": True}
    py_app = BUILD / "py_app"
    py_app.mkdir(exist_ok=True)
    shutil.copyfile(BUILD / "hello.py", py_app / "__main__.py")
    pyz = BUILD / "hello.pyz"
    zipapp.create_archive(py_app, pyz, interpreter="/usr/bin/env python3")
    pyz.chmod(pyz.stat().st_mode | 0o111)
    results["python_zipapp"] = {"build": "python3 -m zipapp py_app -p '/usr/bin/env python3'",
                                 **checked(["./hello.pyz"]), "requires_external_interpreter": True}
    results["python_interpreter_file_bytes"] = Path(shutil.which("python3")).resolve().stat().st_size

    js = run(["node", "hello.js"])
    assert js.stdout == EXPECTED and not js.stderr
    results["node_source"] = {"command": ["node", "hello.js"],
                               "size_bytes": (BUILD / "hello.js").stat().st_size,
                               "requires_external_runtime": True, "verified": True}
    results["node_runtime_file_bytes"] = Path(shutil.which("node")).resolve().stat().st_size
    sea_config = {"main": "hello.js", "output": "sea-prep.blob",
                  "disableExperimentalSEAWarning": True}
    (BUILD / "sea-config.json").write_text(json.dumps(sea_config))
    run(["node", "--experimental-sea-config", "sea-config.json"])
    results["node_sea_preparation_only"] = {
        "size_bytes": (BUILD / "sea-prep.blob").stat().st_size,
        "runnable": False, "note": "Preparation blob only; no valid injected executable was produced."}

    java = run(["java", "Hello.java"])
    assert java.stdout == EXPECTED and not java.stderr
    results["java_source"] = {"command": ["java", "Hello.java"],
                               "size_bytes": (BUILD / "Hello.java").stat().st_size,
                               "requires_external_runtime": True, "verified": True}
    run(["java", "Compile.java"])
    results["java_class"] = {"command": ["java", "Hello"],
                              "size_bytes": (BUILD / "Hello.class").stat().st_size,
                              "requires_external_runtime": True, "verified": True}
    assert run(["java", "Hello"]).stdout == EXPECTED
    input_dir = BUILD / "java_input"
    input_dir.mkdir(exist_ok=True)
    jar = input_dir / "Hello.jar"
    with ZipFile(jar, "w", compression=ZIP_DEFLATED) as z:
        z.writestr("META-INF/MANIFEST.MF", "Manifest-Version: 1.0\nMain-Class: Hello\n\n")
        z.write(BUILD / "Hello.class", "Hello.class")
    assert run(["java", "-jar", str(jar)]).stdout == EXPECTED
    results["java_jar"] = {"size_bytes": jar.stat().st_size,
                            "requires_external_runtime": True, "verified": True}
    if args.include_jpackage:
        java_home = Path(shutil.which("java")).resolve().parent.parent
        dest = BUILD / "java_image"
        if (dest / "HelloWorld").exists():
            shutil.rmtree(dest / "HelloWorld")
        dest.mkdir(exist_ok=True)
        command = ["jpackage", "--type", "app-image", "--input", str(input_dir),
                   "--main-jar", "Hello.jar", "--name", "HelloWorld",
                   "--runtime-image", str(java_home), "--dest", str(dest)]
        run(command)
        assert run([str(dest / "HelloWorld" / "bin" / "HelloWorld")]).stdout == EXPECTED
        results["java_full_jre_app_image"] = {
            "size_bytes": directory_bytes(dest / "HelloWorld"), "verified": True,
            "includes_full_installed_jre": True,
            "build": [str(part).replace(str(ROOT) + "/", "") for part in command]}

    for name, choices in {
        "Zig": ["zig"], "Nim": ["nim"], "Rust": ["rustc"],
        "Crystal": ["crystal"], "Go": ["go"], "C#": ["dotnet", "mcs", "csc"],
        "Swift": ["swiftc"], "Dart": ["dart"], "Bun": ["bun"], "Deno": ["deno"],
    }.items():
        if not any(shutil.which(tool) for tool in choices):
            data["unavailable_toolchains"][name] = choices

    output = args.output if args.output.is_absolute() else ROOT / args.output
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n")
    count = sum(isinstance(v, dict) and v.get("verified", False) for v in results.values())
    print(f"Verified {count} runnable artifacts (including multiple variants per language); wrote {output}")


if __name__ == "__main__":
    main()
