"""The convenience extractor must preserve identity and existing experiments."""
import hashlib
from pathlib import Path
import tempfile
import unittest

from extract_seed import DEFAULT_SEED, FILES, SEED_SHA256, extract, source_blocks


class SeedExtractionTests(unittest.TestCase):
    def test_fixed_source_and_exact_block_bytes(self):
        raw = DEFAULT_SEED.read_bytes()
        self.assertEqual(hashlib.sha256(raw).hexdigest(), SEED_SHA256)
        with tempfile.TemporaryDirectory() as folder:
            output = Path(folder) / 'new'
            receipt = extract(DEFAULT_SEED, output)
            for name in FILES:
                marker = ('```python\n').encode()
                # Independently locate the named section and its fenced source.
                start = raw.index(('Archivo `' + name + '`').encode())
                expected = raw[start:].split(marker, 1)[1].split(b'\n```', 1)[0] + b'\n'
                self.assertEqual((output / name).read_bytes(), expected)
            self.assertFalse(receipt['code_executed'])
            self.assertFalse(receipt['isolation_established'])
            self.assertEqual({p.name for p in output.iterdir()}, set(FILES) | {'extraction.json'})

    def test_modified_document_is_rejected_before_writing(self):
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder) / 'modified.md'
            source.write_bytes(DEFAULT_SEED.read_bytes() + b'\nchanged\n')
            destination = Path(folder) / 'output'
            with self.assertRaisesRegex(ValueError, 'SHA-256 mismatch'):
                extract(source, destination)
            self.assertFalse(destination.exists())

    def test_existing_directory_and_files_are_preserved(self):
        with tempfile.TemporaryDirectory() as folder:
            output = Path(folder) / 'prior'
            output.mkdir()
            sentinel = output / FILES[0]
            sentinel.write_bytes(b'previous experiment\n')
            with self.assertRaises(FileExistsError):
                extract(DEFAULT_SEED, output)
            self.assertEqual(sentinel.read_bytes(), b'previous experiment\n')
            self.assertFalse((output / FILES[1]).exists())

    def test_extraction_does_not_execute_demo_or_create_database(self):
        with tempfile.TemporaryDirectory() as folder:
            output = Path(folder) / 'new'
            extract(DEFAULT_SEED, output)
            self.assertEqual(len(list(output.iterdir())), 3)
            self.assertFalse(any(output.glob('*.db')))

    def test_truncated_input_is_not_accepted(self):
        with self.assertRaisesRegex(ValueError, 'SHA-256 mismatch'):
            source_blocks(DEFAULT_SEED.read_bytes()[:1000])



if __name__ == '__main__':
    unittest.main()
