from __future__ import annotations

import unittest
from pathlib import Path

from trust_hn.data.phase3_features import load_phase3_study_data


class Phase3DataTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.root = Path(__file__).resolve().parents[1]

    def test_development_loaders_exclude_sealed_rows(self) -> None:
        expected = {
            "RADCURE": (1215, 303),
            "HANCOCK": (489, 122),
            "TCGA-HNSC": (415, 104),
        }
        for study, counts in expected.items():
            data = load_phase3_study_data(self.root, study, build_expression=False)
            self.assertEqual((len(data.train_ids), len(data.calibration_ids)), counts)
            self.assertTrue(data.train_event.shape == data.train_time.shape)
            self.assertTrue(data.calibration_event.shape == data.calibration_time.shape)
            self.assertNotIn("sealed_test", set(data.split_roles))
            self.assertNotIn("external_test", set(data.split_roles))

    def test_hancock_has_structured_modality_features(self) -> None:
        data = load_phase3_study_data(self.root, "HANCOCK", build_expression=False)
        self.assertIsNotNone(data.modality)
        self.assertGreater(data.modality.shape[1], 10)

    def test_radcure_modality_remains_blocked(self) -> None:
        data = load_phase3_study_data(self.root, "RADCURE", build_expression=False)
        self.assertIsNone(data.modality)
        self.assertIn("ORCESTRA", data.modality_blocker or "")


if __name__ == "__main__":
    unittest.main()
