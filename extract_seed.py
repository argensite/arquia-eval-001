"""Extract the fixed SEED-001 Python blocks; never import or execute them."""
import argparse
import hashlib
import json
from pathlib import Path
import re


SEED_SHA256 = '27b2ddab9d23ffcafb05c976fe2c679da287773d4a1ef694343399aa7591a14b'
DEFAULT_SEED = Path(__file__).resolve().parent / 'semilla/ARQUIA_SEMILLA_UNIVERSAL_AGENTES_v0.1.md'
FILES = ('arquia_seed_reference.py', 'test_arquia_seed_reference.py')


def source_blocks(raw):
    """Identify the entire release before accepting either named code block."""
    if hashlib.sha256(raw).hexdigest() != SEED_SHA256:
        raise ValueError('SEED-001 SHA-256 mismatch; no files extracted')
    blocks = {}
    for section, name in zip(('A', 'B'), FILES):
        heading = ('### 6.' + section + '. Archivo `' + name + '`\n\n```python\n').encode()
        if raw.count(heading) != 1:
            raise ValueError('missing or ambiguous block: ' + name)
        body = raw.split(heading, 1)[1]
        match = re.search(rb'^```\s*$', body, re.MULTILINE)
        if match is None:
            raise ValueError('unterminated block: ' + name)
        blocks[name] = body[:match.start()]
    return blocks


def extract(seed, output):
    blocks = source_blocks(Path(seed).read_bytes())
    destination = Path(output)
    # A fresh directory prevents overwriting a prior experiment or following a
    # pre-existing destination symlink. Review the extracted source before use.
    destination.mkdir(parents=False, exist_ok=False)
    hashes = {}
    for name, content in blocks.items():
        with (destination / name).open('xb') as stream:
            stream.write(content)
        hashes[name] = hashlib.sha256(content).hexdigest()
    receipt = {'schema': 'arquia.seed-extraction/1', 'seed_sha256': SEED_SHA256,
               'files_sha256': hashes, 'code_executed': False,
               'isolation_established': False}
    (destination / 'extraction.json').write_text(json.dumps(receipt, indent=2) + '\n', encoding='utf-8')
    return receipt


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('seed', nargs='?', type=Path, default=DEFAULT_SEED)
    parser.add_argument('--output', required=True, type=Path,
                        help='new directory inside your authorized isolated workspace')
    args = parser.parse_args()
    try:
        receipt = extract(args.seed, args.output)
    except (OSError, ValueError) as error:
        parser.exit(1, str(error) + '\n')
    print(json.dumps(receipt, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
