"""Daemon launcher for evolution loop in Daytona sandbox.

Usage: python3 scripts/daemon_evolve.py [max_steps]

Loads .env, forks to background, writes PID to daemon.pid.
"""

import os
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
os.chdir(PROJECT_ROOT)

# Load .env
env_file = PROJECT_ROOT / ".env"
if env_file.exists():
    for line in env_file.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            os.environ[k] = v

max_steps = sys.argv[1] if len(sys.argv) > 1 else "10"

log = open(PROJECT_ROOT / "evolution.log", "w")
proc = subprocess.Popen(
    [
        sys.executable,
        "-u",
        "cli.py",
        "evolve",
        "run",
        "--max-steps",
        max_steps,
        "--mode",
        "burst",
    ],
    stdout=log,
    stderr=log,
    start_new_session=True,
    cwd=str(PROJECT_ROOT),
)

pid_file = PROJECT_ROOT / "daemon.pid"
pid_file.write_text(str(proc.pid))
print(proc.pid)
