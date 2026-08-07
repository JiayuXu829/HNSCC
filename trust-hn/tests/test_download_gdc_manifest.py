import csv
import tempfile
import unittest
from pathlib import Path

from trust_hn.data.acquisition import AcquisitionPolicyError

from scripts.download_gdc_manifest import destination_name, load_frozen_rows


class GDCManifestDownloadTests(unittest.TestCase):
    def write_manifest(self, row):
        directory = tempfile.TemporaryDirectory()
        path = Path(directory.name) / "manifest.tsv"
        with path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(row), delimiter="\t")
            writer.writeheader()
            writer.writerow(row)
        return directory, path

    def base_row(self):
        return {
            "file_id": "uuid-1",
            "file_name": "counts.tsv",
            "md5sum": "abc",
            "file_size": "10",
            "access": "open",
            "workflow_type": "STAR - Counts",
            "case_submitter_ids": "TCGA-AA-0001",
            "sample_types": "Primary Tumor",
        }

    def test_frozen_primary_tumor_row_is_accepted(self):
        directory, path = self.write_manifest(self.base_row())
        try:
            rows = load_frozen_rows(path)
            self.assertEqual(destination_name(rows[0]), "uuid-1__counts.tsv")
        finally:
            directory.cleanup()

    def test_non_primary_or_controlled_row_is_rejected(self):
        for field, value in [("sample_types", "Solid Tissue Normal"), ("access", "controlled")]:
            row = self.base_row()
            row[field] = value
            directory, path = self.write_manifest(row)
            try:
                with self.assertRaises(AcquisitionPolicyError):
                    load_frozen_rows(path)
            finally:
                directory.cleanup()


if __name__ == "__main__":
    unittest.main()
