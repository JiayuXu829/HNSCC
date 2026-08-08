from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from trust_hn.evaluation.phase5 import build_sealed_cohort_manifest


class Phase5FreezeTests(unittest.TestCase):
    def test_sealed_manifest_contains_only_aggregate_set_digest(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "adapter_records.csv"
            source.write_text(
                "native_id,split_role,eligible,endpoint_status,event\n"
                "secret-1,sealed_test,True,suppressed,\n"
                "secret-2,train,True,usable,1\n",
                encoding="utf-8",
            )
            result = build_sealed_cohort_manifest(
                source, cohort="TEST", split_roles={"sealed_test"}
            )
            rendered = json.dumps(result)
            self.assertEqual(result["patient_count"], 1)
            self.assertNotIn("secret-1", rendered)
            self.assertNotIn("patient_hashes", result)
            self.assertEqual(len(result["ordered_id_set_sha256"]), 64)


if __name__ == "__main__":
    unittest.main()
