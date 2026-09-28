#!/usr/bin/env python3
"""Run in a private mount namespace; even tools ignoring TMPDIR use the data disk."""
import os
import subprocess
import sys

temporary, *command = sys.argv[1:]
for target in ('/tmp', '/var/tmp'):
    subprocess.run(['/usr/bin/mount', '--bind', temporary, target], check=True)
os.execvpe(command[0], command, os.environ)
