"""Запускает .exe на 5 сек, читает stdout/stderr и лог, ищет подсказки о пропавших локалях."""
import subprocess
import sys
import time
from pathlib import Path

exe = Path("dist/KeepAwake.exe").resolve()
print(f"Testing: {exe} ({exe.stat().st_size:,} bytes)")
print()

# Run .exe, capture all output for 4 seconds, then kill
proc = subprocess.Popen(
    [str(exe)],
    cwd=str(exe.parent),
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    creationflags=subprocess.CREATE_NO_WINDOW,
)
try:
    stdout, stderr = proc.communicate(timeout=4)
except subprocess.TimeoutExpired:
    proc.kill()
    stdout, stderr = proc.communicate()

print("--- STDOUT ---")
if stdout:
    print(stdout.decode("utf-8", errors="replace"))
else:
    print("(empty)")

print("--- STDERR ---")
if stderr:
    print(stderr.decode("utf-8", errors="replace"))
else:
    print("(empty)")

print(f"--- exit code: {proc.returncode} ---")
