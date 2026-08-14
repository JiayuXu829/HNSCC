from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

from trust_hn.pattern_surv_hn import HancockContractBuilder
from trust_hn.pattern_surv_hn.v0_clinical_anchor import (
    DEFAULT_SPEC_RELATIVE,
    V0Spec,
    _development_arrays,
    _event_stratified_splits,
    assert_aggregate_only,
    evaluate_predictions,
    nested_cross_fit,
    structured_survival,
)


@pytest.fixture(scope="session")
def project_root() -> Path:
    return Path(__file__).resolve().parents[1]


@pytest.fixture(scope="session")
def contract(project_root: Path):
    return HancockContractBuilder(project_root).build()


def test_frozen_v0_spec_matches_approved_protocol(project_root: Path):
    spec = V0Spec.from_yaml(project_root / DEFAULT_SPEC_RELATIVE)
    assert spec.horizon_days == 730.5
    assert spec.outer_folds == 5
    assert spec.outer_repetition_seeds == (17, 29, 43, 71, 101)
    assert spec.inner_folds == 3
    assert spec.alpha_grid == (0.005, 0.01, 0.05, 0.1)
    assert spec.l1_ratio_grid == (0.1, 0.5, 0.9)
    assert len(spec.candidates) == 12


def test_development_estimand_and_official_test_sealing(contract):
    _, ids, event, time, patterns = _development_arrays(contract)
    assert len(ids) == 610
    assert int(event.sum()) == 173
    assert np.all(time > 0)
    assert len(patterns) == 610
    frame = contract.patient_frame().set_index("native_id")
    sealed_ids = set(frame.index[frame["official_partition"] == "test"])
    assert sealed_ids.isdisjoint(ids)
    assert frame.loc[list(sealed_ids), "duration_days"].isna().all()
    assert frame.loc[list(sealed_ids), "event"].isna().all()


def test_event_stratified_folds_are_deterministic_and_cover_once():
    event = np.asarray([True] * 20 + [False] * 40)
    first = _event_stratified_splits(event, n_splits=5, seed=17)
    second = _event_stratified_splits(event, n_splits=5, seed=17)
    seen: list[int] = []
    for (train_a, valid_a), (train_b, valid_b) in zip(first, second, strict=True):
        assert np.array_equal(train_a, train_b)
        assert np.array_equal(valid_a, valid_b)
        assert event[train_a].any() and (~event[train_a]).any()
        assert event[valid_a].any() and (~event[valid_a]).any()
        seen.extend(valid_a.tolist())
    assert sorted(seen) == list(range(len(event)))


def test_survival_metrics_return_finite_horizon_values():
    train_y = structured_survival(
        [True, False, True, False, True, False, True, False],
        [100, 900, 300, 1100, 500, 1300, 700, 1500],
    )
    eval_y = structured_survival(
        [True, False, True, False],
        [150, 1000, 600, 1400],
    )
    metrics = evaluate_predictions(
        train_y,
        eval_y,
        risk_score=[0.9, 0.2, 0.7, 0.1],
        risk_horizon=[0.8, 0.2, 0.6, 0.1],
        horizon=730.5,
    )
    assert 0 <= metrics["ipcw_brier_24m"] <= 1
    assert 0 <= metrics["harrell_c"] <= 1
    assert np.isfinite(metrics["calibration_in_the_large_24m"])
    assert np.isfinite(metrics["calibration_slope_24m"])


def test_aggregate_guard_rejects_patient_identifier_keys():
    assert_aggregate_only({"results": [{"n": 610, "events": 173}]})
    with pytest.raises(ValueError, match="patient identifier key"):
        assert_aggregate_only({"native_id": "forbidden"})


def test_reduced_nested_cross_fit_is_fold_pure_and_oof_complete(contract):
    spec = V0Spec(
        horizon_days=730.5,
        outer_folds=3,
        outer_repetition_seeds=(17,),
        inner_folds=2,
        alpha_grid=(0.01,),
        l1_ratio_grid=(0.5,),
        max_iter=100000,
        tolerance=1e-7,
        pattern_minimum_n=20,
        pattern_minimum_events=5,
    )
    oof, aggregate = nested_cross_fit(contract, spec)
    assert len(oof) == 610
    assert oof["native_id"].nunique() == 610
    assert oof["repetition_seed"].eq(17).all()
    assert oof["risk_24m"].between(0, 1).all()
    assert np.isfinite(oof[["risk_score", "risk_24m", "survival_24m"]]).all().all()
    assert len(aggregate["folds"]) == 3
    assert len(aggregate["per_seed_metrics"]) == 1
    assert (
        sum(row["outer_fold_count"] for row in aggregate["hyperparameter_selection_frequency"]) == 3
    )
    assert_aggregate_only(aggregate)
