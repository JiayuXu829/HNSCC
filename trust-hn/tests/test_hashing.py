import tempfile
import unittest
from pathlib import Path

from trust_hn.utils.hashing import canonical_json_sha256, sha256_file


class HashingTests(unittest.TestCase):
    def test_canonical_hash_ignores_mapping_order(self):
        self.assertEqual(canonical_json_sha256({"b": 2, "a": 1}), canonical_json_sha256({"a": 1, "b": 2}))

    def test_file_hash_is_deterministic(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "x.txt"
            path.write_text("TRUST-HN\n", encoding="utf-8")
            self.assertEqual(sha256_file(path), sha256_file(path))


if __name__ == "__main__":
    unittest.main()