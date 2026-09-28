# Rocky Linux VM 正式测量结果

测量时间（UTC）：`2026-09-28T06:36:45.778664+00:00`。构建目录：`/mnt/sdb/helloworld-test/build/formal/20260928T063645Z`。

所有有效项目均输出精确的 `Hello World\n`（12 B），stderr 为空，退出码为 0。

A 为工具生成的应用文件集合；B 为补齐依赖、通过 glibc 基线隔离验证的分发集合。
表中单位全部为精确字节 B。外部运行时的源码/class/JAR只列 A，B 的空值不等于零。

文件统计、基线、压缩与语义边界见 [测量标准](../METHODOLOGY.md)。版本与安装见 [VM 环境](../VM_SETUP.md)。

gzip 列是整个 B 集合的 tar+gzip9 下载归档；无 B 的项目则压缩 A。它与原始文件字节分开。

共 51 种配置，51 项通过；42 个分发集合通过隔离验证。

Assembly tiny-rwx 是极限配置附录；源码、字节码和 framework-dependent 行只是 A 口径参照。

| 项目 | 配置 | A 应用（B） | A 文件数 | B 分发（B） | B 文件数 | gzip（B） | 状态 |
|---|---|---:|---:|---:|---:|---:|---|
| Assembly | default | 8896 | 1 | 8896 | 1 | 463 | passed |
| Assembly | stripped | 8488 | 1 | 8488 | 1 | 343 | passed |
| Assembly | tiny-rwx | 456 | 1 | 456 | 1 | 283 | passed |
| C | default | 25792 | 1 | 25792 | 1 | 3026 | passed |
| C | size-dynamic | 21952 | 1 | 21952 | 1 | 2099 | passed |
| C | size-static | 1527184 | 1 | 1527184 | 1 | 328632 | passed |
| C++ | default | 26240 | 1 | 2440904 | 3 | 866236 | passed |
| C++ | size-dynamic | 21976 | 1 | 2436640 | 3 | 864451 | passed |
| C++ | size-static | 2904448 | 1 | 2904448 | 1 | 726898 | passed |
| Zig | Debug std.Io | 10744674 | 1 | 10744674 | 1 | 2190619 | passed |
| Zig | ReleaseSmall std.Io | 145216 | 1 | 145216 | 1 | 62414 | passed |
| Zig | ReleaseSmall libc puts | 4352 | 1 | 4352 | 1 | 1731 | passed |
| Nim | default ORC | 104664 | 1 | 104664 | 1 | 31986 | passed |
| Nim | release size ORC | 38720 | 1 | 38720 | 1 | 13218 | passed |
| Rust | default | 4506728 | 1 | 4614872 | 2 | 1199016 | passed |
| Rust | release | 4505792 | 1 | 4613936 | 2 | 1198675 | passed |
| Rust | release-stripped | 350392 | 1 | 458536 | 2 | 220631 | passed |
| Rust | size-abort | 292200 | 1 | 400344 | 2 | 197607 | passed |
| Crystal | default | 2101056 | 1 | 2209200 | 2 | 713796 | passed |
| Crystal | release stripped | 522352 | 1 | 630496 | 2 | 271814 | passed |
| Go | default | 2346729 | 1 | 2346729 | 1 | 1416596 | passed |
| Go | stripped | 1507488 | 1 | 1507488 | 1 | 681432 | passed |
| C# | Release framework-dependent | 4358 | 3 | — | — | 1997 | passed |
| C# | Release self-contained | 82607153 | 191 | 85021817 | 193 | 36141733 | passed |
| C# | Release self-contained trimmed | 23908099 | 29 | 26322763 | 31 | 10412904 | passed |
| C# | trimmed compressed single-file | 13051818 | 1 | 15466482 | 3 | 6900973 | passed |
| C# | NativeAOT Release | 1271056 | 1 | 1271056 | 1 | 612704 | passed |
| C# | NativeAOT size invariant | 1118960 | 1 | 1118960 | 1 | 546170 | passed |
| Swift | default | 22392 | 1 | 17181008 | 12 | 5181204 | passed |
| Swift | size-dynamic | 12632 | 1 | 16753328 | 11 | 5092104 | passed |
| Swift | size-static-stdlib | 6345896 | 1 | 6454040 | 2 | 2334181 | passed |
| Dart | source | 38 | 1 | — | — | 143 | passed |
| Dart | compile exe | 6501832 | 1 | 6501832 | 1 | 2674081 | passed |
| Python | source | 21 | 1 | — | — | 125 | passed |
| Python | zipapp | 141 | 1 | — | — | 199 | passed |
| Python | PyInstaller onedir | 13342827 | 38 | 13342925 | 42 | 5889724 | passed |
| Python | PyInstaller onefile | 5937360 | 1 | 6039912 | 2 | 5901380 | passed |
| Java | class | 411 | 1 | — | — | 377 | passed |
| Java | JAR | 738 | 1 | — | — | 665 | passed |
| Java | JAR + jlink java.base | 85183548 | 50 | 85286100 | 51 | 36816419 | passed |
| Java | JAR + jlink ALL-MODULE-PATH | 159405727 | 355 | 166517103 | 373 | 103760494 | passed |
| Java | jpackage java.base app-image | 86962394 | 55 | 87064946 | 56 | 37371454 | passed |
| Java | Native Image default | 4946600 | 1 | 5049152 | 2 | 1897446 | passed |
| Java | Native Image size | 4241840 | 1 | 4344392 | 2 | 1660992 | passed |
| Bun | JS source | 28 | 1 | — | — | 132 | passed |
| Deno | JS source | 28 | 1 | — | — | 132 | passed |
| Node.js | JS source | 28 | 1 | — | — | 132 | passed |
| Bun | compile | 81315296 | 1 | 81315296 | 1 | 36538539 | passed |
| Bun | compile minify | 81315296 | 1 | 81315296 | 1 | 36538535 | passed |
| Deno | compile | 104567752 | 1 | 104675896 | 2 | 34293647 | passed |
| Node.js | SEA | 126684352 | 1 | 129099016 | 3 | 43881596 | passed |

## 构建、依赖与边界

### asm-default

Linux write/exit syscall

- 内部压缩/解包：none
- 运行：`./hello`

```text
as hello.s -o hello.o
ld hello.o -o hello
```

### asm-stripped

Linux write/exit syscall

- 内部压缩/解包：none
- 运行：`./hello`

```text
as hello.s -o hello.o
ld -s hello.o -o hello
```

### asm-tiny-rwx

Linux write/exit syscall; RWX LOAD segment, appendix only

- 内部压缩/解包：none
- 运行：`./hello`

```text
as hello.s -o hello.o
ld -N -s hello.o -o hello
```

### c-default

puts

- 内部压缩/解包：none
- 运行：`./hello`

```text
gcc -march=x86-64 hello.c -o hello
```

### c-size-dynamic

puts

- 内部压缩/解包：none
- 运行：`./hello`

```text
gcc -march=x86-64 -Os -s hello.c -o hello
```

### c-size-static

puts

- 内部压缩/解包：none
- 运行：`./hello`

```text
gcc -march=x86-64 -static -Os -s -L/mnt/sdb/helloworld-test/toolchains/static-libs/usr/lib64 -L/mnt/sdb/helloworld-test/toolchains/static-libs/usr/lib/gcc/x86_64-redhat-linux/11 hello.c -o hello
```

### cpp-default

iostream; external libstdc++/libgcc counted in B when dynamic

- 内部压缩/解包：none
- 运行：`./hello`
- B 补齐：`lib/libstdc++.so.6`，来源 `/usr/lib64/libstdc++.so.6.0.29`
- B 补齐：`lib/libgcc_s.so.1`，来源 `/usr/lib64/libgcc_s-11-20221121.so.1`

```text
g++ -march=x86-64 hello.cpp -o hello
```

### cpp-size-dynamic

iostream; external libstdc++/libgcc counted in B when dynamic

- 内部压缩/解包：none
- 运行：`./hello`
- B 补齐：`lib/libstdc++.so.6`，来源 `/usr/lib64/libstdc++.so.6.0.29`
- B 补齐：`lib/libgcc_s.so.1`，来源 `/usr/lib64/libgcc_s-11-20221121.so.1`

```text
g++ -march=x86-64 -Os -s hello.cpp -o hello
```

### cpp-size-static

iostream; external libstdc++/libgcc counted in B when dynamic

- 内部压缩/解包：none
- 运行：`./hello`

```text
g++ -march=x86-64 -static -Os -s -L/mnt/sdb/helloworld-test/toolchains/static-libs/usr/lib64 -L/mnt/sdb/helloworld-test/toolchains/static-libs/usr/lib/gcc/x86_64-redhat-linux/11 hello.cpp -o hello
```

### zig-debug

Debug std.Io

- 内部压缩/解包：none
- 运行：`./hello`

```text
zig build-exe hello.zig -target x86_64-linux -mcpu baseline -femit-bin=hello
```

### zig-small

ReleaseSmall std.Io

- 内部压缩/解包：none
- 运行：`./hello`

```text
zig build-exe hello.zig -target x86_64-linux -mcpu baseline -O ReleaseSmall -fstrip -femit-bin=hello
```

### zig-libc-small

Different output API; separate source

- 内部压缩/解包：none
- 运行：`./hello`

```text
zig build-exe hello-libc.zig -lc -target x86_64-linux-gnu -mcpu baseline -O ReleaseSmall -fstrip -femit-bin=hello
```

### nim-default

default ORC

- 内部压缩/解包：none
- 运行：`./hello`

```text
nim c --mm:orc --nimcache:nimcache --out:hello hello.nim
```

### nim-small

release size ORC

- 内部压缩/解包：none
- 运行：`./hello`

```text
nim c --mm:orc -d:release --opt:size --passC:-march=x86-64 --passC:-Os --passL:-s --nimcache:nimcache --out:hello hello.nim
```

### rust-default

default panic=unwind

- 内部压缩/解包：none
- 运行：`./hello`
- B 补齐：`lib/libgcc_s.so.1`，来源 `/usr/lib64/libgcc_s-11-20221121.so.1`

```text
rustc -C target-cpu=x86-64 hello.rs -o hello
```

### rust-release

default panic=unwind

- 内部压缩/解包：none
- 运行：`./hello`
- B 补齐：`lib/libgcc_s.so.1`，来源 `/usr/lib64/libgcc_s-11-20221121.so.1`

```text
rustc -C target-cpu=x86-64 -C opt-level=3 hello.rs -o hello
```

### rust-release-stripped

default panic=unwind

- 内部压缩/解包：none
- 运行：`./hello`
- B 补齐：`lib/libgcc_s.so.1`，来源 `/usr/lib64/libgcc_s-11-20221121.so.1`

```text
rustc -C target-cpu=x86-64 -C opt-level=3 -C strip=symbols hello.rs -o hello
```

### rust-size-abort

panic=abort changes panic behavior

- 内部压缩/解包：none
- 运行：`./hello`
- B 补齐：`lib/libgcc_s.so.1`，来源 `/usr/lib64/libgcc_s-11-20221121.so.1`

```text
rustc -C target-cpu=x86-64 -C opt-level=z -C strip=symbols -C panic=abort -C lto=fat -C codegen-units=1 hello.rs -o hello
```

### crystal-default

default

- 内部压缩/解包：none
- 运行：`./hello`
- B 补齐：`lib/libgcc_s.so.1`，来源 `/usr/lib64/libgcc_s-11-20221121.so.1`

```text
crystal build hello.cr -o hello
```

### crystal-release

release stripped

- 内部压缩/解包：none
- 运行：`./hello`
- B 补齐：`lib/libgcc_s.so.1`，来源 `/usr/lib64/libgcc_s-11-20221121.so.1`

```text
crystal build --release --no-debug hello.cr -o hello
strip --strip-unneeded hello
```

### go-default

default

- 内部压缩/解包：none
- 运行：`./hello`

```text
go build -o hello hello.go
```

### go-stripped

stripped

- 内部压缩/解包：none
- 运行：`./hello`

```text
go build -trimpath '-ldflags=-s -w' -o hello hello.go
```

### csharp-framework

External .NET runtime; DLL/config directory

- 内部压缩/解包：none
- 运行：`dotnet Hello.dll`

```text
dotnet publish Hello.csproj -c Release -r linux-x64 -o publish --self-contained false -p:UseAppHost=false
```

### csharp-selfcontained

Directory deployment, full .NET runtime

- 内部压缩/解包：none
- 运行：`./Hello`
- B 补齐：`lib/libstdc++.so.6`，来源 `/usr/lib64/libstdc++.so.6.0.29`
- B 补齐：`lib/libgcc_s.so.1`，来源 `/usr/lib64/libgcc_s-11-20221121.so.1`
- ldd 单独扫描未解析 `liblttng-ust.so.0`：not shipped; not exercised by this Hello World run

```text
dotnet publish Hello.csproj -c Release -r linux-x64 -o publish --self-contained true
```

### csharp-trimmed

Trimming changes reflection availability

- 内部压缩/解包：none
- 运行：`./Hello`
- B 补齐：`lib/libstdc++.so.6`，来源 `/usr/lib64/libstdc++.so.6.0.29`
- B 补齐：`lib/libgcc_s.so.1`，来源 `/usr/lib64/libgcc_s-11-20221121.so.1`
- ldd 单独扫描未解析 `liblttng-ust.so.0`：not shipped; not exercised by this Hello World run

```text
dotnet publish Hello.csproj -c Release -r linux-x64 -o publish --self-contained true -p:PublishTrimmed=true
```

### csharp-singlefile

Native libraries extracted to /tmp; validation covers this output path only

- 内部压缩/解包：internal compression + runtime extraction
- 运行：`./Hello`
- B 补齐：`lib/libgcc_s.so.1`，来源 `/usr/lib64/libgcc_s-11-20221121.so.1`
- B 补齐：`lib/libstdc++.so.6`，来源 `/usr/lib64/libstdc++.so.6.0.29`

```text
dotnet publish Hello.csproj -c Release -r linux-x64 -o publish --self-contained true -p:PublishTrimmed=true -p:PublishSingleFile=true -p:IncludeNativeLibrariesForSelfExtract=true -p:EnableCompressionInSingleFile=true
```

### csharp-aot

External .dbg excluded; NativeAOT has reflection/dynamic-code limits

- 内部压缩/解包：none
- 运行：`./Hello`

```text
dotnet publish Hello.csproj -c Release -r linux-x64 -o publish --self-contained true -p:PublishAot=true
```

### csharp-aot-small-invariant

Size preference + invariant globalization; culture-specific behavior is restricted; external .dbg excluded

- 内部压缩/解包：none
- 运行：`./Hello`

```text
dotnet publish Hello.csproj -c Release -r linux-x64 -o publish --self-contained true -p:PublishAot=true -p:OptimizationPreference=Size -p:InvariantGlobalization=true
```

### swift-default

Swift shared runtime counted in B

- 内部压缩/解包：none
- 运行：`./hello`
- B 补齐：`lib/libswiftSwiftOnoneSupport.so`，来源 `/mnt/sdb/helloworld-test/toolchains/swift/6.3.3/usr/lib/swift/linux/libswiftSwiftOnoneSupport.so`
- B 补齐：`lib/libswiftCore.so`，来源 `/mnt/sdb/helloworld-test/toolchains/swift/6.3.3/usr/lib/swift/linux/libswiftCore.so`
- B 补齐：`lib/libswift_Concurrency.so`，来源 `/mnt/sdb/helloworld-test/toolchains/swift/6.3.3/usr/lib/swift/linux/libswift_Concurrency.so`
- B 补齐：`lib/libswift_StringProcessing.so`，来源 `/mnt/sdb/helloworld-test/toolchains/swift/6.3.3/usr/lib/swift/linux/libswift_StringProcessing.so`
- B 补齐：`lib/libswift_RegexParser.so`，来源 `/mnt/sdb/helloworld-test/toolchains/swift/6.3.3/usr/lib/swift/linux/libswift_RegexParser.so`
- B 补齐：`lib/libstdc++.so.6`，来源 `/usr/lib64/libstdc++.so.6.0.29`
- B 补齐：`lib/libgcc_s.so.1`，来源 `/usr/lib64/libgcc_s-11-20221121.so.1`
- B 补齐：`lib/libdispatch.so`，来源 `/mnt/sdb/helloworld-test/toolchains/swift/6.3.3/usr/lib/swift/linux/libdispatch.so`
- B 补齐：`lib/libswift_Builtin_float.so`，来源 `/mnt/sdb/helloworld-test/toolchains/swift/6.3.3/usr/lib/swift/linux/libswift_Builtin_float.so`
- B 补齐：`lib/libswiftGlibc.so`，来源 `/mnt/sdb/helloworld-test/toolchains/swift/6.3.3/usr/lib/swift/linux/libswiftGlibc.so`
- B 补齐：`lib/libBlocksRuntime.so`，来源 `/mnt/sdb/helloworld-test/toolchains/swift/6.3.3/usr/lib/swift/linux/libBlocksRuntime.so`

```text
swiftc -target x86_64-unknown-linux-gnu -module-cache-path /mnt/sdb/helloworld-test/cache/swift-modules hello.swift -o hello
```

### swift-size-dynamic

Swift shared runtime counted in B

- 内部压缩/解包：none
- 运行：`./hello`
- B 补齐：`lib/libswiftCore.so`，来源 `/mnt/sdb/helloworld-test/toolchains/swift/6.3.3/usr/lib/swift/linux/libswiftCore.so`
- B 补齐：`lib/libswift_Concurrency.so`，来源 `/mnt/sdb/helloworld-test/toolchains/swift/6.3.3/usr/lib/swift/linux/libswift_Concurrency.so`
- B 补齐：`lib/libswift_StringProcessing.so`，来源 `/mnt/sdb/helloworld-test/toolchains/swift/6.3.3/usr/lib/swift/linux/libswift_StringProcessing.so`
- B 补齐：`lib/libswift_RegexParser.so`，来源 `/mnt/sdb/helloworld-test/toolchains/swift/6.3.3/usr/lib/swift/linux/libswift_RegexParser.so`
- B 补齐：`lib/libstdc++.so.6`，来源 `/usr/lib64/libstdc++.so.6.0.29`
- B 补齐：`lib/libgcc_s.so.1`，来源 `/usr/lib64/libgcc_s-11-20221121.so.1`
- B 补齐：`lib/libdispatch.so`，来源 `/mnt/sdb/helloworld-test/toolchains/swift/6.3.3/usr/lib/swift/linux/libdispatch.so`
- B 补齐：`lib/libswift_Builtin_float.so`，来源 `/mnt/sdb/helloworld-test/toolchains/swift/6.3.3/usr/lib/swift/linux/libswift_Builtin_float.so`
- B 补齐：`lib/libswiftGlibc.so`，来源 `/mnt/sdb/helloworld-test/toolchains/swift/6.3.3/usr/lib/swift/linux/libswiftGlibc.so`
- B 补齐：`lib/libBlocksRuntime.so`，来源 `/mnt/sdb/helloworld-test/toolchains/swift/6.3.3/usr/lib/swift/linux/libBlocksRuntime.so`

```text
swiftc -target x86_64-unknown-linux-gnu -module-cache-path /mnt/sdb/helloworld-test/cache/swift-modules -Osize hello.swift -o hello
strip --strip-unneeded hello
```

### swift-size-static-stdlib

-static-stdlib does not mean all system libraries are static

- 内部压缩/解包：none
- 运行：`./hello`
- B 补齐：`lib/libgcc_s.so.1`，来源 `/usr/lib64/libgcc_s-11-20221121.so.1`
- 修正前构建/失败证据保留于 JSON 的 `superseded_attempts` 路径。

```text
swiftc -target x86_64-unknown-linux-gnu -module-cache-path /mnt/sdb/helloworld-test/cache/swift-modules -Osize -static-stdlib -L/mnt/sdb/helloworld-test/toolchains/static-libs/usr/lib/gcc/x86_64-redhat-linux/11 hello.swift -o hello
strip --strip-unneeded hello
```

### dart-source

External Dart runtime

- 内部压缩/解包：none
- 运行：`dart hello.dart`

```text
```

### dart-aot

Dart AOT executable

- 内部压缩/解包：none
- 运行：`./hello`

```text
dart compile exe hello.dart -o hello
```

### python-source

External Python runtime

- 内部压缩/解包：none
- 运行：`python3 hello.py`

```text
```

### python-zipapp

ZIP container; external Python runtime

- 内部压缩/解包：none
- 运行：`python3 hello.pyz`

```text
python3 -c 'from pathlib import Path; import zipapp; Path('"'"'zipapp'"'"').mkdir(); Path('"'"'zipapp/__main__.py'"'"').write_bytes(Path('"'"'hello.py'"'"').read_bytes()); zipapp.create_archive('"'"'zipapp'"'"', '"'"'hello.pyz'"'"')'
```

### python-onedir

Bootloader + Python runtime; no UPX

- 内部压缩/解包：internal PYZ compression
- 运行：`./hello`
- B 补齐：`lib/libz.so.1`，来源 `/mnt/sdb/helloworld-test/build/formal/20260928T063645Z/python-onedir/deployment/_internal/libz.so.1`
- B 补齐：`lib/libcrypto.so.3`，来源 `/mnt/sdb/helloworld-test/build/formal/20260928T063645Z/python-onedir/deployment/_internal/libcrypto.so.3`
- B 补齐：`lib/libbz2.so.1`，来源 `/mnt/sdb/helloworld-test/build/formal/20260928T063645Z/python-onedir/deployment/_internal/libbz2.so.1`
- B 补齐：`lib/liblzma.so.5`，来源 `/mnt/sdb/helloworld-test/build/formal/20260928T063645Z/python-onedir/deployment/_internal/liblzma.so.5`
- 修正前构建/失败证据保留于 JSON 的 `superseded_attempts` 路径。

```text
pyinstaller --onedir --noconfirm --clean --noupx --name hello hello.py
```

### python-onefile

Bootloader + Python runtime; no UPX

- 内部压缩/解包：internal PYZ compression + runtime extraction
- 运行：`./hello`
- B 补齐：`lib/libz.so.1`，来源 `/usr/lib64/libz.so.1.2.11`
- 修正前构建/失败证据保留于 JSON 的 `superseded_attempts` 路径。

```text
pyinstaller --onefile --noconfirm --clean --noupx --name hello hello.py
```

### java-class

External JVM

- 内部压缩/解包：none
- 运行：`java Hello`

```text
javac -J-Djava.io.tmpdir=/mnt/sdb/helloworld-test/tmp Hello.java
```

### java-jar

External JVM; JAR uses ZIP compression

- 内部压缩/解包：JAR ZIP compression
- 运行：`java -jar Hello.jar`

```text
javac -J-Djava.io.tmpdir=/mnt/sdb/helloworld-test/tmp Hello.java
jar --create --file Hello.jar --main-class Hello Hello.class
```

### java-jlink-base

Module set differs; full runtime directory counted

- 内部压缩/解包：jlink zip-6 resources + JAR
- 运行：`./runtime/bin/java -jar Hello.jar`
- B 补齐：`lib/libz.so.1`，来源 `/usr/lib64/libz.so.1.2.11`
- ldd 单独扫描未解析 `libjvm.so`：bundled; runtime loader resolves it during successful execution；已打包 `runtime/lib/server/libjvm.so`

```text
javac -J-Djava.io.tmpdir=/mnt/sdb/helloworld-test/tmp Hello.java
jar --create --file Hello.jar --main-class Hello Hello.class
jlink -J-Djava.io.tmpdir=/mnt/sdb/helloworld-test/tmp --add-modules java.base --strip-debug --no-header-files --no-man-pages --compress=zip-6 --output runtime
```

### java-jlink-all

Module set differs; full runtime directory counted

- 内部压缩/解包：jlink zip-6 resources + JAR
- 运行：`./runtime/bin/java -jar Hello.jar`
- B 补齐：`lib/libz.so.1`，来源 `/usr/lib64/libz.so.1.2.11`
- B 补齐：`lib/libX11.so.6`，来源 `/usr/lib64/libX11.so.6.4.0`
- B 补齐：`lib/libXext.so.6`，来源 `/usr/lib64/libXext.so.6.4.0`
- B 补齐：`lib/libXi.so.6`，来源 `/usr/lib64/libXi.so.6.1.0`
- B 补齐：`lib/libXrender.so.1`，来源 `/usr/lib64/libXrender.so.1.3.0`
- B 补齐：`lib/libXtst.so.6`，来源 `/usr/lib64/libXtst.so.6.1.0`
- B 补齐：`lib/libxcb.so.1`，来源 `/usr/lib64/libxcb.so.1.1.0`
- B 补齐：`lib/libXau.so.6`，来源 `/usr/lib64/libXau.so.6.0.0`
- B 补齐：`lib/libfreetype.so.6`，来源 `/usr/lib64/libfreetype.so.6.17.4`
- B 补齐：`lib/libbz2.so.1`，来源 `/usr/lib64/libbz2.so.1.0.8`
- B 补齐：`lib/libpng16.so.16`，来源 `/usr/lib64/libpng16.so.16.37.0`
- B 补齐：`lib/libharfbuzz.so.0`，来源 `/usr/lib64/libharfbuzz.so.0.20704.0`
- B 补齐：`lib/libbrotlidec.so.1`，来源 `/usr/lib64/libbrotlidec.so.1.0.9`
- B 补齐：`lib/libglib-2.0.so.0`，来源 `/usr/lib64/libglib-2.0.so.0.6800.4`
- B 补齐：`lib/libgraphite2.so.3`，来源 `/usr/lib64/libgraphite2.so.3.2.1`
- B 补齐：`lib/libbrotlicommon.so.1`，来源 `/usr/lib64/libbrotlicommon.so.1.0.9`
- B 补齐：`lib/libpcre.so.1`，来源 `/usr/lib64/libpcre.so.1.2.12`
- B 补齐：`lib/libasound.so.2`，来源 `/usr/lib64/libasound.so.2.0.0`
- ldd 单独扫描未解析 `libjvm.so`：bundled; runtime loader resolves it during successful execution；已打包 `runtime/lib/server/libjvm.so`
- 修正前构建/失败证据保留于 JSON 的 `superseded_attempts` 路径。

```text
javac -J-Djava.io.tmpdir=/mnt/sdb/helloworld-test/tmp Hello.java
jar --create --file Hello.jar --main-class Hello Hello.class
jlink -J-Djava.io.tmpdir=/mnt/sdb/helloworld-test/tmp --module-path /mnt/sdb/helloworld-test/toolchains/java/jmods --add-modules ALL-MODULE-PATH --strip-debug --no-header-files --no-man-pages --compress=zip-6 --output runtime
```

### java-jpackage

Entire launcher/app/runtime image, not launcher alone

- 内部压缩/解包：jlink zip-6 resources + JAR
- 运行：`./bin/HelloJava`
- B 补齐：`lib/libz.so.1`，来源 `/usr/lib64/libz.so.1.2.11`
- ldd 单独扫描未解析 `libjvm.so`：bundled; runtime loader resolves it during successful execution；已打包 `lib/runtime/lib/server/libjvm.so`

```text
javac -J-Djava.io.tmpdir=/mnt/sdb/helloworld-test/tmp Hello.java
python3 -c 'from pathlib import Path; Path('"'"'input'"'"').mkdir()'
jar --create --file input/Hello.jar --main-class Hello Hello.class
jpackage -J-Djava.io.tmpdir=/mnt/sdb/helloworld-test/tmp --type app-image --input input --main-jar Hello.jar --name HelloJava --add-modules java.base --jlink-options '--strip-debug --no-header-files --no-man-pages --compress=zip-6' --dest package
```

### java-native-default

Closed-world AOT; no JVM; --no-fallback

- 内部压缩/解包：none
- 运行：`./hello`
- B 补齐：`lib/libz.so.1`，来源 `/usr/lib64/libz.so.1.2.11`
- 修正前构建/失败证据保留于 JSON 的 `superseded_attempts` 路径。

```text
javac -J-Djava.io.tmpdir=/mnt/sdb/helloworld-test/tmp Hello.java
native-image --no-fallback -march=x86-64 -J-Xmx3g -J-Djava.io.tmpdir=/mnt/sdb/helloworld-test/tmp -H:NativeLinkerOption=-L/mnt/sdb/helloworld-test/toolchains/static-libs/usr/lib/gcc/x86_64-redhat-linux/11 Hello hello
```

### java-native-size

Closed-world AOT; no JVM; --no-fallback

- 内部压缩/解包：none
- 运行：`./hello`
- B 补齐：`lib/libz.so.1`，来源 `/usr/lib64/libz.so.1.2.11`
- 修正前构建/失败证据保留于 JSON 的 `superseded_attempts` 路径。

```text
javac -J-Djava.io.tmpdir=/mnt/sdb/helloworld-test/tmp Hello.java
native-image --no-fallback -march=x86-64 -J-Xmx3g -J-Djava.io.tmpdir=/mnt/sdb/helloworld-test/tmp -H:NativeLinkerOption=-L/mnt/sdb/helloworld-test/toolchains/static-libs/usr/lib/gcc/x86_64-redhat-linux/11 -Os Hello hello
strip --strip-unneeded hello
```

### bun-source

External Bun runtime

- 内部压缩/解包：none
- 运行：`bun hello.js`

```text
```

### deno-source

External Deno runtime

- 内部压缩/解包：none
- 运行：`deno hello.js`

```text
```

### node-source

External Node.js runtime

- 内部压缩/解包：none
- 运行：`node hello.js`

```text
```

### bun-compile

Embedded Bun runtime

- 内部压缩/解包：none
- 运行：`./hello`

```text
bun build --compile hello.js --outfile hello
```

### bun-minify

Embedded Bun runtime; JS minified

- 内部压缩/解包：none
- 运行：`./hello`

```text
bun build --compile --minify hello.js --outfile hello
```

### deno-compile

Embedded Deno runtime

- 内部压缩/解包：none
- 运行：`./hello`
- B 补齐：`lib/libgcc_s.so.1`，来源 `/usr/lib64/libgcc_s-11-20221121.so.1`

```text
deno compile --output hello hello.js
```

### node-sea

Official Node SEA blob + copied Node executable

- 内部压缩/解包：none
- 运行：`./hello`
- B 补齐：`lib/libstdc++.so.6`，来源 `/usr/lib64/libstdc++.so.6.0.29`
- B 补齐：`lib/libgcc_s.so.1`，来源 `/usr/lib64/libgcc_s-11-20221121.so.1`

```text
python3 -c 'import json,shutil; from pathlib import Path; Path('"'"'sea.json'"'"').write_text(json.dumps(dict(main='"'"'hello.js'"'"',output='"'"'sea.blob'"'"',disableExperimentalSEAWarning=True))); shutil.copy2(shutil.which('"'"'node'"'"'), '"'"'hello'"'"')'
node --experimental-sea-config sea.json
postject hello NODE_SEA_BLOB sea.blob --sentinel-fuse NODE_SEA_FUSE_fce680ab2cc467b6e072b8b5df1996b2
```

## 原始证据

- [JSON](2026-09-28-rocky9-measurements.json)：源文件与产物哈希、版本、完整 argv、构建日志、ELF/ldd 依赖、隔离验证、基线清单。
- [CSV](2026-09-28-rocky9-measurements.csv)：可直接分析的精确整数。
- VM 数据盘保留每个项目的 application/、deployment/、归档和构建日志；JSON 记录绝对位置。

最终产物审计：GNU find 的文件字节数与 sha256sum 独立复核通过，51 项、16 个项目、42 个隔离分发集合。
