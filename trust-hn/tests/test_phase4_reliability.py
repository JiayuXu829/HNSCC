from __future__ import annotations

import unittest

import numpy as np

from trust_hn.reliability.gating import (
    TripleOODDetector,
    assign_actions,
    empirical_percentile,
    equal_weight_score,
    gated_risk,
    quantile_threshold,
)


class Phase4ReliabilityTests(unittest.TestCase):
    def test_synthetic_shift_has_higher_ood_scores(self) -> None:
        rng = np.random.default_rng(17)
        train = rng.normal(0.0, 1.0, size=(180, 8))
        in_distribution = rng.normal(0.0, 1.0, size=(60, 8))
        shifted = rng.normal(4.0, 1.0, size=(60, 8))
        detector = TripleOODDetector(
            n_neighbors=8,
            isolation_estimators=50,
            max_features=8,
            random_state=17,
        ).fit(train)
        in_scores = detector.score(in_distribution)
        shift_scores = detector.score(shifted)
        self.assertGreater(np.median(shift_scores.mahalanobis), np.median(in_scores.mahalanobis))
        self.assertGreater(np.median(shift_scores.knn), np.median(in_scores.knn))
        self.assertGreater(
            np.median(shift_scores.isolation_forest),
            np.median(in_scores.isolation_forest),
        )

    def test_calibration_referenced_percentiles_and_equal_weights(self) -> None:
        reference = np.array([1.0, 2.0, 3.0, 4.0])
        ranks = empirical_percentile(np.array([0.0, 2.0, 5.0]), reference)
        np.testing.assert_allclose(ranks, [0.0, 0.5, 1.0])
        score = equal_weight_score(ranks, np.array([0.0, 1.0, 0.5]))
        np.testing.assert_allclose(score, [0.0, 0.75, 0.75])
        self.assertEqual(quantile_threshold(reference, 0.5), 3.0)
        constant = empirical_percentile(np.array([0.0, 1.0]), np.zeros(4))
        np.testing.assert_allclose(constant, [0.0, 1.0])

    def test_gate_precedence_and_final_risk(self) -> None:
        actions, reasons = assign_actions(
            np.array([0.1, 0.1, 0.9]),
            np.array([0.1, 0.9, 0.1]),
            np.array([False, False, True]),
            clinical_threshold=0.8,
            modality_threshold=0.8,
        )
        self.assertEqual(actions.tolist(), ["AUGMENT", "FALLBACK", "ABSTAIN"])
        self.assertEqual(
            reasons.tolist(),
            ["modality_reliable", "modality_unreliable", "clinical_unreliable"],
        )
        risk = gated_risk(
            np.array([0.2, 0.3, 0.4]),
            np.array([0.25, 0.35, 0.45]),
            actions,
        )
        self.assertAlmostEqual(risk[0], 0.25)
        self.assertAlmostEqual(risk[1], 0.3)
        self.assertTrue(np.isnan(risk[2]))


if __name__ == "__main__":
    unittest.main()
