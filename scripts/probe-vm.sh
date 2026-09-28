#!/usr/bin/env bash
set -u
for t in as ld gcc g++ clang python3 pip3 node npm javac java jar jlink jpackage zig nim rustc cargo crystal go dotnet swiftc dart bun deno curl wget tar unzip xz make pkg-config cmake docker; do
  p=$(command -v "$t" || true)
  if [ -n "$p" ]; then
    printf '\nTOOL %s PATH %s\n' "$t" "$p"
    case "$t" in
      java) java -version;;
      go) go version;;
      dotnet) dotnet --list-sdks;;
      as|ld|gcc|g++|clang|python3|pip3|node|npm|javac|jar|jlink|jpackage|zig|nim|rustc|cargo|crystal|swiftc|dart|bun|deno|curl|wget|tar|unzip|xz|make|pkg-config|cmake|docker) "$t" --version 2>&1 | head -4;;
    esac
  else
    printf '\nMISSING %s\n' "$t"
  fi
done
printf '\nSYSTEM LIBRARIES\n'
rpm -q glibc glibc-devel libstdc++ libstdc++-devel zlib zlib-devel libicu libicu-devel libxml2 libxml2-devel libedit libedit-devel libcurl-devel openssl-devel libgc-devel pcre2-devel clang llvm python3-devel python3-pip
printf '\nSHARED REPOSITORY\n'
ls -la /home/dev/common/helloworld-test
sha256sum /home/dev/common/helloworld-test/README.md
printf '\nEXISTING OPTIONAL TOOL DIRECTORIES\n'
find /mnt/sdb /opt /usr/local -maxdepth 3 -type d \( -name '*swift*' -o -name '*rust*' -o -name '*go*' -o -name '*dotnet*' -o -name '*zig*' -o -name '*nim*' -o -name '*dart*' -o -name '*bun*' -o -name '*deno*' -o -name '*crystal*' \) 2>/dev/null
