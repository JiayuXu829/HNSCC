import tempfile
import unittest
from pathlib import Path

from trust_hn.data.acquisition import AcquisitionPolicy, AcquisitionPolicyError


class AcquisitionTests(unittest.TestCase):
    def setUp(self):
        self.policy = AcquisitionPolicy(
            allowed_hosts=frozenset({"example.org"}),
            allowed_roles=frozenset({"clinical_table"}),
            forbidden_roles=frozenset({"raw_ct"}),
            max_single_file_bytes=100,
            max_planned_total_bytes=1000,
            https_required=True,
            raw_destination_root="data/raw",
        )

    def test_approved_small_https_request_passes(self):
        self.policy.validate_request("https://example.org/clinical.csv", "clinical_table", 50)

    def test_forbidden_or_unknown_role_is_rejected(self):
        with self.assertRaises(AcquisitionPolicyError):
            self.policy.validate_request("https://example.org/image.zip", "raw_ct", 50)
        with self.assertRaises(AcquisitionPolicyError):
            self.policy.validate_request("https://example.org/x", "mystery", 50)

    def test_host_scheme_and_size_are_enforced(self):
        with self.assertRaises(AcquisitionPolicyError):
            self.policy.validate_request("http://example.org/x", "clinical_table", 50)
        with self.assertRaises(AcquisitionPolicyError):
            self.policy.validate_request("https://evil.example/x", "clinical_table", 50)
        with self.assertRaises(AcquisitionPolicyError):
            self.policy.validate_request("https://example.org/x", "clinical_table", 101)

    def test_destination_cannot_escape_raw_root(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            destination = self.policy.resolve_destination(root, "radcure", "clinical.csv")
            self.assertEqual(destination, (root / "data" / "raw" / "radcure" / "clinical.csv").resolve())
            with self.assertRaises(AcquisitionPolicyError):
                self.policy.resolve_destination(root, "radcure", "..\\secret.txt")


if __name__ == "__main__":
    unittest.main()