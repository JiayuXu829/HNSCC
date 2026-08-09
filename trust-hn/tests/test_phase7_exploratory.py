from __future__ import annotations

import json
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

from trust_hn.metrics.survival import structured_survival
from trust_hn.phase7.models import (
    Phase7FeaturePreprocessor,
    breslow_risk_at_horizon,
    encode_xgb_cox_labels,
    fit_predict_phase7_model,
)
from trust_hn.phase7.runner import aggregate_seed_predictions, verify_phase6_frozen_files


class Phase7ComparatorTests(unittest.TestCase):
    @staticmethod
    def synthetic_data(seed: int = 17):
        rng = np.random.default_rng(seed)
        n_train, n_eval = 72, 18
        clinical_train = pd.DataFrame(
            {
                "age": rng.normal(60, 8, n_train),
                "sex": rng.choice(["Female", "Male"], n_train),
                "stage": rng.choice(["II", "III", "IV"], n_train),
            }
        )
        clinical_eval = pd.DataFrame(
            {
                "age": rng.normal(62, 8, n_eval),
                "sex": rng.choice(["Female", "Male"], n_eval),
                "stage": rng.choice(["II", "III", "IV"], n_eval),
            }
        )
        modality_train = pd.DataFrame(rng.normal(size=(n_train, 8)))
        modality_eval = pd.DataFrame(rng.normal(size=(n_eval, 8)))
        modality_train.iloc[::7, 0] = np.nan
        modality_eval.iloc[::5, 0] = np.nan
        linear = (
            0.4 * (clinical_train["age"].to_numpy() - 60) / 8
            + 0.7 * modality_train[1].fillna(0).to_numpy()
        )
        event_time = rng.exponential(700 / np.exp(linear)) + 1.0
        censor_time = rng.exponential(1100, n_train) + 1.0
        event = event_time <= censor_time
        time = np.minimum(event_time, censor_time)
        y = structured_survival(event, time)
        return clinical_train, modality_train, y, clinical_eval, modality_eval

    def config(self) -> dict[str, object]:
        return {
            "cv_folds": 3,
            "numeric_modality_top_k": 8,
            "coxnet_alpha": 0.05,
            "coxnet_l1_ratio": 0.5,
            "coxnet_max_iter": 10000,
            "late_fusion_meta_alpha": 0.01,
            "gbsa_n_estimators": 20,
            "gbsa_learning_rate": 0.05,
            "gbsa_max_depth": 2,
            "gbsa_min_samples_leaf": 5,
            "gbsa_max_features": "sqrt",
            "xgb_n_estimators": 20,
            "xgb_learning_rate": 0.05,
            "xgb_max_depth": 2,
            "xgb_min_child_weight": 2.0,
            "xgb_subsample": 0.9,
            "xgb_colsample_bytree": 0.9,
            "xgb_reg_alpha": 0.0,
            "xgb_reg_lambda": 1.0,
            "xgb_tree_method": "hist",
            "xgb_n_jobs": 1,
        }

    def test_config_declares_post_hoc_scope_and_four_new_methods(self) -> None:
        path = Path("configs/phase7_exploratory_benchmarks.json")
        payload = json.loads(path.read_text(encoding="utf-8-sig"))
        self.assertEqual(payload["analysis_label"], "post hoc exploratory benchmark")
        self.assertEqual(set(payload["new_comparators"]), {"C1", "C2", "C3", "C4"})
        self.assertFalse(payload["governance"]["prespecified_locked_comparison"])
        self.assertFalse(payload["governance"]["external_outcomes_for_tuning"])
        self.assertEqual(payload["method_count_after_completion"]["total_labeled_approaches"], 14)

    def test_xgb_label_encoding_and_breslow_risk(self) -> None:
        event = np.array([True, False, True, False])
        time = np.array([2.0, 3.0, 5.0, 8.0])
        labels = encode_xgb_cox_labels(event, time)
        np.testing.assert_array_equal(labels, np.array([2.0, -3.0, 5.0, -8.0]))
        risk = breslow_risk_at_horizon(event, time, np.zeros(4), np.zeros(3), 5.0)
        self.assertTrue(np.isfinite(risk).all())
        self.assertTrue(((risk >= 0.0) & (risk <= 1.0)).all())
        self.assertTrue(np.allclose(risk, risk[0]))

    def test_preprocessor_is_train_only_and_preserves_missingness(self) -> None:
        clinical_train, modality_train, _, clinical_eval, modality_eval = self.synthetic_data()
        prep = Phase7FeaturePreprocessor("TCGA-HNSC", top_k=8).fit(clinical_train, modality_train)
        before = prep.modality_preprocessor.medians_.copy()
        blocks = prep.transform(clinical_eval, modality_eval)
        np.testing.assert_array_equal(before, prep.modality_preprocessor.medians_)
        self.assertEqual(blocks.clinical.shape[0], len(clinical_eval))
        self.assertEqual(blocks.modality.shape[0], len(clinical_eval))
        self.assertEqual(blocks.missing_aware.shape[0], len(clinical_eval))
        self.assertGreater(blocks.missing_aware.shape[1], blocks.modality.shape[1])
        self.assertTrue(np.isfinite(blocks.missing_aware).all())

    def test_all_new_models_return_finite_probabilities(self) -> None:
        clinical_train, modality_train, y, clinical_eval, modality_eval = self.synthetic_data()
        prep = Phase7FeaturePreprocessor("TCGA-HNSC", top_k=8).fit(clinical_train, modality_train)
        train = prep.transform(clinical_train, modality_train)
        evaluation = prep.transform(clinical_eval, modality_eval)
        for model_id in ("C1", "C2", "C3", "C4"):
            with self.subTest(model=model_id):
                prediction = fit_predict_phase7_model(
                    model_id,
                    train,
                    y,
                    evaluation,
                    horizon=730.5,
                    random_state=17,
                    config=self.config(),
                )
                self.assertEqual(prediction.risk_score.shape, (len(clinical_eval),))
                self.assertTrue(np.isfinite(prediction.risk_score).all())
                self.assertTrue(np.isfinite(prediction.risk_horizon).all())
                self.assertTrue(
                    ((prediction.risk_horizon >= 0.0) & (prediction.risk_horizon <= 1.0)).all()
                )

    def test_fixed_seed_predictions_are_deterministic(self) -> None:
        clinical_train, modality_train, y, clinical_eval, modality_eval = self.synthetic_data()
        prep = Phase7FeaturePreprocessor("TCGA-HNSC", top_k=8).fit(clinical_train, modality_train)
        train = prep.transform(clinical_train, modality_train)
        evaluation = prep.transform(clinical_eval, modality_eval)
        for model_id in ("C1", "C2", "C3", "C4"):
            first = fit_predict_phase7_model(
                model_id, train, y, evaluation, 730.5, 29, self.config()
            )
            second = fit_predict_phase7_model(
                model_id, train, y, evaluation, 730.5, 29, self.config()
            )
            np.testing.assert_allclose(first.risk_score, second.risk_score)
            np.testing.assert_allclose(first.risk_horizon, second.risk_horizon)

    def test_seed_aggregation_requires_complete_aligned_rows(self) -> None:
        rows = []
        for seed, offset in ((17, 0.0), (29, 0.2)):
            for native_id, score in (("p1", 0.1), ("p2", 0.3)):
                rows.append(
                    {
                        "native_id": native_id,
                        "cohort": "TEST",
                        "model": "C1",
                        "seed": seed,
                        "risk_score": score + offset,
                        "risk_horizon": score + offset,
                    }
                )
        aggregated = aggregate_seed_predictions(pd.DataFrame(rows), [17, 29])
        self.assertEqual(aggregated["native_id"].tolist(), ["p1", "p2"])
        np.testing.assert_allclose(aggregated["risk_score"], [0.2, 0.4])
        with self.assertRaises(ValueError):
            aggregate_seed_predictions(pd.DataFrame(rows[:-1]), [17, 29])

    def test_phase6_registered_files_remain_unchanged(self) -> None:
        verification = verify_phase6_frozen_files(Path("."))
        self.assertTrue(verification["all_match"])
        self.assertEqual(verification["mismatches"], [])

    def test_prediction_directory_is_git_ignored(self) -> None:
        ignore = Path(".gitignore").read_text(encoding="utf-8")
        self.assertIn("/results/predictions/*", ignore)


if __name__ == "__main__":
    unittest.main()
