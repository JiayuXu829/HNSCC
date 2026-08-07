from __future__ import annotations

import unittest

import numpy as np

from trust_hn.metrics.survival import (
    evaluate_survival_predictions,
    ipcw_binary_outcomes,
)


class Phase3MetricTests(unittest.TestCase):
    def setUp(self) -> None:
        self.train_event = np.array([1, 0, 1, 0, 1, 0, 1, 0], dtype=bool)
        self.train_time = np.array([100, 900, 300, 1000, 600, 1200, 700, 1500], dtype=float)

    def test_early_censored_patient_has_zero_ipcw_weight(self) -> None:
        event = np.array([False, True, False, True])
        time = np.array([200.0, 300.0, 900.0, 800.0])
        outcome, weight = ipcw_binary_outcomes(
            self.train_event, self.train_time, event, time, horizon=730.5
        )
        self.assertEqual(outcome.tolist(), [0.0, 1.0, 0.0, 0.0])
        self.assertEqual(weight[0], 0.0)
        self.assertGreater(weight[1], 0.0)
        self.assertGreater(weight[2], 0.0)
        self.assertGreater(weight[3], 0.0)

    def test_better_risk_has_lower_ipcw_brier_and_higher_cindex(self) -> None:
        event = np.array([True, True, False, False, True, False])
        time = np.array([100, 400, 900, 1200, 650, 1500], dtype=float)
        good = np.array([0.9, 0.8, 0.1, 0.05, 0.7, 0.1])
        bad = 1.0 - good
        good_metrics = evaluate_survival_predictions(
            self.train_event, self.train_time, event, time, good, good, 730.5
        )
        bad_metrics = evaluate_survival_predictions(
            self.train_event, self.train_time, event, time, bad, bad, 730.5
        )
        self.assertLess(good_metrics["ipcw_brier"], bad_metrics["ipcw_brier"])
        self.assertGreater(good_metrics["harrell_c"], bad_metrics["harrell_c"])
        self.assertIn("calibration_in_the_large", good_metrics)
        self.assertIn("calibration_slope", good_metrics)


if __name__ == "__main__":
    unittest.main()
