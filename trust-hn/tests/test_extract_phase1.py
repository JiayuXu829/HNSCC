import tempfile
import unittest
import zipfile
from pathlib import Path

from scripts.extract_phase1 import safe_extract_zip


class SafeExtractionTests(unittest.TestCase):
    def test_safe_zip_extracts(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "safe.zip"
            with zipfile.ZipFile(source, "w") as archive:
                archive.writestr("folder/file.txt", "ok")
            report = safe_extract_zip(source, root / "out")
            self.assertEqual(report["files"], 1)
            self.assertEqual((root / "out/folder/file.txt").read_text(), "ok")

    def test_path_traversal_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "unsafe.zip"
            with zipfile.ZipFile(source, "w") as archive:
                archive.writestr("../escape.txt", "bad")
            with self.assertRaises(ValueError):
                safe_extract_zip(source, root / "out")


if __name__ == "__main__":
    unittest.main()
