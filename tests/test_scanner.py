import os
import tempfile
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from file_scanner import scan_files, find_duplicates
from hash_calculator import sha256_hash


class TestScanner(unittest.TestCase):
    def test_one_duplicate_group(self):
        with tempfile.TemporaryDirectory() as d:
            for name in ("a.txt", "b.txt", "c.txt"):
                with open(os.path.join(d, name), "w") as f:
                    f.write("same content")
            with open(os.path.join(d, "x.txt"), "w") as f:
                f.write("other")
            with open(os.path.join(d, "y.txt"), "w") as f:
                f.write("yet another")

            files = scan_files(d)
            dup, zero = find_duplicates(files, sha256_hash)
            self.assertEqual(len(dup), 1)
            self.assertEqual(len(dup[0]), 3)

    def test_zero_byte(self):
        with tempfile.TemporaryDirectory() as d:
            open(os.path.join(d, "empty.txt"), "w").close()
            files = scan_files(d)
            _, zero = find_duplicates(files, sha256_hash)
            self.assertEqual(len(zero), 1)


if __name__ == "__main__":
    unittest.main()
