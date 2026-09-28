#!/usr/bin/env python3
"""Called inside a new mount/PID namespace, before launching a measured app."""
import json
import os
import subprocess
import sys

root, encoded = sys.argv[1:]
command = json.loads(encoded)
subprocess.run(['/usr/bin/mount', '-t', 'proc', 'proc', root + '/proc'], check=True)
os.chroot(root)
os.chdir('/app')
env = {'PATH': '/app', 'HOME': '/tmp', 'TMPDIR': '/tmp', 'LC_ALL': 'C',
       'LD_LIBRARY_PATH': '/app/lib', 'DOTNET_BUNDLE_EXTRACT_BASE_DIR': '/tmp/dotnet-bundle',
       'DOTNET_CLI_TELEMETRY_OPTOUT': '1'}
os.execve(command[0], command, env)
