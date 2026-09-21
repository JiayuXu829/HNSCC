from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
import torch
import yaml

from trust_hn.pattern_surv_hn.t1r_development_cv import (
    T1RSpec,
    apply_t1r_gate,
    development_cross_fit,
)
from trust_hn.pattern_surv_hn.t1r_model import (
    TrainableClinicalResidualTranscriptomeCox,
)
from trust_hn.pattern_surv_hn.t1r_runner import _validate_patient_output_root
from trust_hn.pattern_surv_hn.transcriptome_contract import TranscriptomeContract
from trust_hn.pattern_surv_hn.v0_clinical_anchor import assert_aggregate_only

ROOT = Path(__file__).resolve().parents[1]
U8_DIR = (
    ROOT
    / "research_studies/01_pattern_surv_hn/core_backbone/"
    "U8_T1R_transcriptome_residual_shrinkage"
)
SPEC_PATH = U8_DIR / "frozen_t1r_transcriptome_spec.yaml"
GATE_PATH = U8_DIR / "frozen_t1r_exploratory_gate.yaml"


@pytest.fixture(scope="module")
def contract() -> TranscriptomeContract:
    return TranscriptomeContract.from_development(ROOT)


@pytest.fixture(scope="module")
def reduced_result(contract):
    full = T1RSpec.from_yaml(SPEC_PATH)
    reduced = replace(
        full,
        outer_folds=2,
        outer_repetition_seeds=(17,),
        inner_folds=2,
        top_k=5,
        residual_hidden_dim=2,
        anchor_alpha_grid=(0.01,),
        anchor_l1_ratio_grid=(0.5,),
        residual_penalty_grid=(0.1,),
        checkpoint_steps=(0, 1),
        residual_scale_grid=(0.2, 1.0),
    )
    return development_cross_fit(contract, reduced)


def test_frozen_u8_spec_matches_authorized_protocol():
    spec = T1RSpec.from_yaml(SPEC_PATH)
    assert spec.horizon_days == 730.5
    assert spec.outer_folds == 5
    assert spec.outer_repetition_seeds == (17, 29, 43, 71, 101)
    assert spec.inner_folds == 3
    assert spec.top_k == 500
    assert spec.residual_hidden_dim == 32
    assert spec.residual_penalty_grid == (0.01, 0.1, 1.0)
    assert spec.checkpoint_steps == (0, 10, 25, 50)
    assert spec.residual_scale_grid == (0.1, 0.2, 0.3, 0.4, 0.5, 1.0)
    assert spec.expected_n == 519
    assert spec.expected_events == 221
    assert spec.deterministic_algorithms is True


def test_t1r_model_has_frozen_scale_exact_fallback_and_rejects_bad_active_rows():
    model = TrainableClinicalResidualTranscriptomeCox(500, 32, seed=17)
    assert model.parameter_count == 16065
    assert model.parameter_count <= 50000
    assert all(parameter.dtype == torch.float64 for parameter in model.parameters())

    clinical = torch.tensor([0.2, -0.4, 0.8], dtype=torch.float64)
    transcriptome = torch.zeros((3, 500), dtype=torch.float64)
    transcriptome[0, 0] = np.nan
    active = torch.tensor([False, True, True], dtype=torch.bool)
    result = model(clinical, transcriptome, active)
    assert result.residual_score[0] == 0
    assert result.fused_score[0] == clinical[0]

    broken_active = active.clone()
    broken_active[1] = False
    broken = transcriptome.clone()
    broken[2, 1] = torch.inf
    with pytest.raises(ValueError, match="active transcriptome values must be finite"):
        model(clinical, broken, broken_active)


def test_reduced_t1r_cv_is_oof_complete_fold_bound_and_aggregate_only(reduced_result):
    oof, aggregate = reduced_result
    assert len(oof) == 519
    assert oof["native_id"].nunique() == 519
    assert set(oof["repetition_seed"]) == {17}
    assert oof["outer_fold"].nunique() == 2
    assert np.isfinite(
        oof[
            [
                "v0_risk_score",
                "v0_risk_24m",
                "t1r_residual_score",
                "t1r_risk_score",
                "t1r_risk_24m",
            ]
        ]
    ).all().all()
    assert oof["v0_risk_24m"].between(0, 1).all()
    assert oof["t1r_risk_24m"].between(0, 1).all()
    assert set(oof["selected_residual_scale"]).issubset({0.2, 1.0})
    assert len(aggregate["folds"]) == 2
    assert all(
        row["clinical_preprocessing"]["clinical_fit_n"] == row["train_n"]
        for row in aggregate["folds"]
    )
    assert all(
        row["modality_preprocessing"]["fit_n"] == row["train_n"]
        for row in aggregate["folds"]
    )
    assert max(row["fallback_residual_max_abs_error"] for row in aggregate["folds"]) == 0
    assert max(row["fallback_fused_max_abs_error"] for row in aggregate["folds"]) == 0
    assert_aggregate_only(aggregate)


def test_complexity_gate_rejects_equivalent_t1r_without_incremental_value():
    gate = yaml.safe_load(GATE_PATH.read_text(encoding="utf-8-sig"))
    oof = pd.DataFrame({
        "native_id": ["a", "b"] * 5,
        "v0_risk_score": [0.1] * 10,
        "v0_risk_24m": [0.2] * 10,
        "t1r_risk_score": [0.1] * 10,
        "t1r_risk_24m": [0.2] * 10,
    })
    metrics = {
        "ipcw_brier_24m": 0.18,
        "uno_c_24m": 0.61,
        "calibration_in_the_large_24m": 0.02,
        "calibration_slope_24m": 0.95,
    }
    per_seed = [
        {
            "repetition_seed": seed,
            "V0": metrics,
            "T1R": metrics,
            "delta_T1R_minus_V0": {"ipcw_brier_24m": 0.0, "uno_c_24m": 0.0},
        }
        for seed in (17, 29, 43, 71, 101)
    ]
    aggregate = {
        "per_seed_metrics": per_seed,
        "pattern_stratified_metrics": [
            {
                "metric_support": True,
                "delta_T1R_minus_V0": {"ipcw_brier_24m": 0.0},
            }
        ],
        "folds": [
            {
                "fallback_residual_max_abs_error": 0.0,
                "fallback_fused_max_abs_error": 0.0,
            }
        ],
        "parameter_count": 16065,
    }
    result = apply_t1r_gate(oof, aggregate, gate)
    assert result["coverage"]["pass"] is True
    assert result["structural"]["pass"] is True
    assert result["safety"]["pass"] is True
    assert result["incremental_value"]["pass"] is False
    assert result["decision"] == "T1R_DOES_NOT_EARN_COMPLEXITY"


def test_runner_keeps_patient_output_inside_git_ignored_prediction_root():
    allowed = ROOT / "results/predictions/pattern_surv_hn/U8_T1R_test"
    _validate_patient_output_root(ROOT, allowed)
    with pytest.raises(ValueError, match="patient-level output must remain"):
        _validate_patient_output_root(ROOT, ROOT / "results/metrics/U8_T1R")


def test_u8_spec_declares_post_hoc_exploratory_governance():
    spec_payload = yaml.safe_load(SPEC_PATH.read_text(encoding="utf-8-sig"))
    gate_payload = yaml.safe_load(GATE_PATH.read_text(encoding="utf-8-sig"))
    governance = spec_payload["governance"]
    assert spec_payload["status"] == "FROZEN_BEFORE_EXECUTION"
    assert governance["post_hoc_exploratory"] is True
    assert governance["outcomes_already_consumed"] is True
    assert governance["confirmatory_claim_allowed"] is False
    assert governance["external_validation_claim_allowed"] is False
    assert gate_payload["claim_boundary"]["does_not_support"] == [
        "confirmatory_superiority",
        "external_generalization",
        "transportability",
        "clinical_utility",
        "pristine_locked_confirmation",
    ]
