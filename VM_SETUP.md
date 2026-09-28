# 现有 VM：工具链安装与空间边界

本文件记录正式体积实验之前的环境准备。安装验收和正式实验结果分别保存，不能把安装包、SDK 目录或验收构建当作 Hello World 的分发体积。

## 已确认的环境

- 检查日期：2026-09-28。
- VM：Rocky Linux 9.2 (Blue Onyx)，x86-64，VMware 虚拟化。
- 内核：`5.14.0-284.30.1.el9_2.x86_64`。
- VM 暴露的 CPU：Intel Xeon Silver 4210 @ 2.20 GHz，12 个逻辑处理器；这不是此前检查的 Windows PC 的 CPU。
- 内存：约 7.5 GiB；交换空间约 4 GiB。
- 系统盘：`/dev/mapper/rl-root`，XFS，约 35 GiB；准备前约 23 GiB 已用，剩余约 12 GiB。
- 数据盘：`/dev/sdb` 挂载 `/mnt/sdb`，XFS，约 60 GiB；准备前约 7.4 GiB 已用，剩余约 53 GiB；挂载选项允许执行程序。
- 共享源码：`/home/dev/common/helloworld-test`，通过 CIFS 挂载 Windows 工作区。
- 初始仓库提交：`08d1f77074f9ad08c5fde9337e8e3ef301182c11`。

正式构建在数据盘的 XFS 目录进行，避免 CIFS 的权限、符号链接和文件元数据行为参与构建。源码和最终文本/JSON 报告保存在共享仓库。

## 非系统分区安装是否可行

可以。软件不要求与操作系统安装在同一分区；实际约束是挂载存在、允许执行、CPU/ABI 匹配，以及所需系统库可用。SDK 可以放在数据盘，但 SDK、下载缓存、包缓存、编译缓存和临时文件需要分别处理。

| 工具 | 安装到数据盘的方法 | 官方依据 |
| --- | --- | --- |
| 汇编、C、C++ | 复用已有 GNU Binutils 和 GCC/G++；新增静态库单独解包到私有前缀 | [GCC 链接选项](https://gcc.gnu.org/onlinedocs/gcc/Link-Options.html) |
| Zig | 官方归档解压到专用目录；设置 PATH 与 Zig 缓存目录 | [Zig 安装说明](https://ziglang.org/learn/getting-started/)明确允许放在任意目录 |
| Nim | 官方 Linux 二进制归档解压；复用 GCC；构建时明确 nimcache | [Nim 安装说明](https://nim-lang.org/install_unix.html) |
| Rust | 设置 `CARGO_HOME`、`RUSTUP_HOME`；按所需组件安装工具链 | [rustup 安装位置](https://rust-lang.github.io/rustup/installation/) |
| Crystal | 官方 bundled 二进制归档解压，保留自带库的相对目录结构 | [Crystal tarball 安装说明](https://crystal-lang.org/install/from_targz/) |
| Go | 官方归档解压，配置 PATH、GOPATH、GOCACHE、GOMODCACHE | [Go 安装说明](https://go.dev/doc/install)、[Go 环境变量](https://pkg.go.dev/cmd/go#hdr-Environment_variables) |
| C#/.NET | SDK 官方 tarball 解压；设置 DOTNET_ROOT、DOTNET_CLI_HOME 和 NuGet 缓存 | [Microsoft 安装脚本文档](https://learn.microsoft.com/en-us/dotnet/core/tools/dotnet-install-script)支持自定义 install-dir，并说明依赖库另行处理 |
| Swift | Swiftly 的 HOME、BIN、TOOLCHAINS 路径均指向专用目录；选择 UBI 9 发行包在 Rocky 9.2 上验证 | [Swift Linux 安装](https://www.swift.org/install/linux/)、[Swiftly 入门](https://www.swift.org/swiftly/documentation/swiftly/getting-started/) |
| Dart | 官方 SDK zip 解压，设置 PATH 与 PUB_CACHE | [Dart SDK archive](https://dart.dev/get-dart/archive) |
| Python | 复用系统 Python；在数据盘建立 venv 并安装 PyInstaller，pip 缓存也在数据盘 | [Python venv](https://docs.python.org/3.9/library/venv.html)、[PyInstaller 安装](https://pyinstaller.org/en/stable/installation.html) |
| Java | 复用已有 JDK 11 作历史环境；另外解压 GraalVM Community JDK，补齐 jpackage 与 Native Image | [GraalVM Linux 安装](https://www.graalvm.org/latest/getting-started/linux/) |
| Bun | 官方 zip 解压；配置 BUN_INSTALL 与安装缓存 | [Bun 安装说明](https://bun.com/docs/installation) |
| Deno | 官方 zip 解压；配置 DENO_INSTALL、DENO_DIR | [Deno 安装与缓存位置](https://docs.deno.com/runtime/getting_started/installation/) |
| Node.js | 复用系统 Node 16 作历史环境；解压支持 SEA 的 Node 24 LTS；postject 安装到自定义 npm prefix | [Node 下载](https://nodejs.org/en/download)、[SEA 文档](https://nodejs.org/docs/latest-v24.x/api/single-executable-applications.html) |

VM 本身已存在 GCC/G++ 11.3.1、Binutils 2.35.2、glibc 2.34、Python 3.9.16、Node 16.20.2、OpenJDK 11.0.21。它们保留在原路径。Node 的 SEA 功能与 Java 的 jpackage/Native Image 功能缺失，所以并行安装所需版本，不替换系统版本。

## 目录与使用方式

专用根目录：`/mnt/sdb/helloworld-test/`。

| 子目录 | 用途 |
| --- | --- |
| `toolchains/` | 新装 SDK、编译器、Python venv、npm 工具与私有静态库 |
| `bin/` | 专用工具命令的符号链接 |
| `downloads/` | 下载归档及官方 RPM；保留供复现 |
| `cache/` | 各语言包管理器、编译器和运行器缓存 |
| `tmp/` | 安装、编译、打包、运行解包的临时文件 |
| `build/` | 安装验收与后续实验的构建目录 |
| `logs/` | 安装、下载、验收日志 |
| `config/`、`data/` | 实验工具的 XDG 配置和数据 |

在 VM 中显式启用环境：

```bash
source /home/dev/common/helloworld-test/scripts/vm-env.sh
```

不修改 `/root/.bashrc`、系统 PATH 或系统工具链。启用该环境之后，专用 PATH 优先使用实验所需版本；未启用时继续使用 VM 原有工具。

`vm-env.sh` 配置各工具支持的安装与缓存变量，不重定义 HOME。必须在每次构建和运行时加载。Nim 使用显式 `--nimcache`，Swift 使用显式 `-module-cache-path`；Java 工具需要在构建命令中指定 `-J-Djava.io.tmpdir=...`，Java 运行器使用 `-Djava.io.tmpdir=...`，不能仅依赖 TMPDIR。其他新增工具也应先核对自身缓存和临时目录约定。

SDK 安装在数据盘不意味着生成的程序不依赖系统库。正式实验必须记录动态依赖、语言运行时是否随包分发、CPU 目标和构建参数。VM 上已经安装的库也不能充当“分发包完整”的证明。

## 安装过程与复现记录

- 官方归档的版本、URL 和官方校验值解析一次后写入数据盘 `toolchain-lock.json`，重试时沿用，不漂移到新版本。
- 能取得上游 SHA-256/SHA-512 的归档均做校验；所有下载额外记录实际 SHA-256。Swift 安装由官方 Swiftly 完成。
- VM 对部分站点下载缓慢时，通过 Windows PC 获取归档，再经 SSH 流式写入数据盘；不在 Windows 系统目录或 VM 系统目录暂存归档。
- Dart 的网络回退使用 Flutter 官方文档列出的 CFUG 镜像，仍与 Google 官方发布的 SHA-256 比对：[中国网络访问说明](https://docs.flutter.dev/community/china)。
- 静态库使用匹配现有版本的 Rocky 9.2 官方 RPM：`glibc-static-2.34-60.el9_2.7`、`libstdc++-static-11.3.1-4.3.el9`。验证 RPM 签名后，只解包到 `toolchains/static-libs/`，不运行系统包安装或升级。
- 私有 `libm.a` 是包含绝对系统路径的文本链接脚本。将其中的 `/usr/lib64/` 前缀去掉，使其引用同目录中的归档；原文保留为 `libm.a.upstream`，实际静态库归档未改动。[GNU ld 文件搜索说明](https://sourceware.org/binutils/docs/ld/File-Commands.html)
- 正式实验中使用这些私有静态库时，完整保留链接搜索目录；不能隐藏该条件。

安装验收脚本 `scripts/verify-vm-setup.py` 的目的，是验证工具可以构建并运行程序。它不记录供排名使用的体积。其中 Zig 使用 libc puts 仅验证编译链可用；正式实验应另行确定标准输出写法及 libc 依赖口径。

## 已完成的安装验收

2026-09-28，21 项验收全部通过，覆盖原帖的 16 项以及若干发布方式。每项均实际运行，标准输出精确为 12 个字节的 `Hello World\n`，标准错误为空，退出码为 0。

| 原帖项目 | 实际使用版本 | 工具位置 |
| --- | --- | --- |
| 汇编 | GNU Binutils 2.35.2 | 原有 `/usr/bin/as`、`/usr/bin/ld` |
| Zig | 0.16.0 | 数据盘 `toolchains/zig` |
| C | GCC 11.3.1 | 原有 `/usr/bin/gcc` |
| C++ | G++ 11.3.1 | 原有 `/usr/bin/g++` |
| Nim | 2.2.12 | 数据盘 `toolchains/nim` |
| Rust | rustc 1.98.1、cargo 1.98.1 | 数据盘 `toolchains/rustup`、`toolchains/cargo` |
| Crystal | 1.21.1 | 数据盘 `toolchains/crystal` |
| Go | 1.27.1 | 数据盘 `toolchains/go` |
| C# | .NET SDK 10.0.401、运行时 10.0.12 | 数据盘 `toolchains/dotnet` |
| Swift | 6.3.3；Swiftly 1.2.0 | 数据盘 `toolchains/swift`、`toolchains/swiftly` |
| Dart | 3.13.4 | 数据盘 `toolchains/dart` |
| Python | 3.9.16；PyInstaller 6.22.3 | 原有 `/usr/bin/python3`；打包器在数据盘 `toolchains/python-packaging` |
| Java | GraalVM Community 25.4.4.1.1、JDK 25.0.4.1.1 | 数据盘 `toolchains/java`；原有 JDK 11 保留 |
| Bun | 1.4.2 | 数据盘 `toolchains/bun` |
| Deno | 2.9.7 | 数据盘 `toolchains/deno` |
| Node.js | 24.21.0；postject 1.0.0-alpha.6 | 数据盘 `toolchains/node`、`toolchains/npm`；原有 Node 16 保留 |

额外验收包括 C/C++ 静态链接、C# self-contained 与 Native AOT、Java jpackage 应用目录与 Native Image、Python PyInstaller 单文件、Bun/Deno 编译单文件、Node SEA 注入单文件。Native AOT 所用 Clang 21.0.0 来自数据盘内的 Swift 工具链。

虚拟化存储故障中断后，Dart 的一个 SDK 文件和完成标记为空。已复核归档哈希并重新解压，随后 Dart AOT 编译运行通过。其余存储归档也全部重新检查了校验值。验收没有发现其他阻碍这些构建的损坏。

空间记录采用 GiB（1 GiB = 2^30 B），目录磁盘占用来自 `du -sB1`，与后续测量产物逻辑字节数的口径不同：

- SDK、工具及私有库：约 **8.1 GiB**。
- 专用目录合计，包括下载、缓存和验收产物：约 **10.5 GiB**。
- 数据分区剩余：约 **42.2 GiB**；系统分区剩余：约 **11.8 GiB**。
- 已删除约 184 MiB 的中断下载片段；保留完整且经过校验的归档。
- 没有安装或升级系统 RPM 包。操作系统日志、共享内存和原有系统运行时自身的少量临时状态仍可能写入系统分区，不能把这解释为系统盘完全零写入。

完整版本、路径、构建命令、校验记录及空间数据见：

- [安装验收 JSON](results/2026-09-28-rocky9-vm-setup.json)
- [工具下载版本与校验锁](results/2026-09-28-toolchain-lock.json)

这些是安装可用性结果，运行发生在已有依赖的 VM 上。随后完成的正式测量另见 [正式报告](results/2026-09-28-rocky9-report.md) 与 [测量标准](METHODOLOGY.md)，其中分发集合经过限定 glibc 基线的隔离运行验证。

脚本入口：

```bash
source /home/dev/common/helloworld-test/scripts/vm-env.sh
python3 /home/dev/common/helloworld-test/scripts/verify-vm-setup.py
# 修复后仅重试指定项，保留其余记录：
python3 /home/dev/common/helloworld-test/scripts/verify-vm-setup.py --only cpp_static,dart
python3 /home/dev/common/helloworld-test/scripts/finalize-vm-setup.py
```

原有 `scripts/run.py` 保留用于早期实验。正式实验使用 `scripts/measure.py`，构建与产物保存在数据盘 XFS，不使用共享目录作为构建目录。`NATIVE_IMAGE_USER_HOME` 也指向数据盘缓存。

正式测量中观察到 Native Image 的驱动器仍使用 `/tmp/driverRoot-*`，即使给构建 JVM 传入 `-J-Djava.io.tmpdir`。随后重测这两项时，使用私有 mount namespace 将 `/tmp`、`/var/tmp` 映射到数据盘临时目录；挂载只影响该构建及子进程，其他程序的系统临时目录不变。先前少量驱动参数临时文件由工具退出时清理，未把 SDK 或下载迁回系统盘。
