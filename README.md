# Hello World 体积：16 个项目的实测与比较边界

**2026-09-28，现有 Rocky Linux VM：16 个项目、51 种构建/发布配置运行通过；42 个分发集合通过隔离验证。** 本实验测量文件体积，不测性能，不将不同发布方式拼成“语言固有体积”排行榜。

入口：**[全部精确结果与构建命令](results/2026-09-28-rocky9-report.md)** · **[测量标准](METHODOLOGY.md)** · [环境与工具链](VM_SETUP.md) · [JSON 原始证据](results/2026-09-28-rocky9-measurements.json) · [CSV](results/2026-09-28-rocky9-measurements.csv)。

## 环境与测量口径

- Rocky Linux 9.2，Linux x86-64，glibc 2.34，内核 `5.14.0-284.30.1.el9_2.x86_64`；VMware，12 vCPU（Xeon Silver 4210）、约 7.5 GiB RAM。
- 所有源码位于 `src/standard/`；必须 stdout 精确输出 12 B 的 `Hello World\n`，stderr 为空、退出码为 0。使用常见输出 API，Zig 的标准库与 libc 写法单列。
- **A：工具直接生成的应用文件集合。B：在明确系统基线下补齐依赖的分发集合。** 单文件、目录、源码、字节码和包含运行时的包均标明形式。
- B 的基线仅豁免本 VM 的 glibc 共享库/加载器及最小系统设施；libstdc++、libgcc_s、Swift 运行库等额外依赖计入 B。42 个集合在新 mount/PID namespace 的 chroot 内运行，无法访问外部 SDK 路径。
- 普通文件按逻辑字节 `stat.st_size` 求和；符号链接按目标文本字节计。目录元数据不计，外部调试文件单列。主单位为精确整数 B，KiB/MiB 用 1024 进制。
- tar+gzip9 的下载体积另列。PyInstaller、.NET 单文件或 jlink 自带的内部压缩也明确标注，不能把压缩包与未压缩 ELF 直接比较。
- 编译、产物、缓存及下载放在 `/mnt/sdb/helloworld-test/`，构建在 XFS 上进行；CIFS 共享目录仅保存源码与报告。版本和 SHA-256 固定在工具锁与测量 JSON。

B 验证的是本 Hello World 执行路径在上述基线下能运行，不承诺所有 Linux 发行版兼容或运行时的全部可选功能。例如目录版 .NET 的 LTTng 追踪依赖未安装；本次输出无需该组件。具体边界和 ldd 记录见测量标准及 JSON。

## 从结果能看到什么

以下均为本次产物的精确字节数，完整 51 行表按项目和配置组织，没有选取每种语言的最小值排序。

- **输出 API 影响大小。** Zig `ReleaseSmall` 标准库输出为 **145,216 B**；另一份源码调用 libc `puts` 为 **4,352 B**。二者不能用同一个“Zig 大小”代替。
- **动态依赖影响比较。** C++ `-Os -s` 应用为 **21,976 B**，补齐 libstdc++/libgcc_s 后 B 为 **2,436,640 B**。C 的动态应用为 **21,952 B**，静态方案为 **1,527,184 B**。这台发行版的构建属性 note 保留并计入。
- **保留符号与优化是不同维度。** Rust `opt-level=3` 为 **4,505,792 B**，相同优化并 strip 后为 **350,392 B**；进一步使用 LTO、size 优化及 `panic=abort` 为 **292,200 B**，该方案改变 panic 行为。三个方案均另需 **108,144 B** 的 libgcc_s，计入 B。
- **运行时放在哪里影响大小。** Swift `-Osize` 应用为 **12,632 B**，B 为 **16,753,328 B**；静态标准库方案应用为 **6,345,896 B**，B 为 **6,454,040 B**。小启动文件不代表小分发集合。
- **同一语言可有多种发布方式。** C# self-contained 目录 A 为 **82,607,153 B**；NativeAOT A/B 为 **1,271,056 B**。另有 trimmed、压缩单文件及限制全局化的 AOT 方案，各自单列。
- **打包不能等同于普通编译。** Python PyInstaller onedir 的 B 为 **13,342,925 B**，带内部压缩/解包的 onefile 的 B 为 **6,039,912 B**；21 B 源码与 141 B zipapp 都仍依赖外部 Python。
- **JVM 与 AOT 是不同发布前提。** Java JAR 为 **738 B**，依赖外部 JVM；JAR+jlink java.base 的 B 为 **85,286,100 B**，全模块方案为 **166,517,103 B**，Native Image size 的 B 为 **4,344,392 B**。AOT 具有闭世界限制，不包含通用 JVM。
- **JS 运行器占据固定成本。** Bun compile 的 B 为 **81,315,296 B**，Deno compile 为 **104,675,896 B**，Node SEA 为 **129,099,016 B**。它们是包含相应运行器的真实可运行产物，28 B JS 源文件单列为外部运行时参照。

Nim、Crystal、Go、Dart 及各项目默认构建也全部在正式结果表中。汇编常规 stripped 为 **8,488 B**；`ld -N -s` 的 **456 B** 产物具有 RWX LOAD 段，作为极限配置附录，不能充当常规发布代表。

原帖缺少 OS、CPU 架构、工具版本、源码、构建参数和运行时边界，因此不适合作为无条件排名。这份实测提供明确条件下的数据；某项接近原帖不等于复现了原作者条件，某项不同也不证明那个数字在任何条件下都不可能。Hello World 主要反映固定成本，不能外推真实项目的体积、性能或语言价值。

## 复现与证据

需要这套已验收的 Linux 工具链和 root（用于 namespace/chroot）；不会自动安装或升级工具。源码、工具版本、命令、环境覆盖项、产物清单、哈希、ELF/ldd 和运行结果保存在 JSON。最终用 GNU find 与 sha256sum 独立核对保存产物的字节数和哈希。

```bash
source /home/dev/common/helloworld-test/scripts/vm-env.sh
python3 /home/dev/common/helloworld-test/scripts/measure.py
```

每次创建新的数据盘构建目录。本次快照在 `/mnt/sdb/helloworld-test/build/formal/20260928T063645Z`，包含各配置的 application/、deployment/、下载归档及日志。重试会保留被替代的尝试，不修改系统工具链。

```bash
# 续跑：已通过项目保留，仅执行失败/缺失项目
python3 /home/dev/common/helloworld-test/scripts/measure.py \
  --resume /mnt/sdb/helloworld-test/build/formal/20260928T063645Z

# 显式重测特定配置；其他记录保留
python3 /home/dev/common/helloworld-test/scripts/measure.py \
  --resume /mnt/sdb/helloworld-test/build/formal/20260928T063645Z \
  --only cpp-size-dynamic,python-onefile

# 核对保存文件并重新生成报告，不重新构建
python3 /home/dev/common/helloworld-test/scripts/finalize-measurements.py \
  /mnt/sdb/helloworld-test/build/formal/20260928T063645Z
```

重建可能因时间戳、路径或 build-id 改变哈希及少量体积。精确数字对应保存的本次快照，归档压缩参数对相同输入固定。测量过程中遇到的 Swift 链接路径、Python 启动依赖及 Java jlink 参数问题已修正；替代尝试和失败证据的路径保存在 JSON。

## 历史实验

[2026-09-27 局部实验说明](HISTORY-2026-09-27.md) 与 [旧 JSON](results/2026-09-27-linux-x86_64.json)来自另一环境，工具版本与发布方案不同，不合并到本次表中。旧脚本 `scripts/run.py` 保留；正式测量入口是 `scripts/measure.py`。
