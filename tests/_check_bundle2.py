"""Search for locale bytes in the .exe (binary, even if zlib-compressed)."""
from pathlib import Path

data = Path("dist/KeepAwake.exe").read_bytes()
print(f"Size: {len(data):,} bytes")

# Find any locale .json entries by searching the PyInstaller TOC
# (stored as a marshalled dict somewhere in the binary)
import re
# Look for any string ending with .json
matches = re.findall(rb"[\w/\\]+\.json", data)
uniq = sorted(set(matches))
print(f"Found {len(uniq)} .json references in binary:")
for m in uniq[:30]:
    print(f"  {m.decode('ascii', errors='replace')}")
