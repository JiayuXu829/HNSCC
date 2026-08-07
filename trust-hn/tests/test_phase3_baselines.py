from __future__ import annotations

import unittest

import numpy as np
import pandas as pd

from trust_hn.models.survival_baselines import (
    TabularPreprocessor,
    fit_predict_survival_model,
    structured_survival,
)


class Phase3BaselineTests(unittest.TestCase):
    def synthetic(self):
        rng = np.random.default_rng(17)
        n = 80
        age = rng.normal(60, 8, n)
        stage = np.where(age > 60, "III/IV", "I/II")
        sex = np.where(np.arange(n) % 2, "male", "female")
        x = pd.DataFrame({"age": age, "stage": stage, "sex": sex})
        event = rng.random(n) < 0.55
        time = np.maximum(20.0, 1200.0 - 8.0 * age + rng.normal(0, 120, n))
        return x, event, time

    def test_preprocessor_fits_median_on_training_only(self) -> None:
        train = pd.DataFrame({"age": [10.0, np.nan, 30.0], "site": ["A", "B", None]})
        evaluation = pd.DataFrame({"age": [10000.0], "site": ["UNSEEN"]})
        prep = TabularPreprocessor(numeric=["age"], categorical=["site"])
        prep.fit(train)
        transformed = prep.transform(evaluation)
        self.assertTrue(np.isfinite(transformed).all())
        self.assertAlmostEqual(float(prep.numeric_medians_["age"]), 20.0)

    def test_b0_to_b3_produce_valid_probabilities(self) -> None:
        x, event, time = self.synthetic()
        y = structured_survival(event, time)
        train = np.arange(60)
        evaluation = np.arange(60, 80)
        prep = TabularPreprocessor(numeric=["age"], categorical=["stage", "sex"])
        x_train = prep.fit_transform(x.iloc[train])
        x_eval = prep.transform(x.iloc[evaluation])
        for model_id in ("B0", "B1", "B2", "B3"):
            prediction = fit_predict_survival_model(
                model_id=model_id,
                x_train=x_train,
                y_train=y[train],
                x_eval=x_eval,
                horizon=730.5,
                random_state=17,
                config={
                    "coxph_alpha": 0.01,
                    "coxnet_alpha": 0.05,
                    "coxnet_l1_ratio": 0.5,
                    "coxnet_max_iter": 100000,
                    "rsf_n_estimators": 25,
                    "rsf_min_samples_leaf": 5,
                    "rsf_max_features": "sqrt",
                },
            )
            self.assertEqual(prediction.risk_horizon.shape, (20,))
            self.assertTrue(np.isfinite(prediction.risk_horizon).all())
            self.assertTrue(((prediction.risk_horizon >= 0) & (prediction.risk_horizon <= 1)).all())

    def test_random_survival_forest_is_seed_reproducible(self) -> None:
        x, event, time = self.synthetic()
        y = structured_survival(event, time)
        prep = TabularPreprocessor(numeric=["age"], categorical=["stage", "sex"])
        matrix = prep.fit_transform(x)
        cfg = {
            "rsf_n_estimators": 20,
            "rsf_min_samples_leaf": 5,
            "rsf_max_features": "sqrt",
        }
        first = fit_predict_survival_model("B3", matrix[:60], y[:60], matrix[60:], 730.5, 29, cfg)
        second = fit_predict_survival_model("B3", matrix[:60], y[:60], matrix[60:], 730.5, 29, cfg)
        np.testing.assert_allclose(first.risk_horizon, second.risk_horizon)


if __name__ == "__main__":
    unittest.main()
