# Hello World 体积：局部复现实验

这份实验用于核查一张流传的“各语言 Hello World 二进制文件大小”表。**它不是跨语言性能排行榜，也没有复现原帖全部 16 项。**编译参数、操作系统、动态库和运行时是否打包，都会改变数字。所有标为“实测”的程序都已在本机运行，退出码为 0，并输出精确的 `Hello World\n`。

本次环境：**2026-09-27，隔离的 Linux x86-64 环境**，GCC/G++ 13.3.0、GNU Binutils 2.42、Python 3.12.14、Node.js 24.19.0、OpenJDK 17.0.20。以下按十进制字节（B）记录磁盘上的**文件**大小；目录另有标注。完整机器记录见 [`results/2026-09-27-linux-x86_64.json`](results/2026-09-27-linux-x86_64.json)。

## 编译型程序

| 源码 | 构建条件 | 字节数 | 实际运行 |
| --- | --- | ---: | --- |
| x86-64 汇编 | `as` + `ld` 默认 | 8,848 | ✓ |
| x86-64 汇编 | `ld -s` | 8,488 | ✓ |
| x86-64 汇编 | `ld -N -s` | **456** | ✓，链接器警告 RWX 段 |
| C | `gcc` 默认，动态链接 | 15,960 | ✓ |
| C | `gcc -Os -s`，动态链接 | **14,472** | ✓ |
| C | `gcc -static -Os -s`，静态链接 | **706,568** | ✓ |
| C++ | `g++` 默认，动态链接 | 16,504 | ✓ |
| C++ | `g++ -Os -s`，动态链接 | **14,472** | ✓ |
| C++ | `g++ -static -Os -s`，静态链接 | **1,862,280** | ✓ |

相同源码和 `-Os -s` 选项下，C 的静态产物是动态产物的 **48.8 倍**，C++ 是 **128.7 倍**。动态产物本身不包含共用库：本机 C 产物还依赖约 2,125,328 B 的 `libc.so.6` 和 236,616 B 的动态加载器；C++ 另外依赖 `libstdc++.so.6` 等库。机器上已有的共用库不能简单算作每个程序的单独负担，但也不能把 14 KB 文件叫作“不依赖环境”。

汇编做到 456 B 使用了 `ld -N`；链接器给出可写且可执行（RWX）段警告。**原帖约 300 B 没有复现**，也不建议把这个极端产物作为常规发布配置。

## 源码、归档与运行时

| 形式 | 字节数 | 实际运行 | 是否包含运行时 |
| --- | ---: | --- | --- |
| Python 源文件 | 21 | ✓ | 否 |
| Python `zipapp` | 164 | ✓ | 否，仍调用本机 `python3` |
| 本机 Python 解释器文件 | 30,894,944 | 用于上述运行 | 不是打包后的 Hello World |
| JavaScript 源文件 | 27 | ✓ | 否 |
| 本机 Node.js 运行器文件 | 125,989,464 | 用于上述运行 | 不是打包后的 Hello World |
| Node SEA 准备 blob | 60 | 不是可执行文件 | **没有得到能运行的单文件产物** |
| Java 源文件 | 94 | ✓ | 否 |
| Java `.class` | 411 | ✓ | 否 |
| Java JAR | 558 | ✓ | 否 |
| Java `jpackage` 应用**目录**，包含本机整套 JRE | **193,204,190** | ✓ | 是，未做模块裁剪 |

Node 24 的 SEA 需要把准备 blob 正确注入 Node 可执行文件。本环境没有 `postject`；曾尝试手工注入但产物运行失败，**没有把失败产物算作实验结果**。Java 的 193 MB 是包含现成完整 JRE 的目录大小，不能据此排除别的精简 JRE 打包方案。Python 的 164 B 归档同样不能拿来反驳包含解释器的分发体积。

## 原帖覆盖情况

- 汇编、C、C++：本机编译并运行；默认构建与若干不同链接方式已测，但并未获得原帖使用的环境和参数。
- Python、Java、Node.js：测了本机可用的源码、归档和运行方式；**原帖的 12 MB、14 MB、85 MB 分别未复现**。
- Zig、Nim、Rust、Crystal、Go、C#、Swift、Dart、Bun、Deno：本机无对应编译器或打包器，**未测试，也不判断原帖数字真假**。

## 如何复现

源码在 [`src/`](src/)，自动实验在 [`scripts/run.py`](scripts/run.py)。需要 Linux、Python 3、GNU `as`/`ld`/`gcc`/`g++`、Node.js 与包含 `jdk.compiler` 模块的 Java 17。脚本不下载安装工具链，会对每个有效产物运行校验，并把生成文件放在被 Git 忽略的 `build/`：

```sh
python3 scripts/run.py
```

若要额外构建包含完整本机 JRE 的 Java 应用目录（此处约 193 MB），在具备 `jpackage` 的环境执行：

```sh
python3 scripts/run.py --include-jpackage --output build/results.json
```

默认输出为 `build/results.json`，仓库中的 `results/2026-09-27-linux-x86_64.json` 是本次机器运行包含 `--include-jpackage` 时的快照。**不同机器或工具版本的字节数预计会变化。**

技术依据：[Python `zipapp` 文档](https://docs.python.org/3.12/library/zipapp.html)、[Node.js 单文件应用文档](https://nodejs.org/docs/latest-v24.x/api/single-executable-applications.html)、[Java `jpackage` 文档](https://docs.oracle.com/en/java/javase/17/jpackage/packaging-overview.html)。
