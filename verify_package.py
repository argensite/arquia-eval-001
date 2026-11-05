"""Verify the public manifest; it is a checksum check, not a signature."""
import hashlib
from pathlib import Path
import sys

root = Path(__file__).resolve().parent
failed = []
for line in (root / "CHECKSUMS.sha256").read_text().splitlines():
    digest, name = line.split("  ", 1)
    p = (root / name).resolve()
    if root not in p.parents or not p.is_file() or hashlib.sha256(p.read_bytes()).hexdigest() != digest:
        failed.append(name)
if failed:
    print("Checksum mismatch or missing file: " + ", ".join(failed))
    sys.exit(1)
print("All manifest checksums match. Check the archive digest against its publication record.")
