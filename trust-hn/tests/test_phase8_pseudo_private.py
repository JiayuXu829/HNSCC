from __future__ import annotations

import unittest
from pathlib import Path

from trust_hn.phase8.runner import METHODS, load_config, load_inner_hancock_features


class Phase8PseudoPrivateTests(unittest.TestCase):
    def test_config_preserves_overlap_disclosure(self) -> None:
        config = load_config(Path("."))
        self.assertEqual(config["cohort_alias"], "inner_hancock")
        self.assertFalse(config["independent_private_validation"])
        self.assertTrue(config["known_cohort_overlap"])
        self.assertEqual(tuple(config["methods"]), METHODS)

    def test_135_cases_are_reassembled_with_expected_source_roles(self) -> None:
        features, provenance = load_inner_hancock_features(Path("."))
        self.assertEqual(features.cohort, "inner_hancock")
        self.assertEqual(features.role, "pseudo_private_overlap")
        self.assertEqual(len(features.ids), 135)
        self.assertEqual(
            provenance["source_partition"].value_counts().to_dict(),
            {"train": 88, "sealed_test": 30, "calibration": 17},
        )
        self.assertEqual(len(set(features.ids.astype(str))), 135)

    def test_patient_predictions_remain_git_ignored(self) -> None:
        ignore = Path(".gitignore").read_text(encoding="utf-8")
        self.assertIn("/results/predictions/*", ignore)


if __name__ == "__main__":
    unittest.main()
