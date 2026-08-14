from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path

import numpy as np
import pytest

from trust_hn.pattern_surv_hn.hancock_contract import (
    BLOOD_FEATURES,
    ICD_FEATURES,
    TMA_FEATURES,
    ModalityStatus,
)
from trust_hn.pattern_surv_hn.v1_deep_sets_smoke import (
    ClinicalResidualDeepSetsCox,
    ModalityBatch,
    V1SmokeSpec,
    negative_cox_partial_log_likelihood,
    run_structural_smoke,
)

ROOT = Path(__file__).resolve().parents[1]
SPEC_PATH = (
    ROOT
    / "research_studies/01_pattern_surv_hn/core_backbone/U1_3_V1_smoke/"
    "frozen_v1_smoke_spec.yaml"
)


@pytest.fixture(scope="module")
def spec() -> V1SmokeSpec:
    return V1SmokeSpec.from_yaml(SPEC_PATH)


@pytest.fixture(scope="module")
def model(spec: V1SmokeSpec) -> ClinicalResidualDeepSetsCox:
    return ClinicalResidualDeepSetsCox(spec)


def make_batch(
    spec: V1SmokeSpec,
    name: str,
    *,
    rows: int = 5,
    active: np.ndarray | None = None,
    status: str = ModalityStatus.USABLE_COMPLETE.value,
    quality: np.ndarray | None = None,
    seed: int = 4,
) -> ModalityBatch:
    rng = np.random.default_rng(seed + ("blood", "icd", "tma").index(name))
    content = rng.normal(size=(rows, spec.modality_input_dimensions[name]))
    mask = np.ones(rows, dtype=bool) if active is None else np.asarray(active, dtype=bool)
    content[~mask] = np.nan
    quality_values = (
        np.tile(np.asarray([0.0, 1.0]), (rows, 1))
        if quality is None
        else np.asarray(quality, dtype=float)
    )
    statuses = [status if value else ModalityStatus.ABSENT.value for value in mask]
    return ModalityBatch(name, content, mask, statuses, quality_values)


def test_frozen_dimensions_match_fold_preprocessed_contract(spec: V1SmokeSpec):
    assert spec.modality_input_dimensions == {
        "blood": 2 * len(BLOOD_FEATURES),
        "icd": 2 * len(ICD_FEATURES),
        "tma": 2 * len(TMA_FEATURES),
    }


def test_forward_is_permutation_invariant_and_accepts_arbitrary_subsets(
    spec: V1SmokeSpec, model: ClinicalResidualDeepSetsCox
):
    clinical = np.linspace(-0.5, 0.5, 5)
    batches = tuple(make_batch(spec, name) for name in ("blood", "icd", "tma"))
    canonical = model.forward(clinical, batches)
    permuted = model.forward(clinical, (batches[2], batches[0], batches[1]))
    subset = model.forward(clinical, (batches[0], batches[2]))
    np.testing.assert_allclose(canonical.fused_score, permuted.fused_score, atol=1e-12)
    assert np.isfinite(subset.fused_score).all()
    assert np.array_equal(subset.active_token_count, np.full(5, 2))


def test_clinical_only_fallback_is_exact_even_with_nan_placeholders(
    spec: V1SmokeSpec, model: ClinicalResidualDeepSetsCox
):
    clinical = np.asarray([-1.0, 0.0, 1.0])
    batches = []
    for name in ("blood", "icd", "tma"):
        rows = clinical.size
        batches.append(
            ModalityBatch(
                name=name,
                content=np.full((rows, spec.modality_input_dimensions[name]), np.nan),
                active=np.zeros(rows, dtype=bool),
                status=[ModalityStatus.ABSENT.value] * rows,
                quality=np.tile(np.asarray([1.0, 0.0]), (rows, 1)),
            )
        )
    result = model.forward(clinical, batches)
    np.testing.assert_array_equal(result.residual_score, np.zeros(clinical.size))
    np.testing.assert_array_equal(result.fused_score, clinical)
    np.testing.assert_array_equal(result.active_token_count, np.zeros(clinical.size, dtype=int))


def test_active_nonfinite_content_is_rejected(spec: V1SmokeSpec, model):
    batch = make_batch(spec, "blood", rows=3)
    broken = batch.content.copy()
    broken[0, 0] = np.nan
    with pytest.raises(ValueError, match="active modality content must be finite"):
        model.forward(
            np.zeros(3),
            [replace(batch, content=broken)],
        )


def test_identity_status_and_quality_encodings_are_operational(spec: V1SmokeSpec, model):
    assert np.linalg.norm(model.identity_embeddings[0] - model.identity_embeddings[1]) > 0
    clinical = np.zeros(5)
    base = make_batch(spec, "blood")
    base_result = model.forward(clinical, [base])

    changed_status = replace(
        base,
        status=[ModalityStatus.USABLE_PARTIAL.value] * 5,
    )
    status_result = model.forward(clinical, [changed_status])
    assert np.max(np.abs(base_result.fused_score - status_result.fused_score)) > 0

    changed_quality = replace(
        base,
        quality=np.tile(np.asarray([0.75, 0.25]), (5, 1)),
    )
    quality_result = model.forward(clinical, [changed_quality])
    assert np.max(np.abs(base_result.fused_score - quality_result.fused_score)) > 0


def test_inactive_rows_do_not_use_content_placeholders(spec: V1SmokeSpec, model):
    mask = np.asarray([True, False, True, False, True])
    base = make_batch(spec, "tma", active=mask)
    changed = base.content.copy()
    changed[~mask] = 1e12
    first = model.forward(np.zeros(5), [base])
    second = model.forward(np.zeros(5), [replace(base, content=changed)])
    np.testing.assert_array_equal(first.fused_score, second.fused_score)


def test_duplicate_or_unknown_modalities_are_rejected(spec: V1SmokeSpec, model):
    blood = make_batch(spec, "blood")
    with pytest.raises(ValueError, match="at most once"):
        model.forward(np.zeros(5), [blood, blood])
    with pytest.raises(ValueError, match="unknown modality"):
        model.forward(np.zeros(5), [replace(blood, name="unknown")])


def test_cox_partial_likelihood_is_finite_and_shift_invariant():
    duration = np.asarray([2.0, 4.0, 5.0, 8.0, 10.0])
    event = np.asarray([1, 0, 1, 1, 0])
    score = np.asarray([0.7, -0.2, 0.4, -0.1, -0.5])
    loss = negative_cox_partial_log_likelihood(duration, event, score)
    shifted = negative_cox_partial_log_likelihood(duration, event, score + 19.0)
    assert np.isfinite(loss)
    assert shifted == pytest.approx(loss, abs=1e-12)


def test_aggregate_smoke_audit_passes_without_patient_identifiers(spec: V1SmokeSpec):
    result = run_structural_smoke(spec)
    assert result["all_checks_pass"] is True
    assert result["model_training_performed"] is False
    assert result["patient_level_data_used"] is False
    assert result["official_test_accessed"] is False
    assert result["external_data_accessed"] is False
    assert result["formal_development_cv_performed"] is False
    text = json.dumps(result).lower()
    for key in ("native_id", "patient_id", "case_id", "submitter_id"):
        assert key not in text
    assert result["parameter_count"] <= spec.maximum_parameter_count
