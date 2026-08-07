import unittest

from trust_hn.data.gdc import GDCQueryError, build_post_body, normalize_file_hits


class GDCTests(unittest.TestCase):
    def test_query_body_serializes_filters(self):
        body = build_post_body(
            {
                "endpoint": "https://api.gdc.cancer.gov/files",
                "filters": {"op": "in", "content": {"field": "x", "value": ["y"]}},
                "size": 1,
            }
        ).decode()
        self.assertIn("filters=", body)
        self.assertIn("size=1", body)
        self.assertNotIn("endpoint", body)

    def test_file_hits_are_normalized_without_outcomes(self):
        payload = {
            "data": {
                "hits": [
                    {
                        "file_id": "f2",
                        "file_name": "counts.tsv",
                        "md5sum": "abc",
                        "file_size": 10,
                        "data_format": "TSV",
                        "access": "open",
                        "analysis": {"workflow_type": "STAR - Counts"},
                        "cases": [
                            {
                                "case_id": "c1",
                                "submitter_id": "TCGA-AA-0001",
                                "samples": [{"sample_type": "Primary Tumor"}],
                            }
                        ],
                    }
                ]
            }
        }
        rows = normalize_file_hits(payload)
        self.assertEqual(rows[0]["file_id"], "f2")
        self.assertEqual(rows[0]["sample_types"], "Primary Tumor")
        self.assertNotIn("vital_status", rows[0])

    def test_missing_hits_are_rejected(self):
        with self.assertRaises(GDCQueryError):
            normalize_file_hits({"data": {}})


if __name__ == "__main__":
    unittest.main()