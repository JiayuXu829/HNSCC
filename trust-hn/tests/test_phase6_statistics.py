from __future__ import annotations

import unittest
from pathlib import Path

import numpy as np
import pandas as pd

from trust_hn.data.phase3_features import StudyData
from trust_hn.evaluation.phase6 import (
    OutcomeData,
    aggregate_seed_predictions,
    load_phase6_outcomes,
    paired_bootstrap_metrics,
    paired_comparison_metrics,
    paired_prediction_set_bootstrap,
    percentile_intervals,
)
from trust_hn.reliability.gating import assign_actions


def synthetic_development(n_train: int = 80, n_calibration: int = 20) -> StudyData:
    rng = np.random.default_rng(11)
    total = n_train + n_calibration
    train_time = rng.uniform(100, 1800, n_train)
    train_event = rng.random(n_train) < 0.55
    calibration_time = rng.uniform(100, 1600, n_calibration)
    calibration_event = rng.random(n_calibration) < 0.5
    return StudyData(
        study="TEST",
        train_ids=np.asarray([f"t{i}" for i in range(n_train)]),
        calibration_ids=np.asarray([f"c{i}" for i in range(n_calibration)]),
        train_event=train_event,
        train_time=train_time,
        calibration_event=calibration_event,
        calibration_time=calibration_time,
        split_roles=tuple(["train"] * n_train + ["calibration"] * n_calibration),
        clinical=pd.DataFrame({"age": rng.normal(60, 5, total)}),
        modality=pd.DataFrame({"x": rng.normal(size=total)}),
    )


def synthetic_predictions(n: int = 40) -> pd.DataFrame:
    base = np.linspace(0.05, 0.75, n)
    frame = pd.DataFrame()
    for offset, model in enumerate(("b2", "b4", "b5", "b6")):
        frame[f"{model}_score"] = base + offset * 0.01
        frame[f"{model}_risk"] = np.clip(base + offset * 0.01, 0, 1)
    frame["b7_score"] = frame["b6_score"]
    frame["b7_risk"] = frame["b6_risk"]
    missing_rows = [index for index in (2, 7) if index < n]
    frame.loc[missing_rows, ["b7_score", "b7_risk"]] = np.nan
    return frame


class Phase6StatisticsTests(unittest.TestCase):
    def test_outcomes_refuse_access_before_consumption(self) -> None:
        root = Path(__file__).resolve().parents[1]
        with self.assertRaises(PermissionError):
            load_phase6_outcomes(root, "GSE65858", ["secret"])

    def test_complete_modality_missingness_forces_fallback_unless_abstaining(self) -> None:
        actions, _ = assign_actions(
            np.asarray([0.2, 0.95]),
            np.asarray([0.1, 0.1]),
            np.asarray([True, True]),
            clinical_threshold=0.9,
            modality_threshold=0.9,
        )
        self.assertEqual(actions.tolist(), ["FALLBACK", "ABSTAIN"])

    def test_seed_aggregation_uses_majority_consensus(self) -> None:
        frames = []
        for seed in range(5):
            frame = synthetic_predictions(3).iloc[:3].copy()
            frame["b7_action_90"] = [
                "ABSTAIN" if seed < 3 else "AUGMENT",
                "FALLBACK" if seed < 3 else "AUGMENT",
                "AUGMENT",
            ]
            frame["b7_risk_90"] = [np.nan if seed < 3 else 0.2, 0.6, 0.7]
            frames.append(frame)
        result = aggregate_seed_predictions(frames)
        self.assertEqual(result["b7_action"].tolist(), ["ABSTAIN", "FALLBACK", "AUGMENT"])
        self.assertTrue(np.isnan(result.loc[0, "b7_risk"]))
        self.assertAlmostEqual(result.loc[1, "b7_risk"], result.loc[1, "b2_risk"])

    def test_paired_point_comparisons_use_identical_b7_subset(self) -> None:
        development = synthetic_development()
        n = 40
        rng = np.random.default_rng(29)
        outcomes = OutcomeData(
            "TEST", np.asarray([f"p{i}" for i in range(n)]),
            rng.random(n) < 0.5, rng.uniform(100, 1400, n),
        )
        predictions = synthetic_predictions(n)
        result = paired_comparison_metrics(
            development, outcomes, predictions, horizon=730.5, survival_floor=0.05
        ).set_index("comparison")
        self.assertEqual(int(result.loc["B7_vs_B6", "n"]), n - 2)
        self.assertEqual(int(result.loc["B7_vs_B2", "n"]), n - 2)
        self.assertEqual(int(result.loc["B6_vs_B5", "n"]), n)

    def test_paired_bootstrap_is_deterministic_and_uses_same_b7_subset(self) -> None:
        development = synthetic_development()
        n = 40
        rng = np.random.default_rng(19)
        outcomes = OutcomeData(
            "TEST",
            np.asarray([f"p{i}" for i in range(n)]),
            rng.random(n) < 0.5,
            rng.uniform(100, 1400, n),
        )
        predictions = synthetic_predictions(n)
        first_metrics, first_comparisons = paired_bootstrap_metrics(
            development,
            outcomes,
            predictions,
            replicates=8,
            random_state=77,
            horizon=730.5,
            survival_floor=0.05,
        )
        second_metrics, second_comparisons = paired_bootstrap_metrics(
            development,
            outcomes,
            predictions,
            replicates=8,
            random_state=77,
            horizon=730.5,
            survival_floor=0.05,
        )
        pd.testing.assert_frame_equal(first_metrics, second_metrics)
        pd.testing.assert_frame_equal(first_comparisons, second_comparisons)
        b7_comparisons = first_comparisons.loc[
            first_comparisons["comparison"].isin(["B7_vs_B6", "B7_vs_B2"])
        ]
        pivot = b7_comparisons.pivot(index="replicate", columns="comparison", values="n")
        self.assertTrue((pivot["B7_vs_B6"] == pivot["B7_vs_B2"]).all())

    def test_prediction_set_bootstrap_is_paired_and_deterministic(self) -> None:
        development = synthetic_development()
        n = 30
        rng = np.random.default_rng(23)
        outcomes = OutcomeData(
            "TEST",
            np.asarray([f"p{i}" for i in range(n)]),
            rng.random(n) < 0.5,
            rng.uniform(100, 1400, n),
        )
        reference = synthetic_predictions(n)
        control = synthetic_predictions(n)
        control["b6_risk"] = np.clip(control["b6_risk"] + 0.03, 0, 1)
        first = paired_prediction_set_bootstrap(
            development,
            outcomes,
            reference,
            {"control": control},
            models=("B6", "B7"),
            replicates=5,
            random_state=91,
            horizon=730.5,
            survival_floor=0.05,
        )
        second = paired_prediction_set_bootstrap(
            development,
            outcomes,
            reference,
            {"control": control},
            models=("B6", "B7"),
            replicates=5,
            random_state=91,
            horizon=730.5,
            survival_floor=0.05,
        )
        pd.testing.assert_frame_equal(first, second)
        self.assertEqual(set(first["model"]), {"B6", "B7"})
        self.assertTrue((first["reference_assay"] == "original").all())

    def test_percentile_intervals_are_aggregate_only(self) -> None:
        bootstrap = pd.DataFrame(
            {
                "model": ["B2"] * 4,
                "ipcw_brier": [0.1, 0.2, 0.15, 0.12],
            }
        )
        result = percentile_intervals(
            bootstrap, group_columns=["model"], value_columns=["ipcw_brier"]
        )
        self.assertEqual(result.loc[0, "model"], "B2")
        self.assertEqual(result.loc[0, "valid_replicates"], 4)
        self.assertNotIn("patient_id", result.columns)


if __name__ == "__main__":
    unittest.main()
