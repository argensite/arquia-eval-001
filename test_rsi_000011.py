"""Regression for exponent-overflow JSON numbers in the bounded parser."""
import unittest

import schemas


class RSI000011Tests(unittest.TestCase):
    def test_exponent_overflow_is_rejected_as_nonfinite_json_number(self):
        for raw in ('{"x":1e400}', '{"x":-1e400}'):
            with self.subTest(raw=raw):
                with self.assertRaisesRegex(ValueError, "nonfinite JSON number"):
                    schemas.strict_json(raw)

    def test_large_finite_exponent_remains_accepted(self):
        parsed = schemas.strict_json('{"x":1e308}')
        self.assertEqual(parsed["x"], 1e308)
        self.assertTrue(parsed["x"] < float("inf"))


if __name__ == "__main__":
    unittest.main()
