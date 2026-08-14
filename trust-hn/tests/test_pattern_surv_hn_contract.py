"""Tests for the PATTERN-Surv-HN U1.1 postoperative HANCOCK contract."""

from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from trust_hn.data.contracts import DataContractError
from trust_hn.pattern_surv_hn.hancock_contract import (
    ANCHOR_FEATURES,
    BLOOD_FEATURES,
    ICD_FEATURES,
    PROHIBITED_PREDICTORS,
    TMA_FEATURES,
    FoldBoundBlockPreprocessor,
    FoldBoundMixedPreprocessor,
    HancockContractBuilder,
    ModalityStatus,
    derive_postoperative_endpoint,
    validate_hancock_contract,
)


@pytest.fixture(scope="module")
def project_root() -> Path:
    return Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def contract(project_root: Path):
    return HancockContractBuilder(project_root).build()


def test_endpoint_is_postoperative_and_binary():
    duration, event = derive_postoperative_endpoint(1_000, 25, "deceased")
    assert duration == 975.0
    assert event == 1
    assert derive_postoperative_endpoint(500, 20, "living") == (480.0, 0)


def test_contract_population_split_and_sealing(contract):
    report = validate_hancock_contract(contract)
    assert report.records == 763
    assert report.eligible == 762
    assert report.excluded == 1
    assert report.sealed == 152
    frame = contract.patient_frame()
    assert frame["native_id"].is_unique
    split_counts = frame["split_role"].value_counts().to_dict()
    assert split_counts == {"train": 489, "sealed_test": 152, "calibration": 122}
    sealed = frame[frame["split_role"] == "sealed_test"]
    assert sealed["outcome_sealed"].all()
    assert sealed["duration_days"].isna().all()
    assert sealed["event"].isna().all()
    development = frame[frame["split_role"].isin(["train", "calibration"])]
    assert development["duration_days"].notna().all()
    assert development["event"].notna().all()
    excluded = development[~development["eligible"]]
    assert len(excluded) == 1
    assert excluded["exclusion_reason"].eq("nonpositive_postoperative_duration").all()



def test_aggregate_summary_does_not_encode_sealed_events_as_zero(contract):
    summary = contract.aggregate_summary()
    sealed_split = next(
        row for row in summary["split_counts"] if row["split_role"] == "sealed_test"
    )
    assert sealed_split["outcomes_sealed"] == 152
    assert sealed_split["events_exposed"] is None
    sealed_patterns = [
        row
        for row in summary["acquisition_patterns"]
        if row["split_role"] == "sealed_test"
    ]
    assert sealed_patterns == [
        {
            "split_role": "sealed_test",
            "pattern": "111",
            "n": 152,
            "eligible": 152,
            "events_exposed": None,
            "outcomes_sealed": 152,
        }
    ]

def test_anchor_boundary_and_no_post_prediction_predictors(contract):
    assert tuple(contract.anchor.columns) == ANCHOR_FEATURES
    assert not (set(contract.anchor.columns) & PROHIBITED_PREDICTORS)
    assert not (set(contract.blood.columns) & PROHIBITED_PREDICTORS)
    assert not (set(contract.icd.columns) & PROHIBITED_PREDICTORS)
    assert not (set(contract.tma.columns) & PROHIBITED_PREDICTORS)
    assert "primarily_metastasis" not in contract.anchor.columns
    assert "adjuvant_radiotherapy" not in contract.anchor.columns
    assert set(contract.anchor["grading"].dropna().unique()) == {"G1", "G2", "G3", "HPV_OSCC"}


def test_independent_modalities_and_quality_states(contract):
    frame = contract.patient_frame()
    assert tuple(contract.blood.columns) == BLOOD_FEATURES
    assert tuple(contract.icd.columns) == ICD_FEATURES
    assert tuple(contract.tma.columns) == TMA_FEATURES
    assert int(frame["blood_acquired"].sum()) == 693
    assert int(frame["blood_usable"].sum()) == 683
    assert int(frame["icd_acquired"].sum()) == 712
    assert int(frame["icd_usable"].sum()) == 712
    assert int(frame["tma_acquired"].sum()) == 736
    assert int(frame["tma_usable"].sum()) == 736
    assert int(frame["blood_status"].eq(ModalityStatus.ACQUIRED_UNUSABLE.value).sum()) == 10
    assert int(frame["blood_status"].eq(ModalityStatus.USABLE_PARTIAL.value).sum()) == 79
    assert int(frame["tma_status"].eq(ModalityStatus.USABLE_PARTIAL.value).sum()) == 97
    assert frame.loc[frame["icd_usable"], "icd_status"].eq(
        ModalityStatus.CONDITIONAL_PROVENANCE.value
    ).all()


def test_blood_reconstruction_is_raw_timed_and_not_cohort_imputed(contract):
    assert contract.blood_timing["min"].ge(0).all()
    assert contract.blood_timing["max"].le(14).all()
    assert len(contract.blood_timing) == 693
    assert len(contract.blood) == 684
    assert int(contract.blood.isna().all(axis=1).sum()) == 1
    assert int(contract.blood.isna().sum().sum()) == 284
    assert int(contract.blood.notna().all(axis=1).sum()) == 604


def test_tma_absence_is_distinct_from_internal_missingness(contract):
    frame = contract.patient_frame()
    absent = frame[~frame["tma_acquired"]]
    partial = frame[frame["tma_status"] == ModalityStatus.USABLE_PARTIAL.value]
    assert len(absent) == 27
    assert len(partial) == 97
    assert partial["tma_usable"].all()
    assert partial["tma_missing_fraction"].gt(0).all()


def test_acquisition_patterns_preserve_u0_counts(contract):
    frame = contract.patient_frame()
    counts = frame.groupby("acquisition_pattern").size().to_dict()
    assert counts == {"001": 7, "010": 4, "011": 59, "100": 1, "101": 43, "110": 22, "111": 627}
    sealed = frame[frame["split_role"] == "sealed_test"]
    assert sealed["acquisition_pattern"].eq("111").all()
    assert sealed["usable_pattern"].eq("111").all()


def test_fold_bound_preprocessor_rejects_nontraining_fit_ids(contract):
    frame = contract.patient_frame().set_index("native_id")
    training_ids = frame.index[frame["split_role"] == "train"].tolist()
    calibration_ids = frame.index[frame["split_role"] == "calibration"].tolist()
    allowed = set(training_ids)
    prep = FoldBoundBlockPreprocessor(
        BLOOD_FEATURES,
        allowed_fit_ids=allowed,
    )
    fit_ids = [native_id for native_id in training_ids if native_id in contract.blood.index]
    transformed = prep.fit_transform(contract.blood, fit_ids)
    assert transformed.values.shape == (len(fit_ids), 2 * len(BLOOD_FEATURES))
    assert np.isfinite(transformed.values).all()
    with pytest.raises(DataContractError, match="non-training IDs"):
        prep.fit(contract.blood, [fit_ids[0], calibration_ids[0]])


def test_preprocessor_statistics_ignore_nontraining_rows():
    frame = pd.DataFrame({"x": [1.0, 3.0, 1000.0]}, index=["train_a", "train_b", "held"])
    prep = FoldBoundBlockPreprocessor(["x"], allowed_fit_ids={"train_a", "train_b"})
    prep.fit(frame, ["train_a", "train_b"])
    assert prep.medians_ is not None
    assert prep.medians_["x"] == 2.0
    held = prep.transform(frame, ["held"])
    assert held.values[0, 0] > 100


def test_patient_frame_without_identifiers_is_aggregate_safe(contract):
    public = contract.patient_frame(include_identifiers=False)
    assert "native_id" not in public.columns
    assert len(public) == 763



def test_mixed_anchor_preprocessor_is_fold_bound(contract):
    frame = contract.patient_frame().set_index("native_id")
    training_ids = frame.index[frame["split_role"] == "train"].tolist()
    calibration_ids = frame.index[frame["split_role"] == "calibration"].tolist()
    prep = FoldBoundMixedPreprocessor(
        numeric=["age_at_initial_diagnosis"],
        categorical=[column for column in ANCHOR_FEATURES if column != "age_at_initial_diagnosis"],
        allowed_fit_ids=set(training_ids),
    )
    transformed = prep.fit_transform(contract.anchor, training_ids)
    assert transformed.values.shape[0] == len(training_ids)
    assert transformed.missing_indicators.shape == (len(training_ids), len(ANCHOR_FEATURES))
    assert np.isfinite(transformed.values).all()
    with pytest.raises(DataContractError, match="non-training IDs"):
        prep.fit(contract.anchor, [training_ids[0], calibration_ids[0]])
