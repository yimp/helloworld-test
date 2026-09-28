#!/usr/bin/env bash
# Source explicitly; do not modify login profiles or replace system installations.
export HW_ROOT=/mnt/sdb/helloworld-test
if ! mountpoint -q /mnt/sdb; then
  printf 'Required data disk /mnt/sdb is not mounted\n' >&2
  return 1 2>/dev/null || exit 1
fi
export TMPDIR="$HW_ROOT/tmp" TMP="$HW_ROOT/tmp" TEMP="$HW_ROOT/tmp"
export XDG_CACHE_HOME="$HW_ROOT/cache/xdg"
export XDG_CONFIG_HOME="$HW_ROOT/config"
export XDG_DATA_HOME="$HW_ROOT/data"
export PIP_CACHE_DIR="$HW_ROOT/cache/pip"
export PYTHONPYCACHEPREFIX="$HW_ROOT/cache/pycache"
export CARGO_HOME="$HW_ROOT/toolchains/cargo"
export RUSTUP_HOME="$HW_ROOT/toolchains/rustup"
export CARGO_TARGET_DIR="$HW_ROOT/build/cargo"
export GOPATH="$HW_ROOT/cache/gopath" GOCACHE="$HW_ROOT/cache/go-build"
export GOMODCACHE="$HW_ROOT/cache/go-mod" GOTMPDIR="$HW_ROOT/tmp"
export ZIG_GLOBAL_CACHE_DIR="$HW_ROOT/cache/zig" ZIG_LOCAL_CACHE_DIR="$HW_ROOT/build/zig-cache"
export NIMBLE_DIR="$HW_ROOT/cache/nimble"
export CRYSTAL_CACHE_DIR="$HW_ROOT/cache/crystal"
export DOTNET_ROOT="$HW_ROOT/toolchains/dotnet"
export DOTNET_CLI_HOME="$HW_ROOT/cache/dotnet-cli"
export DOTNET_CLI_TELEMETRY_OPTOUT=1 DOTNET_SKIP_FIRST_TIME_EXPERIENCE=1 DOTNET_NOLOGO=1
export NUGET_PACKAGES="$HW_ROOT/cache/nuget/packages"
export NUGET_HTTP_CACHE_PATH="$HW_ROOT/cache/nuget/http"
export NUGET_PLUGINS_CACHE_PATH="$HW_ROOT/cache/nuget/plugins"
export npm_config_cache="$HW_ROOT/cache/npm" npm_config_prefix="$HW_ROOT/toolchains/npm"
export BUN_INSTALL="$HW_ROOT/toolchains/bun" BUN_INSTALL_CACHE_DIR="$HW_ROOT/cache/bun"
export DENO_INSTALL="$HW_ROOT/toolchains/deno" DENO_DIR="$HW_ROOT/cache/deno"
export PUB_CACHE="$HW_ROOT/cache/dart-pub"
export NATIVE_IMAGE_USER_HOME="$HW_ROOT/cache/native-image"
export SWIFTLY_HOME_DIR="$HW_ROOT/toolchains/swiftly"
export SWIFTLY_BIN_DIR="$HW_ROOT/toolchains/swiftly/bin"
export SWIFTLY_TOOLCHAINS_DIR="$HW_ROOT/toolchains/swift"
export CLANG_MODULE_CACHE_PATH="$HW_ROOT/cache/clang-modules"
export SWIFT_MODULECACHE_PATH="$HW_ROOT/cache/swift-modules"
export GNUPGHOME="$HW_ROOT/config/gnupg"
if [ -x "$HW_ROOT/toolchains/java/bin/java" ]; then
  export JAVA_HOME="$HW_ROOT/toolchains/java"
fi
export PATH="$HW_ROOT/bin:$CARGO_HOME/bin:$DOTNET_ROOT:$SWIFTLY_BIN_DIR:$npm_config_prefix/bin:$PATH"
mkdir -p "$HW_ROOT"/{bin,toolchains,downloads,cache,tmp,build,logs,config,data}
mkdir -p "$DOTNET_CLI_HOME" "$NUGET_PACKAGES" "$GOCACHE" "$GOMODCACHE"
mkdir -p "$GNUPGHOME"
chmod 700 "$GNUPGHOME"
