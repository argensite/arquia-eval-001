"""Check manifest completeness and bytes. Checksums are NOT digital signatures."""
import hashlib
from pathlib import Path, PurePosixPath
import re
import sys

ROOT = Path(__file__).resolve().parent
REQUIRED = {'runner.py', 'engine.py', 'verify_package.py', 'cases.json', 'VERSION', 'LICENSE'}


def safe_file(root, name):
    p = PurePosixPath(name)
    if (not name or '\\' in name or ':' in name or p.is_absolute() or '..' in p.parts
            or '.' in p.parts or p.as_posix() != name):
        raise ValueError('unsafe path: ' + name)
    target = root / name
    # Inspect the package boundary, not unrelated system ancestors such as
    # macOS /var -> /private/var. Resolution still has to stay inside root.
    if root.is_symlink() or any(root.joinpath(*p.parts[:i]).is_symlink() for i in range(1,len(p.parts)+1)):
        raise ValueError('symlink: ' + name)
    if not target.resolve().is_relative_to(root.resolve()) or not target.is_file():
        raise ValueError('missing/nonregular file: ' + name)
    return target


def verify(root=ROOT):
    entries = {}
    for line in (root / 'CHECKSUMS.sha256').read_text(encoding='utf-8').splitlines():
        if not re.fullmatch(r'[0-9a-f]{64}  .+', line):
            raise ValueError('malformed manifest line')
        digest, name = line.split('  ', 1)
        if name in entries or name == 'CHECKSUMS.sha256':
            raise ValueError('duplicate/self manifest entry: ' + name)
        target = safe_file(root, name)
        if hashlib.sha256(target.read_bytes()).hexdigest() != digest:
            raise ValueError('checksum mismatch: ' + name)
        entries[name] = digest
    if not REQUIRED <= entries.keys():
        raise ValueError('missing required manifest entries: ' + ', '.join(sorted(REQUIRED - entries.keys())))
    # The distribution inventory is an allowlist, not a recursive sweep of a user's directory.
    inventory = root / 'PACKAGE_FILES.json'
    if inventory.is_file():
        import json
        names = json.loads(inventory.read_text(encoding='utf-8'))
        if not isinstance(names, list) or not all(isinstance(x, str) for x in names):
            raise ValueError('invalid distribution inventory')
        if len(names) != len(set(names)) or set(names) != set(entries):
            raise ValueError('manifest/inventory coverage mismatch')
    return len(entries)


def main():
    try:
        count = verify()
    except (OSError, ValueError) as exc:
        print('Verification failed: ' + str(exc), file=sys.stderr)
        return 1
    print(f'{count} manifest entries verified. Hash identity is not authorship or authenticity.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
