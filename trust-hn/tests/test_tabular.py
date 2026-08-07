import gzip
import tempfile
import unittest
from pathlib import Path

from trust_hn.data.tabular import (
    TableAuditError,
    parse_binary_event,
    read_delimited,
    resolve_unique_field,
)


class TabularTests(unittest.TestCase):
    def test_reads_gzip_tsv(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "table.tsv.gz"
            with gzip.open(path, "wt", encoding="utf-8", newline="") as handle:
                handle.write("patient\tevent\nA\t1\n")
            headers, rows = read_delimited(path)
            self.assertEqual(headers, ["patient", "event"])
            self.assertEqual(rows[0]["patient"], "A")

    def test_resolution_normalizes_format_not_semantics(self):
        self.assertEqual(
            resolve_unique_field(["Patient ID", "Outcome"], ["patient_id"]),
            "Patient ID",
        )
        self.assertIsNone(resolve_unique_field(["Subject"], ["patient_id"]))

    def test_ambiguous_resolution_is_rejected(self):
        with self.assertRaises(TableAuditError):
            resolve_unique_field(["patient_id", "Patient ID"], ["patient_id"])

    def test_event_mapping_requires_explicit_unknown_mapping(self):
        self.assertEqual(parse_binary_event("Dead"), 1)
        with self.assertRaises(TableAuditError):
            parse_binary_event("DOD")
        self.assertEqual(parse_binary_event("DOD", {"DOD": 1}), 1)


if __name__ == "__main__":
    unittest.main()