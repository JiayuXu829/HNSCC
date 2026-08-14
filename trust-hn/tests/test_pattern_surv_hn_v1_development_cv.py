from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
import torch
import yaml

from trust_hn.pattern_surv_hn import HancockContractBuilder
from trust_hn.pattern_surv_hn.v0_clinical_anchor import V0Spec
from trust_hn.pattern_surv_hn.v1_deep_sets_smoke import V1SmokeSpec
from trust_hn.pattern_surv_hn.v1_development_cv import (
    DEFAULT_ARCHITECTURE_SPEC_RELATIVE,
    DEFAULT_GATE_RELATIVE,
    DEFAULT_SPEC_RELATIVE,
    DEFAULT_V0_OOF_RELATIVE,
    DEFAULT_V0_SPEC_RELATIVE,
    U2Spec,
    _load_v0_reference,
    _make_cox_loss_plan,
    _negative_breslow_cox_loss,
    apply_complexity_gate,
    breslow_risk_at_horizon,
    development_cross_fit,
)
from trust_hn.pattern_surv_hn.v1_trainable_smoke import negative_breslow_cox_loss

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def contract():
    return HancockContractBuilder(ROOT).build()


@pytest.fixture(scope="module")
def architecture():
    return V1SmokeSpec.from_yaml(ROOT / DEFAULT_ARCHITECTURE_SPEC_RELATIVE)


def test_frozen_u2_spec_matches_authorized_development_protocol():
    spec = U2Spec.from_yaml(ROOT / DEFAULT_SPEC_RELATIVE)
    assert spec.outer_folds == 5
    assert spec.outer_repetition_seeds == (17, 29, 43, 71, 101)
    assert spec.inner_folds == 3
    assert spec.residual_penalty_grid == (0.01, 0.1)
    assert spec.checkpoint_steps == (0, 25, 50, 100, 200)
    assert spec.expected_n == 610
    assert spec.expected_events == 173


def test_frozen_v0_reference_has_exact_repeated_oof_coverage():
    frame = _load_v0_reference(ROOT / DEFAULT_V0_OOF_RELATIVE)
    assert len(frame) == 3050
    assert frame["native_id"].nunique() == 610
    assert set(frame["repetition_seed"]) == {17, 29, 43, 71, 101}
    assert frame.groupby(["repetition_seed", "native_id"]).size().eq(1).all()


def test_vectorized_breslow_loss_matches_u1_4_reference_with_ties():
    duration = torch.tensor([8.0, 8.0, 5.0, 4.0, 4.0, 2.0], dtype=torch.float64)
    event = torch.tensor([0, 1, 1, 0, 1, 1], dtype=torch.bool)
    score = torch.tensor([0.4, -0.2, 0.7, 0.1, -0.3, 0.6], dtype=torch.float64)
    expected = negative_breslow_cox_loss(duration, event, score)
    observed = _negative_breslow_cox_loss(score, _make_cox_loss_plan(duration, event))
    assert float(observed) == pytest.approx(float(expected), abs=1e-12)


def test_training_fold_breslow_risk_is_score_shift_invariant():
    duration = np.asarray([100, 250, 500, 800, 1000], dtype=float)
    event = np.asarray([1, 1, 0, 1, 0], dtype=bool)
    train_score = np.asarray([-0.4, 0.2, 0.8, -0.1, 0.5])
    eval_score = np.asarray([-0.2, 0.4, 1.0])
    first = breslow_risk_at_horizon(duration, event, train_score, eval_score, 730.5)
    second = breslow_risk_at_horizon(
        duration, event, train_score + 19.0, eval_score + 19.0, 730.5
    )
    np.testing.assert_allclose(first, second, atol=1e-12, rtol=0)
    assert np.all((first >= 0) & (first <= 1))


def test_complexity_gate_rejects_equivalent_model_without_incremental_value():
    gate = yaml.safe_load((ROOT / DEFAULT_GATE_RELATIVE).read_text(encoding="utf-8-sig"))
    oof = pd.DataFrame({
        "native_id": ["a", "b", "a", "b", "a", "b", "a", "b", "a", "b"],
        "v0_risk_score": [0.1] * 10,
        "v0_risk_24m": [0.2] * 10,
        "v1_risk_score": [0.1] * 10,
        "v1_risk_24m": [0.2] * 10,
    })
    seed_rows = []
    for seed in (17, 29, 43, 71, 101):
        metrics = {
            "ipcw_brier_24m": 0.18,
            "uno_c_24m": 0.61,
            "calibration_in_the_large_24m": 0.02,
            "calibration_slope_24m": 0.95,
        }
        seed_rows.append({
            "repetition_seed": seed,
            "V0": metrics,
            "V1": metrics,
            "delta_V1_minus_V0": {"ipcw_brier_24m": 0.0, "uno_c_24m": 0.0},
        })
    aggregate = {
        "per_seed_metrics": seed_rows,
        "pattern_stratified_metrics": [{
            "metric_support": True,
            "delta_V1_minus_V0": {"ipcw_brier_24m": 0.0},
        }],
        "folds": [{
            "fallback_residual_max_abs_error": 0.0,
            "fallback_fused_max_abs_error": 0.0,
        }],
        "parameter_count": 3225,
    }
    result = apply_complexity_gate(oof, aggregate, gate)
    assert result["coverage"]["pass"] is True
    assert result["structural"]["pass"] is True
    assert result["safety"]["pass"] is True
    assert result["incremental_value"]["pass"] is False
    assert result["decision"] == "V1_DOES_NOT_EARN_COMPLEXITY"


def test_reduced_development_cv_is_oof_complete_fold_bound_and_sealed(
    contract, architecture
):
    full_u2 = U2Spec.from_yaml(ROOT / DEFAULT_SPEC_RELATIVE)
    reduced_u2 = replace(
        full_u2,
        outer_folds=2,
        outer_repetition_seeds=(17,),
        inner_folds=2,
        residual_penalty_grid=(0.1,),
        checkpoint_steps=(0, 1),
    )
    full_v0 = V0Spec.from_yaml(ROOT / DEFAULT_V0_SPEC_RELATIVE)
    reduced_v0 = replace(
        full_v0,
        outer_folds=2,
        outer_repetition_seeds=(17,),
        inner_folds=2,
        alpha_grid=(0.01,),
        l1_ratio_grid=(0.5,),
    )
    oof, aggregate = development_cross_fit(
        contract,
        reduced_u2,
        reduced_v0,
        architecture,
        v0_reference=None,
    )
    assert len(oof) == 610
    assert oof["native_id"].nunique() == 610
    assert oof["outer_fold"].nunique() == 2
    assert np.isfinite(
        oof[["v0_risk_score", "v0_risk_24m", "v1_risk_score", "v1_risk_24m"]]
    ).all().all()
    assert oof["v1_risk_24m"].between(0, 1).all()
    assert len(aggregate["folds"]) == 2
    assert all(
        row["clinical_preprocessing"]["clinical_fit_n"] == row["train_n"]
        for row in aggregate["folds"]
    )
    assert all(
        modality["fit_n"] == row["train_n"]
        for row in aggregate["folds"]
        for modality in row["modality_preprocessing"].values()
    )
    frame = contract.patient_frame()
    sealed = frame[frame["official_partition"] == "test"]
    assert sealed["duration_days"].isna().all()
    assert sealed["event"].isna().all()
    assert max(row["fallback_residual_max_abs_error"] for row in aggregate["folds"]) == 0
    assert max(row["fallback_fused_max_abs_error"] for row in aggregate["folds"]) == 0
