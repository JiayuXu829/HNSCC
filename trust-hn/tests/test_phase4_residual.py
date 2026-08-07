from __future__ import annotations

import unittest

import numpy as np

from trust_hn.metrics.survival import structured_survival
from trust_hn.models.residual_fusion import StackedResidualSurvivalModel


class Phase4ResidualModelTests(unittest.TestCase):
    def test_stacked_residual_model_returns_valid_reproducible_risks(self) -> None:
        rng = np.random.default_rng(29)
        n = 100
        anchor = rng.normal(size=n)
        modality = rng.normal(size=(n, 5))
        linear = anchor + 0.7 * modality[:, 0]
        time = np.maximum(20.0, 900.0 - 140.0 * linear + rng.normal(0, 80, n))
        event = rng.random(n) < 0.7
        outcome = structured_survival(event, time)
        config = {
            "coxnet_alpha": 0.05,
            "coxnet_l1_ratio": 0.5,
            "coxnet_max_iter": 100000,
        }
        first = StackedResidualSurvivalModel(config).fit(
            anchor[:80], modality[:80], outcome[:80], horizon=730.5
        )
        second = StackedResidualSurvivalModel(config).fit(
            anchor[:80], modality[:80], outcome[:80], horizon=730.5
        )
        prediction = first.predict(anchor[80:], modality[80:])
        repeat = second.predict(anchor[80:], modality[80:])
        self.assertEqual(prediction.risk_horizon.shape, (20,))
        self.assertTrue(np.isfinite(prediction.risk_horizon).all())
        self.assertTrue(((prediction.risk_horizon >= 0) & (prediction.risk_horizon <= 1)).all())
        np.testing.assert_allclose(prediction.risk_horizon, repeat.risk_horizon)


if __name__ == "__main__":
    unittest.main()
