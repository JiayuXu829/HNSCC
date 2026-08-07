import json
import tempfile
import unittest
from pathlib import Path

from trust_hn.data.profile import endpoint_summary, run_profile, split_summary


class ProfileTests(unittest.TestCase):
    def test_split_overlap_is_counted_without_exporting_ids(self):
        rows = [
            {"id": "A", "split": "train"},
            {"id": "A", "split": "test"},
            {"id": "B", "split": "train"},
        ]
        result = split_summary(rows, "id", "split")
        self.assertEqual(result["patient_overlap_count"], 1)
        self.assertNotIn("A", json.dumps(result))

    def test_endpoint_summary_keeps_early_censoring_unknown(self):
        rows = [
            {"time": "100", "event": "1", "split": "train"},
            {"time": "300", "event": "0", "split": "train"},
            {"time": "900", "event": "0", "split": "test"},
        ]
        result = endpoint_summary(rows, "time", "event", 1.0, None, 730.5, "split")
        self.assertEqual(result["horizon_counts"]["event_by_horizon"], 1)
        self.assertEqual(result["horizon_counts"]["censored_before_horizon"], 1)
        self.assertEqual(result["horizon_counts"]["event_free_at_horizon"], 1)
        self.assertFalse(result["early_censoring_is_binary_negative"])

    def test_profile_writes_expected_artifacts(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            table = root / "patients.csv"
            table.write_text(
                "patient_id,split,os_days,event,age\n"
                "A,train,100,1,60\n"
                "B,calibration,300,0,\n"
                "C,test,900,0,70\n",
                encoding="utf-8",
            )
            spec = root / "spec.json"
            spec.write_text(
                json.dumps(
                    {
                        "study": "SYNTHETIC",
                        "field_candidates": {
                            "patient_id": ["patient_id"],
                            "split": ["split"],
                            "duration": ["os_days"],
                            "event": ["event"],
                        },
                        "duration_multiplier_to_days": 1.0,
                        "horizon_days": 730.5,
                    }
                ),
                encoding="utf-8",
            )
            output = root / "audit"
            summary = run_profile(table, spec, output)
            self.assertEqual(summary["n_rows"], 3)
            self.assertEqual(summary["split"]["patient_overlap_count"], 0)
            for name in (
                "data_dictionary_auto.csv",
                "missingness_auto.csv",
                "field_resolution.json",
                "audit_summary.json",
                "automated_audit.md",
            ):
                self.assertTrue((output / name).is_file(), name)


if __name__ == "__main__":
    unittest.main()