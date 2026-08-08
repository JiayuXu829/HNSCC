from __future__ import annotations

import unittest

import numpy as np
import pandas as pd

from trust_hn.evaluation.phase5 import (
    _acceptance_checks,
    apply_modality_perturbation,
    learned_nonnegative_weights,
    subgroup_labels,
)
from trust_hn.reliability.ablations import ablated_unreliability, weighted_score


class Phase5StressTests(unittest.TestCase):
    def test_random_dropout_is_deterministic_and_severity_ordered(self) -> None:
        frame = pd.DataFrame(np.arange(200, dtype=float).reshape(20, 10))
        low = apply_modality_perturbation(
            frame, frame, study="TCGA-HNSC", scenario="random_cell_dropout_10pct", seed=17
        )
        repeat = apply_modality_perturbation(
            frame, frame, study="TCGA-HNSC", scenario="random_cell_dropout_10pct", seed=17
        )
        high = apply_modality_perturbation(
            frame, frame, study="TCGA-HNSC", scenario="random_cell_dropout_30pct", seed=17
        )
        pd.testing.assert_frame_equal(low, repeat)
        self.assertGreater(high.isna().sum().sum(), low.isna().sum().sum())
        self.assertEqual(frame.isna().sum().sum(), 0)

    def test_complete_dropout_masks_every_modality_value(self) -> None:
        frame = pd.DataFrame({"blood": [1.0, 2.0], "cd3_z": [3.0, 4.0]})
        result = apply_modality_perturbation(
            frame, frame, study="HANCOCK", scenario="complete_modality_dropout", seed=29
        )
        self.assertTrue(result.isna().all().all())

    def test_gate_ablation_uses_only_prespecified_components(self) -> None:
        frame = pd.DataFrame(
            {
                "clinical_ood_rank": [0.2, 0.8],
                "modality_ood_rank": [0.3, 0.7],
                "rank_clinical_uncertainty_sd": [0.4, 0.6],
                "rank_modality_uncertainty_sd": [0.5, 0.9],
                "clinical_unreliability": [0.1, 0.2],
                "modality_unreliability": [0.2, 0.3],
            }
        )
        clinical, modality = ablated_unreliability(frame, "ood_only")
        np.testing.assert_allclose(clinical, [0.2, 0.8])
        np.testing.assert_allclose(modality, [0.3, 0.7])
        clinical, modality = ablated_unreliability(frame, "uncertainty_only")
        np.testing.assert_allclose(clinical, [0.4, 0.6])
        np.testing.assert_allclose(modality, [0.5, 0.9])

    def test_nonnegative_weights_and_weighted_score(self) -> None:
        x = np.array([[0.0, 1.0], [1.0, 0.0], [1.0, 1.0], [0.0, 0.0]])
        target = np.array([0.1, 0.8, 0.9, 0.0])
        weights = learned_nonnegative_weights(x, target)
        self.assertTrue((weights >= 0).all())
        self.assertAlmostEqual(float(weights.sum()), 1.0)
        score = weighted_score(x, weights)
        self.assertEqual(score.shape, (4,))
        self.assertTrue(((score >= 0) & (score <= 1)).all())

    def test_acceptance_uses_identical_b7_selected_subset(self) -> None:
        metrics = pd.DataFrame(
            [
                {
                    "study": "TEST",
                    "seed": 17,
                    "scenario": "clean",
                    "model": "B7",
                    "gate_variant": "full_equal_weight",
                    "profile": "90",
                    "ipcw_brier": 0.20,
                    "b6_subset_ipcw_brier": 0.19,
                    "b2_subset_ipcw_brier": 0.30,
                },
                {
                    "study": "TEST",
                    "seed": 17,
                    "scenario": "clean",
                    "model": "B6",
                    "gate_variant": "none",
                    "profile": "full",
                    "ipcw_brier": 0.05,
                },
                {
                    "study": "TEST",
                    "seed": 17,
                    "scenario": "complete_modality_dropout",
                    "model": "B7",
                    "gate_variant": "full_equal_weight",
                    "profile": "100",
                    "ipcw_brier": 0.21,
                    "b6_subset_ipcw_brier": 0.50,
                    "b2_subset_ipcw_brier": 0.20,
                },
            ]
        )
        actions = pd.DataFrame(
            [
                {
                    "study": "TEST",
                    "seed": 17,
                    "scenario": scenario,
                    "gate_variant": "full_equal_weight",
                    "profile": profile,
                    "action": action,
                    "rate": rate,
                }
                for scenario, profile, action, rate in [
                    ("clean", "90", "AUGMENT", 1.0),
                    ("clean", "90", "FALLBACK", 0.0),
                    ("clean", "90", "ABSTAIN", 0.0),
                    ("location_shift_1sd", "90", "FALLBACK", 0.2),
                    ("location_shift_1sd", "90", "ABSTAIN", 0.0),
                    ("complete_modality_dropout", "90", "FALLBACK", 1.0),
                    ("complete_modality_dropout", "90", "ABSTAIN", 0.0),
                    ("complete_modality_dropout", "100", "FALLBACK", 1.0),
                ]
            ]
        )
        margins = {
            "clean_b7_vs_b6_brier_noninferiority": 0.01,
            "complete_dropout_b7_100_vs_b2_brier_noninferiority": 0.01,
            "complete_dropout_fallback_rate_minimum": 0.90,
            "severe_shift_action_response_increase_minimum": 0.10,
        }
        checks = _acceptance_checks(metrics, actions, margins, seed_count=1).set_index("check")
        self.assertAlmostEqual(checks.loc["clean_primary_b7_vs_b6_brier", "value"], 0.01)
        self.assertAlmostEqual(checks.loc["complete_dropout_b7_100_vs_b2_brier", "value"], 0.01)

    def test_subgroup_labels_are_stable_and_outcome_free(self) -> None:
        clinical = pd.DataFrame(
            {
                "sex": ["male", "female"],
                "age": [60, 70],
                "site": ["Oropharynx", "Oral cavity"],
                "stage": ["II", "IV"],
                "hpv": ["positive", None],
            }
        )
        missing = np.array([False, True])
        labels = subgroup_labels(clinical, missing, study="TCGA-HNSC")
        self.assertEqual(labels["age_group"].tolist(), ["<65", ">=65"])
        self.assertEqual(labels["site_group"].tolist(), ["oropharynx", "other"])
        self.assertEqual(labels["natural_modality_missingness"].tolist(), ["complete", "missing"])


if __name__ == "__main__":
    unittest.main()
