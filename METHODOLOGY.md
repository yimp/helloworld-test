# Hello World 体积测量标准

本实验回答：在固定 Linux x86-64 环境中，同一个标准输出任务，采用明确的构建和发布方式，需要多少应用文件，以及多少分发文件。它不测性能，也不试图证明某种语言有固定的“二进制大小”。

## 程序与环境

- 标准输出必须是精确的 12 个字节 `Hello World\n`；标准错误为空、退出码为 0。以字节比较，禁止文本模式的换行转换。
- 源码在 `src/standard/`，UTF-8、无 BOM、LF。使用常见语言输出 API；C++ 使用 iostream，Go 使用 fmt，Zig 使用 0.16 标准库 stdout API。额外的 Zig libc puts 写法单列，不替代标准库版本。
- 汇编使用 Linux x86-64 write/exit 系统调用，不使用语言运行时；这是其编程接口的边界。
- Rocky Linux 9.2、glibc 2.34、x86-64，VM 内核/CPU/版本见 JSON。工具版本沿用已验收工具链，构建在 `/mnt/sdb/helloworld-test/build/` 的 XFS 上进行。
- 不使用 `-march=native`；在支持的工具中显式选择 x86-64/baseline，Go 使用 GOAMD64=v1。不保证所有打包运行器均支持同一最老 CPU，第三方预编译运行器的 CPU 下限仍由供应商决定。
- 环境、命令、源码 SHA-256、产物清单及 SHA-256、ELF 依赖、运行结果与构建警告均记录。失败与未验证产物没有“有效分发体积”。

## 两个主要口径

### A：工具直接生成的应用文件

单个可执行文件按文件逻辑字节数计；应用目录按目录内各文件逻辑字节求和。保留工具输出中运行所需内容；单独生成的 `.pdb`/`.dbg` 调试文件另列而不计入运行文件。可执行文件内部的符号和调试内容仍计入，是否 strip 单独注明。

脚本、Python zipapp、Java class/JAR、C# framework-dependent 输出属于依赖外部运行时的应用文件，不称为包含运行时的独立二进制。解释器或 JVM/SDK 自身的大小不代替打包程序的大小。

### B：固定系统基线下的分发文件集合

系统基线提供这台 VM 的 **glibc 共享库及动态加载器**，Linux 内核、proc、基本设备、临时目录及最小配置。基线文件有独立清单和哈希，不计入每个应用的新增分发体积。

应用需要的语言运行时和其他共享库都计入，包括未随工具产物附带的 Swift 库、libstdc++、libgcc_s、zlib、ICU 等。根据 ELF 依赖与运行需要把它们收集到分发目录，再验证。已有脚本/JAR等仅作 A 口径，不把系统上恰好安装的运行时当成 B 的免费依赖；对应 B 使用明确的 PyInstaller、jlink、Native Image 或其他打包方式。

B 是这个 Hello World 执行路径在该基线下的分发需求。未被这次执行使用的动态加载功能不因此获得完整依赖覆盖承诺，例如文化相关操作可能进一步需要 ICU。常见 Linux 系统往往已有 libstdc++ 等库，本实验选择只豁免 glibc，方便公开一致的基线；B 不等同于每台用户电脑上的实际新增磁盘占用。

本次具体发现：C# self-contained 与 trimmed 目录里的 `libcoreclrtraceptprovider.so` 的 LTTng 依赖未安装，Hello World 的主路径仍通过验证；本报告不覆盖 LTTng 追踪。JVM 的部分库单独运行 ldd 时找不到 `libjvm.so`，但它已在 runtime/lib/server 内打包，并由 JVM 自身加载；报告保留这两种不同情况的原始记录。

验证在新的 mount/PID namespace 中运行：chroot 根目录只放系统基线与该分发文件集合，清空开发环境变量，不能正常访问 VM 的 SDK/缓存/共享源码路径。提供 C locale、`/tmp`、proc 和基本设备；额外库通过明确的 `LD_LIBRARY_PATH=/app/lib` 寻址。运行命令一起公开。

这证明的是本程序在该基线下运行成功，并不证明任意 Linux 发行版、任意 glibc/内核/CPU 版本都兼容。chroot 是依赖验证方式，不作为对恶意程序的安全隔离承诺。

## 字节统计规则

- 主指标是精确整数 **B**，辅助单位为 KiB/MiB（1024 进制），不使用含义不明的 KB/MB。
- 普通文件按 `stat.st_size` 求和；每个路径计一次，不依赖磁盘分配块、文件系统压缩或稀疏分配。
- 符号链接按 UTF-8 链接目标文本字节计，目标文件如在集合中则按普通文件另计。目录项元数据不计；硬链接按分发路径各计一次。分发集合不保留指向集合外部文件的链接。
- SDK、编译缓存、下载包、源码、对象文件、临时构建目录、基线 OS 均不计入应用分发体积。
- 原始可执行文件、应用目录和补齐依赖后的分发集合分别记录；启动器的小文件大小不代替其运行目录大小。
- 单文件仅描述交付文件数量，不意味着静态链接或运行时不解压。PyInstaller/.NET 单文件内部可能压缩，属于文件本身的内容，仍按实际大小计；内部压缩与解包行为明确注明。
- 另外生成确定参数的 tar+gzip（level 9，时间/属主归零）并记录下载归档字节数。这是辅助指标，与上述逻辑字节分开。外部压缩后的大小不能混入原始可执行文件表。

## 构建配置边界

默认构建展示工具默认值；release/size 构建展示显式参数。各工具的“默认”“release”和“size”不是同一组语义，不能把标签当成统一优化级别。

本报告的 default 指没有显式增加优化/strip 选项，仍会固定目标架构、输出路径或 GC 等条件；实际 argv 与环境覆盖项优先于简写标签。C# 使用仓库内的最小 net10.0 项目并关闭外部调试符号。`rustc` 直接构建的 release 保留符号，另外测 release-stripped，不能将它等同于所有 Cargo 项目的发布配置。

动态/静态链接、是否裁剪运行时、内部压缩、panic=abort、全局化限制、单文件/目录等分别标注。Rust size 方案改变 panic 为 abort；.NET 的裁剪、单文件压缩和全局化限制作为具体发布方案公开。Java jlink 使用 java.base 模块的方案与全模块运行时分开；Java Native Image 是 AOT 方案，与 JAR+jlink 分开。

常规优化不使用 UPX、手写 ELF、去掉系统安全约束等极限手段。汇编 `ld -N -s` 的 RWX 段产物单独作为极限配置附录，不能充当正常发布方案的排名代表。

文件内发行版工具链附加的构建属性 note 也计入，例如这台 Rocky 的 C 产物含 `.gnu.build.attributes`。没有为了贴近原帖数字而自动删除这类元数据。

精确字节和哈希对应本次保存的产物。编译器 build-id、时间戳、路径或打包元数据可能导致重建的哈希乃至字节数变化；这里的“可复现”指源码、工具、参数和验证过程可重复，不承诺所有工具输出逐字节确定。

## 结果如何比较

先比较同一语言、同一源码的配置差异；跨语言比较必须同时看到 A/B 口径、运行时包含情况、文件形式和构建参数。报告按项目与配置组织，不给每种语言挑一个有利的最小值拼成统一排行榜。

Hello World 反映的是输出路径、运行时、标准库和打包的固定成本，不能线性外推真实项目，也不能衡量开发效率、运行性能或生态价值。

原帖没有给出 OS、架构、版本、源码与参数，本实验只能提供本条件下的可复现数据；某个数值接近或不同于原帖，都不能单独证明完整复现或普遍证伪。

## 技术参考

- [Zig 0.16 语言与标准库](https://ziglang.org/documentation/0.16.0/)
- [Rust codegen 选项](https://doc.rust-lang.org/rustc/codegen-options/index.html)
- [.NET 单文件部署与解包](https://learn.microsoft.com/en-us/dotnet/core/deploying/single-file/overview)
- [.NET Native AOT](https://learn.microsoft.com/en-us/dotnet/core/deploying/native-aot/)
- [.NET Native AOT 体积与全局化选项](https://learn.microsoft.com/en-us/dotnet/core/deploying/native-aot/optimizing)
- [Java jlink](https://docs.oracle.com/en/java/javase/25/docs/specs/man/jlink.html)
- [PyInstaller 文件与目录发布](https://pyinstaller.org/en/stable/operating-mode.html)
- [Node SEA](https://nodejs.org/docs/latest-v24.x/api/single-executable-applications.html)
- [Annobin 构建属性 note](https://sourceware.org/annobin/annobin.html/Plugins.html)
- [.NET Linux 追踪机制](https://github.com/dotnet/runtime/blob/main/docs/project/linux-performance-tracing.md)
